#!/usr/bin/env python3
"""
Test script to verify UI fixes:
1. API count refresh bug fix
2. Better PRO badge placement
"""

import requests
import json

# Configuration
API_BASE = "http://localhost:5000"
TEST_EMAIL = "ui.test@example.com"
TEST_PASSWORD = "TestPassword123!"

def test_ui_fixes():
    """Test the UI fixes."""
    
    print("🎨 TESTING UI FIXES")
    print("=" * 40)
    
    # Step 1: Create/Login test user
    print("1. Creating fresh test user...")
    signup_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "firstName": "UI",
        "lastName": "Test"
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/auth/signup", json=signup_data)
        if response.status_code == 201:
            print(f"✅ Fresh user created: {TEST_EMAIL}")
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
    
    # Step 2: Test API count persistence
    print("\n2. Testing API count persistence...")
    
    # Validate one email
    try:
        response = requests.post(
            f"{API_BASE}/api/validate",
            json={"email": "test1@gmail.com", "advanced": True},
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            api_usage = result.get('api_usage', {})
            print(f"   ✅ Validation 1 - Usage: {api_usage.get('calls_used', '?')}/{api_usage.get('calls_limit', '?')}")
            
            # Test the /api/auth/me endpoint (refresh simulation)
            me_response = requests.get(f"{API_BASE}/api/auth/me", headers=headers)
            if me_response.status_code == 200:
                me_data = me_response.json()
                me_user = me_data.get('user', {})
                print(f"   ✅ Refresh test - Usage: {me_user.get('apiCallsCount', '?')}/{me_user.get('apiCallsLimit', '?')}")
                
                if me_user.get('apiCallsCount') == api_usage.get('calls_used'):
                    print("   ✅ API count persistence: FIXED! ✨")
                else:
                    print("   ❌ API count persistence: Still broken")
            else:
                print(f"   ❌ /api/auth/me failed: {me_response.status_code}")
                
        else:
            print(f"   ❌ Validation failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Step 3: Test batch validation restriction
    print("\n3. Testing batch validation restriction...")
    batch_headers = headers.copy()
    batch_headers["X-User-ID"] = "12345678-1234-4567-8901-123456789012"
    
    try:
        response = requests.post(
            f"{API_BASE}/api/validate/batch/stream",
            json={"emails": ["batch1@test.com"], "advanced": True},
            headers=batch_headers
        )
        
        if response.status_code == 403:
            error_data = response.json()
            print("   ✅ Batch validation blocked for free tier")
            print(f"      Message: {error_data.get('message', 'No message')}")
        else:
            print(f"   ❌ Batch should be blocked - got status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 UI TESTING INSTRUCTIONS")
    print("=" * 40)
    
    print("1. 🌐 Go to http://localhost:3000")
    print(f"2. 🔑 Login with: {TEST_EMAIL} / {TEST_PASSWORD}")
    print("3. 👀 Check these UI improvements:")
    print("   ✅ API counter shows tier badge and better layout")
    print("   ✅ Batch Validation tab has PRO badge and is disabled")
    print("   ✅ Send Emails tab has PRO badge and is disabled")
    print("   ✅ Clicking disabled tabs shows upgrade error with button")
    print("   ✅ API counter updates immediately after validation")
    print("   ✅ Refreshing page keeps correct API count")
    print("4. 🔄 Test refresh bug fix:")
    print("   - Validate an email")
    print("   - Note the API counter (should show 2/10 or similar)")
    print("   - Refresh the page (F5)")
    print("   - API counter should still show correct count!")
    print("5. 🎨 Check PRO badges:")
    print("   - Should have nice gradient and pulse animation")
    print("   - Tabs should look disabled but professional")
    print("   - Error messages should have upgrade buttons")

if __name__ == "__main__":
    test_ui_fixes()