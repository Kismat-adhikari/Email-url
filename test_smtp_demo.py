#!/usr/bin/env python3
"""
Quick demo to show SMTP verification in action
"""

from email_validator_smtp import validate_email_with_smtp

print("=" * 70)
print("SMTP VERIFICATION DEMO")
print("=" * 70)
print()

# Test emails
test_emails = [
    "test@gmail.com",           # Likely doesn't exist
    "support@google.com",       # Might exist
    "fakeemail12345@yahoo.com", # Definitely doesn't exist
]

for email in test_emails:
    print(f"\n🔍 Testing: {email}")
    print("-" * 70)
    
    try:
        result = validate_email_with_smtp(
            email,
            enable_smtp=True,
            check_dns=True,
            check_mx=True,
            smtp_timeout=10
        )
        
        print(f"✓ Valid: {result['valid']}")
        print(f"✓ Confidence: {result.get('confidence_score', 0)}/100")
        
        if 'smtp_details' in result:
            smtp = result['smtp_details']
            print(f"\n📧 SMTP Check:")
            print(f"   - Mailbox exists: {smtp.get('smtp_valid', 'Unknown')}")
            print(f"   - Server response: {smtp.get('smtp_response', 'N/A')}")
            print(f"   - Catch-all domain: {smtp.get('is_catch_all', False)}")
        
        if result.get('reason'):
            print(f"\n💡 Reason: {result['reason']}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

print("\n" + "=" * 70)
print("Note: Some servers block SMTP verification to prevent spam")
print("=" * 70)
