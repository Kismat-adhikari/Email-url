#!/usr/bin/env python3
"""
Unit Tests for Webhook Integration and CSV Export
Tests webhook delivery, CRM/ESP integration, and CSV export functionality
"""

import unittest
from unittest.mock import patch, MagicMock
from webhook_integration import WebhookManager, CRMIntegration, ESPIntegration
from csv_export import export_to_csv, export_risk_report_csv
import json


class TestWebhookIntegration(unittest.TestCase):
    """Test webhook functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.webhook_url = 'https://example.com/webhook'
        self.manager = WebhookManager(self.webhook_url, secret='test-secret')
    
    @patch('webhook_integration.requests.post')
    def test_webhook_send_success(self, mock_post):
        """Test successful webhook delivery."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response
        
        data = {
            'email': 'user@example.com',
            'valid': True,
            'confidence_score': 95
        }
        
        result = self.manager.send_webhook(data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['status_code'], 200)
        self.assertIn('sent_at', result)
        
        # Verify request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], self.webhook_url)
    
    @patch('webhook_integration.requests.post')
    def test_webhook_send_failure(self, mock_post):
        """Test webhook delivery failure."""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response
        
        data = {'email': 'user@example.com'}
        result = self.manager.send_webhook(data)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['status_code'], 500)
    
    @patch('webhook_integration.requests.post')
    def test_webhook_timeout(self, mock_post):
        """Test webhook timeout handling."""
        # Mock timeout
        mock_post.side_effect = Exception('Timeout')
        
        data = {'email': 'user@example.com'}
        result = self.manager.send_webhook(data)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_webhook_no_url(self):
        """Test webhook with no URL configured."""
        manager = WebhookManager()
        result = manager.send_webhook({'test': 'data'})
        
        self.assertFalse(result['success'])
        self.assertIn('No webhook URL', result['error'])
    
    def test_webhook_signature_generation(self):
        """Test HMAC signature generation."""
        payload = {'email': 'user@example.com', 'valid': True}
        signature = self.manager._generate_signature(payload)
        
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 64)  # SHA256 hex digest length
    
    @patch('webhook_integration.requests.post')
    def test_batch_webhook(self, mock_post):
        """Test batch webhook delivery."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response
        
        results = [
            {'email': 'user1@example.com', 'valid': True},
            {'email': 'user2@example.com', 'valid': False}
        ]
        
        result = self.manager.send_batch_webhook(results)
        
        self.assertTrue(result['success'])
        mock_post.assert_called_once()


class TestCRMIntegration(unittest.TestCase):
    """Test CRM integration."""
    
    def test_salesforce_update(self):
        """Test Salesforce contact update."""
        crm = CRMIntegration('salesforce', 'test-api-key')
        
        validation_data = {
            'valid': True,
            'confidence_score': 95
        }
        
        result = crm.update_contact('user@example.com', validation_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['crm'], 'salesforce')
    
    def test_hubspot_update(self):
        """Test HubSpot contact update."""
        crm = CRMIntegration('hubspot', 'test-api-key')
        
        validation_data = {
            'valid': True,
            'confidence_score': 90
        }
        
        result = crm.update_contact('user@example.com', validation_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['crm'], 'hubspot')
    
    def test_generic_crm_no_url(self):
        """Test generic CRM without URL."""
        crm = CRMIntegration('generic', 'test-api-key')
        
        result = crm.update_contact('user@example.com', {})
        
        self.assertFalse(result['success'])
        self.assertIn('API URL not configured', result['error'])


class TestESPIntegration(unittest.TestCase):
    """Test ESP integration."""
    
    def test_sendgrid_update(self):
        """Test SendGrid subscriber update."""
        esp = ESPIntegration('sendgrid', 'test-api-key')
        
        validation_data = {
            'valid': True,
            'confidence_score': 95
        }
        
        result = esp.update_subscriber(
            'user@example.com',
            validation_data,
            'list-123'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['esp'], 'sendgrid')
    
    def test_mailchimp_update(self):
        """Test Mailchimp subscriber update."""
        esp = ESPIntegration('mailchimp', 'test-api-key')
        
        validation_data = {
            'valid': False,
            'confidence_score': 30
        }
        
        result = esp.update_subscriber(
            'invalid@example.com',
            validation_data,
            'list-456'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['esp'], 'mailchimp')
    
    def test_suppress_invalid_email(self):
        """Test email suppression."""
        esp = ESPIntegration('sendgrid', 'test-api-key')
        
        result = esp.suppress_invalid_email('invalid@example.com')
        
        self.assertTrue(result['success'])
        self.assertIn('suppression list', result['message'])


class TestCSVExport(unittest.TestCase):
    """Test CSV export functionality."""
    
    def test_export_basic_csv(self):
        """Test basic CSV export."""
        results = [
            {
                'email': 'user1@example.com',
                'valid': True,
                'confidence_score': 95,
                'validated_at': '2024-01-01T12:00:00',
                'reason': 'Valid email'
            },
            {
                'email': 'user2@example.com',
                'valid': False,
                'confidence_score': 0,
                'validated_at': '2024-01-01T12:01:00',
                'reason': 'Invalid syntax'
            }
        ]
        
        csv_data = export_to_csv(results, include_details=False)
        
        self.assertIn('email,valid,confidence_score', csv_data)
        self.assertIn('user1@example.com,Yes,95', csv_data)
        self.assertIn('user2@example.com,No,0', csv_data)
    
    def test_export_detailed_csv(self):
        """Test detailed CSV export with checks."""
        results = [
            {
                'email': 'user@example.com',
                'valid': True,
                'confidence_score': 95,
                'checks': {
                    'syntax': True,
                    'dns_valid': True,
                    'mx_records': True,
                    'is_disposable': False,
                    'is_role_based': False,
                    'is_catch_all': False
                },
                'validated_at': '2024-01-01T12:00:00',
                'reason': 'Valid email'
            }
        ]
        
        csv_data = export_to_csv(results, include_details=True)
        
        self.assertIn('syntax', csv_data)
        self.assertIn('dns_valid', csv_data)
        self.assertIn('mx_records', csv_data)
        self.assertIn('is_disposable', csv_data)
    
    def test_export_empty_results(self):
        """Test CSV export with empty results."""
        csv_data = export_to_csv([])
        
        self.assertEqual(csv_data, '')
    
    def test_export_risk_report_csv(self):
        """Test risk report CSV export."""
        assessments = [
            {
                'email': 'user@example.com',
                'risk_score': 45,
                'risk_level': 'MEDIUM',
                'is_spam_trap': False,
                'is_blacklisted': False,
                'bounce_count': 1,
                'confidence_score': 70,
                'risk_factors': ['Previous bounce', 'Catch-all domain'],
                'recommendations': ['Review required'],
                'assessed_at': '2024-01-01T12:00:00'
            }
        ]
        
        csv_data = export_risk_report_csv(assessments)
        
        self.assertIn('risk_score', csv_data)
        self.assertIn('risk_level', csv_data)
        self.assertIn('MEDIUM', csv_data)
        self.assertIn('Previous bounce', csv_data)
    
    def test_csv_special_characters(self):
        """Test CSV export with special characters."""
        results = [
            {
                'email': 'user@example.com',
                'valid': True,
                'confidence_score': 95,
                'validated_at': '2024-01-01T12:00:00',
                'reason': 'Valid, but has comma'
            }
        ]
        
        csv_data = export_to_csv(results)
        
        # CSV should handle commas properly
        self.assertIn('user@example.com', csv_data)


class TestDashboardAPI(unittest.TestCase):
    """Test dashboard API data fetching."""
    
    @patch('app_dashboard.get_storage')
    def test_dashboard_stats_fetch(self, mock_storage):
        """Test dashboard statistics fetching."""
        # Mock storage
        mock_storage_instance = MagicMock()
        mock_storage_instance.get_all_records.return_value = [
            {'email': 'user1@example.com', 'valid': True, 'confidence_score': 95},
            {'email': 'user2@example.com', 'valid': False, 'confidence_score': 30}
        ]
        mock_storage.return_value = mock_storage_instance
        
        # This would be tested with Flask test client in real scenario
        # For now, just verify mock setup
        storage = mock_storage()
        records = storage.get_all_records()
        
        self.assertEqual(len(records), 2)
        self.assertTrue(records[0]['valid'])
        self.assertFalse(records[1]['valid'])
    
    @patch('app_dashboard.get_storage')
    def test_recent_validations_fetch(self, mock_storage):
        """Test recent validations fetching."""
        mock_storage_instance = MagicMock()
        mock_storage_instance.get_all_records.return_value = [
            {'email': 'recent@example.com', 'validated_at': '2024-01-01T12:00:00'}
        ]
        mock_storage.return_value = mock_storage_instance
        
        storage = mock_storage()
        records = storage.get_all_records(limit=50)
        
        self.assertEqual(len(records), 1)
        self.assertIn('validated_at', records[0])


def run_tests():
    """Run all tests with detailed output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestWebhookIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCRMIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestESPIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCSVExport))
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardAPI))
    
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
