#!/usr/bin/env python3
"""
Test the production SMTP validator with your email
"""

from production_smtp_validator import validate_email_production_ready
import time

def test_your_email():
    """Test with your actual email"""
    
    email = "kismatalt02@gmail.com"
    
    print("🧪 TESTING YOUR EMAIL WITH PRODUCTION SMTP")
    print("=" * 50)
    print(f"📧 Email: {email}")
    print("-" * 30)
    
    try:
        start_time = time.time()
        result = validate_email_production_ready(email, enable_smtp=True)
        elapsed = int((time.time() - start_time) * 1000)
        
        print(f"✅ Valid: {result.get('valid', False)}")
        print(f"📊 Confidence: {result.get('confidence_score', 0)}%")
        print(f"⏱️  Total Time: {elapsed}ms")
        print(f"🎯 Deliverability: {result.get('deliverability', 'Unknown')}")
        
        if result.get('smtp_details'):
            smtp = result['smtp_details']
            print(f"\n🔍 SMTP DETAILS:")
            if smtp.get('skipped'):
                print(f"  ⏭️  Status: SKIPPED")
                print(f"  💡 Reason: {smtp.get('smtp_message', 'N/A')}")
                print(f"  🏭 Method: DNS/MX verification (Gmail blocks SMTP)")
            else:
                print(f"  📨 SMTP Valid: {smtp.get('smtp_valid', 'N/A')}")
                print(f"  🔍 SMTP Code: {smtp.get('smtp_code', 'N/A')}")
                print(f"  ⚡ SMTP Time: {smtp.get('response_time_ms', 0)}ms")
                print(f"  🖥️  MX Server: {smtp.get('mx_server', 'N/A')}")
                if smtp.get('error'):
                    print(f"  ⚠️  Error: {smtp['error']}")
        
        if result.get('reason'):
            print(f"\n💡 Explanation: {result['reason']}")
        
        print(f"\n🎉 RESULT SUMMARY:")
        print(f"   Your email is: {'✅ VALID' if result.get('valid') else '❌ INVALID'}")
        print(f"   Confidence: {result.get('confidence_score', 0)}% ({result.get('deliverability', 'Unknown')})")
        print(f"   Speed: {elapsed}ms (vs old method: ~156 seconds)")
        
        # Show what the frontend will display
        print(f"\n🖥️  FRONTEND WILL SHOW:")
        print(f"   Status: {'Valid Email ✅' if result.get('valid') else 'Invalid Email ❌'}")
        print(f"   Confidence Bar: {result.get('confidence_score', 0)}% (Green/Excellent)")
        print(f"   Deliverability: {result.get('deliverability', 'Unknown')}")
        if result.get('smtp_details', {}).get('skipped'):
            print(f"   SMTP Status: Skipped (Provider blocks verification)")
        else:
            print(f"   SMTP Status: Attempted")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_your_email()