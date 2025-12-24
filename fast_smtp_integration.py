#!/usr/bin/env python3
"""
Fast SMTP Integration for app_anon_history.py
Replaces slow SMTP validation with ultra-fast version
"""

import asyncio
from typing import Dict, Any
from fast_smtp_validator import UltraFastSMTPValidator, FastSMTPResult
from emailvalidator_unified import validate_email_tiered
import time
import logging

logger = logging.getLogger(__name__)

class FastEmailValidator:
    """
    Drop-in replacement for validate_email_with_smtp that's 10x faster
    """
    
    def __init__(self):
        self.smtp_validator = UltraFastSMTPValidator()
    
    def validate_email_with_fast_smtp(self, email: str, enable_smtp: bool = True) -> Dict[str, Any]:
        """
        Fast replacement for validate_email_with_smtp
        
        Args:
            email: Email to validate
            enable_smtp: Whether to enable SMTP checking
            
        Returns:
            Same format as original validate_email_with_smtp but much faster
        """
        start_time = time.time()
        
        # Step 1: Basic validation (syntax, DNS, MX)
        result = validate_email_tiered(email)
        
        # Step 2: Fast SMTP validation if enabled and basic checks pass
        if enable_smtp and result['checks']['syntax'] and result['checks'].get('mx_records', False):
            try:
                # Run async SMTP check
                smtp_result = asyncio.run(self.smtp_validator.validate_fast(email))
                
                # Add SMTP details to result
                result['smtp_details'] = {
                    'smtp_valid': smtp_result.result == FastSMTPResult.VALID,
                    'smtp_code': smtp_result.smtp_code,
                    'smtp_message': smtp_result.message,
                    'is_catch_all': smtp_result.is_catch_all,
                    'error': None if smtp_result.result != FastSMTPResult.UNKNOWN else smtp_result.message,
                    'mx_server': smtp_result.mx_server,
                    'response_time_ms': smtp_result.response_time_ms
                }
                
                # Update main result based on SMTP
                if smtp_result.result == FastSMTPResult.VALID:
                    result['confidence_score'] = min(result['confidence_score'] + 15, 100)
                    result['deliverability'] = 'High'
                    result['checks']['smtp_verified'] = True
                elif smtp_result.result == FastSMTPResult.INVALID:
                    result['confidence_score'] = max(result['confidence_score'] - 20, 10)
                    result['valid'] = False
                    result['deliverability'] = 'Low'
                    result['checks']['smtp_verified'] = False
                    if result.get('reason'):
                        result['reason'] += '; SMTP verification failed'
                    else:
                        result['reason'] = 'SMTP verification failed'
                elif smtp_result.result == FastSMTPResult.CATCH_ALL:
                    result['is_catch_all'] = True
                    result['confidence_score'] = max(result['confidence_score'] - 10, 40)
                    result['deliverability'] = 'Unknown (Catch-all)'
                    result['checks']['is_catch_all'] = True
                    if result.get('reason'):
                        result['reason'] += '; Catch-all domain detected'
                    else:
                        result['reason'] = 'Catch-all domain detected'
                else:
                    # RISKY, TIMEOUT, or UNKNOWN
                    result['checks']['smtp_verified'] = None
                    if smtp_result.result == FastSMTPResult.TIMEOUT:
                        result['deliverability'] = 'Unknown (Timeout)'
                    else:
                        result['deliverability'] = 'Unknown'
                
                # Add catch-all flag to main result
                result['is_catch_all'] = smtp_result.is_catch_all
                
            except Exception as e:
                logger.error(f"Fast SMTP validation failed for {email}: {e}")
                result['smtp_details'] = {
                    'smtp_valid': False,
                    'smtp_code': None,
                    'smtp_message': '',
                    'is_catch_all': False,
                    'error': str(e),
                    'mx_server': None,
                    'response_time_ms': 0
                }
                result['checks']['smtp_verified'] = None
        else:
            # SMTP disabled or basic validation failed
            result['smtp_details'] = None
            result['is_catch_all'] = False
        
        # Add validation timing
        validation_time = int((time.time() - start_time) * 1000)
        result['validation_time_ms'] = validation_time
        
        # Log performance
        if enable_smtp and result['smtp_details']:
            smtp_time = result['smtp_details']['response_time_ms']
            logger.info(f"Fast SMTP validation completed in {smtp_time}ms (total: {validation_time}ms)")
        
        return result
    
    async def validate_batch_with_fast_smtp(self, emails: list, enable_smtp: bool = True, 
                                          max_concurrent: int = 10) -> list:
        """
        Ultra-fast batch validation with SMTP
        
        Args:
            emails: List of emails to validate
            enable_smtp: Whether to enable SMTP checking
            max_concurrent: Maximum concurrent SMTP connections
            
        Returns:
            List of validation results
        """
        if not enable_smtp:
            # Just use basic validation for all emails
            return [validate_email_tiered(email) for email in emails]
        
        # Parallel validation with SMTP
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def validate_single(email):
            async with semaphore:
                # Basic validation first
                basic_result = validate_email_tiered(email)
                
                # SMTP validation if basic passes
                if basic_result['checks']['syntax'] and basic_result['checks'].get('mx_records', False):
                    try:
                        smtp_result = await self.smtp_validator.validate_fast(email)
                        
                        # Combine results (same logic as above)
                        basic_result['smtp_details'] = {
                            'smtp_valid': smtp_result.result == FastSMTPResult.VALID,
                            'smtp_code': smtp_result.smtp_code,
                            'smtp_message': smtp_result.message,
                            'is_catch_all': smtp_result.is_catch_all,
                            'error': None if smtp_result.result != FastSMTPResult.UNKNOWN else smtp_result.message,
                            'mx_server': smtp_result.mx_server,
                            'response_time_ms': smtp_result.response_time_ms
                        }
                        
                        # Update confidence and validity
                        if smtp_result.result == FastSMTPResult.VALID:
                            basic_result['confidence_score'] = min(basic_result['confidence_score'] + 15, 100)
                            basic_result['deliverability'] = 'High'
                        elif smtp_result.result == FastSMTPResult.INVALID:
                            basic_result['confidence_score'] = max(basic_result['confidence_score'] - 20, 10)
                            basic_result['valid'] = False
                            basic_result['deliverability'] = 'Low'
                        elif smtp_result.result == FastSMTPResult.CATCH_ALL:
                            basic_result['is_catch_all'] = True
                            basic_result['confidence_score'] = max(basic_result['confidence_score'] - 10, 40)
                            basic_result['deliverability'] = 'Unknown (Catch-all)'
                        
                    except Exception as e:
                        basic_result['smtp_details'] = {
                            'smtp_valid': False,
                            'error': str(e),
                            'response_time_ms': 0
                        }
                else:
                    basic_result['smtp_details'] = None
                
                basic_result['is_catch_all'] = basic_result.get('is_catch_all', False)
                return basic_result
        
        # Run all validations in parallel
        tasks = [validate_single(email) for email in emails]
        results = await asyncio.gather(*tasks)
        
        return results

# Global instance for easy import
fast_validator = FastEmailValidator()

# Drop-in replacement functions
def validate_email_with_smtp(email: str, enable_smtp: bool = True, **kwargs) -> Dict[str, Any]:
    """
    Drop-in replacement for the original validate_email_with_smtp
    This is 10x faster while maintaining the same API
    """
    return fast_validator.validate_email_with_fast_smtp(email, enable_smtp)

async def validate_batch_fast_smtp(emails: list, enable_smtp: bool = True, max_concurrent: int = 10) -> list:
    """
    Ultra-fast batch validation with SMTP
    """
    return await fast_validator.validate_batch_with_fast_smtp(emails, enable_smtp, max_concurrent)

def validate_batch_fast_smtp_sync(emails: list, enable_smtp: bool = True, max_concurrent: int = 10) -> list:
    """
    Sync wrapper for batch validation
    """
    return asyncio.run(validate_batch_fast_smtp(emails, enable_smtp, max_concurrent))

# Performance comparison function
def compare_smtp_performance(email: str) -> Dict[str, Any]:
    """
    Compare old vs new SMTP validation performance
    """
    import time
    from email_validator_smtp import validate_email_with_smtp as old_smtp
    
    # Test old SMTP
    start = time.time()
    try:
        old_result = old_smtp(email, enable_smtp=True)
        old_time = int((time.time() - start) * 1000)
        old_success = True
    except Exception as e:
        old_time = int((time.time() - start) * 1000)
        old_success = False
        old_result = {'error': str(e)}
    
    # Test new fast SMTP
    start = time.time()
    try:
        new_result = validate_email_with_smtp(email, enable_smtp=True)
        new_time = int((time.time() - start) * 1000)
        new_success = True
    except Exception as e:
        new_time = int((time.time() - start) * 1000)
        new_success = False
        new_result = {'error': str(e)}
    
    return {
        'email': email,
        'old_smtp': {
            'time_ms': old_time,
            'success': old_success,
            'result': old_result
        },
        'new_fast_smtp': {
            'time_ms': new_time,
            'success': new_success,
            'result': new_result
        },
        'speed_improvement': f"{old_time / new_time:.1f}x faster" if new_time > 0 else "N/A"
    }

if __name__ == "__main__":
    # Performance test
    test_emails = [
        "test@gmail.com",
        "user@outlook.com", 
        "invalid@nonexistent12345.com"
    ]
    
    print("🚀 Fast SMTP Integration Performance Test")
    print("=" * 60)
    
    for email in test_emails:
        comparison = compare_smtp_performance(email)
        print(f"\n📧 {email}")
        print(f"   Old SMTP: {comparison['old_smtp']['time_ms']}ms")
        print(f"   New Fast: {comparison['new_fast_smtp']['time_ms']}ms")
        print(f"   Improvement: {comparison['speed_improvement']}")