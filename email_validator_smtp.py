#!/usr/bin/env python3
"""
Enhanced Email Validator with SMTP Verification and Catch-all Detection
Extends emailvalidator_unified.py with SMTP-level mailbox verification
"""

import smtplib
import socket
import dns.resolver
import random
import time
from typing import Dict, Any, Optional, Tuple, List
from emailvalidator_unified import (
    validate_email, 
    validate_email_advanced,
    _is_disposable_email,
    _is_role_based_email,
    _check_dns_and_mx
)

# SMTP Configuration
SMTP_TIMEOUT = 15  # seconds (increased for better reliability)
SMTP_MAX_RETRIES = 2  # Number of retry attempts
SMTP_RETRY_DELAY = 3  # Seconds between retries

# Randomized sender emails to avoid blocking
SMTP_SENDER_POOL = [
    "verify@example.com",
    "check@example.org",
    "validate@example.net",
    "test@verification.com",
    "noreply@validator.com",
    "system@emailcheck.com"
]


def _get_random_sender() -> str:
    """Get a random sender email from the pool."""
    return random.choice(SMTP_SENDER_POOL)


def _get_mx_servers(domain: str) -> List[str]:
    """
    Get all MX servers for a domain, sorted by priority.
    
    Args:
        domain: Domain name
    
    Returns:
        List of MX server hostnames
    """
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        # Sort by priority (lower number = higher priority)
        sorted_mx = sorted(mx_records, key=lambda x: x.preference)
        return [str(mx.exchange).rstrip('.') for mx in sorted_mx]
    except Exception:
        return []


def verify_smtp_mailbox(email: str, timeout: int = SMTP_TIMEOUT, max_retries: int = SMTP_MAX_RETRIES) -> Dict[str, Any]:
    """
    Perform SMTP-level mailbox verification with retry logic and multiple MX servers.
    
    This function connects to the mail server and performs an SMTP handshake
    to verify if the mailbox actually exists without sending an email.
    
    Improvements:
    - Tries multiple MX servers (fallback)
    - Randomized sender emails
    - Retry logic with delays
    - Better error handling
    
    Args:
        email: Email address to verify
        timeout: Connection timeout in seconds (default: 15)
        max_retries: Number of retry attempts (default: 2)
    
    Returns:
        Dictionary with:
            - smtp_valid: bool - Whether SMTP verification passed
            - smtp_code: int or None - SMTP response code
            - smtp_message: str - SMTP response message
            - is_catch_all: bool - Whether domain accepts all emails
            - error: str or None - Error message if verification failed
            - mx_server: str - MX server that was used
    
    Example:
        >>> result = verify_smtp_mailbox("user@gmail.com")
        >>> result['smtp_valid']
        True
        >>> result['smtp_code']
        250
    """
    result = {
        'smtp_valid': False,
        'smtp_code': None,
        'smtp_message': '',
        'is_catch_all': False,
        'error': None,
        'mx_server': None
    }
    
    try:
        # Extract domain
        domain = email.split('@')[1]
        
        # Get all MX servers
        mx_servers = _get_mx_servers(domain)
        if not mx_servers:
            result['error'] = "No MX records found"
            return result
        
        # Try each MX server with retries
        for mx_index, mx_host in enumerate(mx_servers[:3]):  # Try up to 3 MX servers
            for attempt in range(max_retries + 1):
                try:
                    # Add delay between retries (but not on first attempt)
                    if attempt > 0:
                        time.sleep(SMTP_RETRY_DELAY)
                    
                    # Get random sender email
                    sender_email = _get_random_sender()
                    
                    # Connect to SMTP server
                    server = smtplib.SMTP(timeout=timeout)
                    server.set_debuglevel(0)
                    
                    # Connect
                    code, message = server.connect(mx_host)
                    if code != 220:
                        raise Exception(f"Connection failed: {code}")
                    
                    # HELO with random hostname
                    hostname = f"mail{random.randint(1, 999)}.validator.com"
                    code, message = server.helo(hostname)
                    if code != 250:
                        raise Exception(f"HELO failed: {code}")
                    
                    # MAIL FROM with random sender
                    code, message = server.mail(sender_email)
                    if code != 250:
                        raise Exception(f"MAIL FROM failed: {code}")
                    
                    # RCPT TO - verify actual email
                    code, message = server.rcpt(email)
                    result['smtp_code'] = code
                    result['smtp_message'] = message.decode() if isinstance(message, bytes) else str(message)
                    result['mx_server'] = mx_host
                    
                    if code == 250:
                        result['smtp_valid'] = True
                        # Check for catch-all domain
                        result['is_catch_all'] = _detect_catch_all(server, domain)
                        server.quit()
                        return result  # Success!
                    elif code == 550:
                        result['smtp_valid'] = False
                        result['error'] = "Mailbox does not exist"
                        server.quit()
                        return result  # Definitive answer
                    else:
                        result['smtp_valid'] = False
                        result['error'] = f"Unexpected response: {code}"
                    
                    server.quit()
                    
                except smtplib.SMTPServerDisconnected:
                    result['error'] = "Server disconnected"
                    continue  # Try next attempt or MX server
                except smtplib.SMTPConnectError:
                    result['error'] = "Connection refused"
                    continue
                except socket.timeout:
                    result['error'] = "Connection timeout"
                    continue
                except socket.error as e:
                    result['error'] = f"Network error: {str(e)}"
                    continue
                except Exception as e:
                    result['error'] = str(e)
                    continue
            
            # If we got here, all retries for this MX server failed
            # Try next MX server
            if mx_index < len(mx_servers) - 1:
                time.sleep(1)  # Brief delay before trying next MX server
    
    except Exception as e:
        result['error'] = f"Verification error: {str(e)}"
    
    return result


def _detect_catch_all(server: smtplib.SMTP, domain: str) -> bool:
    """
    Detect if domain is a catch-all (accepts all emails).
    
    Tests with a random/invalid email address to see if it's accepted.
    
    Args:
        server: Active SMTP connection
        domain: Domain to test
    
    Returns:
        bool: True if domain is catch-all, False otherwise
    """
    try:
        # Test with obviously fake email using random string
        random_string = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=20))
        fake_email = f"nonexistent{random_string}@{domain}"
        code, message = server.rcpt(fake_email)
        
        # If fake email is accepted (250), domain is catch-all
        return code == 250
    except:
        return False


def validate_email_with_smtp(
    email: str,
    enable_smtp: bool = True,
    check_dns: bool = True,
    check_mx: bool = True,
    check_disposable: bool = True,
    check_typos: bool = True,
    check_role_based: bool = True,
    smtp_timeout: int = SMTP_TIMEOUT
) -> Dict[str, Any]:
    """
    Complete email validation with optional SMTP verification.
    
    This is the main function combining all validation features:
    - Syntax validation
    - DNS/MX checks
    - Disposable email detection
    - Role-based detection
    - SMTP mailbox verification (optional)
    - Catch-all domain detection
    - Confidence scoring
    
    Args:
        email: Email address to validate
        enable_smtp: Enable SMTP mailbox verification (default: True)
        check_dns: Check DNS records (default: True)
        check_mx: Check MX records (default: True)
        check_disposable: Check disposable domains (default: True)
        check_typos: Suggest typo corrections (default: True)
        check_role_based: Check role-based emails (default: True)
        smtp_timeout: SMTP connection timeout in seconds (default: 10)
    
    Returns:
        Dictionary with complete validation results including:
            - valid: bool - Overall validity
            - email: str - Original email
            - checks: dict - All validation checks
            - confidence_score: int - Score 0-100
            - smtp_details: dict - SMTP verification results (if enabled)
            - is_catch_all: bool - Catch-all domain detection
            - suggestion: str or None - Typo suggestion
            - reason: str - Explanation
    
    Example:
        >>> result = validate_email_with_smtp("user@gmail.com")
        >>> result['valid']
        True
        >>> result['confidence_score']
        100
        >>> result['smtp_details']['smtp_valid']
        True
    """
    # Start with advanced validation
    result = validate_email_advanced(
        email,
        check_dns=check_dns,
        check_mx=check_mx,
        check_disposable=check_disposable,
        check_typos=check_typos,
        check_role_based=check_role_based
    )
    
    # Add SMTP verification if enabled and syntax is valid
    if enable_smtp and result['checks']['syntax']:
        smtp_result = verify_smtp_mailbox(email, timeout=smtp_timeout)
        result['smtp_details'] = smtp_result
        result['is_catch_all'] = smtp_result['is_catch_all']
        
        # Update checks
        result['checks']['smtp_verified'] = smtp_result['smtp_valid']
        result['checks']['is_catch_all'] = smtp_result['is_catch_all']
        
        # Recalculate confidence score with SMTP data
        result['confidence_score'] = _calculate_confidence_with_smtp(result['checks'])
        
        # SMTP is just additional info - don't override validity
        # Email is still valid if syntax, DNS, and MX are good
        # SMTP just tells us if mailbox exists (which often fails due to blocks)
        
        # Add SMTP info to reason
        if not smtp_result['smtp_valid']:
            smtp_note = 'SMTP verification failed'
            if smtp_result['error']:
                smtp_note += f': {smtp_result["error"]}'
            
            if result['reason']:
                result['reason'] += f'; {smtp_note}'
            else:
                result['reason'] = smtp_note
        
        # Add catch-all warning
        if smtp_result['is_catch_all']:
            catch_all_note = 'Catch-all domain (accepts all emails)'
            if result['reason']:
                result['reason'] += f'; {catch_all_note}'
            else:
                result['reason'] = catch_all_note
    else:
        result['smtp_details'] = None
        result['is_catch_all'] = False
    
    return result


def _calculate_confidence_with_smtp(checks: Dict[str, bool]) -> int:
    """
    Calculate confidence score including SMTP verification.
    
    Scoring:
        - Valid syntax: 30 points
        - DNS valid: +15 points
        - MX records: +15 points
        - SMTP verified: +20 points
        - NOT disposable: +10 points
        - NOT role-based: +5 points
        - NOT catch-all: +5 points
    
    Args:
        checks: Dictionary of validation checks
    
    Returns:
        int: Confidence score 0-100
    """
    score = 0
    
    # Syntax (30 points)
    if checks.get('syntax', False):
        score += 30
    
    # DNS (15 points)
    if checks.get('dns_valid', False):
        score += 15
    
    # MX records (15 points)
    if checks.get('mx_records', False):
        score += 15
    
    # SMTP verification (10 points bonus if verified, but don't penalize if not)
    # Many servers block SMTP verification, so we give bonus if it works
    # but don't subtract if it doesn't
    if checks.get('smtp_verified', False):
        score += 10
    elif checks.get('smtp_verified') is None:
        # SMTP not attempted, give base score
        score += 5
    
    # Not disposable (10 points)
    if not checks.get('is_disposable', True):
        score += 10
    
    # Not role-based (5 points)
    if not checks.get('is_role_based', True):
        score += 5
    
    # Not catch-all (5 points)
    if not checks.get('is_catch_all', True):
        score += 5
    
    return min(score, 100)


def detect_catch_all_domain(domain: str, timeout: int = SMTP_TIMEOUT) -> Dict[str, Any]:
    """
    Standalone catch-all domain detection.
    
    Args:
        domain: Domain to test
        timeout: Connection timeout in seconds
    
    Returns:
        Dictionary with:
            - is_catch_all: bool
            - test_email: str - Email used for testing
            - smtp_code: int or None
            - error: str or None
    
    Example:
        >>> result = detect_catch_all_domain("example.com")
        >>> result['is_catch_all']
        False
    """
    result = {
        'is_catch_all': False,
        'test_email': None,
        'smtp_code': None,
        'error': None
    }
    
    try:
        # Get MX records
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_host = str(mx_records[0].exchange).rstrip('.')
        
        # Create test email
        test_email = f"nonexistent-catchall-test-{hash(domain)}@{domain}"
        result['test_email'] = test_email
        
        # Connect and test
        server = smtplib.SMTP(timeout=timeout)
        server.set_debuglevel(0)
        server.connect(mx_host)
        server.helo()
        server.mail(SMTP_TEST_EMAIL)
        
        code, message = server.rcpt(test_email)
        result['smtp_code'] = code
        result['is_catch_all'] = (code == 250)
        
        server.quit()
        
    except Exception as e:
        result['error'] = str(e)
    
    return result
