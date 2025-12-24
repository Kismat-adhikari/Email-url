#!/usr/bin/env python3
"""
Enhanced Email Validator with SMTP Verification V2
Integrates multi-strategy SMTP validation with intelligence layer
"""

import asyncio
from typing import Dict, Any, Optional
from enhanced_smtp_validator import EnhancedSMTPValidator, SMTPResult
from smtp_intelligence import SMTPIntelligence, EmailPatternLearner
from emailvalidator_unified import validate_email_advanced
import time
import logging

logger = logging.getLogger(__name__)

class EmailValidatorV2:
    """
    Enhanced email validator that combines:
    1. Traditional validation (syntax, DNS, MX)
    2. Multi-strategy SMTP verification
    3. Intelligence layer with reputation scoring
    4. Pattern learning for improved accuracy
    """
    
    def __init__(self):
        self.smtp_validator = EnhancedSMTPValidator()
        self.intelligence = SMTPIntelligence()
        self.pattern_learner = EmailPatternLearner()
    
    async def validate_email_complete(self, email: str, enable_smtp: bool = True) -> Dict[str, Any]:
        """
        Complete email validation with all enhancements
        """
        start_time = time.time()
        
        # Step 1: Basic validation (syntax, DNS, MX)
        basic_result = validate_email_advanced(email)
        
        # Step 2: Get domain intelligence
        domain = email.split('@')[1].lower()
        intelligence = self.intelligence.get_domain_intelligence(domain)
        strategy = self.intelligence.get_optimal_strategy(domain)
        
        # Step 3: Pattern-based prediction
        pattern_prediction = self.pattern_learner.predict_validity(email)
        
        # Step 4: SMTP validation (if enabled and recommended)
        smtp_result = None
        if enable_smtp and basic_result['checks']['syntax'] and strategy['use_smtp']:
            try:
                smtp_result = await self.smtp_validator.verify_email_multi_strategy(email)
                
                # Update intelligence with result
                self.intelligence.update_reputation(
                    domain=domain,
                    smtp_code=smtp_result.smtp_code,
                    response_time=smtp_result.response_time_ms,
                    success=smtp_result.result == SMTPResult.DELIVERABLE,
                    is_catch_all=smtp_result.is_catch_all
                )
                
            except Exception as e:
                logger.error(f"SMTP validation failed: {e}")
                smtp_result = None
        
        # Step 5: Combine all results
        final_result = self._combine_all_results(
            basic_result, smtp_result, intelligence, pattern_prediction, strategy
        )
        
        # Step 6: Learn from this validation
        self.pattern_learner.learn_from_result(
            email, final_result['valid'], final_result['confidence_score'] / 100
        )
        
        final_result['validation_time_ms'] = int((time.time() - start_time) * 1000)
        return final_result
    
    def _combine_all_results(self, basic_result: Dict, smtp_result, intelligence: Dict, 
                           pattern_prediction: Dict, strategy: Dict) -> Dict[str, Any]:
        """
        Intelligently combine all validation results
        """
        result = basic_result.copy()
        
        # Base confidence from basic validation
        confidence = result['confidence_score']
        
        # Add SMTP intelligence
        if smtp_result:
            smtp_confidence = int(smtp_result.confidence * 100)
            
            if smtp_result.result == SMTPResult.DELIVERABLE:
                confidence = max(confidence, 85)
                result['deliverability'] = 'High'
            elif smtp_result.result == SMTPResult.UNDELIVERABLE:
                confidence = min(confidence, 20)
                result['deliverability'] = 'Low'
                result['valid'] = False
            elif smtp_result.result == SMTPResult.CATCH_ALL:
                confidence = max(confidence - 15, 50)  # Reduce confidence for catch-all
                result['deliverability'] = 'Unknown (Catch-all)'
            elif smtp_result.result == SMTPResult.RISKY:
                confidence = max(confidence - 10, 40)
                result['deliverability'] = 'Risky'
            
            result['smtp_details'] = {
                'result': smtp_result.result.value,
                'confidence': smtp_result.confidence,
                'smtp_code': smtp_result.smtp_code,
                'message': smtp_result.message,
                'response_time_ms': smtp_result.response_time_ms,
                'is_catch_all': smtp_result.is_catch_all,
                'mx_server': smtp_result.mx_server
            }
        else:
            result['smtp_details'] = None
        
        # Add domain intelligence
        if intelligence['has_data']:
            if intelligence['blocks_smtp']:
                result['reason'] = (result.get('reason', '') + '; Domain blocks SMTP verification').strip('; ')
            
            if intelligence['is_catch_all']:
                result['is_catch_all'] = True
                confidence = max(confidence - 10, 30)
            
            # Adjust confidence based on domain reputation
            if intelligence['success_rate'] > 0.8:
                confidence = min(confidence + 5, 100)
            elif intelligence['success_rate'] < 0.3:
                confidence = max(confidence - 10, 20)
        
        # Add pattern prediction
        if pattern_prediction['recommendation'] == 'high_confidence':
            if pattern_prediction['predicted_valid']:
                confidence = min(confidence + 5, 100)
            else:
                confidence = max(confidence - 15, 10)
                result['valid'] = False
        
        # Add strategy information
        result['validation_strategy'] = {
            'used_smtp': smtp_result is not None,
            'strategy_priority': strategy['priority'],
            'domain_intelligence': intelligence['recommendation'] if intelligence['has_data'] else 'no_data',
            'pattern_matches': pattern_prediction['local_pattern_matches'] + pattern_prediction['domain_pattern_matches']
        }
        
        # Final confidence score
        result['confidence_score'] = max(min(confidence, 100), 0)
        
        # Enhanced reason with more context
        reasons = []
        if result.get('reason'):
            reasons.append(result['reason'])
        
        if smtp_result and smtp_result.error:
            reasons.append(f"SMTP: {smtp_result.error}")
        
        if intelligence['has_data'] and intelligence['blocks_smtp']:
            reasons.append("Domain known to block SMTP verification")
        
        if pattern_prediction['recommendation'] == 'high_confidence' and not pattern_prediction['predicted_valid']:
            reasons.append("Pattern analysis suggests invalid")
        
        result['reason'] = '; '.join(reasons) if reasons else None
        
        return result

# Convenience functions for backward compatibility
async def validate_email_with_smtp_v2(email: str, enable_smtp: bool = True) -> Dict[str, Any]:
    """
    Enhanced email validation with SMTP V2 - async version
    """
    validator = EmailValidatorV2()
    return await validator.validate_email_complete(email, enable_smtp)

def validate_email_with_smtp_sync_v2(email: str, enable_smtp: bool = True) -> Dict[str, Any]:
    """
    Enhanced email validation with SMTP V2 - sync version
    """
    return asyncio.run(validate_email_with_smtp_v2(email, enable_smtp))

# Example usage and testing
if __name__ == "__main__":
    async def test_validation():
        validator = EmailValidatorV2()
        
        test_emails = [
            "user@gmail.com",
            "invalid@nonexistentdomain12345.com", 
            "test@example.com",
            "admin@outlook.com"
        ]
        
        for email in test_emails:
            print(f"\n--- Testing: {email} ---")
            result = await validator.validate_email_complete(email)
            
            print(f"Valid: {result['valid']}")
            print(f"Confidence: {result['confidence_score']}%")
            print(f"Deliverability: {result.get('deliverability', 'Unknown')}")
            print(f"Strategy: {result['validation_strategy']['strategy_priority']}")
            print(f"Time: {result['validation_time_ms']}ms")
            
            if result['smtp_details']:
                smtp = result['smtp_details']
                print(f"SMTP Result: {smtp['result']} (Code: {smtp['smtp_code']})")
            
            if result.get('reason'):
                print(f"Reason: {result['reason']}")
    
    # Run test
    asyncio.run(test_validation())