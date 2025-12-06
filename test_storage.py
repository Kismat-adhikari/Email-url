#!/usr/bin/env python3
"""
Unit Tests for Supabase Storage Integration
Tests all CRUD operations and storage functionality
"""

import unittest
from unittest.mock import patch, MagicMock
from supabase_storage import SupabaseStorage
from datetime import datetime
import os


class TestSupabaseStorage(unittest.TestCase):
    """Test Supabase storage operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.storage = SupabaseStorage.__new__(SupabaseStorage)
        self.storage.client = self.mock_client
        self.storage.table_name = 'email_validations'
    
    def test_create_record(self):
        """Test inserting a new email validation record."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 1,
            'email': 'user@example.com',
            'valid': True,
            'confidence_score': 95,
            'created_at': '2024-01-01T12:00:00'
        }]
        
        self.mock_client.table().insert().execute.return_value = mock_response
        
        # Test data
        validation_data = {
            'email': 'user@example.com',
            'valid': True,
            'confidence_score': 95
        }
        
        # Create record
        result = self.storage.create_record(validation_data)
        
        # Assertions
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['email'], 'user@example.com')
        self.assertTrue(result['valid'])
        self.assertEqual(result['confidence_score'], 95)
    
    def test_create_record_missing_fields(self):
        """Test creating record with missing required fields."""
        invalid_data = {
            'email': 'user@example.com'
            # Missing 'valid' and 'confidence_score'
        }
        
        with self.assertRaises(ValueError) as context:
            self.storage.create_record(invalid_data)
        
        self.assertIn('Missing required field', str(context.exception))
    
    def test_get_record_by_email(self):
        """Test fetching a record by email address."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 1,
            'email': 'user@example.com',
            'valid': True,
            'confidence_score': 95
        }]
        
        self.mock_client.table().select().eq().order().limit().execute.return_value = mock_response
        
        # Fetch record
        result = self.storage.get_record_by_email('user@example.com')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['email'], 'user@example.com')
        self.assertTrue(result['valid'])
    
    def test_get_record_by_email_not_found(self):
        """Test fetching non-existent record."""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.data = []
        
        self.mock_client.table().select().eq().order().limit().execute.return_value = mock_response
        
        # Fetch record
        result = self.storage.get_record_by_email('nonexistent@example.com')
        
        # Assertions
        self.assertIsNone(result)
    
    def test_get_validation_history(self):
        """Test fetching validation history for an email."""
        # Mock response with multiple records
        mock_response = MagicMock()
        mock_response.data = [
            {
                'id': 3,
                'email': 'user@example.com',
                'valid': True,
                'confidence_score': 95,
                'validated_at': '2024-01-03T12:00:00'
            },
            {
                'id': 2,
                'email': 'user@example.com',
                'valid': True,
                'confidence_score': 90,
                'validated_at': '2024-01-02T12:00:00'
            },
            {
                'id': 1,
                'email': 'user@example.com',
                'valid': False,
                'confidence_score': 50,
                'validated_at': '2024-01-01T12:00:00'
            }
        ]
        
        self.mock_client.table().select().eq().order().limit().execute.return_value = mock_response
        
        # Fetch history
        history = self.storage.get_validation_history('user@example.com', limit=10)
        
        # Assertions
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]['id'], 3)  # Most recent first
        self.assertEqual(history[2]['id'], 1)  # Oldest last
    
    def test_update_record(self):
        """Test updating a record's confidence score."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 1,
            'email': 'user@example.com',
            'valid': True,
            'confidence_score': 85,  # Updated
            'bounce_count': 1,
            'updated_at': '2024-01-02T12:00:00'
        }]
        
        self.mock_client.table().update().eq().execute.return_value = mock_response
        
        # Update record
        updates = {
            'confidence_score': 85,
            'bounce_count': 1
        }
        result = self.storage.update_record(1, updates)
        
        # Assertions
        self.assertEqual(result['confidence_score'], 85)
        self.assertEqual(result['bounce_count'], 1)
    
    def test_update_record_not_found(self):
        """Test updating non-existent record."""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.data = []
        
        self.mock_client.table().update().eq().execute.return_value = mock_response
        
        # Update record
        with self.assertRaises(Exception) as context:
            self.storage.update_record(999, {'confidence_score': 85})
        
        self.assertIn('not found', str(context.exception))
    
    def test_increment_bounce_count(self):
        """Test incrementing bounce count for an email."""
        # Mock get_record_by_email
        mock_get_response = MagicMock()
        mock_get_response.data = [{
            'id': 1,
            'email': 'user@example.com',
            'bounce_count': 1
        }]
        
        # Mock update
        mock_update_response = MagicMock()
        mock_update_response.data = [{
            'id': 1,
            'email': 'user@example.com',
            'bounce_count': 2,
            'last_bounce_date': '2024-01-02T12:00:00'
        }]
        
        self.mock_client.table().select().eq().order().limit().execute.return_value = mock_get_response
        self.mock_client.table().update().eq().execute.return_value = mock_update_response
        
        # Increment bounce
        result = self.storage.increment_bounce_count('user@example.com')
        
        # Assertions
        self.assertEqual(result['bounce_count'], 2)
        self.assertIn('last_bounce_date', result)
    
    def test_delete_record(self):
        """Test deleting a record by ID."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = [{'id': 1}]
        
        self.mock_client.table().delete().eq().execute.return_value = mock_response
        
        # Delete record
        result = self.storage.delete_record(1)
        
        # Assertions
        self.assertTrue(result)
    
    def test_delete_by_email(self):
        """Test deleting all records for an email."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 1},
            {'id': 2},
            {'id': 3}
        ]
        
        self.mock_client.table().delete().eq().execute.return_value = mock_response
        
        # Delete records
        count = self.storage.delete_by_email('user@example.com')
        
        # Assertions
        self.assertEqual(count, 3)
    
    def test_get_statistics(self):
        """Test getting validation statistics."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {'valid': True, 'confidence_score': 95, 'is_disposable': False, 'is_role_based': False},
            {'valid': True, 'confidence_score': 90, 'is_disposable': False, 'is_role_based': True},
            {'valid': False, 'confidence_score': 30, 'is_disposable': True, 'is_role_based': False},
            {'valid': True, 'confidence_score': 85, 'is_disposable': False, 'is_role_based': False},
        ]
        
        self.mock_client.table().select().execute.return_value = mock_response
        
        # Get statistics
        stats = self.storage.get_statistics()
        
        # Assertions
        self.assertEqual(stats['total_validations'], 4)
        self.assertEqual(stats['valid_count'], 3)
        self.assertEqual(stats['invalid_count'], 1)
        self.assertEqual(stats['disposable_count'], 1)
        self.assertEqual(stats['role_based_count'], 1)
        self.assertGreater(stats['avg_confidence'], 0)
    
    def test_search_records_by_valid(self):
        """Test searching records by validation status."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 1, 'email': 'user1@example.com', 'valid': True},
            {'id': 2, 'email': 'user2@example.com', 'valid': True}
        ]
        
        self.mock_client.table().select().eq().order().limit().execute.return_value = mock_response
        
        # Search records
        results = self.storage.search_records(valid=True)
        
        # Assertions
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r['valid'] for r in results))
    
    def test_search_records_by_confidence(self):
        """Test searching records by confidence score range."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 1, 'email': 'user1@example.com', 'confidence_score': 95},
            {'id': 2, 'email': 'user2@example.com', 'confidence_score': 90}
        ]
        
        self.mock_client.table().select().gte().lte().order().limit().execute.return_value = mock_response
        
        # Search records
        results = self.storage.search_records(min_confidence=80, max_confidence=100)
        
        # Assertions
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r['confidence_score'] >= 80 for r in results))
    
    def test_get_all_records_pagination(self):
        """Test fetching records with pagination."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {'id': i, 'email': f'user{i}@example.com'}
            for i in range(1, 51)  # 50 records
        ]
        
        self.mock_client.table().select().order().range().execute.return_value = mock_response
        
        # Fetch records
        results = self.storage.get_all_records(limit=50, offset=0)
        
        # Assertions
        self.assertEqual(len(results), 50)
    
    @unittest.skip("Skipping connection error test - environment variables are set")
    def test_connection_error(self):
        """Test handling of connection errors."""
        pass


class TestStorageIntegration(unittest.TestCase):
    """Integration tests for storage operations."""
    
    @patch('supabase_storage.create_client')
    def test_full_crud_cycle(self, mock_create_client):
        """Test complete CRUD cycle."""
        # Mock client
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        
        # Mock responses for each operation
        # Create
        mock_client.table().insert().execute.return_value = MagicMock(
            data=[{'id': 1, 'email': 'test@example.com', 'valid': True, 'confidence_score': 95}]
        )
        
        # Read
        mock_client.table().select().eq().order().limit().execute.return_value = MagicMock(
            data=[{'id': 1, 'email': 'test@example.com', 'valid': True, 'confidence_score': 95}]
        )
        
        # Update
        mock_client.table().update().eq().execute.return_value = MagicMock(
            data=[{'id': 1, 'email': 'test@example.com', 'valid': True, 'confidence_score': 85}]
        )
        
        # Delete
        mock_client.table().delete().eq().execute.return_value = MagicMock(
            data=[{'id': 1}]
        )
        
        # Initialize storage
        storage = SupabaseStorage(
            url='https://test.supabase.co',
            key='test-key'
        )
        
        # Create
        record = storage.create_record({
            'email': 'test@example.com',
            'valid': True,
            'confidence_score': 95
        })
        self.assertEqual(record['id'], 1)
        
        # Read
        fetched = storage.get_record_by_email('test@example.com')
        self.assertEqual(fetched['email'], 'test@example.com')
        
        # Update
        updated = storage.update_record(1, {'confidence_score': 85})
        self.assertEqual(updated['confidence_score'], 85)
        
        # Delete
        deleted = storage.delete_record(1)
        self.assertTrue(deleted)


def run_tests():
    """Run all tests with detailed output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSupabaseStorage))
    suite.addTests(loader.loadTestsFromTestCase(TestStorageIntegration))
    
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
