#!/usr/bin/env python3
"""
Enhanced Email Validator with SMTP Verification and Catch-all Detection
Extends emailvalidator_unified.py with SMTP-level mailbox verification
"""

import smtplib
import socket
import dns.resolver
from typing import Dict, Any, Optional, Tuple
from emailvalidator_unified import (
    validate_email, 
    validate_email_advanced,
    _is_disposable_email,
    _is_role_based_email,
    _check_dns_and_mx
)

# SMTP Configuration
SMTP_TIMEOUT = 10  # seconds
SMTP_TEST_EMAIL = "test@example.com"  # Used for catch-all detection


def verify_smtp_mailbox(email: str, timeout: int = SMTP_TIMEOUT) -> Dict[str, Any]:
    """
    Perform SMTP-level mailbox verification.
    
    This function connects to the mail server and performs an SMTP handshake
    to verify if the mailbox actually exists without sending an email.
    
    Args:
        email: Email address to verify
        timeout: Connection timeout in seconds (default: 10)
    
    Returns:
        Dictionary with:
            - smtp_valid: bool - Whether SMTP verification passed
            - smtp_code: int or None - SMTP response code
            - smtp_message: str - SMTP response message
            - is_catch_all: bool - Whether domain accepts all emails
            - error: str or None - Error message if verification failed
    
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
        'error': None
    }
    
    try:
        # Extract domain
        domain = email.split('@')[1]
        
        # Get MX records
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange).rstrip('.')
        except Exception as e:
            result['error'] = f"No MX records found: {str(e)}"
            return result
        
        # Connect to SMTP server
        try:
            server = smtplib.SMTP(timeout=timeout)
            server.set_debuglevel(0)
            
            # Connect
            code, message = server.connect(mx_host)
            if code != 220:
                result['error'] = f"SMTP connection failed: {code} {message}"
                return result
            
            # HELO
            code, message = server.helo()
            if code != 250:
                result['error'] = f"HELO failed: {code} {message}"
                server.quit()
                return result
            
            # MAIL FROM
            code, message = server.mail(SMTP_TEST_EMAIL)
            if code != 250:
                result['error'] = f"MAIL FROM failed: {code} {message}"
                server.quit()
                return result
            
            # RCPT TO - verify actual email
            code, message = server.rcpt(email)
            result['smtp_code'] = code
            result['smtp_message'] = message.decode() if isinstance(message, bytes) else str(message)
            
            if code == 250:
                result['smtp_valid'] = True
            elif code == 550:
                result['smtp_valid'] = False
                result['error'] = "Mailbox does not exist"
            else:
                result['smtp_valid'] = False
                result['error'] = f"Unexpected response: {code} {message}"
            
            # Check for catch-all domain
            result['is_catch_all'] = _detect_catch_all(server, domain)
            
            # Close connection
            server.quit()
            
        except smtplib.SMTPServerDisconnected:
            result['error'] = "SMTP server disconnected"
        except smtplib.SMTPConnectError as e:
            result['error'] = f"SMTP connection error: {str(e)}"
        except socket.timeout:
            result['error'] = "SMTP connection timeout"
        except socket.error as e:
            result['error'] = f"Socket error: {str(e)}"
        except Exception as e:
            result['error'] = f"SMTP verification failed: {str(e)}"
    
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
        # Test with obviously fake email
        fake_email = f"nonexistent-test-{hash(domain)}@{domain}"
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
        
        # Update validity based on SMTP
        if not smtp_result['smtp_valid'] and smtp_result['error']:
            result['valid'] = False
            if 'Mailbox does not exist' in smtp_result['error']:
                result['reason'] = 'Mailbox does not exist (SMTP verification failed)'
        
        # Add catch-all warning
        if smtp_result['is_catch_all']:
            if result['reason']:
                result['reason'] += '; Warning: Catch-all domain (accepts all emails)'
            else:
                result['reason'] = 'Warning: Catch-all domain (accepts all emails)'
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
    
    # SMTP verification (20 points)
    if checks.get('smtp_verified', False):
        score += 20
    
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
