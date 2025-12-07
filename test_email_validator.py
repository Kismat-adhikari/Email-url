#!/usr/bin/env python3
"""
Unit and Integration Tests for Email Validation System
Tests typo correction, SMTP validation, Supabase operations, and API endpoints
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from emailvalidator_unified import (
    validate_email,
    validate_email_advanced,
    validate_batch,
    _suggest_domain_correction,
    _is_disposable_email,
    _is_role_based_email
)


class TestBasicValidation(unittest.TestCase):
    """Test basic email syntax validation"""
    
    def test_valid_emails(self):
        """Test valid email addresses"""
        valid_emails = [
            'user@example.com',
            'john.doe@company.co.uk',
            'test+tag@gmail.com',
            'user_name@domain.org',
            'a@b.co'
        ]
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(validate_email(email), f"{email} should be valid")
    
    def test_invalid_emails(self):
        """Test invalid email addresses"""
        invalid_emails = [
            'invalid',
            '@example.com',
            'user@',
            'user @example.com',
            'user@.com',
            'user..name@example.com',
            '.user@example.com',
            'user.@example.com',
            'user@domain',
            'user@domain..com',
            'a' * 65 + '@example.com',  # Local part too long
            'user@' + 'a' * 254 + '.com'  # Domain too long
        ]
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(validate_email(email), f"{email} should be invalid")
    
    def test_edge_cases(self):
        """Test edge cases"""
        self.assertFalse(validate_email(''))
        self.assertFalse(validate_email('   '))
        self.assertFalse(validate_email('user@@example.com'))
        self.assertFalse(validate_email('user@exam ple.com'))


class TestTypoCorrection(unittest.TestCase):
    """Test typo detection and correction"""
    
    def test_exact_typo_corrections(self):
        """Test exact typo mappings"""
        typos = {
            'gamil.com': 'gmail.com',
            'gmial.com': 'gmail.com',
            'hotnail.com': 'hotmail.com',
            'hotmial.com': 'hotmail.com',
            'outlok.com': 'outlook.com',
            'yahooo.com': 'yahoo.com',
            'iclod.com': 'icloud.com'
        }
        for typo, correct in typos.items():
            with self.subTest(typo=typo):
                suggestion = _suggest_domain_correction(typo)
                self.assertEqual(suggestion, correct, 
                    f"{typo} should suggest {correct}, got {suggestion}")
    
    def test_fuzzy_typo_corrections(self):
        """Test fuzzy matching for typos"""
        # These should trigger fuzzy matching
        fuzzy_typos = [
            ('gmaill.com', 'gmail.com'),
            ('yaho.com', 'yahoo.com'),
            ('hotmai.com', 'hotmail.com')
        ]
        for typo, expected in fuzzy_typos:
            with self.subTest(typo=typo):
                suggestion = _suggest_domain_correction(typo)
                self.assertEqual(suggestion, expected,
                    f"{typo} should suggest {expected}, got {suggestion}")
    
    def test_no_suggestion_for_valid_domains(self):
        """Test that valid domains don't get suggestions"""
        valid_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        for domain in valid_domains:
            with self.subTest(domain=domain):
                suggestion = _suggest_domain_correction(domain)
                self.assertIsNone(suggestion, 
                    f"{domain} should not get a suggestion")
    
    def test_no_suggestion_for_unknown_domains(self):
        """Test that completely different domains don't get suggestions"""
        unknown_domains = ['mycompany.com', 'example.org', 'test123.net']
        for domain in unknown_domains:
            with self.subTest(domain=domain):
                suggestion = _suggest_domain_correction(domain)
                # Should be None or not match common domains
                if suggestion:
                    self.fail(f"{domain} should not suggest {suggestion}")


class TestAdvancedValidation(unittest.TestCase):
    """Test advanced validation features"""
    
    def test_disposable_email_detection(self):
        """Test disposable email domain detection"""
        disposable = [
            'tempmail.com',
            'guerrillamail.com',
            '10minutemail.com',
            'mailinator.com'
        ]
        for domain in disposable:
            with self.subTest(domain=domain):
                self.assertTrue(_is_disposable_email(domain),
                    f"{domain} should be detected as disposable")
    
    def test_non_disposable_emails(self):
        """Test that regular domains are not flagged as disposable"""
        regular = ['gmail.com', 'yahoo.com', 'company.com']
        for domain in regular:
            with self.subTest(domain=domain):
                self.assertFalse(_is_disposable_email(domain),
                    f"{domain} should not be disposable")
    
    def test_role_based_detection(self):
        """Test role-based email detection"""
        role_based = ['admin', 'info', 'support', 'sales', 'noreply']
        for local in role_based:
            with self.subTest(local=local):
                self.assertTrue(_is_role_based_email(local),
                    f"{local} should be detected as role-based")
    
    def test_non_role_based(self):
        """Test that personal emails are not flagged as role-based"""
        personal = ['john.doe', 'jane', 'user123']
        for local in personal:
            with self.subTest(local=local):
                self.assertFalse(_is_role_based_email(local),
                    f"{local} should not be role-based")
    
    @patch('emailvalidator_unified.socket.gethostbyname')
    @patch('emailvalidator_unified.dns.resolver.resolve')
    def test_advanced_validation_structure(self, mock_dns, mock_socket):
        """Test advanced validation returns correct structure"""
        mock_socket.return_value = '1.2.3.4'
        mock_dns.return_value = [Mock(exchange='mx.example.com')]
        
        result = validate_email_advanced('user@example.com')
        
        # Check structure
        self.assertIn('valid', result)
        self.assertIn('email', result)
        self.assertIn('checks', result)
        self.assertIn('confidence_score', result)
        self.assertIn('reason', result)
        
        # Check checks structure
        checks = result['checks']
        self.assertIn('syntax', checks)
        self.assertIn('dns_valid', checks)
        self.assertIn('mx_records', checks)
        self.assertIn('is_disposable', checks)
        self.assertIn('is_role_based', checks)


class TestBatchValidation(unittest.TestCase):
    """Test batch validation"""
    
    def test_batch_validation_basic(self):
        """Test basic batch validation"""
        emails = [
            'valid@example.com',
            'invalid@',
            'another@test.com'
        ]
        results = validate_batch(emails, advanced=False)
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn('email', result)
            self.assertIn('valid', result)
    
    def test_batch_validation_advanced(self):
        """Test advanced batch validation"""
        emails = ['user@gmail.com', 'test@yahoo.com']
        results = validate_batch(emails, advanced=True)
        
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn('confidence_score', result)
            self.assertIn('checks', result)
    
    def test_empty_batch(self):
        """Test empty batch"""
        results = validate_batch([])
        self.assertEqual(len(results), 0)


class TestSMTPValidation(unittest.TestCase):
    """Test SMTP validation (mocked)"""
    
    @patch('email_validator_smtp.smtplib.SMTP')
    @patch('email_validator_smtp.dns.resolver.resolve')
    def test_smtp_validation_success(self, mock_dns, mock_smtp):
        """Test successful SMTP validation"""
        from email_validator_smtp import verify_smtp_mailbox
        
        # Mock DNS
        mock_mx = Mock()
        mock_mx.exchange = 'mx.gmail.com.'
        mock_dns.return_value = [mock_mx]
        
        # Mock SMTP
        mock_server = MagicMock()
        mock_server.connect.return_value = (220, b'Ready')
        mock_server.helo.return_value = (250, b'OK')
        mock_server.mail.return_value = (250, b'OK')
        mock_server.rcpt.return_value = (250, b'OK')
        mock_smtp.return_value = mock_server
        
        result = verify_smtp_mailbox('user@gmail.com')
        
        self.assertTrue(result['smtp_valid'])
        self.assertEqual(result['smtp_code'], 250)
    
    @patch('email_validator_smtp.smtplib.SMTP')
    @patch('email_validator_smtp.dns.resolver.resolve')
    def test_smtp_validation_failure(self, mock_dns, mock_smtp):
        """Test SMTP validation failure"""
        from email_validator_smtp import verify_smtp_mailbox
        
        # Mock DNS
        mock_mx = Mock()
        mock_mx.exchange = 'mx.example.com.'
        mock_dns.return_value = [mock_mx]
        
        # Mock SMTP - mailbox doesn't exist
        mock_server = MagicMock()
        mock_server.connect.return_value = (220, b'Ready')
        mock_server.helo.return_value = (250, b'OK')
        mock_server.mail.return_value = (250, b'OK')
        mock_server.rcpt.return_value = (550, b'Mailbox not found')
        mock_smtp.return_value = mock_server
        
        result = verify_smtp_mailbox('nonexistent@example.com')
        
        self.assertFalse(result['smtp_valid'])
        self.assertEqual(result['smtp_code'], 550)


class TestSupabaseStorage(unittest.TestCase):
    """Test Supabase storage operations (mocked)"""
    
    @patch('supabase_storage.create_client')
    def test_create_record(self, mock_client):
        """Test creating a validation record"""
        from supabase_storage import SupabaseStorage
        
        # Mock Supabase client
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_response = Mock()
        mock_response.data = [{'id': 123, 'email': 'test@example.com'}]
        
        mock_table.insert.return_value.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        mock_client.return_value = mock_supabase
        
        storage = SupabaseStorage(url='http://test', key='test-key')
        
        record = storage.create_record({
            'anon_user_id': 'test-uuid',
            'email': 'test@example.com',
            'valid': True,
            'confidence_score': 95
        })
        
        self.assertEqual(record['id'], 123)
        self.assertEqual(record['email'], 'test@example.com')
    
    @patch('supabase_storage.create_client')
    def test_get_user_history(self, mock_client):
        """Test fetching user history"""
        from supabase_storage import SupabaseStorage
        
        # Mock Supabase client
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_response = Mock()
        mock_response.data = [
            {'id': 1, 'email': 'test1@example.com'},
            {'id': 2, 'email': 'test2@example.com'}
        ]
        
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        mock_client.return_value = mock_supabase
        
        storage = SupabaseStorage(url='http://test', key='test-key')
        history = storage.get_user_history('test-uuid')
        
        self.assertEqual(len(history), 2)


class TestAPIEndpoints(unittest.TestCase):
    """Test Flask API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        os.environ['SUPABASE_URL'] = 'http://test'
        os.environ['SUPABASE_KEY'] = 'test-key'
        
        from app_anon_history import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.headers = {'X-User-ID': '12345678-1234-4234-8234-123456789012'}
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_validate_missing_header(self):
        """Test validation without user ID header"""
        response = self.client.post('/api/validate',
            json={'email': 'test@example.com'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Authentication required', data['error'])
    
    def test_validate_invalid_uuid(self):
        """Test validation with invalid UUID"""
        response = self.client.post('/api/validate',
            json={'email': 'test@example.com'},
            headers={'X-User-ID': 'invalid-uuid'})
        self.assertEqual(response.status_code, 400)
    
    def test_validate_missing_email(self):
        """Test validation without email parameter"""
        response = self.client.post('/api/validate',
            json={},
            headers=self.headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Missing email parameter', data['error'])
    
    @patch('app_anon_history.get_storage')
    @patch('app_anon_history.validate_email_advanced')
    def test_validate_success(self, mock_validate, mock_storage):
        """Test successful validation"""
        # Mock validation result
        mock_validate.return_value = {
            'valid': True,
            'email': 'test@example.com',
            'confidence_score': 95,
            'checks': {'syntax': True}
        }
        
        # Mock storage
        mock_storage_instance = MagicMock()
        mock_storage_instance.create_record.return_value = {'id': 123}
        mock_storage.return_value = mock_storage_instance
        
        response = self.client.post('/api/validate',
            json={'email': 'test@example.com', 'advanced': True},
            headers=self.headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['valid'])
        self.assertEqual(data['email'], 'test@example.com')
    
    def test_batch_validate_invalid_input(self):
        """Test batch validation with invalid input"""
        response = self.client.post('/api/validate/batch',
            json={'emails': 'not-an-array'},
            headers=self.headers)
        self.assertEqual(response.status_code, 400)
    
    def test_batch_validate_too_many(self):
        """Test batch validation with too many emails"""
        emails = ['test@example.com'] * 1001
        response = self.client.post('/api/validate/batch',
            json={'emails': emails},
            headers=self.headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Too many emails', data['error'])


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBasicValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestTypoCorrection))
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestBatchValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestSMTPValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestSupabaseStorage))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIEndpoints))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
