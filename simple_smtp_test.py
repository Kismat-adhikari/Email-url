#!/usr/bin/env python3
"""
Simple SMTP test without async complexity
"""

import time
from email_validator_smtp import validate_email_with_smtp  # Your current SMTP

def test_current_smtp():
    """Test your current SMTP validation"""
    
    test_emails = [
        "user@gmail.com",
        "fake@nonexistent12345.com"
    ]
    
    print("🧪 TESTING YOUR CURRENT SMTP")
    print("=" * 40)
    
    for email in test_emails:
        print(f"\n📧 Testing: {email}")
        print("-" * 25)
        
        try:
            start_time = time.time()
            result = validate_email_with_smtp(email, enable_smtp=True)
            elapsed = int((time.time() - start_time) * 1000)
            
            print(f"✅ Valid: {result.get('valid', False)}")
            print(f"📊 Confidence: {result.get('confidence_score', 0)}%")
            print(f"⏱️  Time: {elapsed}ms")
            
            if result.get('smtp_details'):
                smtp = result['smtp_details']
                print(f"🔍 SMTP Code: {smtp.get('smtp_code', 'N/A')}")
                print(f"📨 SMTP Valid: {smtp.get('smtp_valid', False)}")
            
            print(f"🎯 Deliverability: {result.get('deliverability', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing your current SMTP validation...")
    print("This will show you what you're getting now.")
    print()
    
    test_current_smtp()
    
    print("\n" + "=" * 40)
    print("🎯 CURRENT SMTP TEST COMPLETE")
    print("This is what your app currently produces.")