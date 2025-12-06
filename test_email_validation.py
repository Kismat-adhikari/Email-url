#!/usr/bin/env python3
"""
Unit Tests for Email Validation with SMTP Verification
Tests all validation features including SMTP and catch-all detection
"""

import unittest
from unittest.mock import patch, MagicMock
from email_validator_smtp import (
    validate_email_with_smtp,
    verify_smtp_mailbox,
    detect_catch_all_domain,
    _calculate_confidence_with_smtp
)
from emailvalidator_unified import validate_email, validate_email_advanced


class TestBasicValidation(unittest.TestCase):
    """Test basic email syntax validation."""
    
    def test_valid_email(self):
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "alice+tag@test.org",
            "admin@subdomain.example.com",
            "test_123@domain.com"
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                result = validate_email(email)
                self.assertTrue(result, f"{email} should be valid")
    
    def test_invalid_email(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "invalid",
            "@example.com",
            "user@",
            "user@@example.com",
            "user@example",
            ".user@example.com",
            "user..name@example.com",
            "user @example.com",
            ""
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                result = validate_email(email)
                self.assertFalse(result, f"{email} should be invalid")


class TestDisposableEmailDetection(unittest.TestCase):
    """Test disposable email detection."""
    
    def test_disposable_email(self):
        """Test detection of disposable email domains."""
        disposable_emails = [
            "test@tempmail.com",
            "user@guerrillamail.com",
            "fake@10minutemail.com",
            "temp@mailinator.com",
            "throwaway@yopmail.com"
        ]
        
        for email in disposable_emails:
            with self.subTest(email=email):
                result = validate_email_advanced(email, check_dns=False, check_mx=False)
                self.assertTrue(result['checks']['is_disposable'], 
                              f"{email} should be detected as disposable")
    
    def test_non_disposable_email(self):
        """Test that legitimate domains are not flagged as disposable."""
        legitimate_emails = [
            "user@gmail.com",
            "test@yahoo.com",
            "admin@outlook.com",
            "contact@company.com"
        ]
        
        for email in legitimate_emails:
            with self.subTest(email=email):
                result = validate_email_advanced(email, check_dns=False, check_mx=False)
                self.assertFalse(result['checks']['is_disposable'],
                               f"{email} should NOT be disposable")


class TestRoleBasedDetection(unittest.TestCase):
    """Test role-based email detection."""
    
    def test_role_based_email(self):
        """Test detection of role-based email addresses."""
        role_emails = [
            "admin@example.com",
            "info@company.com",
            "support@test.org",
            "sales@business.com",
            "noreply@service.com"
        ]
        
        for email in role_emails:
            with self.subTest(email=email):
                result = validate_email_advanced(email, check_dns=False, check_mx=False)
                self.assertTrue(result['checks']['is_role_based'],
                              f"{email} should be detected as role-based")
    
    def test_personal_email(self):
        """Test that personal emails are not flagged as role-based."""
        personal_emails = [
            "john.doe@example.com",
            "alice.smith@company.com",
            "bob123@test.org"
        ]
        
        for email in personal_emails:
            with self.subTest(email=email):
                result = validate_email_advanced(email, check_dns=False, check_mx=False)
                self.assertFalse(result['checks']['is_role_based'],
                               f"{email} should NOT be role-based")


class TestSMTPVerification(unittest.TestCase):
    """Test SMTP mailbox verification."""
    
    @patch('email_validator_smtp.smtplib.SMTP')
    @patch('email_validator_smtp.dns.resolver.resolve')
    def test_smtp_success(self, mock_dns, mock_smtp):
        """Test successful SMTP verification."""
        # Mock DNS MX records
        mock_mx = MagicMock()
        mock_mx.exchange = "mail.example.com."
        mock_dns.return_value = [mock_mx]
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_server.connect.return_value = (220, "Ready")
        mock_server.helo.return_value = (250, "OK")
        mock_server.mail.return_value = (250, "OK")
        mock_server.rcpt.return_value = (250, "OK")
        mock_smtp.return_value = mock_server
        
        result = verify_smtp_mailbox("user@example.com")
        
        self.assertTrue(result['smtp_valid'])
        self.assertEqual(result['smtp_code'], 250)
        self.assertIsNone(result['error'])
    
    @patch('email_validator_smtp.smtplib.SMTP')
    @patch('email_validator_smtp.dns.resolver.resolve')
    def test_smtp_mailbox_not_exist(self, mock_dns, mock_smtp):
        """Test SMTP verification when mailbox doesn't exist."""
        # Mock DNS MX records
        mock_mx = MagicMock()
        mock_mx.exchange = "mail.example.com."
        mock_dns.return_value = [mock_mx]
        
        # Mock SMTP server - mailbox doesn't exist
        mock_server = MagicMock()
        mock_server.connect.return_value = (220, "Ready")
        mock_server.helo.return_value = (250, "OK")
        mock_server.mail.return_value = (250, "OK")
        mock_server.rcpt.return_value = (550, "Mailbox not found")
        mock_smtp.return_value = mock_server
        
        result = verify_smtp_mailbox("nonexistent@example.com")
        
        self.assertFalse(result['smtp_valid'])
        self.assertEqual(result['smtp_code'], 550)
        self.assertIn("Mailbox does not exist", result['error'])
    
    @patch('email_validator_smtp.smtplib.SMTP')
    @patch('email_validator_smtp.dns.resolver.resolve')
    def test_smtp_connection_failure(self, mock_dns, mock_smtp):
        """Test SMTP verification when connection fails."""
        # Mock DNS MX records
        mock_mx = MagicMock()
        mock_mx.exchange = "mail.example.com."
        mock_dns.return_value = [mock_mx]
        
        # Mock SMTP connection failure
        mock_smtp.side_effect = Exception("Connection refused")
        
        result = verify_smtp_mailbox("user@example.com")
        
        self.assertFalse(result['smtp_valid'])
        self.assertIsNotNone(result['error'])
    
    def test_smtp_no_mx_records(self):
        """Test SMTP verification when domain has no MX records."""
        result = verify_smtp_mailbox("user@nonexistent-domain-12345.com")
        
        self.assertFalse(result['smtp_valid'])
        self.assertIn("No MX records", result['error'])


class TestCatchAllDetection(unittest.TestCase):
    """Test catch-all domain detection."""
    
    @patch('email_validator_smtp.smtplib.SMTP')
    @patch('email_validator_smtp.dns.resolver.resolve')
    def test_catch_all_domain(self, mock_dns, mock_smtp):
        """Test detection of catch-all domains."""
        # Mock DNS MX records
        mock_mx = MagicMock()
        mock_mx.exchange = "mail.catchall.com."
        mock_dns.return_value = [mock_mx]
        
        # Mock SMTP server - accepts all emails (catch-all)
        mock_server = MagicMock()
        mock_server.connect.return_value = (220, "Ready")
        mock_server.helo.return_value = (250, "OK")
        mock_server.mail.return_value = (250, "OK")
        mock_server.rcpt.return_value = (250, "OK")  # Accepts fake email
        mock_smtp.return_value = mock_server
        
        result = detect_catch_all_domain("catchall.com")
        
        self.assertTrue(result['is_catch_all'])
        self.assertEqual(result['smtp_code'], 250)
    
    @patch('email_validator_smtp.smtplib.SMTP')
    @patch('email_validator_smtp.dns.resolver.resolve')
    def test_non_catch_all_domain(self, mock_dns, mock_smtp):
        """Test detection of non-catch-all domains."""
        # Mock DNS MX records
        mock_mx = MagicMock()
        mock_mx.exchange = "mail.example.com."
        mock_dns.return_value = [mock_mx]
        
        # Mock SMTP server - rejects fake emails (not catch-all)
        mock_server = MagicMock()
        mock_server.connect.return_value = (220, "Ready")
        mock_server.helo.return_value = (250, "OK")
        mock_server.mail.return_value = (250, "OK")
        mock_server.rcpt.return_value = (550, "Mailbox not found")  # Rejects fake email
        mock_smtp.return_value = mock_server
        
        result = detect_catch_all_domain("example.com")
        
        self.assertFalse(result['is_catch_all'])


class TestConfidenceScoring(unittest.TestCase):
    """Test confidence score calculation."""
    
    def test_perfect_score(self):
        """Test perfect confidence score (100)."""
        checks = {
            'syntax': True,
            'dns_valid': True,
            'mx_records': True,
            'smtp_verified': True,
            'is_disposable': False,
            'is_role_based': False,
            'is_catch_all': False
        }
        
        score = _calculate_confidence_with_smtp(checks)
        self.assertEqual(score, 100)
    
    def test_syntax_only_score(self):
        """Test score with only syntax validation."""
        checks = {
            'syntax': True,
            'dns_valid': False,
            'mx_records': False,
            'smtp_verified': False,
            'is_disposable': True,
            'is_role_based': True,
            'is_catch_all': True
        }
        
        score = _calculate_confidence_with_smtp(checks)
        self.assertEqual(score, 30)
    
    def test_no_smtp_score(self):
        """Test score without SMTP verification."""
        checks = {
            'syntax': True,
            'dns_valid': True,
            'mx_records': True,
            'smtp_verified': False,
            'is_disposable': False,
            'is_role_based': False,
            'is_catch_all': False
        }
        
        score = _calculate_confidence_with_smtp(checks)
        self.assertEqual(score, 80)
    
    def test_disposable_penalty(self):
        """Test score penalty for disposable emails."""
        checks = {
            'syntax': True,
            'dns_valid': True,
            'mx_records': True,
            'smtp_verified': True,
            'is_disposable': True,  # Penalty
            'is_role_based': False,
            'is_catch_all': False
        }
        
        score = _calculate_confidence_with_smtp(checks)
        self.assertEqual(score, 90)  # -10 for disposable


class TestIntegration(unittest.TestCase):
    """Integration tests for complete validation flow."""
    
    @patch('email_validator_smtp.verify_smtp_mailbox')
    def test_complete_validation_with_smtp(self, mock_smtp):
        """Test complete validation with SMTP enabled."""
        # Mock SMTP verification
        mock_smtp.return_value = {
            'smtp_valid': True,
            'smtp_code': 250,
            'smtp_message': 'OK',
            'is_catch_all': False,
            'error': None
        }
        
        result = validate_email_with_smtp(
            "user@example.com",
            enable_smtp=True,
            check_dns=False,
            check_mx=False
        )
        
        self.assertIn('smtp_details', result)
        self.assertIn('is_catch_all', result)
        self.assertIn('confidence_score', result)
        self.assertTrue(result['checks']['smtp_verified'])
    
    def test_complete_validation_without_smtp(self):
        """Test complete validation with SMTP disabled."""
        result = validate_email_with_smtp(
            "user@example.com",
            enable_smtp=False,
            check_dns=False,
            check_mx=False
        )
        
        self.assertIsNone(result['smtp_details'])
        self.assertFalse(result['is_catch_all'])
        self.assertIn('confidence_score', result)


def run_tests():
    """Run all tests with detailed output."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBasicValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestDisposableEmailDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestRoleBasedDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestSMTPVerification))
    suite.addTests(loader.loadTestsFromTestCase(TestCatchAllDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestConfidenceScoring))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
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
