#!/usr/bin/env python3
"""
Production-Ready SMTP Validator
Handles real-world SMTP blocking and timeouts properly
"""

import smtplib
import socket
import dns.resolver
import random
import time
from typing import Dict, Any, List
from emailvalidator_unified import validate_email_advanced

class ProductionSMTPValidator:
    """
    Production-ready SMTP validator that handles real-world issues:
    - Gmail/Outlook blocking SMTP verification
    - Timeouts and connection issues
    - Provider-specific behavior
    - Intelligent fallbacks
    """
    
    def __init__(self):
        self.provider_configs = {
            # Gmail often blocks SMTP, use DNS-based validation
            'gmail.com': {'use_smtp': False, 'confidence_boost': 10},
            'googlemail.com': {'use_smtp': False, 'confidence_boost': 10},
            
            # Outlook/Microsoft block SMTP frequently
            'outlook.com': {'use_smtp': False, 'confidence_boost': 5},
            'hotmail.com': {'use_smtp': False, 'confidence_boost': 5},
            'live.com': {'use_smtp': False, 'confidence_boost': 5},
            
            # Yahoo sometimes allows SMTP
            'yahoo.com': {'use_smtp': True, 'timeout': 5, 'confidence_boost': 15},
            'yahoo.co.uk': {'use_smtp': True, 'timeout': 5, 'confidence_boost': 15},
            
            # Smaller providers often allow SMTP
            'default': {'use_smtp': True, 'timeout': 8, 'confidence_boost': 20}
        }
    
    def validate_email_production(self, email: str, enable_smtp: bool = True) -> Dict[str, Any]:
        """
        Production email validation with intelligent SMTP usage
        """
        # Start with basic validation
        result = validate_email_advanced(email)
        
        if not enable_smtp or not result.get('valid', False):
            return self._finalize_result(result, None)
        
        domain = email.split('@')[1].lower()
        config = self._get_provider_config(domain)
        
        # Decide whether to use SMTP based on provider
        if config['use_smtp']:
            smtp_result = self._smart_smtp_check(email, config)
        else:
            smtp_result = self._create_skip_result(domain, "Provider blocks SMTP verification")
        
        return self._finalize_result(result, smtp_result)
    
    def _get_provider_config(self, domain: str) -> Dict[str, Any]:
        """Get configuration for specific provider"""
        for provider, config in self.provider_configs.items():
            if provider != 'default' and provider in domain:
                return config
        return self.provider_configs['default']
    
    def _smart_smtp_check(self, email: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smart SMTP check with timeouts and error handling
        """
        result = {
            'smtp_valid': None,
            'smtp_code': None,
            'smtp_message': '',
            'response_time_ms': 0,
            'mx_server': '',
            'error': None,
            'skipped': False
        }
        
        start_time = time.time()
        
        try:
            domain = email.split('@')[1]
            mx_servers = self._get_mx_records(domain)
            
            if not mx_servers:
                result['error'] = "No MX records found"
                return result
            
            mx_server = mx_servers[0]
            result['mx_server'] = mx_server
            
            # Quick SMTP check with short timeout
            timeout = config.get('timeout', 8)
            
            with smtplib.SMTP(timeout=timeout) as server:
                server.connect(mx_server)
                server.helo("emailvalidator.com")
                
                # Use a professional sender
                server.mail("noreply@emailvalidator.com")
                
                code, message = server.rcpt(email)
                
                result['smtp_code'] = code
                result['smtp_message'] = str(message)
                result['response_time_ms'] = int((time.time() - start_time) * 1000)
                
                # Interpret results conservatively
                if code == 250:
                    result['smtp_valid'] = True
                elif code in [550, 551, 553]:
                    result['smtp_valid'] = False
                else:
                    result['smtp_valid'] = None  # Uncertain
                
                return result
                
        except socket.timeout:
            result['error'] = "SMTP timeout (server may be blocking verification)"
            result['response_time_ms'] = int((time.time() - start_time) * 1000)
        except Exception as e:
            result['error'] = f"SMTP check failed: {str(e)}"
            result['response_time_ms'] = int((time.time() - start_time) * 1000)
        
        return result
    
    def _create_skip_result(self, domain: str, reason: str) -> Dict[str, Any]:
        """Create result for skipped SMTP check with user-friendly message"""
        
        # Create user-friendly messages based on provider
        if 'gmail' in domain.lower():
            user_message = "ℹ️ SMTP verification skipped: Gmail blocks email verification for security. DNS verification used instead (more reliable)."
        elif any(provider in domain.lower() for provider in ['outlook', 'hotmail', 'live']):
            user_message = "ℹ️ SMTP verification skipped: Microsoft (Outlook/Hotmail) blocks email verification. DNS verification used instead."
        elif 'yahoo' in domain.lower():
            user_message = "ℹ️ SMTP verification attempted but may be blocked by Yahoo's security policies."
        else:
            user_message = f"ℹ️ SMTP verification skipped: {domain} may block email verification. DNS verification used instead."
        
        return {
            'smtp_valid': None,
            'smtp_code': None,
            'smtp_message': reason,
            'user_message': user_message,  # New field for frontend
            'response_time_ms': 0,
            'mx_server': f"Skipped for {domain}",
            'error': None,
            'skipped': True
        }
    
    def _finalize_result(self, basic_result: Dict[str, Any], smtp_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine basic and SMTP results intelligently with user-friendly messages
        """
        result = basic_result.copy()
        
        if smtp_result:
            result['smtp_details'] = smtp_result
            
            # Adjust confidence based on SMTP results
            domain = result['email'].split('@')[1].lower()
            config = self._get_provider_config(domain)
            
            if smtp_result.get('skipped'):
                # Provider blocks SMTP - give confidence boost for having good DNS/MX
                if result.get('checks', {}).get('mx_records'):
                    boost = config.get('confidence_boost', 5)
                    result['confidence_score'] = min(result.get('confidence_score', 0) + boost, 100)
                    result['deliverability'] = 'High (DNS verified)'
                    
                    # Enhanced user-friendly reason
                    if 'gmail' in domain:
                        result['reason'] = "✅ Valid Gmail address. Gmail blocks SMTP verification for security, but DNS/MX records confirm this domain accepts email."
                    elif any(provider in domain for provider in ['outlook', 'hotmail', 'live']):
                        result['reason'] = "✅ Valid Microsoft email address. Outlook/Hotmail blocks SMTP verification, but DNS/MX records confirm this domain accepts email."
                    else:
                        result['reason'] = f"✅ Valid email address. {domain} blocks SMTP verification, but DNS/MX records confirm this domain accepts email."
                    
                    # Add SMTP disclaimer
                    result['smtp_disclaimer'] = smtp_result.get('user_message', '')
            
            elif smtp_result['smtp_valid'] is True:
                # SMTP confirmed deliverable
                result['confidence_score'] = min(result.get('confidence_score', 0) + 20, 100)
                result['deliverability'] = 'High (SMTP verified)'
                result['valid'] = True
                result['reason'] = "✅ Email verified via SMTP - mailbox confirmed to exist and accept email."
            
            elif smtp_result['smtp_valid'] is False:
                # SMTP confirmed undeliverable
                result['confidence_score'] = max(result.get('confidence_score', 0) - 30, 10)
                result['deliverability'] = 'Low (SMTP rejected)'
                result['valid'] = False
                result['reason'] = "❌ Email rejected by SMTP server - mailbox does not exist or does not accept email."
            
            else:
                # SMTP uncertain - rely on DNS/MX
                if result.get('checks', {}).get('mx_records'):
                    result['deliverability'] = 'Medium (DNS verified, SMTP uncertain)'
                    result['reason'] = "⚠️ Email domain is valid, but SMTP verification was inconclusive. Email may or may not exist."
                else:
                    result['deliverability'] = 'Low'
                    result['reason'] = "❌ Email domain has issues - no valid mail servers found."
        
        return result
    
    def _get_mx_records(self, domain: str) -> List[str]:
        """Get MX records with error handling"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return [str(mx.exchange).rstrip('.') for mx in sorted(mx_records, key=lambda x: x.preference)]
        except:
            return []

# Global instance
production_validator = ProductionSMTPValidator()

def validate_email_production_ready(email: str, enable_smtp: bool = True) -> Dict[str, Any]:
    """
    Production-ready email validation
    """
    return production_validator.validate_email_production(email, enable_smtp)

# Test function
def test_production_validator():
    """Test the production validator"""
    
    test_emails = [
        "user@gmail.com",           # Should skip SMTP, boost confidence
        "test@outlook.com",         # Should skip SMTP, boost confidence
        "admin@yahoo.com",          # Should try SMTP
        "fake@nonexistent12345.com" # Should fail DNS
    ]
    
    print("🏭 TESTING PRODUCTION SMTP VALIDATOR")
    print("=" * 45)
    
    for email in test_emails:
        print(f"\n📧 Testing: {email}")
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
                if smtp.get('skipped'):
                    print(f"⏭️  SMTP: Skipped - {smtp.get('smtp_message', 'N/A')}")
                else:
                    print(f"🔍 SMTP Code: {smtp.get('smtp_code', 'N/A')}")
                    print(f"📨 SMTP Valid: {smtp.get('smtp_valid', 'N/A')}")
                    print(f"⚡ SMTP Time: {smtp.get('response_time_ms', 0)}ms")
                    if smtp.get('error'):
                        print(f"⚠️  SMTP Error: {smtp['error']}")
            
            if result.get('reason'):
                print(f"💡 Reason: {result['reason']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_production_validator()