#!/usr/bin/env python3
"""
Unit Tests for Feedback Loop System
Tests feedback submission, score updates, and scheduled re-verification
"""

import unittest
from unittest.mock import patch, MagicMock
from feedback_loop import FeedbackLoop, process_bounce, process_delivery
from datetime import datetime, timedelta


class TestFeedbackSubmission(unittest.TestCase):
    """Test feedback submission."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loop = FeedbackLoop()
        self.loop.storage = MagicMock()
    
    def test_hard_bounce_processing(self):
        """Test hard bounce marks email as invalid."""
        # Mock storage
        self.loop.storage.get_record_by_email.return_value = {
            'id': 1,
            'email': 'user@example.com',
            'confidence_score': 80,
            'bounce_count': 0
        }
        
        self.loop.storage.increment_bounce_count.return_value = {
            'bounce_count': 1
        }
        
        self.loop.storage.update_record.return_value = {}
        
        # Process hard bounce
        result = self.loop.process_bounce(
            'user@example.com',
            'hard',
            'Mailbox does not exist'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['bounce_type'], 'hard')
        self.assertEqual(result['confidence_score'], 0)
        self.assertTrue(result['marked_invalid'])
        self.assertIn('hard bounce', result['action_taken'].lower())
    
    def test_soft_bounce_processing(self):
        """Test soft bounce reduces confidence."""
        # Mock storage
        self.loop.storage.get_record_by_email.return_value = {
            'id': 1,
            'email': 'user@example.com',
            'confidence_score': 80,
            'bounce_count': 0
        }
        
        self.loop.storage.increment_bounce_count.return_value = {
            'bounce_count': 1
        }
        
        self.loop.storage.update_record.return_value = {}
        
        # Process soft bounce
        result = self.loop.process_bounce(
            'user@example.com',
            'soft',
            'Mailbox full'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['bounce_type'], 'soft')
        self.assertLess(result['confidence_score'], 80)
        self.assertFalse(result['marked_invalid'])
    
    def test_repeated_soft_bounces(self):
        """Test repeated soft bounces mark email invalid."""
        # Mock storage - 3rd soft bounce
        self.loop.storage.get_record_by_email.return_value = {
            'id': 1,
            'email': 'user@example.com',
            'confidence_score': 60,
            'bounce_count': 2
        }
        
        self.loop.storage.increment_bounce_count.return_value = {
            'bounce_count': 3
        }
        
        self.loop.storage.update_record.return_value = {}
        
        # Process 3rd soft bounce
        result = self.loop.process_bounce(
            'user@example.com',
            'soft',
            'Temporary failure'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['bounce_count'], 3)
        self.assertTrue(result['marked_invalid'])
    
    def test_delivery_confirmation(self):
        """Test successful delivery increases confidence."""
        # Mock storage
        self.loop.storage.get_record_by_email.return_value = {
            'id': 1,
            'email': 'user@example.com',
            'confidence_score': 70
        }
        
        self.loop.storage.update_record.return_value = {}
        
        # Process delivery
        result = self.loop.process_delivery(
            'user@example.com',
            'delivered'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['delivery_status'], 'delivered')
        self.assertGreater(result['confidence_score'], 70)
    
    def test_email_opened_feedback(self):
        """Test email opened increases confidence more."""
        # Mock storage
        self.loop.storage.get_record_by_email.return_value = {
            'id': 1,
            'email': 'user@example.com',
            'confidence_score': 70
        }
        
        self.loop.storage.update_record.return_value = {}
        
        # Process opened
        result = self.loop.process_delivery(
            'user@example.com',
            'opened'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['delivery_status'], 'opened')
        self.assertGreaterEqual(result['confidence_score'], 80)
    
    def test_spam_complaint(self):
        """Test spam complaint zeros confidence."""
        # Mock storage
        self.loop.storage.get_record_by_email.return_value = {
            'id': 1,
            'email': 'user@example.com',
            'confidence_score': 90
        }
        
        self.loop.storage.update_record.return_value = {}
        
        # Process complaint
        result = self.loop.process_complaint(
            'user@example.com',
            'spam'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['complaint_type'], 'spam')
        self.assertEqual(result['confidence_score'], 0)
        self.assertIn('removal', result['action_taken'].lower())
    
    def test_email_not_found(self):
        """Test feedback for non-existent email."""
        # Mock storage - email not found
        self.loop.storage.get_record_by_email.return_value = None
        
        result = self.loop.process_bounce(
            'nonexistent@example.com',
            'hard'
        )
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'].lower())


class TestScoreUpdate(unittest.TestCase):
    """Test automatic score updates."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loop = FeedbackLoop()
        self.loop.storage = MagicMock()
    
    def test_confidence_score_update(self):
        """Test confidence score is updated correctly."""
        # Mock storage
        self.loop.storage.get_record_by_email.return_value = {
            'id': 1,
            'email': 'user@example.com',
            'confidence_score': 80,
            'bounce_count': 0
        }
        
        self.loop.storage.increment_bounce_count.return_value = {
            'bounce_count': 1
        }
        
        # Track update calls
        update_calls = []
        def track_update(record_id, updates):
            update_calls.append(updates)
            return {}
        
        self.loop.storage.update_record.side_effect = track_update
        
        # Process bounce
        result = self.loop.process_bounce('user@example.com', 'soft')
        
        # Verify update was called with new confidence
        self.assertEqual(len(update_calls), 1)
        self.assertIn('confidence_score', update_calls[0])
        self.assertLess(update_calls[0]['confidence_score'], 80)
    
    def test_risk_score_recalculation(self):
        """Test risk score is recalculated after feedback."""
        # Mock storage
        self.loop.storage.get_record_by_email.return_value = {
            'id': 1,
            'email': 'user@example.com',
            'confidence_score': 80,
            'bounce_count': 0,
            'is_disposable': False,
            'is_role_based': False,
            'is_catch_all': False
        }
        
        self.loop.storage.increment_bounce_count.return_value = {
            'bounce_count': 1
        }
        
        self.loop.storage.update_record.return_value = {}
        
        # Process bounce
        result = self.loop.process_bounce('user@example.com', 'hard')
        
        # Verify risk score is included
        self.assertIn('risk_score', result)
        self.assertIn('risk_level', result)


class TestBatchFeedback(unittest.TestCase):
    """Test batch feedback processing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loop = FeedbackLoop()
        self.loop.storage = MagicMock()
    
    def test_batch_feedback_processing(self):
        """Test processing multiple feedback events."""
        # Mock storage
        def get_record(email):
            return {
                'id': 1,
                'email': email,
                'confidence_score': 70,
                'bounce_count': 0
            }
        
        self.loop.storage.get_record_by_email.side_effect = get_record
        self.loop.storage.increment_bounce_count.return_value = {'bounce_count': 1}
        self.loop.storage.update_record.return_value = {}
        
        # Batch feedback
        feedback = [
            {'email': 'user1@example.com', 'type': 'bounce', 'bounce_type': 'hard'},
            {'email': 'user2@example.com', 'type': 'delivery', 'delivery_status': 'delivered'},
            {'email': 'user3@example.com', 'type': 'complaint', 'complaint_type': 'spam'}
        ]
        
        result = self.loop.batch_process_feedback(feedback)
        
        self.assertEqual(result['total'], 3)
        self.assertEqual(result['processed'], 3)
        self.assertEqual(result['bounces'], 1)
        self.assertEqual(result['deliveries'], 1)
        self.assertEqual(result['complaints'], 1)
        self.assertEqual(result['errors'], 0)


class TestScheduledReverification(unittest.TestCase):
    """Test scheduled re-verification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loop = FeedbackLoop()
        self.loop.storage = MagicMock()
    
    def test_schedule_reverification(self):
        """Test scheduling re-verification of old emails."""
        # Mock old records
        old_date = (datetime.utcnow() - timedelta(days=35)).isoformat()
        recent_date = (datetime.utcnow() - timedelta(days=5)).isoformat()
        
        self.loop.storage.get_all_records.return_value = [
            {'email': 'old1@example.com', 'validated_at': old_date},
            {'email': 'old2@example.com', 'validated_at': old_date},
            {'email': 'recent@example.com', 'validated_at': recent_date}
        ]
        
        result = self.loop.schedule_reverification(days_old=30, max_emails=100)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['total_old_emails'], 2)
        self.assertEqual(result['scheduled_for_reverification'], 2)
        self.assertIn('old1@example.com', result['emails'])
        self.assertIn('old2@example.com', result['emails'])
        self.assertNotIn('recent@example.com', result['emails'])
    
    @patch('feedback_loop.validate_email_with_smtp')
    def test_reverify_email(self, mock_validate):
        """Test re-verifying a single email."""
        # Mock validation
        mock_validate.return_value = {
            'valid': True,
            'confidence_score': 85,
            'checks': {'syntax': True, 'dns_valid': True}
        }
        
        self.loop.storage.create_record.return_value = {
            'id': 1,
            'email': 'user@example.com'
        }
        
        result = self.loop.reverify_email('user@example.com')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['email'], 'user@example.com')
        self.assertTrue(result['valid'])
        self.assertEqual(result['confidence_score'], 85)
        self.assertIn('reverified_at', result)
    
    @patch('feedback_loop.validate_email_with_smtp')
    @patch('feedback_loop.time.sleep')
    def test_batch_reverify(self, mock_sleep, mock_validate):
        """Test batch re-verification with delay."""
        # Mock validation
        mock_validate.return_value = {
            'valid': True,
            'confidence_score': 90,
            'checks': {}
        }
        
        self.loop.storage.create_record.return_value = {'id': 1}
        
        emails = ['user1@example.com', 'user2@example.com']
        result = self.loop.batch_reverify(emails, delay_seconds=1)
        
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['successful'], 2)
        self.assertEqual(result['failed'], 0)
        
        # Verify delay was called
        self.assertEqual(mock_sleep.call_count, 2)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    @patch('feedback_loop.FeedbackLoop')
    def test_process_bounce_function(self, mock_loop_class):
        """Test convenience bounce function."""
        mock_loop = MagicMock()
        mock_loop.process_bounce.return_value = {'success': True}
        mock_loop_class.return_value = mock_loop
        
        result = process_bounce('user@example.com', 'hard', 'Test')
        
        self.assertTrue(result['success'])
        mock_loop.process_bounce.assert_called_once()
    
    @patch('feedback_loop.FeedbackLoop')
    def test_process_delivery_function(self, mock_loop_class):
        """Test convenience delivery function."""
        mock_loop = MagicMock()
        mock_loop.process_delivery.return_value = {'success': True}
        mock_loop_class.return_value = mock_loop
        
        result = process_delivery('user@example.com', 'delivered')
        
        self.assertTrue(result['success'])
        mock_loop.process_delivery.assert_called_once()


def run_tests():
    """Run all tests with detailed output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFeedbackSubmission))
    suite.addTests(loader.loadTestsFromTestCase(TestScoreUpdate))
    suite.addTests(loader.loadTestsFromTestCase(TestBatchFeedback))
    suite.addTests(loader.loadTestsFromTestCase(TestScheduledReverification))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))
    
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
