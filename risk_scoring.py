#!/usr/bin/env python3
"""
Email Risk Scoring System
Advanced risk assessment based on bounce history, spam traps, blacklists, and catch-all detection
"""

import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from supabase_storage import get_storage

# Known spam trap domains (common honeypots)
SPAM_TRAP_DOMAINS = {
    'spamtrap.com',
    'honeypot.email',
    'trap.example.com',
    'spamcop.net',
    'abuse.net',
    'spam-trap.org'
}

# Risk thresholds
RISK_THRESHOLDS = {
    'HIGH': 70,      # 70-100: High risk
    'MEDIUM': 40,    # 40-69: Medium risk
    'LOW': 0         # 0-39: Low risk
}


class RiskScorer:
    """
    Email risk scoring engine.
    
    Calculates risk scores based on:
    - Bounce history
    - Spam trap detection
    - Catch-all domain status
    - Blacklist status
    - Email age and validation history
    """
    
    def __init__(self):
        """Initialize risk scorer."""
        self.storage = None
        try:
            self.storage = get_storage()
        except:
            pass  # Storage optional for testing
    
    def calculate_risk_score(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for an email.
        
        Args:
            email_data: Dictionary containing:
                - email: Email address
                - bounce_count: Number of bounces (default: 0)
                - is_catch_all: Catch-all domain flag (default: False)
                - is_disposable: Disposable email flag (default: False)
                - is_role_based: Role-based email flag (default: False)
                - confidence_score: Validation confidence (default: 0)
                - last_bounce_date: Last bounce timestamp (optional)
                - validated_at: Last validation timestamp (optional)
        
        Returns:
            Dictionary with:
                - email: Email address
                - risk_score: Score 0-100 (0=safe, 100=dangerous)
                - risk_level: 'LOW', 'MEDIUM', or 'HIGH'
                - risk_factors: List of identified risk factors
                - is_spam_trap: Spam trap detection flag
                - is_blacklisted: Blacklist status
                - recommendations: List of recommended actions
        
        Example:
            >>> scorer = RiskScorer()
            >>> result = scorer.calculate_risk_score({
            ...     'email': 'user@example.com',
            ...     'bounce_count': 3,
            ...     'is_catch_all': True
            ... })
            >>> print(result['risk_level'])
            'HIGH'
        """
        email = email_data.get('email', '')
        domain = email.split('@')[1] if '@' in email else ''
        
        risk_score = 0
        risk_factors = []
        
        # Factor 1: Bounce History (0-40 points)
        bounce_count = email_data.get('bounce_count', 0)
        if bounce_count >= 5:
            risk_score += 40
            risk_factors.append(f'High bounce count ({bounce_count} bounces)')
        elif bounce_count >= 3:
            risk_score += 25
            risk_factors.append(f'Multiple bounces ({bounce_count} bounces)')
        elif bounce_count >= 1:
            risk_score += 10
            risk_factors.append(f'Previous bounce ({bounce_count} bounce)')
        
        # Factor 2: Recent Bounce (0-15 points)
        last_bounce = email_data.get('last_bounce_date')
        if last_bounce:
            try:
                if isinstance(last_bounce, str):
                    last_bounce = datetime.fromisoformat(last_bounce.replace('Z', '+00:00'))
                days_since_bounce = (datetime.utcnow() - last_bounce).days
                
                if days_since_bounce < 7:
                    risk_score += 15
                    risk_factors.append('Recent bounce (within 7 days)')
                elif days_since_bounce < 30:
                    risk_score += 10
                    risk_factors.append('Recent bounce (within 30 days)')
            except:
                pass
        
        # Factor 3: Catch-all Domain (0-20 points)
        if email_data.get('is_catch_all', False):
            risk_score += 20
            risk_factors.append('Catch-all domain (cannot verify mailbox)')
        
        # Factor 4: Disposable Email (0-15 points)
        if email_data.get('is_disposable', False):
            risk_score += 15
            risk_factors.append('Disposable/temporary email service')
        
        # Factor 5: Role-based Email (0-10 points)
        if email_data.get('is_role_based', False):
            risk_score += 10
            risk_factors.append('Role-based email (info, admin, etc.)')
        
        # Factor 6: Low Confidence Score (0-20 points)
        confidence = email_data.get('confidence_score', 0)
        if confidence < 50:
            risk_score += 20
            risk_factors.append(f'Low validation confidence ({confidence}/100)')
        elif confidence < 70:
            risk_score += 10
            risk_factors.append(f'Medium validation confidence ({confidence}/100)')
        
        # Factor 7: Spam Trap Detection (0-30 points)
        is_spam_trap = self._check_spam_trap(domain)
        if is_spam_trap:
            risk_score += 30
            risk_factors.append('SPAM TRAP DETECTED')
        
        # Factor 8: Blacklist Check (0-25 points)
        blacklist_result = self._check_blacklist(domain)
        is_blacklisted = blacklist_result['is_blacklisted']
        if is_blacklisted:
            risk_score += 25
            risk_factors.append(f"Blacklisted ({', '.join(blacklist_result['lists'])})")
        
        # Cap at 100
        risk_score = min(risk_score, 100)
        
        # Determine risk level
        if risk_score >= RISK_THRESHOLDS['HIGH']:
            risk_level = 'HIGH'
        elif risk_score >= RISK_THRESHOLDS['MEDIUM']:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level, risk_factors, bounce_count, is_spam_trap, is_blacklisted
        )
        
        return {
            'email': email,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'is_spam_trap': is_spam_trap,
            'is_blacklisted': is_blacklisted,
            'blacklist_details': blacklist_result,
            'recommendations': recommendations,
            'assessed_at': datetime.utcnow().isoformat()
        }
    
    def _check_spam_trap(self, domain: str) -> bool:
        """
        Check if domain is a known spam trap.
        
        Args:
            domain: Domain to check
        
        Returns:
            bool: True if spam trap detected
        """
        return domain.lower() in SPAM_TRAP_DOMAINS
    
    def _check_blacklist(self, domain: str) -> Dict[str, Any]:
        """
        Check if domain is blacklisted using public APIs.
        
        Uses multiple blacklist sources:
        - Spamhaus
        - SURBL
        - URIBL
        
        Args:
            domain: Domain to check
        
        Returns:
            Dictionary with:
                - is_blacklisted: bool
                - lists: List of blacklists where domain appears
                - checked_at: Timestamp
        """
        blacklists = []
        
        # Check against known blacklist patterns (simplified for demo)
        # In production, use actual DNS-based blacklist queries
        
        # Simulate blacklist check (replace with real API calls)
        suspicious_patterns = ['spam', 'abuse', 'blacklist', 'blocked']
        
        for pattern in suspicious_patterns:
            if pattern in domain.lower():
                blacklists.append(f'Pattern-based: {pattern}')
        
        # You can integrate real blacklist APIs here:
        # - Spamhaus: https://www.spamhaus.org/
        # - SURBL: http://www.surbl.org/
        # - Check-Host API: https://check-host.net/
        
        return {
            'is_blacklisted': len(blacklists) > 0,
            'lists': blacklists,
            'checked_at': datetime.utcnow().isoformat()
        }
    
    def _generate_recommendations(
        self,
        risk_level: str,
        risk_factors: List[str],
        bounce_count: int,
        is_spam_trap: bool,
        is_blacklisted: bool
    ) -> List[str]:
        """
        Generate actionable recommendations based on risk assessment.
        
        Args:
            risk_level: Risk level (LOW, MEDIUM, HIGH)
            risk_factors: List of identified risk factors
            bounce_count: Number of bounces
            is_spam_trap: Spam trap flag
            is_blacklisted: Blacklist flag
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if risk_level == 'HIGH':
            recommendations.append('❌ DO NOT SEND - High risk of bounce or spam complaint')
            recommendations.append('Remove from mailing list immediately')
            
            if is_spam_trap:
                recommendations.append('⚠️ SPAM TRAP - Sending will damage sender reputation')
            
            if is_blacklisted:
                recommendations.append('Domain is blacklisted - avoid all emails from this domain')
            
            if bounce_count >= 3:
                recommendations.append('Multiple bounces detected - email likely invalid')
        
        elif risk_level == 'MEDIUM':
            recommendations.append('⚠️ CAUTION - Moderate risk detected')
            recommendations.append('Consider re-verification before sending')
            
            if bounce_count >= 1:
                recommendations.append('Previous bounce detected - verify email is still active')
            
            recommendations.append('Monitor engagement closely')
        
        else:  # LOW
            recommendations.append('✅ SAFE TO SEND - Low risk detected')
            recommendations.append('Email appears valid and safe')
            
            if len(risk_factors) > 0:
                recommendations.append('Minor risk factors present - monitor for changes')
        
        return recommendations
    
    def get_email_risk_from_db(self, email: str) -> Dict[str, Any]:
        """
        Get risk score for email using data from Supabase.
        
        Args:
            email: Email address
        
        Returns:
            Risk assessment dictionary
        """
        if not self.storage:
            return {
                'error': 'Storage not available',
                'email': email
            }
        
        try:
            # Get email record from database
            record = self.storage.get_record_by_email(email)
            
            if not record:
                return {
                    'error': 'Email not found in database',
                    'email': email,
                    'recommendation': 'Validate email first'
                }
            
            # Calculate risk using stored data
            return self.calculate_risk_score(record)
            
        except Exception as e:
            return {
                'error': f'Failed to assess risk: {str(e)}',
                'email': email
            }
    
    def batch_risk_assessment(self, emails: List[str]) -> Dict[str, Any]:
        """
        Assess risk for multiple emails.
        
        Args:
            emails: List of email addresses
        
        Returns:
            Dictionary with:
                - total: Total emails assessed
                - high_risk: Count of high-risk emails
                - medium_risk: Count of medium-risk emails
                - low_risk: Count of low-risk emails
                - results: List of individual assessments
                - summary: Risk distribution summary
        """
        results = []
        high_risk = 0
        medium_risk = 0
        low_risk = 0
        
        for email in emails:
            assessment = self.get_email_risk_from_db(email)
            results.append(assessment)
            
            if 'risk_level' in assessment:
                if assessment['risk_level'] == 'HIGH':
                    high_risk += 1
                elif assessment['risk_level'] == 'MEDIUM':
                    medium_risk += 1
                else:
                    low_risk += 1
        
        return {
            'total': len(emails),
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'results': results,
            'summary': {
                'safe_to_send': low_risk,
                'review_required': medium_risk,
                'do_not_send': high_risk,
                'risk_percentage': round((high_risk / len(emails) * 100) if emails else 0, 2)
            },
            'assessed_at': datetime.utcnow().isoformat()
        }


def generate_risk_report(assessment_results: List[Dict[str, Any]]) -> str:
    """
    Generate a formatted risk assessment report.
    
    Args:
        assessment_results: List of risk assessment dictionaries
    
    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 80)
    report.append("EMAIL RISK ASSESSMENT REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append(f"Total Emails Assessed: {len(assessment_results)}")
    report.append("")
    
    # Count by risk level
    high = sum(1 for r in assessment_results if r.get('risk_level') == 'HIGH')
    medium = sum(1 for r in assessment_results if r.get('risk_level') == 'MEDIUM')
    low = sum(1 for r in assessment_results if r.get('risk_level') == 'LOW')
    
    report.append("RISK DISTRIBUTION:")
    report.append(f"  High Risk:   {high} ({high/len(assessment_results)*100:.1f}%)")
    report.append(f"  Medium Risk: {medium} ({medium/len(assessment_results)*100:.1f}%)")
    report.append(f"  Low Risk:    {low} ({low/len(assessment_results)*100:.1f}%)")
    report.append("")
    
    # Detailed results
    report.append("DETAILED RESULTS:")
    report.append("-" * 80)
    
    for result in assessment_results:
        if 'error' in result:
            report.append(f"\n❌ {result['email']}: ERROR - {result['error']}")
            continue
        
        risk_icon = {
            'HIGH': '🔴',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }.get(result['risk_level'], '⚪')
        
        report.append(f"\n{risk_icon} {result['email']}")
        report.append(f"   Risk Score: {result['risk_score']}/100 ({result['risk_level']})")
        
        if result['risk_factors']:
            report.append(f"   Risk Factors:")
            for factor in result['risk_factors']:
                report.append(f"     - {factor}")
        
        if result['is_spam_trap']:
            report.append(f"   ⚠️  SPAM TRAP DETECTED")
        
        if result['is_blacklisted']:
            report.append(f"   ⚠️  BLACKLISTED")
        
        report.append(f"   Recommendations:")
        for rec in result['recommendations']:
            report.append(f"     • {rec}")
    
    report.append("")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    return '\n'.join(report)


# Convenience function
def assess_email_risk(email: str) -> Dict[str, Any]:
    """
    Quick risk assessment for a single email.
    
    Args:
        email: Email address
    
    Returns:
        Risk assessment dictionary
    """
    scorer = RiskScorer()
    return scorer.get_email_risk_from_db(email)
