#!/usr/bin/env python3
"""
Create a test user with specific API limits for UI testing.
"""

import requests
import json

# Configuration
API_BASE = "http://localhost:5000"
TEST_EMAIL = "uitest@example.com"
TEST_PASSWORD = "TestPassword123!"

def create_ui_test_user():
    """Create a user for UI testing."""
    
    print("🧪 Creating UI Test User")
    print("=" * 30)
    
    # Create user
    signup_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "firstName": "UI",
        "lastName": "Test"
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/auth/signup", json=signup_data)
        if response.status_code == 201:
            print(f"✅ Test user created: {TEST_EMAIL}")
            user_data = response.json()
            print(f"   Token: {user_data.get('token', 'N/A')[:50]}...")
            user_info = user_data.get('user', {})
            print(f"   API Limit: {user_info.get('apiCallsLimit', 'Unknown')}")
            print(f"   Current Usage: {user_info.get('apiCallsCount', 'Unknown')}")
            print(f"   Subscription: {user_info.get('subscriptionTier', 'Unknown')}")
            
            print("\n🌐 Frontend Testing Instructions:")
            print("1. Go to http://localhost:3000")
            print("2. Click 'Login' in the top right")
            print(f"3. Login with: {TEST_EMAIL} / {TEST_PASSWORD}")
            print("4. Try validating emails to see the UI changes:")
            print("   - API counter should show usage")
            print("   - After 8 validations, you should see warnings")
            print("   - After 10 validations, everything should be disabled")
            print("   - Try batch validation to see batch-specific warnings")
            
        elif response.status_code == 409:
            print(f"⚠️  User already exists: {TEST_EMAIL}")
            print("   You can still use it for testing!")
            print(f"   Login with: {TEST_EMAIL} / {TEST_PASSWORD}")
        else:
            print(f"❌ Signup failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_ui_test_user()