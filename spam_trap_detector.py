#!/usr/bin/env python3
"""
Spam Trap & Toxic Domain Detection
Identifies known spam traps, toxic domains, and high-risk emails
"""

from typing import Dict, Any, Set

# Known spam trap domains (public list - real services have proprietary lists)
SPAM_TRAP_DOMAINS = {
    # Honeypot domains
    'spamtrap.com',
    'honeypot.email',
    'spam-trap.net',
    'trapmail.com',
    'spamcop.net',
    'knujon.com',
    
    # Known spam trap providers
    'pristine.spamhaus.org',
    'typo-trap.spamhaus.org',
    'recycled-trap.spamhaus.org',
    
    # Test/trap domains
    'example.com',
    'example.org',
    'example.net',
    'test.com',
    'invalid.invalid',
}

# Toxic/Complainer domains (domains with high complaint rates)
TOXIC_DOMAINS = {
    # Known complainers
    'complainers.com',
    'spamreport.net',
    'abuse-report.com',
    
    # Blacklisted domains
    'blacklisted.email',
    'spam-source.com',
    'known-spammer.net',
    
    # Honeypot services
    'projecthoneypot.org',
    'stopforumspam.com',
}

# Abuse/complaint email patterns
ABUSE_PATTERNS = {
    'abuse',
    'complaints',
    'spam',
    'postmaster',
    'security',
    'legal',
    'dmca',
    'copyright',
    'fraud',
    'phishing',
}

# Suspicious TLDs (often used for spam)
SUSPICIOUS_TLDS = {
    '.tk',      # Tokelau (free domains)
    '.ml',      # Mali (free domains)
    '.ga',      # Gabon (free domains)
    '.cf',      # Central African Republic (free domains)
    '.gq',      # Equatorial Guinea (free domains)
    '.xyz',     # Often used for spam
    '.top',     # Often used for spam
    '.work',    # Often used for spam
    '.click',   # Often used for spam
    '.link',    # Often used for spam
}


def check_spam_trap(email: str, domain: str) -> Dict[str, Any]:
    """
    Check if email is a known spam trap.
    
    Args:
        email: Full email address
        domain: Domain part of email
    
    Returns:
        Dictionary with:
            - is_spam_trap: bool
            - trap_type: str or None
            - confidence: str (high/medium/low)
            - warning: str
    """
    domain_lower = domain.lower()
    local_part = email.split('@')[0].lower()
    
    # Check known spam trap domains
    if domain_lower in SPAM_TRAP_DOMAINS:
        return {
            'is_spam_trap': True,
            'trap_type': 'known_honeypot',
            'confidence': 'high',
            'warning': '⚠️ DANGER: Known spam trap domain - DO NOT SEND'
        }
    
    # Check for spam trap patterns
    spam_keywords = ['spam', 'trap', 'honeypot', 'test', 'invalid']
    if any(keyword in domain_lower for keyword in spam_keywords):
        return {
            'is_spam_trap': True,
            'trap_type': 'suspected_honeypot',
            'confidence': 'medium',
            'warning': '⚠️ WARNING: Suspected spam trap - High risk'
        }
    
    # Check for suspicious local parts
    if local_part in ['spam', 'trap', 'honeypot', 'test', 'invalid', 'fake']:
        return {
            'is_spam_trap': True,
            'trap_type': 'suspicious_pattern',
            'confidence': 'medium',
            'warning': '⚠️ WARNING: Suspicious email pattern'
        }
    
    return {
        'is_spam_trap': False,
        'trap_type': None,
        'confidence': 'none',
        'warning': None
    }


def check_toxic_domain(domain: str) -> Dict[str, Any]:
    """
    Check if domain is toxic/has high complaint rate.
    
    Args:
        domain: Domain to check
    
    Returns:
        Dictionary with:
            - is_toxic: bool
            - toxicity_level: str (high/medium/low)
            - reason: str
            - recommendation: str
    """
    domain_lower = domain.lower()
    
    # Check known toxic domains
    if domain_lower in TOXIC_DOMAINS:
        return {
            'is_toxic': True,
            'toxicity_level': 'high',
            'reason': 'Domain is on toxic/complainer list',
            'recommendation': 'DO NOT SEND - High complaint risk'
        }
    
    # Check suspicious TLDs
    for tld in SUSPICIOUS_TLDS:
        if domain_lower.endswith(tld):
            return {
                'is_toxic': True,
                'toxicity_level': 'medium',
                'reason': f'Suspicious TLD ({tld}) - often used for spam',
                'recommendation': 'Use caution - Monitor closely'
            }
    
    # Check for blacklist-related keywords
    blacklist_keywords = ['blacklist', 'blocklist', 'spam', 'abuse']
    if any(keyword in domain_lower for keyword in blacklist_keywords):
        return {
            'is_toxic': True,
            'toxicity_level': 'medium',
            'reason': 'Domain contains blacklist-related keywords',
            'recommendation': 'High risk - Verify before sending'
        }
    
    return {
        'is_toxic': False,
        'toxicity_level': 'none',
        'reason': None,
        'recommendation': 'Safe to send'
    }


def check_abuse_email(email: str) -> Dict[str, Any]:
    """
    Check if email is an abuse/complaint address.
    
    Args:
        email: Email address to check
    
    Returns:
        Dictionary with:
            - is_abuse_email: bool
            - abuse_type: str or None
            - risk_level: str (critical/high/medium)
            - warning: str
    """
    local_part = email.split('@')[0].lower()
    
    # Check for exact abuse patterns
    if local_part in ABUSE_PATTERNS:
        return {
            'is_abuse_email': True,
            'abuse_type': 'direct_abuse_address',
            'risk_level': 'critical',
            'warning': '🚨 CRITICAL: Abuse/complaint email - NEVER SEND'
        }
    
    # Check for abuse-related patterns
    abuse_keywords = ['abuse', 'complaint', 'spam', 'report', 'legal']
    if any(keyword in local_part for keyword in abuse_keywords):
        return {
            'is_abuse_email': True,
            'abuse_type': 'abuse_related',
            'risk_level': 'high',
            'warning': '⚠️ HIGH RISK: Abuse-related email - Do not send'
        }
    
    return {
        'is_abuse_email': False,
        'abuse_type': None,
        'risk_level': 'none',
        'warning': None
    }


def comprehensive_risk_check(email: str, domain: str) -> Dict[str, Any]:
    """
    Comprehensive risk check combining all detections.
    
    Args:
        email: Email address
        domain: Domain part
    
    Returns:
        Dictionary with all risk factors and overall assessment
    """
    # Run all checks
    spam_trap = check_spam_trap(email, domain)
    toxic = check_toxic_domain(domain)
    abuse = check_abuse_email(email)
    
    # Determine overall risk
    risk_factors = []
    overall_risk = 'low'
    
    if spam_trap['is_spam_trap']:
        risk_factors.append(spam_trap['warning'])
        overall_risk = 'critical'
    
    if abuse['is_abuse_email']:
        risk_factors.append(abuse['warning'])
        overall_risk = 'critical'
    
    if toxic['is_toxic']:
        risk_factors.append(f"Toxic domain: {toxic['reason']}")
        if overall_risk != 'critical':
            overall_risk = 'high' if toxic['toxicity_level'] == 'high' else 'medium'
    
    # Overall recommendation
    if overall_risk == 'critical':
        recommendation = '🚨 DO NOT SEND - Critical risk detected'
        safe_to_send = False
    elif overall_risk == 'high':
        recommendation = '⚠️ HIGH RISK - Not recommended'
        safe_to_send = False
    elif overall_risk == 'medium':
        recommendation = '⚠️ MEDIUM RISK - Use caution'
        safe_to_send = False
    else:
        recommendation = '✅ Safe to send'
        safe_to_send = True
    
    return {
        'spam_trap_check': spam_trap,
        'toxic_domain_check': toxic,
        'abuse_email_check': abuse,
        'overall_risk': overall_risk,
        'risk_factors': risk_factors if risk_factors else ['No risks detected'],
        'safe_to_send': safe_to_send,
        'recommendation': recommendation
    }
