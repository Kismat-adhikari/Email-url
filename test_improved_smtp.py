#!/usr/bin/env python3
"""
Test improved SMTP verification with retry logic and multiple MX servers
"""

from email_validator_smtp import verify_smtp_mailbox
import json

print("=" * 70)
print("IMPROVED SMTP VERIFICATION TEST")
print("=" * 70)
print("\nImprovements:")
print("✓ Tries multiple MX servers (fallback)")
print("✓ Randomized sender emails")
print("✓ Retry logic with delays")
print("✓ Better error handling")
print("\n" + "=" * 70)

# Test emails
test_emails = [
    "kismatadhikari62@gmail.com",  # Your real email
    "support@github.com",           # Real corporate email
    "test@example.com",             # Real but probably no mailbox
]

for email in test_emails:
    print(f"\n🔍 Testing: {email}")
    print("-" * 70)
    
    try:
        result = verify_smtp_mailbox(email, timeout=15, max_retries=2)
        
        print(f"✓ SMTP Valid: {result['smtp_valid']}")
        print(f"✓ SMTP Code: {result.get('smtp_code', 'N/A')}")
        print(f"✓ MX Server Used: {result.get('mx_server', 'N/A')}")
        print(f"✓ Catch-All: {result.get('is_catch_all', False)}")
        
        if result.get('error'):
            print(f"⚠ Error: {result['error']}")
        
        if result.get('smtp_message'):
            print(f"📧 Server Response: {result['smtp_message']}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

print("\n" + "=" * 70)
print("Note: Gmail/Yahoo still block most attempts, but success rate")
print("should be higher for corporate/small business domains")
print("=" * 70)
