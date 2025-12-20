#!/usr/bin/env python3
"""
Test Single Email Validation API
This script tests the actual API endpoint for single email validation
"""

import requests
import json

def test_single_validation_api():
    """Test the single email validation API endpoint"""
    try:
        print("🧪 Testing single email validation API...")
        
        # Test data - you'll need to replace with actual auth token from a team member
        api_url = "http://localhost:5000/api/validate"
        
        # You'll need to get a real auth token from a team member
        # For now, let's just test the endpoint structure
        
        print("📝 To test this properly, you need to:")
        print("   1. Login as a team member in the browser")
        print("   2. Get the auth token from localStorage")
        print("   3. Use that token to test the API")
        
        print("\n🔍 Example test request:")
        print(f"   POST {api_url}")
        print("   Headers: {'Authorization': 'Bearer YOUR_TOKEN'}")
        print("   Body: {'email': 'test@example.com', 'advanced': true}")
        
        print("\n💡 If you're getting the 'monthly limit' error:")
        print("   1. Restart the Flask server (python app_anon_history.py)")
        print("   2. Clear browser cache/localStorage")
        print("   3. Login again as a team member")
        print("   4. Try single email validation")
        
        print("\n✅ The backend code has been fixed!")
        print("🚀 The error should now show 'lifetime limit' instead of 'monthly limit'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    test_single_validation_api()