#!/usr/bin/env python3
"""
Test the UI improvements:
1. Clean navbar API counter
2. Disabled mode switching during validation
"""

import requests
import json

# Configuration
API_BASE = "http://localhost:5000"
TEST_EMAIL = "ui.clean@example.com"
TEST_PASSWORD = "TestPassword123!"

def test_ui_improvements():
    """Test the UI improvements."""
    
    print("🎨 TESTING UI IMPROVEMENTS")
    print("=" * 50)
    
    # Step 1: Create/Login test user
    print("1. Creating test user for UI testing...")
    signup_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "firstName": "Clean",
        "lastName": "UI"
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
    
    print("\n" + "=" * 50)
    print("🎯 UI TESTING CHECKLIST")
    print("=" * 50)
    
    print("1. 🌐 Go to http://localhost:3000")
    print(f"2. 🔑 Login with: {TEST_EMAIL} / {TEST_PASSWORD}")
    print("\n📱 NAVBAR IMPROVEMENTS:")
    print("   ✅ API counter should be clean and compact")
    print("   ✅ Should show 'X/10 Free' (not cluttered text)")
    print("   ✅ No weird tier badges in navbar")
    print("   ✅ Hover hints should be small and clean")
    
    print("\n🔒 MODE SWITCHING DURING VALIDATION:")
    print("   ✅ Start validating an email (Advanced mode)")
    print("   ✅ While it's loading, try clicking 'Basic Mode'")
    print("   ✅ Mode selector should be disabled (grayed out)")
    print("   ✅ No ugly red hover effects")
    print("   ✅ Should not be able to switch modes")
    print("   ✅ After validation completes, modes should work again")
    
    print("\n🎨 VISUAL IMPROVEMENTS:")
    print("   ✅ PRO badges on Batch/Send tabs should pulse nicely")
    print("   ✅ Disabled tabs should look professional")
    print("   ✅ Error messages should have upgrade buttons")
    print("   ✅ Overall UI should feel smooth and polished")
    
    print("\n🧪 TESTING STEPS:")
    print("   1. Login and check navbar looks clean")
    print("   2. Try Advanced mode validation")
    print("   3. While loading, try to click Basic mode (should be disabled)")
    print("   4. Check that PRO features show nice badges")
    print("   5. Try clicking disabled tabs (should show upgrade prompts)")
    
    print(f"\n🎉 Ready to test! Login with: {TEST_EMAIL} / {TEST_PASSWORD}")

if __name__ == "__main__":
    test_ui_improvements()