#!/usr/bin/env python3
"""
Simple Enhanced SMTP Validator (no async)
Improves on your current SMTP without complexity
"""

import smtplib
import socket
import dns.resolver
import random
import time
from typing import Dict, Any, List
from emailvalidator_unified import validate_email_advanced

class SimpleEnhancedSMTP:
    """
    Simple enhanced SMTP validator that's better than current but not complex
    """
    
    def __init__(self):
        self.timeout = 10  # Faster timeout
        self.max_retries = 2
        self.sender_pool = [
            "verify@emailvalidator.com",
            "check@mailverify.org", 
            "validate@emailcheck.net"
        ]
    
    def validate_email_enhanced(self, email: str, enable_smtp: bool = True) -> Dict[str, Any]:
        """
        Enhanced email validation with better SMTP
        """
        # Start with basic validation
        result = validate_email_advanced(email)
        
        if not enable_smtp or not result.get('valid', False):
            return result
        
        # Add enhanced SMTP check
        smtp_result = self._enhanced_smtp_check(email)
        
        # Update result with SMTP data
        result['smtp_details'] = smtp_result
        
        # Update confidence based on SMTP
        if smtp_result['smtp_valid']:
            result['confidence_score'] = min(result.get('confidence_score', 0) + 15, 100)
            result['deliverability'] = 'High'
        elif smtp_result['smtp_code'] == 550:
            result['confidence_score'] = max(result.get('confidence_score', 0) - 20, 10)
            result['deliverability'] = 'Low'
            result['valid'] = False
        
        return result
    
    def _enhanced_smtp_check(self, email: str) -> Dict[str, Any]:
        """
        Enhanced SMTP check with better error handling
        """
        result = {
            'smtp_valid': False,
            'smtp_code': None,
            'smtp_message': '',
            'response_time_ms': 0,
            'mx_server': '',
            'error': None
        }
        
        start_time = time.time()
        
        try:
            domain = email.split('@')[1]
            
            # Get MX records with timeout
            mx_servers = self._get_mx_records(domain)
            if not mx_servers:
                result['error'] = "No MX records found"
                return result
            
            # Try primary MX server with enhanced logic
            mx_server = mx_servers[0]
            result['mx_server'] = mx_server
            
            # Provider-specific optimizations
            if 'gmail' in domain.lower():
                return self._gmail_optimized_check(email, mx_server, result, start_time)
            elif any(provider in domain.lower() for provider in ['outlook', 'hotmail', 'live']):
                return self._microsoft_optimized_check(email, mx_server, result, start_time)
            else:
                return self._standard_smtp_check(email, mx_server, result, start_time)
                
        except Exception as e:
            result['error'] = str(e)
            result['response_time_ms'] = int((time.time() - start_time) * 1000)
            return result
    
    def _gmail_optimized_check(self, email: str, mx_server: str, result: Dict, start_time: float) -> Dict[str, Any]:
        """Gmail-specific SMTP check"""
        try:
            with smtplib.SMTP(timeout=8) as server:  # Shorter timeout for Gmail
                server.connect(mx_server)
                server.helo("validator.com")
                
                sender = random.choice(self.sender_pool)
                server.mail(sender)
                
                code, message = server.rcpt(email)
                
                result['smtp_code'] = code
                result['smtp_message'] = str(message)
                result['response_time_ms'] = int((time.time() - start_time) * 1000)
                
                if code == 250:
                    result['smtp_valid'] = True
                elif code == 550:
                    result['smtp_valid'] = False
                else:
                    result['smtp_valid'] = None  # Uncertain
                
                return result
                
        except Exception as e:
            result['error'] = f"Gmail check failed: {str(e)}"
            result['response_time_ms'] = int((time.time() - start_time) * 1000)
            return result
    
    def _microsoft_optimized_check(self, email: str, mx_server: str, result: Dict, start_time: float) -> Dict[str, Any]:
        """Microsoft (Outlook/Hotmail) optimized check"""
        # Microsoft often blocks SMTP verification, so be quick
        try:
            with smtplib.SMTP(timeout=5) as server:  # Very short timeout
                server.connect(mx_server)
                server.helo("emailvalidator.com")
                
                sender = random.choice(self.sender_pool)
                server.mail(sender)
                
                code, message = server.rcpt(email)
                
                result['smtp_code'] = code
                result['smtp_message'] = str(message)
                result['response_time_ms'] = int((time.time() - start_time) * 1000)
                
                # Microsoft is tricky - be conservative
                if code == 250:
                    result['smtp_valid'] = True
                else:
                    result['smtp_valid'] = None  # Don't assume invalid
                
                return result
                
        except Exception as e:
            # Microsoft blocks are common, don't treat as error
            result['error'] = "Microsoft blocks SMTP verification"
            result['response_time_ms'] = int((time.time() - start_time) * 1000)
            result['smtp_valid'] = None  # Unknown, not invalid
            return result
    
    def _standard_smtp_check(self, email: str, mx_server: str, result: Dict, start_time: float) -> Dict[str, Any]:
        """Standard SMTP check for other providers"""
        try:
            with smtplib.SMTP(timeout=self.timeout) as server:
                server.connect(mx_server)
                server.helo("emailvalidator.com")
                
                sender = random.choice(self.sender_pool)
                server.mail(sender)
                
                code, message = server.rcpt(email)
                
                result['smtp_code'] = code
                result['smtp_message'] = str(message)
                result['response_time_ms'] = int((time.time() - start_time) * 1000)
                
                if code == 250:
                    result['smtp_valid'] = True
                elif code in [550, 551, 553]:
                    result['smtp_valid'] = False
                else:
                    result['smtp_valid'] = None  # Uncertain
                
                return result
                
        except Exception as e:
            result['error'] = str(e)
            result['response_time_ms'] = int((time.time() - start_time) * 1000)
            return result
    
    def _get_mx_records(self, domain: str) -> List[str]:
        """Get MX records with error handling"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return [str(mx.exchange).rstrip('.') for mx in sorted(mx_records, key=lambda x: x.preference)]
        except:
            return []

# Global instance
simple_enhanced_smtp = SimpleEnhancedSMTP()

def validate_email_simple_enhanced(email: str, enable_smtp: bool = True) -> Dict[str, Any]:
    """
    Simple enhanced validation function
    """
    return simple_enhanced_smtp.validate_email_enhanced(email, enable_smtp)

# Test function
def test_simple_enhanced():
    """Test the simple enhanced SMTP"""
    
    test_emails = [
        "user@gmail.com",
        "fake@nonexistent12345.com"
    ]
    
    print("🚀 TESTING SIMPLE ENHANCED SMTP")
    print("=" * 40)
    
    for email in test_emails:
        print(f"\n📧 Testing: {email}")
        print("-" * 25)
        
        try:
            start_time = time.time()
            result = validate_email_simple_enhanced(email, enable_smtp=True)
            elapsed = int((time.time() - start_time) * 1000)
            
            print(f"✅ Valid: {result.get('valid', False)}")
            print(f"📊 Confidence: {result.get('confidence_score', 0)}%")
            print(f"⏱️  Total Time: {elapsed}ms")
            
            if result.get('smtp_details'):
                smtp = result['smtp_details']
                print(f"🔍 SMTP Code: {smtp.get('smtp_code', 'N/A')}")
                print(f"📨 SMTP Valid: {smtp.get('smtp_valid', 'N/A')}")
                print(f"⚡ SMTP Time: {smtp.get('response_time_ms', 0)}ms")
                if smtp.get('error'):
                    print(f"⚠️  SMTP Note: {smtp['error']}")
            
            print(f"🎯 Deliverability: {result.get('deliverability', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_enhanced()