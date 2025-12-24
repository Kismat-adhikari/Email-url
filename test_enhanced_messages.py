#!/usr/bin/env python3
"""
Test the enhanced user messages
"""

from production_smtp_validator import validate_email_production_ready
import json

def test_enhanced_messages():
    """Test enhanced user messages for different providers"""
    
    test_emails = [
        "user@gmail.com",
        "test@outlook.com", 
        "admin@yahoo.com",
        "fake@nonexistent.com"
    ]
    
    print("🧪 TESTING ENHANCED USER MESSAGES")
    print("=" * 50)
    
    for email in test_emails:
        print(f"\n📧 Testing: {email}")
        print("-" * 30)
        
        result = validate_email_production_ready(email, enable_smtp=True)
        
        print(f"✅ Valid: {result.get('valid', False)}")
        print(f"📊 Confidence: {result.get('confidence_score', 0)}%")
        print(f"🎯 Deliverability: {result.get('deliverability', 'Unknown')}")
        
        # Show user-friendly reason
        if result.get('reason'):
            print(f"💡 User Message: {result['reason']}")
        
        # Show SMTP disclaimer if present
        if result.get('smtp_disclaimer'):
            print(f"ℹ️  SMTP Disclaimer: {result['smtp_disclaimer']}")
        
        # Show what frontend will get
        if result.get('smtp_details'):
            smtp = result['smtp_details']
            if smtp.get('user_message'):
                print(f"🖥️  Frontend SMTP Message: {smtp['user_message']}")

if __name__ == "__main__":
    test_enhanced_messages()