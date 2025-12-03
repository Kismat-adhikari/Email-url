#!/usr/bin/env python3
"""
Email Validator - Unified High-Performance System
Automatically chooses the best processing strategy based on input size.
Designed for both CLI and programmatic use (Flask-ready).

Usage: 
    CLI: python emailvalidator_unified.py <filepath> [options]
    API: from emailvalidator_unified import validate_email, validate_batch
"""

import sys
import re
import argparse
from typing import List, Tuple, Optional, Dict, Any, Union
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import socket
from difflib import SequenceMatcher

# Optional DNS checking - gracefully handle if not installed
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    print("Warning: dnspython not installed. DNS/MX checks will be disabled.", file=sys.stderr)
    print("Install with: pip install dnspython", file=sys.stderr)


# ============================================================================
# CORE VALIDATION LOGIC - RFC 5321 COMPLIANT
# ============================================================================

# Compile regex patterns once for efficiency
LOCAL_PART_PATTERN = re.compile(r'^[a-zA-Z0-9._+\-]+$')
DOMAIN_LABEL_PATTERN = re.compile(r'^[a-zA-Z0-9\-]+$')

# Constants for validation limits (RFC 5321)
MAX_EMAIL_LENGTH = 254
MAX_LOCAL_LENGTH = 64
MAX_DOMAIN_LENGTH = 253
MAX_LABEL_LENGTH = 63
MIN_TLD_LENGTH = 2

# Performance thresholds for automatic mode selection
THRESHOLD_PARALLEL = 50000  # Use parallel processing above this
THRESHOLD_STREAMING = 100000  # Use streaming above this

# Advanced validation datasets
DISPOSABLE_DOMAINS = {
    'tempmail.com', 'guerrillamail.com', '10minutemail.com', 'mailinator.com',
    'throwaway.email', 'temp-mail.org', 'fakeinbox.com', 'trashmail.com',
    'yopmail.com', 'maildrop.cc', 'getnada.com', 'sharklasers.com',
    'guerrillamail.info', 'grr.la', 'guerrillamail.biz', 'guerrillamail.de',
    'spam4.me', 'mailnesia.com', 'tempinbox.com', 'dispostable.com'
}

COMMON_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com',
    'aol.com', 'protonmail.com', 'mail.com', 'zoho.com', 'gmx.com',
    'yandex.com', 'live.com', 'msn.com', 'me.com', 'mac.com',
    'yahoo.co.uk', 'googlemail.com', 'hotmail.co.uk', 'outlook.co.uk'
}

ROLE_BASED_PREFIXES = {
    'admin', 'info', 'support', 'sales', 'contact', 'help', 'noreply',
    'postmaster', 'webmaster', 'hostmaster', 'abuse', 'security',
    'marketing', 'billing', 'service', 'feedback', 'enquiry', 'inquiry'
}

# Typo detection threshold (0.0 to 1.0)
TYPO_SIMILARITY_THRESHOLD = 0.85


def validate_email(email: str, detailed: bool = False) -> Union[bool, Dict[str, Any]]:
    """
    Validate a single email address (optimized single-pass algorithm).
    
    This is the main validation function - use this in your Flask API.
    
    Args:
        email: Email address to validate
        detailed: If True, return detailed validation info (for API responses)
    
    Returns:
        bool: True if valid, False if invalid (when detailed=False)
        dict: Detailed validation result (when detailed=True)
    
    Examples:
        >>> validate_email("user@example.com")
        True
        
        >>> validate_email("invalid@", detailed=True)
        {'valid': False, 'email': 'invalid@', 'reason': 'Invalid domain part'}
    """
    original_email = email
    email = email.strip()
    
    # Fast format validation
    if not email or len(email) > MAX_EMAIL_LENGTH:
        return _return_result(False, original_email, "Email too long or empty", detailed)
    
    # Single-pass check for space and @ count
    at_count = 0
    at_pos = -1
    for i, char in enumerate(email):
        if char == ' ':
            return _return_result(False, original_email, "Contains spaces", detailed)
        if char == '@':
            at_count += 1
            at_pos = i
    
    if at_count != 1:
        reason = "Missing @ symbol" if at_count == 0 else "Multiple @ symbols"
        return _return_result(False, original_email, reason, detailed)
    
    local = email[:at_pos]
    domain = email[at_pos + 1:]
    
    # Validate local part
    if not _is_valid_local_part(local):
        return _return_result(False, original_email, "Invalid local part", detailed)
    
    # Validate domain part
    if not _is_valid_domain_part(domain):
        return _return_result(False, original_email, "Invalid domain part", detailed)
    
    return _return_result(True, original_email, "Valid email", detailed)


def _return_result(valid: bool, email: str, reason: str, detailed: bool) -> Union[bool, Dict[str, Any]]:
    """Helper to return appropriate result format."""
    if detailed:
        return {
            'valid': valid,
            'email': email,
            'reason': reason
        }
    return valid


def _is_valid_local_part(local: str) -> bool:
    """Validate the local part (before @) of the email."""
    if not local or len(local) > MAX_LOCAL_LENGTH:
        return False
    
    if local[0] == '.' or local[-1] == '.':
        return False
    
    # Check for consecutive dots
    prev_char = ''
    for char in local:
        if char == '.' and prev_char == '.':
            return False
        prev_char = char
    
    return LOCAL_PART_PATTERN.match(local) is not None


def _is_valid_domain_part(domain: str) -> bool:
    """Validate the domain part (after @) of the email."""
    if not domain or len(domain) > MAX_DOMAIN_LENGTH:
        return False
    
    if '.' not in domain or '..' in domain:
        return False
    
    labels = domain.split('.')
    
    # Validate each label
    for label in labels:
        if not _is_valid_domain_label(label):
            return False
    
    # Check TLD length
    return len(labels[-1]) >= MIN_TLD_LENGTH


def _is_valid_domain_label(label: str) -> bool:
    """Validate a single domain label."""
    if not label or len(label) > MAX_LABEL_LENGTH:
        return False
    
    if label[0] == '-' or label[-1] == '-':
        return False
    
    return DOMAIN_LABEL_PATTERN.match(label) is not None


# ============================================================================
# ADVANCED VALIDATION HELPERS
# ============================================================================

def _check_dns_and_mx(domain: str) -> Tuple[bool, bool]:
    """
    Check if domain has valid DNS records and MX records.
    
    Args:
        domain: Domain name to check
    
    Returns:
        Tuple of (dns_valid, mx_valid) as booleans
    
    Note:
        Gracefully handles all exceptions - never crashes on network errors
    """
    dns_valid = False
    mx_valid = False
    
    # Check DNS resolution
    try:
        socket.gethostbyname(domain)
        dns_valid = True
    except (socket.gaierror, socket.herror, socket.timeout, OSError):
        dns_valid = False
    except Exception:
        # Catch any other unexpected errors
        dns_valid = False
    
    # Check MX records (only if DNS library is available)
    if DNS_AVAILABLE:
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_valid = len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            mx_valid = False
        except dns.exception.Timeout:
            mx_valid = False
        except Exception:
            # Catch any other DNS-related errors
            mx_valid = False
    
    return dns_valid, mx_valid


def _is_disposable_email(domain: str) -> bool:
    """
    Check if domain is a known disposable email provider.
    
    Args:
        domain: Domain name to check
    
    Returns:
        bool: True if domain is disposable, False otherwise
    
    Example:
        >>> _is_disposable_email("tempmail.com")
        True
        >>> _is_disposable_email("gmail.com")
        False
    """
    return domain.lower() in DISPOSABLE_DOMAINS


def _is_role_based_email(local_part: str) -> bool:
    """
    Check if local part is a role-based email address.
    
    Args:
        local_part: Local part of email (before @)
    
    Returns:
        bool: True if role-based, False otherwise
    
    Example:
        >>> _is_role_based_email("info")
        True
        >>> _is_role_based_email("john.doe")
        False
    """
    return local_part.lower() in ROLE_BASED_PREFIXES


def _suggest_domain_correction(domain: str) -> Optional[str]:
    """
    Suggest domain correction if typo is detected.
    
    Uses fuzzy matching to find similar domains from COMMON_DOMAINS.
    
    Args:
        domain: Domain name to check for typos
    
    Returns:
        str: Suggested domain if typo detected, None otherwise
    
    Example:
        >>> _suggest_domain_correction("gmial.com")
        'gmail.com'
        >>> _suggest_domain_correction("gmail.com")
        None
    """
    domain_lower = domain.lower()
    
    # Don't suggest if domain is already in common domains
    if domain_lower in COMMON_DOMAINS:
        return None
    
    best_match = None
    best_ratio = 0.0
    
    for common_domain in COMMON_DOMAINS:
        ratio = SequenceMatcher(None, domain_lower, common_domain).ratio()
        if ratio > best_ratio and ratio >= TYPO_SIMILARITY_THRESHOLD:
            best_ratio = ratio
            best_match = common_domain
    
    return best_match


def _calculate_confidence_score(checks: Dict[str, bool]) -> int:
    """
    Calculate confidence score based on validation checks.
    
    Scoring:
        - Valid syntax: 40 points (base)
        - DNS valid: +20 points
        - MX records exist: +20 points
        - NOT disposable: +10 points
        - NOT role-based: +10 points
    
    Args:
        checks: Dictionary of check results
    
    Returns:
        int: Confidence score from 0 to 100
    
    Example:
        >>> checks = {'syntax': True, 'dns_valid': True, 'mx_records': True, 
        ...           'is_disposable': False, 'is_role_based': False}
        >>> _calculate_confidence_score(checks)
        100
    """
    score = 0
    
    # Base syntax check (40 points)
    if checks.get('syntax', False):
        score += 40
    
    # DNS validation (20 points)
    if checks.get('dns_valid', False):
        score += 20
    
    # MX records (20 points)
    if checks.get('mx_records', False):
        score += 20
    
    # Not disposable (10 points)
    if not checks.get('is_disposable', True):
        score += 10
    
    # Not role-based (10 points)
    if not checks.get('is_role_based', True):
        score += 10
    
    return min(score, 100)  # Cap at 100


# ============================================================================
# ADVANCED VALIDATION - WITH DNS, MX, DISPOSABLE, TYPO DETECTION
# ============================================================================

def validate_email_advanced(
    email: str,
    check_dns: bool = True,
    check_mx: bool = True,
    check_disposable: bool = True,
    check_typos: bool = True,
    check_role_based: bool = True
) -> Dict[str, Any]:
    """
    Advanced email validation with DNS, MX, disposable, and typo detection.
    
    This function performs comprehensive validation including:
    - Syntax validation (RFC 5321)
    - DNS record checking
    - MX record verification
    - Disposable email detection
    - Role-based email detection
    - Typo suggestion for common domains
    - Confidence scoring
    
    Args:
        email: Email address to validate
        check_dns: Check if domain has valid DNS records (default: True)
        check_mx: Check if domain has MX records (default: True)
        check_disposable: Check if domain is disposable (default: True)
        check_typos: Suggest corrections for typos (default: True)
        check_role_based: Check if email is role-based (default: True)
    
    Returns:
        Dictionary with:
            - valid: bool - Overall validity
            - email: str - Original email
            - checks: dict - Individual check results
            - confidence_score: int - Score from 0-100
            - suggestion: str or None - Domain suggestion if typo detected
            - reason: str - Explanation of result
    
    Examples:
        >>> result = validate_email_advanced("user@gmail.com")
        >>> result['valid']
        True
        >>> result['confidence_score']
        100
        
        >>> result = validate_email_advanced("user@gmial.com")
        >>> result['suggestion']
        'gmail.com'
        
        >>> result = validate_email_advanced("test@tempmail.com")
        >>> result['checks']['is_disposable']
        True
        
        >>> result = validate_email_advanced("info@company.com")
        >>> result['checks']['is_role_based']
        True
    """
    original_email = email
    email = email.strip()
    
    # Initialize result structure
    result = {
        'valid': False,
        'email': original_email,
        'checks': {
            'syntax': False,
            'dns_valid': False,
            'mx_records': False,
            'is_disposable': False,
            'is_role_based': False
        },
        'confidence_score': 0,
        'suggestion': None,
        'reason': ''
    }
    
    # Step 1: Syntax validation (using existing function)
    syntax_valid = validate_email(email)
    result['checks']['syntax'] = syntax_valid
    
    if not syntax_valid:
        result['reason'] = 'Invalid email syntax'
        result['confidence_score'] = 0
        return result
    
    # Extract local and domain parts
    try:
        at_pos = email.index('@')
        local_part = email[:at_pos]
        domain = email[at_pos + 1:]
    except (ValueError, IndexError):
        result['reason'] = 'Invalid email format'
        result['confidence_score'] = 0
        return result
    
    # Step 2: Disposable email check
    if check_disposable:
        result['checks']['is_disposable'] = _is_disposable_email(domain)
    
    # Step 3: Role-based email check
    if check_role_based:
        result['checks']['is_role_based'] = _is_role_based_email(local_part)
    
    # Step 4: DNS and MX checks
    dns_valid = False
    mx_valid = False
    
    if check_dns or check_mx:
        dns_valid, mx_valid = _check_dns_and_mx(domain)
        result['checks']['dns_valid'] = dns_valid
        result['checks']['mx_records'] = mx_valid
    else:
        # If checks disabled, assume valid for scoring purposes
        result['checks']['dns_valid'] = True
        result['checks']['mx_records'] = True
    
    # Step 5: Typo suggestion (only if DNS check failed)
    if check_typos and check_dns and not dns_valid:
        suggestion = _suggest_domain_correction(domain)
        if suggestion:
            result['suggestion'] = suggestion
    
    # Step 6: Calculate confidence score
    result['confidence_score'] = _calculate_confidence_score(result['checks'])
    
    # Step 7: Determine overall validity
    # Email is valid if syntax passes AND (DNS disabled OR DNS valid)
    if check_dns:
        result['valid'] = syntax_valid and dns_valid
    else:
        result['valid'] = syntax_valid
    
    # Step 8: Build reason string
    reasons = []
    
    if result['valid']:
        reasons.append('Valid email')
        
        # Add warnings
        if result['checks']['is_disposable']:
            reasons.append('Warning: Disposable email domain')
        if result['checks']['is_role_based']:
            reasons.append('Warning: Role-based email address')
        if check_mx and not result['checks']['mx_records']:
            reasons.append('Warning: No MX records found')
    else:
        if not syntax_valid:
            reasons.append('Invalid syntax')
        elif check_dns and not dns_valid:
            reasons.append('Domain does not exist')
            if result['suggestion']:
                reasons.append(f"Did you mean {result['suggestion']}?")
    
    result['reason'] = '; '.join(reasons) if reasons else 'Unknown'
    
    return result


# ============================================================================
# BATCH VALIDATION - FOR FLASK API
# ============================================================================

def validate_batch(
    emails: List[str], 
    detailed: bool = False,
    advanced: bool = False,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Validate multiple emails efficiently (Flask-ready).
    
    Automatically chooses the best processing strategy based on batch size.
    
    Args:
        emails: List of email addresses to validate
        detailed: Include detailed validation info for each email (basic mode)
        advanced: Use advanced validation with DNS/MX checks (default: False)
        **kwargs: Additional options for advanced mode:
            - check_dns: bool (default: True)
            - check_mx: bool (default: True)
            - check_disposable: bool (default: True)
            - check_typos: bool (default: True)
            - check_role_based: bool (default: True)
    
    Returns:
        List of validation results
    
    Examples:
        >>> # Basic validation
        >>> emails = ["user@example.com", "invalid@", "test@test.com"]
        >>> results = validate_batch(emails)
        >>> results
        [
            {'email': 'user@example.com', 'valid': True},
            {'email': 'invalid@', 'valid': False},
            {'email': 'test@test.com', 'valid': True}
        ]
        
        >>> # Advanced validation
        >>> results = validate_batch(emails, advanced=True)
        >>> results[0]['confidence_score']
        100
        >>> results[0]['checks']
        {'syntax': True, 'dns_valid': True, 'mx_records': True, ...}
    """
    # Input validation
    if not isinstance(emails, list):
        raise TypeError("emails must be a list")
    
    if len(emails) == 0:
        return []
    
    count = len(emails)
    
    # Choose strategy based on size
    if count < THRESHOLD_PARALLEL:
        # Sequential processing for small batches
        results = []
        for email in emails:
            if advanced:
                # Use advanced validation
                result = validate_email_advanced(email, **kwargs)
            else:
                # Use basic validation
                result = {'email': email, 'valid': validate_email(email)}
                if detailed:
                    detailed_result = validate_email(email, detailed=True)
                    if isinstance(detailed_result, dict):
                        result.update(detailed_result)
            results.append(result)
        return results
    else:
        # Parallel processing for large batches
        return _validate_parallel(emails, detailed, advanced, kwargs)


def _validate_parallel(
    emails: List[str], 
    detailed: bool,
    advanced: bool,
    kwargs: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Parallel validation for large batches."""
    workers = min(multiprocessing.cpu_count(), 8)  # Cap at 8 workers
    chunk_size = max(1, len(emails) // (workers * 4))
    chunks = [emails[i:i + chunk_size] for i in range(0, len(emails), chunk_size)]
    
    results = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_validate_chunk, chunk, detailed, advanced, kwargs): chunk 
            for chunk in chunks
        }
        for future in as_completed(futures):
            results.extend(future.result())
    
    return results


def _validate_chunk(
    emails: List[str], 
    detailed: bool,
    advanced: bool,
    kwargs: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Worker function for parallel processing."""
    results = []
    for email in emails:
        if advanced:
            # Use advanced validation
            result = validate_email_advanced(email, **kwargs)
        else:
            # Use basic validation
            result = {'email': email, 'valid': validate_email(email)}
            if detailed:
                detailed_result = validate_email(email, detailed=True)
                if isinstance(detailed_result, dict):
                    result.update(detailed_result)
        results.append(result)
    return results


# ============================================================================
# FILE PROCESSING - FOR CLI
# ============================================================================

def validate_file(
    filepath: str,
    mode: str = 'auto',
    quiet: bool = False,
    show_progress: bool = False
) -> Dict[str, Any]:
    """
    Validate emails from a file with automatic optimization.
    
    Args:
        filepath: Path to file containing emails (one per line)
        mode: 'auto', 'stream', 'batch', or 'parallel'
        quiet: Only return summary (don't print individual results)
        show_progress: Show progress updates
    
    Returns:
        Dictionary with validation results and statistics
    """
    try:
        # Determine file size and choose strategy
        if mode == 'auto':
            mode = _choose_processing_mode(filepath)
        
        if show_progress:
            print(f"Processing mode: {mode}", file=sys.stderr)
        
        # Process based on chosen mode
        if mode == 'stream':
            return _process_streaming(filepath, quiet, show_progress)
        elif mode == 'parallel':
            return _process_parallel_file(filepath, quiet, show_progress)
        else:  # batch
            return _process_batch_file(filepath, quiet, show_progress)
            
    except FileNotFoundError:
        print(f"ERROR: File '{filepath}' does not exist.")
        sys.exit(1)
    except PermissionError:
        print(f"ERROR: Permission denied reading file '{filepath}'.")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"ERROR: File '{filepath}' contains invalid characters.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read file '{filepath}'.")
        print(f"Reason: {e}")
        sys.exit(1)


def _choose_processing_mode(filepath: str) -> str:
    """Automatically choose the best processing mode based on file size."""
    try:
        import os
        file_size = os.path.getsize(filepath)
        
        # Estimate number of emails (avg 50 bytes per email)
        estimated_emails = file_size // 50
        
        if estimated_emails > THRESHOLD_STREAMING:
            return 'stream'
        elif estimated_emails > THRESHOLD_PARALLEL:
            return 'parallel'
        else:
            return 'batch'
    except:
        return 'batch'  # Default to batch if can't determine


def _process_batch_file(filepath: str, quiet: bool, show_progress: bool) -> Dict[str, Any]:
    """Batch processing with optimized output."""
    with open(filepath, 'r', encoding='utf-8') as f:
        emails = [line.strip() for line in f if line.strip()]
    
    if not emails:
        print(f"ERROR: File '{filepath}' contains zero emails.")
        sys.exit(1)
    
    output_buffer = []
    valid_count = 0
    invalid_count = 0
    
    for i, email in enumerate(emails, 1):
        is_valid = validate_email(email)
        
        if is_valid:
            valid_count += 1
            if not quiet:
                output_buffer.append(f"VALID: {email}")
        else:
            invalid_count += 1
            if not quiet:
                output_buffer.append(f"INVALID: {email}")
        
        if show_progress and i % 10000 == 0:
            print(f"Progress: {i}/{len(emails)} ({i*100//len(emails)}%)", file=sys.stderr)
    
    # Single print operation
    if output_buffer:
        print('\n'.join(output_buffer))
    
    return {
        'total': len(emails),
        'valid': valid_count,
        'invalid': invalid_count,
        'mode': 'batch'
    }


def _process_streaming(filepath: str, quiet: bool, show_progress: bool) -> Dict[str, Any]:
    """Streaming processing for constant memory usage."""
    valid_count = 0
    invalid_count = 0
    total = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            email = line.strip()
            if not email:
                continue
            
            total += 1
            is_valid = validate_email(email)
            
            if is_valid:
                valid_count += 1
                if not quiet:
                    print(f"VALID: {email}")
            else:
                invalid_count += 1
                if not quiet:
                    print(f"INVALID: {email}")
            
            if show_progress and total % 10000 == 0:
                print(f"Progress: {total} emails processed...", file=sys.stderr)
    
    if total == 0:
        print(f"ERROR: File '{filepath}' contains zero emails.")
        sys.exit(1)
    
    return {
        'total': total,
        'valid': valid_count,
        'invalid': invalid_count,
        'mode': 'stream'
    }


def _process_parallel_file(filepath: str, quiet: bool, show_progress: bool) -> Dict[str, Any]:
    """Parallel processing for maximum speed."""
    with open(filepath, 'r', encoding='utf-8') as f:
        emails = [line.strip() for line in f if line.strip()]
    
    if not emails:
        print(f"ERROR: File '{filepath}' contains zero emails.")
        sys.exit(1)
    
    workers = min(multiprocessing.cpu_count(), 8)
    chunk_size = max(1, len(emails) // (workers * 4))
    chunks = [emails[i:i + chunk_size] for i in range(0, len(emails), chunk_size)]
    
    if show_progress:
        print(f"Processing {len(emails)} emails using {workers} workers...", file=sys.stderr)
    
    all_results = []
    completed_chunks = 0
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_validate_chunk_simple, chunk): chunk for chunk in chunks}
        
        for future in as_completed(futures):
            results = future.result()
            all_results.extend(results)
            completed_chunks += 1
            
            if show_progress:
                progress = (completed_chunks / len(chunks)) * 100
                print(f"Progress: {progress:.1f}% ({len(all_results)}/{len(emails)} emails)", 
                    file=sys.stderr)
    
    # Count and print results
    valid_count = sum(1 for r in all_results if r['valid'])
    invalid_count = len(all_results) - valid_count
    
    if not quiet:
        output_buffer = []
        for result in all_results:
            status = "VALID" if result['valid'] else "INVALID"
            output_buffer.append(f"{status}: {result['email']}")
        print('\n'.join(output_buffer))
    
    return {
        'total': len(emails),
        'valid': valid_count,
        'invalid': invalid_count,
        'mode': 'parallel',
        'workers': workers
    }


def _validate_chunk_simple(emails: List[str]) -> List[Dict[str, bool]]:
    """Simple worker function for file processing."""
    return [{'email': email, 'valid': validate_email(email)} for email in emails]


# ============================================================================
# CLI INTERFACE
# ============================================================================

def print_summary(stats: Dict[str, Any], elapsed_time: Optional[float] = None) -> None:
    """Print summary statistics."""
    print()
    print("=" * 50)
    print(f"Total processed: {stats['total']}")
    print(f"Total valid: {stats['valid']}")
    print(f"Total invalid: {stats['invalid']}")
    print(f"Processing mode: {stats['mode']}")
    if 'workers' in stats:
        print(f"Workers used: {stats['workers']}")
    if elapsed_time is not None:
        print(f"Processing time: {elapsed_time:.3f} seconds")
        if stats['total'] > 0:
            print(f"Throughput: {int(stats['total'] / elapsed_time)} emails/second")
    print("=" * 50)


def main() -> None:
    """Main CLI entry point."""
    args = _parse_command_line_args()
    
    start_time = time.time()
    
    stats = validate_file(
        args.filepath,
        mode=args.mode,
        quiet=args.quiet,
        show_progress=args.progress
    )
    
    elapsed_time = time.time() - start_time
    
    print_summary(stats, elapsed_time if args.benchmark else None)


def _parse_command_line_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Unified high-performance email validator with automatic optimization.',
        epilog='Example: python emailvalidator_unified.py emails.txt --benchmark'
    )
    parser.add_argument(
        'filepath',
        help='Path to file containing email addresses (one per line)'
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['auto', 'batch', 'stream', 'parallel'],
        default='auto',
        help='Processing mode (default: auto - chooses best mode automatically)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only show summary statistics'
    )
    parser.add_argument(
        '--progress', '-p',
        action='store_true',
        help='Show progress updates'
    )
    parser.add_argument(
        '--benchmark', '-b',
        action='store_true',
        help='Show performance metrics'
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Email Validator Unified 1.0.0'
    )
    return parser.parse_args()


# ============================================================================
# FLASK-READY API
# ============================================================================

# These functions are ready to import in your Flask app:
# from emailvalidator_unified import validate_email, validate_email_advanced, validate_batch

__all__ = ['validate_email', 'validate_email_advanced', 'validate_batch', 'validate_file']


if __name__ == "__main__":
    main()
