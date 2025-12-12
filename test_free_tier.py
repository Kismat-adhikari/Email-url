#!/usr/bin/env python3
"""
Test script to verify free tier limitations work correctly.
Creates a test user with low API limits and tests the validation endpoints.
"""

import requests
import json
import time

# Configuration
API_BASE = "http://localhost:5000"
TEST_EMAIL = "freetier.test@example.com"
TEST_PASSWORD = "TestPassword123!"
TEST_FIRST_NAME = "Free"
TEST_LAST_NAME = "Tier"

def test_free_tier_limits():
    """Test the free tier API limitations."""
    
    print("🧪 Testing Free Tier Limitations")
    print("=" * 50)
    
    # Step 1: Create a test user
    print("1. Creating test user...")
    signup_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "firstName": TEST_FIRST_NAME,
        "lastName": TEST_LAST_NAME
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/auth/signup", json=signup_data)
        if response.status_code == 201:
            print(f"✅ Test user created: {TEST_EMAIL}")
            user_data = response.json()
            token = user_data.get('token')
            user_info = user_data.get('user', {})
            print(f"   API Limit: {user_info.get('apiCallsLimit', 'Unknown')}")
            print(f"   Current Usage: {user_info.get('apiCallsCount', 'Unknown')}")
        elif response.status_code == 409:
            print(f"⚠️  User already exists, logging in...")
            # Try to login
            login_response = requests.post(f"{API_BASE}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if login_response.status_code == 200:
                user_data = login_response.json()
                token = user_data.get('token')
                user_info = user_data.get('user', {})
                print(f"✅ Logged in as: {TEST_EMAIL}")
                print(f"   API Limit: {user_info.get('apiCallsLimit', 'Unknown')}")
                print(f"   Current Usage: {user_info.get('apiCallsCount', 'Unknown')}")
            else:
                print(f"❌ Login failed: {login_response.text}")
                return
        else:
            print(f"❌ Signup failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return
    
    # Step 2: Test single email validation until limit is reached
    print("\n2. Testing single email validation...")
    headers = {"Authorization": f"Bearer {token}"}
    
    test_emails = [
        "test1@gmail.com",
        "test2@yahoo.com", 
        "test3@hotmail.com",
        "test4@outlook.com",
        "test5@icloud.com",
        "test6@protonmail.com",
        "test7@zoho.com",
        "test8@aol.com",
        "test9@mail.com",
        "test10@gmx.com",
        "test11@yandex.com",  # This should fail if limit is 10
        "test12@live.com"     # This should also fail
    ]
    
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
                print(f"         Current Usage: {error_data.get('current_usage', '?')}")
                print(f"         Limit: {error_data.get('limit', '?')}")
                break
            else:
                print(f"      ❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"      ❌ Exception: {e}")
        
        time.sleep(0.1)  # Small delay to avoid overwhelming the server
    
    # Step 3: Test that further validations are blocked
    print(f"\n3. Testing limit enforcement after {successful_validations} validations...")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/validate",
            json={"email": "should.fail@test.com", "advanced": True},
            headers=headers
        )
        
        if response.status_code == 429:
            print("   ✅ Limit enforcement working - further validations blocked")
            error_data = response.json()
            print(f"      Message: {error_data.get('message', 'No message')}")
        else:
            print(f"   ❌ Limit enforcement failed - got status {response.status_code}")
            print(f"      Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception testing limit: {e}")
    
    # Step 4: Test batch validation limit
    print("\n4. Testing batch validation limits...")
    
    batch_emails = [f"batch{i}@test.com" for i in range(1, 6)]  # 5 emails
    
    # Add X-User-ID header for batch validation
    batch_headers = headers.copy()
    batch_headers["X-User-ID"] = "12345678-1234-4567-8901-123456789012"  # Valid UUID format
    
    try:
        response = requests.post(
            f"{API_BASE}/api/validate/batch/stream",
            json={"emails": batch_emails, "advanced": True},
            headers=batch_headers
        )
        
        if response.status_code == 429:
            print("   ✅ Batch limit enforcement working")
            error_data = response.json()
            print(f"      Message: {error_data.get('message', 'No message')}")
        else:
            print(f"   ❌ Batch validation should have been blocked - got status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception testing batch limit: {e}")
    
    # Step 5: Test anonymous validation (should still work)
    print("\n5. Testing anonymous validation (should work)...")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/validate/local",
            json={"email": "anonymous@test.com", "advanced": True}
        )
        
        if response.status_code == 200:
            print("   ✅ Anonymous validation working")
            result = response.json()
            print(f"      Email: {result.get('email')}")
            print(f"      Valid: {result.get('valid')}")
        else:
            print(f"   ❌ Anonymous validation failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception testing anonymous validation: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Free Tier Test Complete!")
    print(f"   Successful validations before limit: {successful_validations}")
    print("   Check the frontend at http://localhost:3000 to see UI changes")

if __name__ == "__main__":
    test_free_tier_limits()