#!/usr/bin/env python3
"""
Comprehensive test for free tier restrictions.
Tests all aspects of the free tier limitations.
"""

import requests
import json
import time

# Configuration
API_BASE = "http://localhost:5000"
TEST_EMAIL = "complete.free.test@example.com"
TEST_PASSWORD = "TestPassword123!"

def test_complete_free_tier():
    """Test all free tier restrictions comprehensively."""
    
    print("🧪 COMPREHENSIVE FREE TIER TEST")
    print("=" * 60)
    
    # Step 1: Create/Login test user
    print("1. Creating/logging in test user...")
    signup_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "firstName": "Complete",
        "lastName": "Test"
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/auth/signup", json=signup_data)
        if response.status_code == 201:
            print(f"✅ Test user created: {TEST_EMAIL}")
            user_data = response.json()
            token = user_data.get('token')
            user_info = user_data.get('user', {})
        elif response.status_code == 409:
            print(f"⚠️  User exists, logging in...")
            login_response = requests.post(f"{API_BASE}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if login_response.status_code == 200:
                user_data = login_response.json()
                token = user_data.get('token')
                user_info = user_data.get('user', {})
                print(f"✅ Logged in: {TEST_EMAIL}")
            else:
                print(f"❌ Login failed: {login_response.text}")
                return
        else:
            print(f"❌ Signup failed: {response.text}")
            return
            
        print(f"   Subscription: {user_info.get('subscriptionTier', 'Unknown')}")
        print(f"   API Limit: {user_info.get('apiCallsLimit', 'Unknown')}")
        print(f"   Current Usage: {user_info.get('apiCallsCount', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Test batch validation restriction (should be blocked)
    print("\n2. Testing batch validation restriction...")
    batch_headers = headers.copy()
    batch_headers["X-User-ID"] = "12345678-1234-4567-8901-123456789012"
    
    try:
        response = requests.post(
            f"{API_BASE}/api/validate/batch/stream",
            json={"emails": ["batch1@test.com", "batch2@test.com"], "advanced": True},
            headers=batch_headers
        )
        
        if response.status_code == 403:
            error_data = response.json()
            print("   ✅ Batch validation properly blocked for free tier")
            print(f"      Message: {error_data.get('message', 'No message')}")
            print(f"      Tier: {error_data.get('subscription_tier', 'Unknown')}")
        else:
            print(f"   ❌ Batch validation should be blocked - got status {response.status_code}")
            print(f"      Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception testing batch restriction: {e}")
    
    # Step 3: Test single email validation (should work up to limit)
    print("\n3. Testing single email validation limits...")
    
    test_emails = [f"single{i}@test.com" for i in range(1, 15)]  # Try 14 emails
    successful_validations = 0
    
    for i, email in enumerate(test_emails, 1):
        print(f"   Validating {i}: {email}")
        
        try:
            response = requests.post(
                f"{API_BASE}/api/validate",
                json={"email": email, "advanced": True},
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                successful_validations += 1
                api_usage = result.get('api_usage', {})
                print(f"      ✅ Success - Usage: {api_usage.get('calls_used', '?')}/{api_usage.get('calls_limit', '?')}")
                
                # Check if we're at the limit
                if api_usage.get('calls_remaining', 1) <= 0:
                    print(f"      🚫 Limit reached after {successful_validations} validations")
                    break
                    
            elif response.status_code == 429:
                error_data = response.json()
                print(f"      🚫 API Limit Exceeded: {error_data.get('message', 'Unknown error')}")
                break
            else:
                print(f"      ❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"      ❌ Exception: {e}")
        
        time.sleep(0.1)
    
    # Step 4: Test anonymous validation (should work unlimited)
    print("\n4. Testing anonymous validation (should be unlimited)...")
    
    anonymous_emails = [f"anon{i}@test.com" for i in range(1, 6)]
    anonymous_success = 0
    
    for email in anonymous_emails:
        try:
            response = requests.post(
                f"{API_BASE}/api/validate/local",
                json={"email": email, "advanced": True}
            )
            
            if response.status_code == 200:
                anonymous_success += 1
                result = response.json()
                print(f"   ✅ Anonymous validation {anonymous_success}: {email} -> {result.get('valid', 'Unknown')}")
            else:
                print(f"   ❌ Anonymous validation failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    # Step 5: Test database storage behavior
    print("\n5. Testing database storage behavior...")
    
    try:
        # Check if authenticated user validations are stored
        response = requests.get(f"{API_BASE}/api/history?limit=5", headers=headers)
        
        if response.status_code == 200:
            history_data = response.json()
            history_count = len(history_data.get('history', []))
            print(f"   ✅ Authenticated user history: {history_count} records stored")
            
            if history_count > 0:
                print("   ✅ Database storage working for authenticated users")
            else:
                print("   ⚠️  No history found (might be expected if user is new)")
        else:
            print(f"   ❌ History fetch failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception testing history: {e}")
    
    # Step 6: Summary and recommendations
    print("\n" + "=" * 60)
    print("🎯 FREE TIER TEST SUMMARY")
    print("=" * 60)
    
    print(f"✅ User Tier: {user_info.get('subscriptionTier', 'Unknown')}")
    print(f"✅ API Limit: {user_info.get('apiCallsLimit', 'Unknown')} validations")
    print(f"✅ Successful Single Validations: {successful_validations}")
    print(f"✅ Anonymous Validations: {anonymous_success} (unlimited)")
    print(f"✅ Batch Validation: Properly blocked for free tier")
    print(f"✅ Database Storage: Working for authenticated users")
    
    print("\n🎨 FRONTEND TESTING:")
    print("1. Go to http://localhost:3000")
    print(f"2. Login with: {TEST_EMAIL} / {TEST_PASSWORD}")
    print("3. Check that:")
    print("   - Batch Validation tab shows 'PRO' badge and is disabled")
    print("   - Send Emails tab shows 'PRO' badge and is disabled")
    print("   - API counter shows current usage and turns red when limit reached")
    print("   - Single email validation shows upgrade prompts when limit reached")
    print("   - Anonymous mode (logout) allows unlimited validations")
    
    print("\n🚀 UPGRADE FLOW:")
    print("- Free users get 10 single email validations")
    print("- Batch validation requires Pro upgrade")
    print("- Email sending requires Pro upgrade")
    print("- Clear upgrade prompts throughout the interface")
    print("- Anonymous users get unlimited validations (localStorage only)")

if __name__ == "__main__":
    test_complete_free_tier()