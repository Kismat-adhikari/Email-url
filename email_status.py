#!/usr/bin/env python3
"""
Email Status Classification
Categorize emails like ZeroBounce/NeverBounce
"""

from typing import Dict, Any

def determine_email_status(validation_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine email status category like professional services.
    
    Status categories:
    - valid: Email is valid and safe to send
    - invalid: Email is invalid, do not send
    - catch-all: Domain accepts all emails (unknown if exists)
    - disposable: Temporary/disposable email
    - unknown: Cannot determine validity
    - abuse: Abuse/complaint email
    - do_not_mail: On blocklist or has bounced
    
    Args:
        validation_result: Full validation result
    
    Returns:
        Dictionary with:
            - status: str (main status)
            - sub_status: str (detailed status)
            - status_code: int (for API)
            - description: str
            - color: str (for UI)
    """
    checks = validation_result.get('checks', {})
    risk_check = validation_result.get('risk_check', {})
    bounce_check = validation_result.get('bounce_check', {})
    
    # Priority 1: Abuse emails
    if risk_check.get('abuse_email_check', {}).get('is_abuse_email'):
        return {
            'status': 'abuse',
            'sub_status': 'abuse_email',
            'status_code': 5,
            'description': 'Abuse or complaint email address',
            'color': 'red',
            'icon': '🚫'
        }
    
    # Priority 2: Spam traps
    if risk_check.get('spam_trap_check', {}).get('is_spam_trap'):
        return {
            'status': 'do_not_mail',
            'sub_status': 'spam_trap',
            'status_code': 6,
            'description': 'Known spam trap - DO NOT SEND',
            'color': 'red',
            'icon': '🪤'
        }
    
    # Priority 3: Hard bounces
    if bounce_check.get('bounce_history', {}).get('hard_bounces', 0) > 0:
        return {
            'status': 'do_not_mail',
            'sub_status': 'hard_bounce',
            'status_code': 6,
            'description': 'Email has hard bounced',
            'color': 'red',
            'icon': '📉'
        }
    
    # Priority 4: Disposable
    if checks.get('is_disposable'):
        return {
            'status': 'disposable',
            'sub_status': 'temporary_email',
            'status_code': 4,
            'description': 'Temporary or disposable email',
            'color': 'orange',
            'icon': '🗑️'
        }
    
    # Priority 5: Catch-all
    if checks.get('is_catch_all') or validation_result.get('is_catch_all'):
        return {
            'status': 'catch-all',
            'sub_status': 'accept_all',
            'status_code': 3,
            'description': 'Domain accepts all emails (cannot verify mailbox)',
            'color': 'yellow',
            'icon': '❓'
        }
    
    # Priority 6: Invalid (syntax, DNS, MX)
    if not validation_result.get('valid'):
        if not checks.get('syntax'):
            return {
                'status': 'invalid',
                'sub_status': 'syntax_error',
                'status_code': 2,
                'description': 'Invalid email syntax',
                'color': 'red',
                'icon': '✗'
            }
        elif not checks.get('dns_valid'):
            return {
                'status': 'invalid',
                'sub_status': 'domain_not_found',
                'status_code': 2,
                'description': 'Domain does not exist',
                'color': 'red',
                'icon': '✗'
            }
        elif not checks.get('mx_records'):
            return {
                'status': 'invalid',
                'sub_status': 'no_mail_server',
                'status_code': 2,
                'description': 'Domain has no mail server',
                'color': 'red',
                'icon': '✗'
            }
        else:
            return {
                'status': 'invalid',
                'sub_status': 'unknown_reason',
                'status_code': 2,
                'description': 'Email is invalid',
                'color': 'red',
                'icon': '✗'
            }
    
    # Priority 7: Valid
    if validation_result.get('valid'):
        # Check confidence
        confidence = validation_result.get('confidence_score', 0)
        if confidence >= 90:
            return {
                'status': 'valid',
                'sub_status': 'high_confidence',
                'status_code': 1,
                'description': 'Valid email - Safe to send',
                'color': 'green',
                'icon': '✓'
            }
        elif confidence >= 70:
            return {
                'status': 'valid',
                'sub_status': 'medium_confidence',
                'status_code': 1,
                'description': 'Valid email - Good to send',
                'color': 'green',
                'icon': '✓'
            }
        else:
            return {
                'status': 'valid',
                'sub_status': 'low_confidence',
                'status_code': 1,
                'description': 'Valid email - Use caution',
                'color': 'yellow',
                'icon': '✓'
            }
    
    # Default: Unknown
    return {
        'status': 'unknown',
        'sub_status': 'cannot_verify',
        'status_code': 0,
        'description': 'Cannot determine email validity',
        'color': 'gray',
        'icon': '?'
    }


def get_status_badge_html(status_info: Dict[str, Any]) -> str:
    """
    Generate HTML badge for status (for reports/exports).
    
    Args:
        status_info: Status information from determine_email_status
    
    Returns:
        HTML string for badge
    """
    color = status_info['color']
    status = status_info['status'].upper()
    
    colors = {
        'green': '#10b981',
        'yellow': '#f59e0b',
        'orange': '#fb923c',
        'red': '#ef4444',
        'gray': '#6b7280'
    }
    
    bg_color = colors.get(color, '#6b7280')
    
    return f'<span style="background:{bg_color};color:white;padding:4px 12px;border-radius:12px;font-weight:600;">{status}</span>'
