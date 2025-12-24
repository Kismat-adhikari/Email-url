#!/usr/bin/env python3
"""
Enhanced SMTP Integration Patch for app_anon_history.py
This provides drop-in replacements for existing validation functions
"""

import logging
from typing import Dict, Any, Optional
from smtp_integration import validate_email_for_flask

logger = logging.getLogger(__name__)

# Enhanced validation functions that can replace existing ones

def validate_email_enhanced_tiered(email: str) -> Dict[str, Any]:
    """
    Enhanced replacement for validate_email_tiered()
    Uses the new multi-strategy SMTP validation
    """
    try:
        result = validate_email_for_flask(email, enable_enhanced_smtp=True)
        
        # Add tiered-specific fields if missing
        if 'tier' not in result:
            confidence = result.get('confidence_score', 0)
            if confidence >= 90:
                result['tier'] = 'premium'
            elif confidence >= 70:
                result['tier'] = 'standard'
            else:
                result['tier'] = 'basic'
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced tiered validation failed for {email}: {e}")
        # Fallback to original
        from emailvalidator_unified import validate_email_tiered
        return validate_email_tiered(email)

def validate_email_enhanced_advanced(email: str) -> Dict[str, Any]:
    """
    Enhanced replacement for validate_email_advanced()
    Uses the new multi-strategy SMTP validation
    """
    try:
        result = validate_email_for_flask(email, enable_enhanced_smtp=True)
        
        # Ensure advanced-specific fields
        if 'advanced_checks' not in result:
            result['advanced_checks'] = {
                'smtp_verified': result.get('smtp_details', {}).get('result') == 'deliverable',
                'catch_all_detected': result.get('is_catch_all', False),
                'reputation_score': result.get('confidence_score', 0),
                'response_time_ms': result.get('validation_time_ms', 0)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced advanced validation failed for {email}: {e}")
        # Fallback to original
        from emailvalidator_unified import validate_email_advanced
        return validate_email_advanced(email)

def validate_email_with_enhanced_smtp(email: str, enable_smtp: bool = True, **kwargs) -> Dict[str, Any]:
    """
    Enhanced replacement for validate_email_with_smtp()
    Uses the new multi-strategy SMTP validation
    """
    try:
        result = validate_email_for_flask(email, enable_enhanced_smtp=enable_smtp)
        
        # Add SMTP-specific fields for backward compatibility
        if enable_smtp and result.get('smtp_details'):
            smtp_details = result['smtp_details']
            result['smtp_valid'] = smtp_details.get('result') == 'deliverable'
            result['smtp_code'] = smtp_details.get('smtp_code')
            result['smtp_message'] = smtp_details.get('message', '')
            result['mx_server'] = smtp_details.get('mx_server', '')
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced SMTP validation failed for {email}: {e}")
        # Fallback to original
        from email_validator_smtp import validate_email_with_smtp
        return validate_email_with_smtp(email, enable_smtp=enable_smtp, **kwargs)

# Batch validation enhancement
def validate_batch_enhanced(emails: list, advanced: bool = True, enable_smtp: bool = False) -> list:
    """
    Enhanced batch validation with intelligent SMTP usage
    """
    results = []
    
    # For large batches, be selective about SMTP to avoid timeouts
    use_smtp_for_batch = enable_smtp and len(emails) <= 50
    
    for email in emails:
        try:
            if advanced:
                result = validate_email_for_flask(email, enable_enhanced_smtp=use_smtp_for_batch)
            else:
                # Basic validation fallback
                from emailvalidator_unified import validate_email
                is_valid = validate_email(email)
                result = {
                    'email': email,
                    'valid': is_valid,
                    'confidence_score': 80 if is_valid else 20,
                    'checks': {'syntax': is_valid}
                }
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Batch validation failed for {email}: {e}")
            # Add error result
            results.append({
                'email': email,
                'valid': False,
                'confidence_score': 0,
                'error': str(e)
            })
    
    return results

# Configuration for gradual rollout
ENHANCED_VALIDATION_CONFIG = {
    'enabled': True,
    'use_for_authenticated': True,  # Use enhanced validation for logged-in users
    'use_for_anonymous': False,     # Keep original for anonymous (faster)
    'use_for_batch': True,          # Use enhanced for batch (but limit SMTP)
    'use_for_admin': True,          # Always use enhanced for admin
    'fallback_on_error': True       # Fall back to original on errors
}

def should_use_enhanced_validation(user_type: str = 'anonymous') -> bool:
    """
    Determine whether to use enhanced validation based on user type and config
    """
    if not ENHANCED_VALIDATION_CONFIG['enabled']:
        return False
    
    if user_type == 'admin':
        return ENHANCED_VALIDATION_CONFIG['use_for_admin']
    elif user_type == 'authenticated':
        return ENHANCED_VALIDATION_CONFIG['use_for_authenticated']
    elif user_type == 'batch':
        return ENHANCED_VALIDATION_CONFIG['use_for_batch']
    else:  # anonymous
        return ENHANCED_VALIDATION_CONFIG['use_for_anonymous']

# Smart validation router
def smart_validate_email(email: str, user_type: str = 'anonymous', 
                        enable_smtp: bool = True, advanced: bool = True) -> Dict[str, Any]:
    """
    Smart validation that chooses the best method based on context
    """
    use_enhanced = should_use_enhanced_validation(user_type)
    
    if use_enhanced:
        logger.info(f"Using enhanced validation for {user_type} user: {email}")
        if advanced:
            return validate_email_enhanced_advanced(email)
        else:
            return validate_email_for_flask(email, enable_enhanced_smtp=enable_smtp)
    else:
        logger.info(f"Using original validation for {user_type} user: {email}")
        if advanced:
            from emailvalidator_unified import validate_email_advanced
            return validate_email_advanced(email)
        else:
            from emailvalidator_unified import validate_email
            is_valid = validate_email(email)
            return {
                'email': email,
                'valid': is_valid,
                'confidence_score': 80 if is_valid else 20
            }

# Performance monitoring
class ValidationPerformanceMonitor:
    """
    Monitor performance differences between old and new validation
    """
    
    def __init__(self):
        self.stats = {
            'enhanced': {'count': 0, 'total_time': 0, 'errors': 0},
            'original': {'count': 0, 'total_time': 0, 'errors': 0}
        }
    
    def record_validation(self, method: str, time_ms: int, success: bool):
        """Record validation performance"""
        if method in self.stats:
            self.stats[method]['count'] += 1
            self.stats[method]['total_time'] += time_ms
            if not success:
                self.stats[method]['errors'] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance comparison report"""
        report = {}
        
        for method, stats in self.stats.items():
            if stats['count'] > 0:
                avg_time = stats['total_time'] / stats['count']
                error_rate = stats['errors'] / stats['count']
                report[method] = {
                    'average_time_ms': round(avg_time, 2),
                    'error_rate': round(error_rate * 100, 2),
                    'total_validations': stats['count']
                }
        
        return report

# Global performance monitor
performance_monitor = ValidationPerformanceMonitor()

# Export functions for easy integration
__all__ = [
    'validate_email_enhanced_tiered',
    'validate_email_enhanced_advanced', 
    'validate_email_with_enhanced_smtp',
    'validate_batch_enhanced',
    'smart_validate_email',
    'should_use_enhanced_validation',
    'performance_monitor',
    'ENHANCED_VALIDATION_CONFIG'
]