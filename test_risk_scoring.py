#!/usr/bin/env python3
"""
Unit Tests for Email Risk Scoring System
Tests risk assessment, spam trap detection, and blacklist checking
"""

import unittest
from unittest.mock import patch, MagicMock
from risk_scoring import RiskScorer, generate_risk_report
from datetime import datetime, timedelta


class TestRiskScoring(unittest.TestCase):
    """Test risk scoring functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scorer = RiskScorer()
        self.scorer.storage = None  # Disable storage for unit tests
    
    def test_low_risk_email(self):
        """Test low-risk email assessment."""
        email_data = {
            'email': 'user@example.com',
            'bounce_count': 0,
            'is_catch_all': False,
            'is_disposable': False,
            'is_role_based': False,
            'confidence_score': 95
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertEqual(result['risk_level'], 'LOW')
        self.assertLess(result['risk_score'], 40)
        self.assertFalse(result['is_spam_trap'])
        self.assertIn('SAFE TO SEND', ' '.join(result['recommendations']))
    
    def test_high_risk_email_multiple_bounces(self):
        """Test high-risk email with multiple bounces."""
        email_data = {
            'email': 'bounced@example.com',
            'bounce_count': 5,
            'is_catch_all': True,  # Add catch-all to push it to HIGH
            'is_disposable': False,
            'is_role_based': False,
            'confidence_score': 30
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertEqual(result['risk_level'], 'HIGH')
        self.assertGreaterEqual(result['risk_score'], 70)
        self.assertIn('High bounce count', ' '.join(result['risk_factors']))
        self.assertIn('DO NOT SEND', ' '.join(result['recommendations']))
    
    def test_medium_risk_email(self):
        """Test medium-risk email assessment."""
        email_data = {
            'email': 'user@example.com',
            'bounce_count': 2,
            'is_catch_all': True,
            'is_disposable': False,
            'is_role_based': False,
            'confidence_score': 60
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertEqual(result['risk_level'], 'MEDIUM')
        self.assertGreaterEqual(result['risk_score'], 40)
        self.assertLess(result['risk_score'], 70)
        self.assertIn('CAUTION', ' '.join(result['recommendations']))
    
    def test_spam_trap_detected(self):
        """Test spam trap detection."""
        email_data = {
            'email': 'trap@spamtrap.com',
            'bounce_count': 1,  # Add bounce to push it to HIGH
            'is_catch_all': False,
            'is_disposable': False,
            'is_role_based': False,
            'confidence_score': 60  # Lower confidence
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertTrue(result['is_spam_trap'])
        self.assertEqual(result['risk_level'], 'HIGH')
        self.assertIn('SPAM TRAP DETECTED', ' '.join(result['risk_factors']))
        self.assertIn('SPAM TRAP', ' '.join(result['recommendations']))
    
    def test_blacklist_flagged(self):
        """Test blacklist detection."""
        email_data = {
            'email': 'user@spam-domain.com',
            'bounce_count': 0,
            'is_catch_all': False,
            'is_disposable': False,
            'is_role_based': False,
            'confidence_score': 70
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertTrue(result['is_blacklisted'])
        self.assertIn('Blacklisted', ' '.join(result['risk_factors']))
        self.assertGreater(result['risk_score'], 0)
    
    def test_disposable_email_risk(self):
        """Test disposable email risk assessment."""
        email_data = {
            'email': 'temp@tempmail.com',
            'bounce_count': 0,
            'is_catch_all': False,
            'is_disposable': True,
            'is_role_based': False,
            'confidence_score': 70
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertIn('Disposable', ' '.join(result['risk_factors']))
        self.assertGreater(result['risk_score'], 0)
    
    def test_role_based_email_risk(self):
        """Test role-based email risk assessment."""
        email_data = {
            'email': 'info@company.com',
            'bounce_count': 0,
            'is_catch_all': False,
            'is_disposable': False,
            'is_role_based': True,
            'confidence_score': 80
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertIn('Role-based', ' '.join(result['risk_factors']))
        self.assertGreater(result['risk_score'], 0)
    
    def test_catch_all_domain_risk(self):
        """Test catch-all domain risk assessment."""
        email_data = {
            'email': 'anyone@catchall-domain.com',
            'bounce_count': 0,
            'is_catch_all': True,
            'is_disposable': False,
            'is_role_based': False,
            'confidence_score': 70
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertIn('Catch-all', ' '.join(result['risk_factors']))
        self.assertGreater(result['risk_score'], 0)
    
    def test_recent_bounce_risk(self):
        """Test recent bounce increases risk."""
        # Recent bounce (2 days ago)
        recent_bounce = (datetime.utcnow() - timedelta(days=2)).isoformat()
        
        email_data = {
            'email': 'user@example.com',
            'bounce_count': 1,
            'last_bounce_date': recent_bounce,
            'is_catch_all': False,
            'is_disposable': False,
            'is_role_based': False,
            'confidence_score': 70
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertIn('Recent bounce', ' '.join(result['risk_factors']))
        self.assertGreater(result['risk_score'], 10)
    
    def test_low_confidence_risk(self):
        """Test low confidence score increases risk."""
        email_data = {
            'email': 'user@example.com',
            'bounce_count': 0,
            'is_catch_all': False,
            'is_disposable': False,
            'is_role_based': False,
            'confidence_score': 30
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertIn('Low validation confidence', ' '.join(result['risk_factors']))
        self.assertGreater(result['risk_score'], 0)
    
    def test_combined_risk_factors(self):
        """Test multiple risk factors compound."""
        email_data = {
            'email': 'info@spam-domain.com',
            'bounce_count': 3,
            'is_catch_all': True,
            'is_disposable': True,
            'is_role_based': True,
            'confidence_score': 40
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertEqual(result['risk_level'], 'HIGH')
        self.assertGreater(len(result['risk_factors']), 3)
        self.assertGreaterEqual(result['risk_score'], 70)
    
    def test_risk_score_capped_at_100(self):
        """Test risk score is capped at 100."""
        email_data = {
            'email': 'trap@spamtrap.com',
            'bounce_count': 10,
            'is_catch_all': True,
            'is_disposable': True,
            'is_role_based': True,
            'confidence_score': 0
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        self.assertLessEqual(result['risk_score'], 100)
    
    def test_spam_trap_domains(self):
        """Test known spam trap domains are detected."""
        spam_trap_domains = [
            'spamtrap.com',
            'honeypot.email',
            'spam-trap.org'
        ]
        
        for domain in spam_trap_domains:
            is_trap = self.scorer._check_spam_trap(domain)
            self.assertTrue(is_trap, f"{domain} should be detected as spam trap")
    
    def test_blacklist_check(self):
        """Test blacklist checking functionality."""
        # Domain with suspicious pattern
        result = self.scorer._check_blacklist('spam-domain.com')
        
        self.assertIn('is_blacklisted', result)
        self.assertIn('lists', result)
        self.assertIn('checked_at', result)
        self.assertTrue(result['is_blacklisted'])
    
    def test_recommendations_high_risk(self):
        """Test recommendations for high-risk emails."""
        email_data = {
            'email': 'trap@spamtrap.com',
            'bounce_count': 5,
            'is_catch_all': False,
            'is_disposable': False,
            'is_role_based': False,
            'confidence_score': 20
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        recommendations = ' '.join(result['recommendations'])
        self.assertIn('DO NOT SEND', recommendations)
        self.assertIn('Remove from mailing list', recommendations)
    
    def test_recommendations_medium_risk(self):
        """Test recommendations for medium-risk emails."""
        email_data = {
            'email': 'user@example.com',
            'bounce_count': 1,
            'is_catch_all': True,
            'is_disposable': False,
            'is_role_based': False,
            'confidence_score': 60
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        recommendations = ' '.join(result['recommendations'])
        self.assertIn('CAUTION', recommendations)
        self.assertIn('re-verification', recommendations)
    
    def test_recommendations_low_risk(self):
        """Test recommendations for low-risk emails."""
        email_data = {
            'email': 'user@example.com',
            'bounce_count': 0,
            'is_catch_all': False,
            'is_disposable': False,
            'is_role_based': False,
            'confidence_score': 95
        }
        
        result = self.scorer.calculate_risk_score(email_data)
        
        recommendations = ' '.join(result['recommendations'])
        self.assertIn('SAFE TO SEND', recommendations)


class TestBatchAssessment(unittest.TestCase):
    """Test batch risk assessment."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scorer = RiskScorer()
        self.scorer.storage = MagicMock()
    
    def test_batch_assessment(self):
        """Test batch risk assessment."""
        # Mock storage responses
        self.scorer.storage.get_record_by_email.side_effect = [
            {'email': 'user1@example.com', 'bounce_count': 0, 'confidence_score': 95,
             'is_catch_all': False, 'is_disposable': False, 'is_role_based': False},
            {'email': 'user2@example.com', 'bounce_count': 5, 'confidence_score': 30,
             'is_catch_all': True, 'is_disposable': False, 'is_role_based': False},
            {'email': 'user3@example.com', 'bounce_count': 2, 'confidence_score': 60,
             'is_catch_all': False, 'is_disposable': True, 'is_role_based': False}
        ]
        
        emails = ['user1@example.com', 'user2@example.com', 'user3@example.com']
        result = self.scorer.batch_risk_assessment(emails)
        
        self.assertEqual(result['total'], 3)
        self.assertIn('high_risk', result)
        self.assertIn('medium_risk', result)
        self.assertIn('low_risk', result)
        self.assertIn('summary', result)
        self.assertEqual(len(result['results']), 3)


class TestReportGeneration(unittest.TestCase):
    """Test report generation."""
    
    def test_generate_risk_report(self):
        """Test risk report generation."""
        assessments = [
            {
                'email': 'user1@example.com',
                'risk_score': 15,
                'risk_level': 'LOW',
                'risk_factors': [],
                'is_spam_trap': False,
                'is_blacklisted': False,
                'recommendations': ['Safe to send']
            },
            {
                'email': 'user2@example.com',
                'risk_score': 85,
                'risk_level': 'HIGH',
                'risk_factors': ['High bounce count', 'Spam trap detected'],
                'is_spam_trap': True,
                'is_blacklisted': False,
                'recommendations': ['Do not send']
            }
        ]
        
        report = generate_risk_report(assessments)
        
        self.assertIn('EMAIL RISK ASSESSMENT REPORT', report)
        self.assertIn('user1@example.com', report)
        self.assertIn('user2@example.com', report)
        self.assertIn('HIGH', report)
        self.assertIn('LOW', report)
        self.assertIn('SPAM TRAP DETECTED', report)


def run_tests():
    """Run all tests with detailed output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRiskScoring))
    suite.addTests(loader.loadTestsFromTestCase(TestBatchAssessment))
    suite.addTests(loader.loadTestsFromTestCase(TestReportGeneration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
