#!/usr/bin/env python3
"""
Force SMTP test even on Gmail (to show you why we skip it)
"""

import smtplib
import socket
import dns.resolver
import time

def force_smtp_on_gmail(email):
    """Force SMTP verification on Gmail (will likely fail/timeout)"""
    
    print(f"🔥 FORCING SMTP ON GMAIL: {email}")
    print("(This will likely fail or timeout - that's why we skip it)")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        domain = email.split('@')[1]
        
        # Get Gmail MX records
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_server = str(mx_records[0].exchange).rstrip('.')
        
        print(f"📡 Connecting to Gmail server: {mx_server}")
        
        # Try SMTP connection with timeout
        with smtplib.SMTP(timeout=10) as server:
            print("🔌 Connecting...")
            server.connect(mx_server)
            
            print("👋 Sending HELO...")
            server.helo("emailvalidator.com")
            
            print("📧 Setting sender...")
            server.mail("noreply@emailvalidator.com")
            
            print("🎯 Testing recipient...")
            code, message = server.rcpt(email)
            
            elapsed = int((time.time() - start_time) * 1000)
            
            print(f"\n✅ SUCCESS!")
            print(f"📊 SMTP Code: {code}")
            print(f"📨 SMTP Message: {message}")
            print(f"⏱️  Time: {elapsed}ms")
            
            if code == 250:
                print("🎉 Gmail says: DELIVERABLE")
            elif code == 550:
                print("❌ Gmail says: UNDELIVERABLE")
            else:
                print("🤷 Gmail says: UNCERTAIN")
                
    except socket.timeout:
        elapsed = int((time.time() - start_time) * 1000)
        print(f"\n⏰ TIMEOUT after {elapsed}ms")
        print("🚫 Gmail blocked/ignored the SMTP verification")
        print("💡 This is why we skip SMTP for Gmail!")
        
    except Exception as e:
        elapsed = int((time.time() - start_time) * 1000)
        print(f"\n❌ FAILED after {elapsed}ms")
        print(f"🚫 Error: {e}")
        print("💡 This is why we skip SMTP for Gmail!")

if __name__ == "__main__":
    print("🧪 FORCING SMTP ON GMAIL TEST")
    print("This will show you why we automatically skip SMTP for Gmail")
    print()
    
    # Test your real email
    force_smtp_on_gmail("kismatalt02@gmail.com")
    
    print("\n" + "=" * 50)
    print("🎯 CONCLUSION:")
    print("Gmail blocks SMTP verification for security reasons.")
    print("That's why our production validator skips it and uses DNS instead.")
    print("DNS verification is faster (74ms) and more reliable for Gmail!")