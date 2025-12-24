#!/usr/bin/env python3
"""
Integration layer for enhanced SMTP validation with existing Flask backend
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from email_validator_smtp_v2 import EmailValidatorV2, validate_email_with_smtp_sync_v2
from emailvalidator_unified import validate_email_advanced

logger = logging.getLogger(__name__)

class SMTPIntegrationLayer:
    """
    Integration layer that provides both sync and async interfaces
    for the enhanced SMTP validator while maintaining backward compatibility
    """
    
    def __init__(self):
        self.enhanced_validator = EmailValidatorV2()
        self._loop = None
    
    def validate_email_enhanced(self, email: str, enable_smtp: bool = True, 
                              fallback_to_basic: bool = True) -> Dict[str, Any]:
        """
        Main validation method that integrates with existing Flask backend
        
        Args:
            email: Email to validate
            enable_smtp: Whether to use enhanced SMTP validation
            fallback_to_basic: Fall back to basic validation if enhanced fails
        
        Returns:
            Enhanced validation result compatible with existing code
        """
        try:
            # Try enhanced validation first
            if enable_smtp:
                result = validate_email_with_smtp_sync_v2(email, enable_smtp=True)
                
                # Add backward compatibility fields
                result = self._ensure_backward_compatibility(result)
                
                logger.info(f"Enhanced SMTP validation completed for {email}: "
                          f"valid={result['valid']}, confidence={result['confidence_score']}")
                
                return result
            
        except Exception as e:
            logger.warning(f"Enhanced SMTP validation failed for {email}: {e}")
            
            if not fallback_to_basic:
                raise
        
        # Fallback to existing validation
        logger.info(f"Using fallback validation for {email}")
        basic_result = validate_email_advanced(email)
        return self._ensure_backward_compatibility(basic_result)
    
    def _ensure_backward_compatibility(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure the result has all fields expected by existing code
        """
        # Make sure all expected fields exist
        if 'deliverability' not in result:
            confidence = result.get('confidence_score', 0)
            if confidence >= 80:
                result['deliverability'] = 'High'
            elif confidence >= 60:
                result['deliverability'] = 'Medium'
            else:
                result['deliverability'] = 'Low'
        
        # Ensure boolean fields
        result['valid'] = bool(result.get('valid', False))
        result['is_catch_all'] = bool(result.get('is_catch_all', False))
        
        # Ensure numeric fields
        result['confidence_score'] = int(result.get('confidence_score', 0))
        
        # Add validation_time_ms if missing
        if 'validation_time_ms' not in result:
            result['validation_time_ms'] = 0
        
        return result

# Global instance for Flask integration
smtp_integration = SMTPIntegrationLayer()

def validate_email_for_flask(email: str, enable_enhanced_smtp: bool = True) -> Dict[str, Any]:
    """
    Flask-compatible validation function
    
    This function can be used as a drop-in replacement for existing
    validation calls in app_anon_history.py
    """
    return smtp_integration.validate_email_enhanced(
        email=email,
        enable_smtp=enable_enhanced_smtp,
        fallback_to_basic=True
    )