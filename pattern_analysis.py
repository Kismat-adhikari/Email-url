#!/usr/bin/env python3
"""
Email Pattern Analysis - Like ZeroBounce/NeverBounce
Detects suspicious patterns and calculates deliverability scores
"""

import re
from typing import Dict, Any, List

# Suspicious patterns
SUSPICIOUS_PATTERNS = [
    r'^test\d+@',           # test123@
    r'^temp\d+@',           # temp456@
    r'^fake\d+@',           # fake789@
    r'^random\d+@',         # random123@
    r'^\d{5,}@',            # 12345@
    r'^[a-z]{20,}@',        # aaaaaaaaaaaaaaaaaaaa@
    r'^\d+[a-z]+\d+@',      # 123abc456@
    r'^noreply@',           # noreply@
    r'^no-reply@',          # no-reply@
    r'^donotreply@',        # donotreply@
]

# Professional patterns (look real)
PROFESSIONAL_PATTERNS = [
    r'^[a-z]+\.[a-z]+@',                    # john.smith@
    r'^[a-z]+_[a-z]+@',                     # john_smith@
    r'^[a-z]+\.[a-z]+\.[a-z]+@',           # john.m.smith@
    r'^[a-z]{3,15}@',                       # reasonable name length
]

# Common real names
COMMON_NAMES = {
    'john', 'jane', 'michael', 'sarah', 'david', 'emily', 'james', 'mary',
    'robert', 'jennifer', 'william', 'linda', 'richard', 'patricia', 'joseph',
    'admin', 'info', 'contact', 'support', 'sales', 'hello', 'team'
}


def analyze_email_pattern(email: str) -> Dict[str, Any]:
    """
    Analyze email pattern to detect suspicious or fake emails.
    
    Args:
        email: Email address to analyze
    
    Returns:
        Dictionary with:
            - pattern_score: int (0-100, higher = more legitimate)
            - is_suspicious: bool
            - pattern_type: str (professional/suspicious/neutral)
            - flags: list of detected issues
            - looks_real: bool
    """
    if '@' not in email:
        return {
            'pattern_score': 0,
            'is_suspicious': True,
            'pattern_type': 'invalid',
            'flags': ['Invalid format'],
            'looks_real': False
        }
    
    local_part, domain = email.split('@', 1)
    local_lower = local_part.lower()
    
    score = 50  # Start neutral
    flags = []
    
    # Check for suspicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if re.match(pattern, local_lower):
            score -= 30
            flags.append('Suspicious pattern detected')
            break
    
    # Check for professional patterns
    for pattern in PROFESSIONAL_PATTERNS:
        if re.match(pattern, local_lower):
            score += 20
            break
    
    # Check if contains common name
    name_parts = re.split(r'[._\-]', local_lower)
    if any(part in COMMON_NAMES for part in name_parts):
        score += 15
    
    # Length checks
    if len(local_part) < 3:
        score -= 10
        flags.append('Very short local part')
    elif len(local_part) > 30:
        score -= 10
        flags.append('Very long local part')
    elif 5 <= len(local_part) <= 20:
        score += 10  # Good length
    
    # Check for excessive numbers
    digit_count = sum(c.isdigit() for c in local_part)
    if digit_count > len(local_part) * 0.5:  # More than 50% digits
        score -= 15
        flags.append('Too many numbers')
    
    # Check for random-looking strings
    if len(set(local_part)) < len(local_part) * 0.4:  # Low character diversity
        score -= 10
        flags.append('Low character diversity')
    
    # Normalize score
    score = max(0, min(100, score))
    
    # Determine pattern type
    if score >= 70:
        pattern_type = 'professional'
        looks_real = True
    elif score >= 40:
        pattern_type = 'neutral'
        looks_real = True
    else:
        pattern_type = 'suspicious'
        looks_real = False
    
    return {
        'pattern_score': score,
        'is_suspicious': score < 40,
        'pattern_type': pattern_type,
        'flags': flags if flags else ['No issues detected'],
        'looks_real': looks_real
    }


def calculate_deliverability_score(
    email: str,
    validation_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate overall deliverability score combining all factors.
    Like ZeroBounce/NeverBounce's quality score.
    
    Args:
        email: Email address
        validation_result: Results from email validation
    
    Returns:
        Dictionary with:
            - deliverability_score: int (0-100)
            - deliverability_grade: str (A+, A, B, C, D, F)
            - can_send: bool
            - quality: str (excellent/good/fair/poor)
            - recommendation: str
    """
    score = 0
    
    # Factor 1: Basic validity (30 points)
    if validation_result.get('valid'):
        score += 30
    
    # Factor 2: DNS & MX (25 points)
    checks = validation_result.get('checks', {})
    if checks.get('dns_valid'):
        score += 12
    if checks.get('mx_records'):
        score += 13
    
    # Factor 3: Pattern analysis (20 points)
    pattern = analyze_email_pattern(email)
    score += int(pattern['pattern_score'] * 0.2)
    
    # Factor 4: Not disposable (15 points)
    if not checks.get('is_disposable', True):
        score += 15
    
    # Factor 5: Not role-based (10 points)
    if not checks.get('is_role_based', True):
        score += 10
    
    # Determine grade
    if score >= 90:
        grade = 'Excellent'
        quality = 'excellent'
        can_send = True
        recommendation = 'Safe to send'
    elif score >= 80:
        grade = 'Very Good'
        quality = 'excellent'
        can_send = True
        recommendation = 'Safe to send'
    elif score >= 70:
        grade = 'Good'
        quality = 'good'
        can_send = True
        recommendation = 'Good to send'
    elif score >= 60:
        grade = 'Fair'
        quality = 'fair'
        can_send = True
        recommendation = 'Acceptable, but monitor'
    elif score >= 40:
        grade = 'Poor'
        quality = 'poor'
        can_send = False
        recommendation = 'Risky - not recommended'
    else:
        grade = 'Very Poor'
        quality = 'poor'
        can_send = False
        recommendation = 'Do not send'
    
    return {
        'deliverability_score': score,
        'deliverability_grade': grade,
        'can_send': can_send,
        'quality': quality,
        'recommendation': recommendation,
        'pattern_analysis': pattern
    }
