#!/usr/bin/env python3
"""
Test Suite for Anonymous User ID History System
Tests user-specific history, privacy, and cross-user isolation
"""

import requests
import uuid
import time
from typing import Dict, Any

# Configuration
BASE_URL = 'http://localhost:5000'
API_URL = f'{BASE_URL}/api'


class TestAnonHistory:
    """Test anonymous user ID system."""
    
    def __init__(self):
        self.user1_id = str(uuid.uuid4())
        self.user2_id = str(uuid.uuid4())
        print(f"🆔 Test User 1 ID: {self.user1_id}")
        print(f"🆔 Test User 2 ID: {self.user2_id}")
    
    def get_headers(self, user_id: str) -> Dict[str, str]:
        """Get headers with anonymous user ID."""
        return {'X-User-ID': user_id}
    
    def test_missing_user_id(self):
        """Test that requests without X-User-ID header are rejected."""
        print("\n" + "="*70)
        print("TEST 1: Missing X-User-ID Header")
        print("="*70)
        
        try:
            response = requests.post(
                f'{API_URL}/validate',
                json={'email': 'test@example.com', 'advanced': True}
            )
            
            if response.status_code == 400:
                print("✅ PASS: Request rejected without X-User-ID header")
                print(f"   Error: {response.json().get('message')}")
                return True
            else:
                print(f"❌ FAIL: Expected 400, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    def test_validate_with_user_id(self):
        """Test email validation with anonymous user ID."""
        print("\n" + "="*70)
        print("TEST 2: Validate Email with Anonymous User ID")
        print("="*70)
        
        try:
            response = requests.post(
                f'{API_URL}/validate',
                json={'email': 'user1@example.com', 'advanced': True},
                headers=self.get_headers(self.user1_id)
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ PASS: Email validated successfully")
                print(f"   Email: {data.get('email')}")
                print(f"   Valid: {data.get('valid')}")
                print(f"   Confidence: {data.get('confidence_score')}")
                print(f"   Record ID: {data.get('record_id')}")
                print(f"   Stored: {data.get('stored')}")
                return True, data.get('record_id')
            else:
                print(f"❌ FAIL: Expected 200, got {response.status_code}")
                print(f"   Response: {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False, None
    
    def test_batch_validation(self):
        """Test batch validation with anonymous user ID."""
        print("\n" + "="*70)
        print("TEST 3: Batch Validation with Anonymous User ID")
        print("="*70)
        
        emails = [
            'user1-batch1@example.com',
            'user1-batch2@test.com',
            'user1-batch3@gmail.com'
        ]
        
        try:
            response = requests.post(
                f'{API_URL}/validate/batch',
                json={'emails': emails, 'advanced': True},
                headers=self.get_headers(self.user1_id)
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ PASS: Batch validation successful")
                print(f"   Total: {data.get('total')}")
                print(f"   Valid: {data.get('valid_count')}")
                print(f"   Invalid: {data.get('invalid_count')}")
                
                for result in data.get('results', []):
                    print(f"   - {result['email']}: {result['valid']} (ID: {result.get('record_id')})")
                
                return True
            else:
                print(f"❌ FAIL: Expected 200, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    def test_get_user_history(self):
        """Test fetching user-specific history."""
        print("\n" + "="*70)
        print("TEST 4: Get User-Specific History")
        print("="*70)
        
        try:
            response = requests.get(
                f'{API_URL}/history',
                headers=self.get_headers(self.user1_id),
                params={'limit': 100}
            )
            
            if response.status_code == 200:
                data = response.json()
                history = data.get('history', [])
                print("✅ PASS: History retrieved successfully")
                print(f"   Total records: {len(history)}")
                
                if history:
                    print(f"   Latest validation:")
                    latest = history[0]
                    print(f"   - Email: {latest.get('email')}")
                    print(f"   - Valid: {latest.get('valid')}")
                    print(f"   - Date: {latest.get('validated_at')}")
                
                return True, history
            else:
                print(f"❌ FAIL: Expected 200, got {response.status_code}")
                return False, []
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False, []
    
    def test_cross_user_isolation(self):
        """Test that users cannot see each other's history."""
        print("\n" + "="*70)
        print("TEST 5: Cross-User History Isolation")
        print("="*70)
        
        # User 1 validates an email
        print("Step 1: User 1 validates email...")
        response1 = requests.post(
            f'{API_URL}/validate',
            json={'email': 'user1-private@example.com', 'advanced': True},
            headers=self.get_headers(self.user1_id)
        )
        
        if response1.status_code != 200:
            print(f"❌ FAIL: User 1 validation failed")
            return False
        
        record_id = response1.json().get('record_id')
        print(f"   User 1 created record ID: {record_id}")
        
        # User 2 validates a different email
        print("\nStep 2: User 2 validates email...")
        response2 = requests.post(
            f'{API_URL}/validate',
            json={'email': 'user2-private@example.com', 'advanced': True},
            headers=self.get_headers(self.user2_id)
        )
        
        if response2.status_code != 200:
            print(f"❌ FAIL: User 2 validation failed")
            return False
        
        print(f"   User 2 created record ID: {response2.json().get('record_id')}")
        
        # User 1 gets their history
        print("\nStep 3: User 1 fetches history...")
        history1 = requests.get(
            f'{API_URL}/history',
            headers=self.get_headers(self.user1_id)
        ).json().get('history', [])
        
        # User 2 gets their history
        print("Step 4: User 2 fetches history...")
        history2 = requests.get(
            f'{API_URL}/history',
            headers=self.get_headers(self.user2_id)
        ).json().get('history', [])
        
        # Check isolation
        user1_emails = [r['email'] for r in history1]
        user2_emails = [r['email'] for r in history2]
        
        print(f"\nUser 1 history: {len(history1)} records")
        print(f"User 2 history: {len(history2)} records")
        
        # User 1 should see their email but not User 2's
        if 'user1-private@example.com' in user1_emails:
            print("✅ User 1 can see their own email")
        else:
            print("❌ FAIL: User 1 cannot see their own email")
            return False
        
        if 'user2-private@example.com' not in user1_emails:
            print("✅ User 1 cannot see User 2's email")
        else:
            print("❌ FAIL: User 1 can see User 2's email (PRIVACY BREACH!)")
            return False
        
        # User 2 should see their email but not User 1's
        if 'user2-private@example.com' in user2_emails:
            print("✅ User 2 can see their own email")
        else:
            print("❌ FAIL: User 2 cannot see their own email")
            return False
        
        if 'user1-private@example.com' not in user2_emails:
            print("✅ User 2 cannot see User 1's email")
        else:
            print("❌ FAIL: User 2 can see User 1's email (PRIVACY BREACH!)")
            return False
        
        print("\n✅ PASS: Cross-user isolation working correctly")
        return True
    
    def test_delete_record(self):
        """Test deleting a specific record."""
        print("\n" + "="*70)
        print("TEST 6: Delete Specific Record")
        print("="*70)
        
        # Create a record
        print("Step 1: Create a record...")
        response = requests.post(
            f'{API_URL}/validate',
            json={'email': 'delete-me@example.com', 'advanced': True},
            headers=self.get_headers(self.user1_id)
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Failed to create record")
            return False
        
        record_id = response.json().get('record_id')
        print(f"   Created record ID: {record_id}")
        
        # Delete the record
        print("\nStep 2: Delete the record...")
        delete_response = requests.delete(
            f'{API_URL}/history/{record_id}',
            headers=self.get_headers(self.user1_id)
        )
        
        if delete_response.status_code == 200:
            print("✅ PASS: Record deleted successfully")
            return True
        else:
            print(f"❌ FAIL: Expected 200, got {delete_response.status_code}")
            return False
    
    def test_delete_wrong_user(self):
        """Test that users cannot delete other users' records."""
        print("\n" + "="*70)
        print("TEST 7: Prevent Cross-User Record Deletion")
        print("="*70)
        
        # User 1 creates a record
        print("Step 1: User 1 creates a record...")
        response = requests.post(
            f'{API_URL}/validate',
            json={'email': 'user1-protected@example.com', 'advanced': True},
            headers=self.get_headers(self.user1_id)
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Failed to create record")
            return False
        
        record_id = response.json().get('record_id')
        print(f"   User 1 created record ID: {record_id}")
        
        # User 2 tries to delete User 1's record
        print("\nStep 2: User 2 attempts to delete User 1's record...")
        delete_response = requests.delete(
            f'{API_URL}/history/{record_id}',
            headers=self.get_headers(self.user2_id)
        )
        
        if delete_response.status_code == 403:
            print("✅ PASS: Deletion blocked (403 Forbidden)")
            print(f"   Message: {delete_response.json().get('message')}")
            return True
        else:
            print(f"❌ FAIL: Expected 403, got {delete_response.status_code}")
            print("   SECURITY ISSUE: User 2 could delete User 1's record!")
            return False
    
    def test_clear_history(self):
        """Test clearing all user history."""
        print("\n" + "="*70)
        print("TEST 8: Clear All User History")
        print("="*70)
        
        # Get current history count
        print("Step 1: Get current history...")
        history_before = requests.get(
            f'{API_URL}/history',
            headers=self.get_headers(self.user1_id)
        ).json().get('history', [])
        
        print(f"   Records before: {len(history_before)}")
        
        # Clear history
        print("\nStep 2: Clear all history...")
        clear_response = requests.delete(
            f'{API_URL}/history',
            headers=self.get_headers(self.user1_id)
        )
        
        if clear_response.status_code != 200:
            print(f"❌ FAIL: Expected 200, got {clear_response.status_code}")
            return False
        
        deleted_count = clear_response.json().get('deleted_count', 0)
        print(f"   Deleted {deleted_count} records")
        
        # Verify history is empty
        print("\nStep 3: Verify history is empty...")
        history_after = requests.get(
            f'{API_URL}/history',
            headers=self.get_headers(self.user1_id)
        ).json().get('history', [])
        
        if len(history_after) == 0:
            print("✅ PASS: History cleared successfully")
            return True
        else:
            print(f"❌ FAIL: History still has {len(history_after)} records")
            return False
    
    def test_analytics(self):
        """Test user-specific analytics."""
        print("\n" + "="*70)
        print("TEST 9: User-Specific Analytics")
        print("="*70)
        
        # Create some test data
        print("Step 1: Create test data...")
        test_emails = [
            'analytics1@example.com',
            'analytics2@test.com',
            'analytics3@gmail.com'
        ]
        
        for email in test_emails:
            requests.post(
                f'{API_URL}/validate',
                json={'email': email, 'advanced': True},
                headers=self.get_headers(self.user1_id)
            )
        
        time.sleep(1)  # Give database time to process
        
        # Get analytics
        print("\nStep 2: Fetch analytics...")
        response = requests.get(
            f'{API_URL}/analytics',
            headers=self.get_headers(self.user1_id)
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PASS: Analytics retrieved successfully")
            print(f"   Total validations: {data.get('total_validations')}")
            print(f"   Valid count: {data.get('valid_count')}")
            print(f"   Invalid count: {data.get('invalid_count')}")
            print(f"   Avg confidence: {data.get('avg_confidence')}")
            
            if data.get('top_domains'):
                print(f"   Top domains: {len(data.get('top_domains'))}")
            
            return True
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all tests."""
        print("\n" + "="*70)
        print("ANONYMOUS USER ID HISTORY SYSTEM - TEST SUITE")
        print("="*70)
        print(f"Backend URL: {BASE_URL}")
        print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = []
        
        # Run tests
        results.append(("Missing User ID", self.test_missing_user_id()))
        
        success, record_id = self.test_validate_with_user_id()
        results.append(("Validate with User ID", success))
        
        results.append(("Batch Validation", self.test_batch_validation()))
        
        success, history = self.test_get_user_history()
        results.append(("Get User History", success))
        
        results.append(("Cross-User Isolation", self.test_cross_user_isolation()))
        results.append(("Delete Record", self.test_delete_record()))
        results.append(("Prevent Cross-User Delete", self.test_delete_wrong_user()))
        results.append(("Clear History", self.test_clear_history()))
        results.append(("User Analytics", self.test_analytics()))
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print("\n" + "="*70)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {total - passed} test(s) failed")
        
        print("="*70)
        
        return passed == total


if __name__ == '__main__':
    print("Starting Anonymous User ID History System Tests...")
    print("Make sure the backend is running on http://localhost:5000")
    print()
    
    input("Press Enter to start tests...")
    
    tester = TestAnonHistory()
    success = tester.run_all_tests()
    
    exit(0 if success else 1)
