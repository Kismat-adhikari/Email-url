#!/usr/bin/env python3
"""
Quick test to compare old vs new SMTP validation
Run this to see the difference before integrating
"""

import asyncio
import time
from email_validator_smtp import validate_email_with_smtp  # Your current SMTP
from email_validator_smtp_v2 import validate_email_with_smtp_sync_v2  # New enhanced SMTP

def test_smtp_comparison():
    """Test both old and new SMTP validation"""
    
    test_emails = [
        "user@gmail.com",
        "test@outlook.com", 
        "fake@nonexistent12345.com",
        "admin@yahoo.com"
    ]
    
    print("🧪 SMTP VALIDATION COMPARISON TEST")
    print("=" * 50)
    
    for email in test_emails:
        print(f"\n📧 Testing: {email}")
        print("-" * 30)
        
        # Test OLD SMTP
        try:
            start_time = time.time()
            old_result = validate_email_with_smtp(email, enable_smtp=True)
            old_time = int((time.time() - start_time) * 1000)
            
            print(f"OLD SMTP:")
            print(f"  ✅ Valid: {old_result.get('valid', False)}")
            print(f"  📊 Confidence: {old_result.get('confidence_score', 0)}%")
            print(f"  ⏱️  Time: {old_time}ms")
            print(f"  🔍 SMTP Code: {old_result.get('smtp_details', {}).get('smtp_code', 'N/A')}")
            
        except Exception as e:
            print(f"OLD SMTP: ❌ Error: {e}")
            old_result = None
        
        # Test NEW ENHANCED SMTP
        try:
            start_time = time.time()
            new_result = validate_email_with_smtp_sync_v2(email, enable_smtp=True)
            new_time = int((time.time() - start_time) * 1000)
            
            print(f"NEW ENHANCED:")
            print(f"  ✅ Valid: {new_result.get('valid', False)}")
            print(f"  📊 Confidence: {new_result.get('confidence_score', 0)}%")
            print(f"  ⏱️  Time: {new_time}ms")
            print(f"  🔍 SMTP Result: {new_result.get('smtp_details', {}).get('result', 'N/A')}")
            print(f"  🎯 Strategy: {new_result.get('validation_strategy', {}).get('strategy_priority', 'N/A')}")
            
        except Exception as e:
            print(f"NEW ENHANCED: ❌ Error: {e}")
            new_result = None
        
        # Compare results
        if old_result and new_result:
            old_conf = old_result.get('confidence_score', 0)
            new_conf = new_result.get('confidence_score', 0)
            
            if new_conf > old_conf:
                print(f"🎉 IMPROVEMENT: +{new_conf - old_conf} confidence points!")
            elif new_conf < old_conf:
                print(f"⚠️  DIFFERENCE: -{old_conf - new_conf} confidence points")
            else:
                print("📊 Same confidence level")

if __name__ == "__main__":
    print("Starting SMTP comparison test...")
    print("This will test your current SMTP vs the enhanced version")
    print("(This is just a test - your app is unchanged)")
    print()
    
    test_smtp_comparison()
    
    print("\n" + "=" * 50)
    print("🎯 TEST COMPLETE")
    print("If you like the enhanced results, follow INTEGRATION_GUIDE.md")
    print("to actually integrate it into your app.")