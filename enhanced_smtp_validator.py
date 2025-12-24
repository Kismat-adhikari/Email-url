#!/usr/bin/env python3
"""
Enhanced Multi-Strategy SMTP Email Validator
Combines multiple verification techniques for maximum accuracy
"""

import smtplib
import socket
import dns.resolver
import random
import time
import asyncio
import aiosmtplib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SMTPResult(Enum):
    DELIVERABLE = "deliverable"
    UNDELIVERABLE = "undeliverable" 
    RISKY = "risky"
    UNKNOWN = "unknown"
    CATCH_ALL = "catch_all"
    GREYLISTED = "greylisted"
    BLOCKED = "blocked"

@dataclass
class SMTPResponse:
    result: SMTPResult
    confidence: float  # 0.0 to 1.0
    smtp_code: Optional[int] = None
    message: str = ""
    mx_server: str = ""
    response_time_ms: int = 0
    is_catch_all: bool = False
    error: Optional[str] = None

class EnhancedSMTPValidator:
    """
    Multi-strategy SMTP validator that combines:
    1. Traditional SMTP verification
    2. Async parallel checking
    3. Provider-specific optimizations
    4. Reputation-based scoring
    5. Fallback strategies
    """
    
    def __init__(self):
        self.timeout = 15
        self.max_retries = 3
        self.sender_pool = [
            "verify@emailvalidator.com",
            "check@mailverify.org", 
            "validate@emailcheck.net",
            "test@verification.io",
            "noreply@validator.co"
        ]
        
        # Provider-specific configurations
        self.provider_configs = {
            'gmail.com': {'timeout': 20, 'retries': 2, 'delay': 5},
            'outlook.com': {'timeout': 25, 'retries': 3, 'delay': 3},
            'yahoo.com': {'timeout': 30, 'retries': 2, 'delay': 7},
            'hotmail.com': {'timeout': 25, 'retries': 3, 'delay': 3},
        }
    
    async def verify_email_multi_strategy(self, email: str) -> SMTPResponse:
        """
        Main verification method using multiple strategies
        """
        domain = email.split('@')[1].lower()
        
        # Strategy 1: Fast async check
        async_result = await self._async_smtp_check(email)
        
        # Strategy 2: Traditional SMTP with retries
        sync_result = self._sync_smtp_check(email)
        
        # Strategy 3: Provider-specific optimization
        provider_result = self._provider_specific_check(email, domain)
        
        # Strategy 4: Catch-all detection
        catch_all_result = await self._advanced_catch_all_detection(domain)
        
        # Combine results with weighted scoring
        final_result = self._combine_results([
            (async_result, 0.3),
            (sync_result, 0.4), 
            (provider_result, 0.2),
            (catch_all_result, 0.1)
        ])
        
        return final_result
    
    async def _async_smtp_check(self, email: str) -> SMTPResponse:
        """Async SMTP verification for speed"""
        try:
            domain = email.split('@')[1]
            mx_records = await self._get_mx_records_async(domain)
            
            if not mx_records:
                return SMTPResponse(
                    result=SMTPResult.UNDELIVERABLE,
                    confidence=0.9,
                    error="No MX records"
                )
            
            # Try multiple MX servers in parallel
            tasks = []
            for mx in mx_records[:3]:  # Top 3 MX servers
                task = self._async_smtp_connect(email, mx)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Return best result
            best_result = self._select_best_result(results)
            return best_result
            
        except Exception as e:
            return SMTPResponse(
                result=SMTPResult.UNKNOWN,
                confidence=0.1,
                error=str(e)
            )
    
    async def _async_smtp_connect(self, email: str, mx_server: str) -> SMTPResponse:
        """Single async SMTP connection"""
        start_time = time.time()
        
        try:
            smtp = aiosmtplib.SMTP(hostname=mx_server, timeout=self.timeout)
            await smtp.connect()
            
            # Random sender
            sender = random.choice(self.sender_pool)
            await smtp.mail(sender)
            
            # Test the actual email
            code, message = await smtp.rcpt(email)
            
            response_time = int((time.time() - start_time) * 1000)
            
            await smtp.quit()
            
            # Interpret response
            if code == 250:
                return SMTPResponse(
                    result=SMTPResult.DELIVERABLE,
                    confidence=0.85,
                    smtp_code=code,
                    message=message,
                    mx_server=mx_server,
                    response_time_ms=response_time
                )
            elif code == 550:
                return SMTPResponse(
                    result=SMTPResult.UNDELIVERABLE,
                    confidence=0.9,
                    smtp_code=code,
                    message=message,
                    mx_server=mx_server,
                    response_time_ms=response_time
                )
            else:
                return SMTPResponse(
                    result=SMTPResult.RISKY,
                    confidence=0.5,
                    smtp_code=code,
                    message=message,
                    mx_server=mx_server,
                    response_time_ms=response_time
                )
                
        except Exception as e:
            return SMTPResponse(
                result=SMTPResult.UNKNOWN,
                confidence=0.2,
                error=str(e),
                mx_server=mx_server
            )
    
    def _sync_smtp_check(self, email: str) -> SMTPResponse:
        """Traditional SMTP check with enhanced retry logic"""
        domain = email.split('@')[1].lower()
        config = self.provider_configs.get(domain, {
            'timeout': self.timeout,
            'retries': self.max_retries,
            'delay': 3
        })
        
        for attempt in range(config['retries']):
            try:
                if attempt > 0:
                    time.sleep(config['delay'])
                
                result = self._single_smtp_check(email, config['timeout'])
                if result.result != SMTPResult.UNKNOWN:
                    return result
                    
            except Exception as e:
                logger.warning(f"SMTP attempt {attempt + 1} failed: {e}")
                continue
        
        return SMTPResponse(
            result=SMTPResult.UNKNOWN,
            confidence=0.1,
            error="All SMTP attempts failed"
        )
    
    def _single_smtp_check(self, email: str, timeout: int) -> SMTPResponse:
        """Single SMTP verification attempt"""
        start_time = time.time()
        
        try:
            domain = email.split('@')[1]
            mx_records = self._get_mx_records(domain)
            
            if not mx_records:
                return SMTPResponse(
                    result=SMTPResult.UNDELIVERABLE,
                    confidence=0.9,
                    error="No MX records"
                )
            
            # Try primary MX server
            mx_server = mx_records[0]
            
            with smtplib.SMTP(timeout=timeout) as server:
                server.connect(mx_server)
                server.helo(f"validator{random.randint(100, 999)}.com")
                
                sender = random.choice(self.sender_pool)
                server.mail(sender)
                
                code, message = server.rcpt(email)
                response_time = int((time.time() - start_time) * 1000)
                
                # Enhanced response interpretation
                if code == 250:
                    confidence = 0.85
                    result = SMTPResult.DELIVERABLE
                elif code in [550, 551, 553]:
                    confidence = 0.9
                    result = SMTPResult.UNDELIVERABLE
                elif code in [450, 451, 452]:
                    confidence = 0.3
                    result = SMTPResult.GREYLISTED
                elif code in [421, 422]:
                    confidence = 0.2
                    result = SMTPResult.BLOCKED
                else:
                    confidence = 0.4
                    result = SMTPResult.RISKY
                
                return SMTPResponse(
                    result=result,
                    confidence=confidence,
                    smtp_code=code,
                    message=str(message),
                    mx_server=mx_server,
                    response_time_ms=response_time
                )
                
        except Exception as e:
            return SMTPResponse(
                result=SMTPResult.UNKNOWN,
                confidence=0.1,
                error=str(e)
            )
    
    def _provider_specific_check(self, email: str, domain: str) -> SMTPResponse:
        """Provider-specific optimizations"""
        
        # Gmail specific
        if 'gmail' in domain:
            return self._gmail_specific_check(email)
        
        # Outlook/Hotmail specific  
        elif any(provider in domain for provider in ['outlook', 'hotmail', 'live']):
            return self._microsoft_specific_check(email)
        
        # Yahoo specific
        elif 'yahoo' in domain:
            return self._yahoo_specific_check(email)
        
        # Generic check
        else:
            return SMTPResponse(
                result=SMTPResult.UNKNOWN,
                confidence=0.0,
                message="No provider-specific optimization"
            )
    
    def _gmail_specific_check(self, email: str) -> SMTPResponse:
        """Gmail-specific validation logic"""
        # Gmail accepts dots anywhere, so normalize
        local_part = email.split('@')[0]
        normalized = local_part.replace('.', '')
        
        # Gmail has specific patterns that are always invalid
        invalid_patterns = ['noreply', 'no-reply', 'donotreply']
        if any(pattern in normalized.lower() for pattern in invalid_patterns):
            return SMTPResponse(
                result=SMTPResult.UNDELIVERABLE,
                confidence=0.8,
                message="Gmail pattern suggests invalid"
            )
        
        return SMTPResponse(
            result=SMTPResult.UNKNOWN,
            confidence=0.0,
            message="Gmail check inconclusive"
        )
    
    def _microsoft_specific_check(self, email: str) -> SMTPResponse:
        """Microsoft (Outlook/Hotmail) specific validation"""
        # Microsoft often blocks SMTP verification
        return SMTPResponse(
            result=SMTPResult.RISKY,
            confidence=0.3,
            message="Microsoft domains often block SMTP verification"
        )
    
    def _yahoo_specific_check(self, email: str) -> SMTPResponse:
        """Yahoo-specific validation logic"""
        # Yahoo has strict SMTP policies
        return SMTPResponse(
            result=SMTPResult.RISKY,
            confidence=0.4,
            message="Yahoo has strict SMTP policies"
        )
    
    async def _advanced_catch_all_detection(self, domain: str) -> SMTPResponse:
        """Advanced catch-all detection with multiple test emails"""
        try:
            # Test with multiple obviously fake emails
            test_emails = [
                f"nonexistent{random.randint(10000, 99999)}@{domain}",
                f"fakeemail{random.randint(10000, 99999)}@{domain}",
                f"invalid{random.randint(10000, 99999)}@{domain}"
            ]
            
            results = []
            for test_email in test_emails:
                result = await self._async_smtp_connect(test_email, domain)
                results.append(result.result == SMTPResult.DELIVERABLE)
            
            # If most fake emails are accepted, it's catch-all
            acceptance_rate = sum(results) / len(results)
            
            if acceptance_rate > 0.7:
                return SMTPResponse(
                    result=SMTPResult.CATCH_ALL,
                    confidence=0.9,
                    is_catch_all=True,
                    message=f"Catch-all detected (acceptance rate: {acceptance_rate:.2f})"
                )
            
            return SMTPResponse(
                result=SMTPResult.UNKNOWN,
                confidence=0.1,
                is_catch_all=False
            )
            
        except Exception as e:
            return SMTPResponse(
                result=SMTPResult.UNKNOWN,
                confidence=0.0,
                error=str(e)
            )
    
    def _combine_results(self, weighted_results: List[Tuple[SMTPResponse, float]]) -> SMTPResponse:
        """Combine multiple results with weighted scoring"""
        
        total_weight = 0
        weighted_confidence = 0
        best_result = SMTPResult.UNKNOWN
        combined_messages = []
        
        for result, weight in weighted_results:
            if result.confidence > 0:
                total_weight += weight
                weighted_confidence += result.confidence * weight
                combined_messages.append(f"{result.result.value}: {result.message}")
                
                # Use result with highest confidence
                if result.confidence > weighted_confidence / total_weight:
                    best_result = result.result
        
        final_confidence = weighted_confidence / total_weight if total_weight > 0 else 0
        
        return SMTPResponse(
            result=best_result,
            confidence=final_confidence,
            message=" | ".join(combined_messages[:3])  # Top 3 messages
        )
    
    async def _get_mx_records_async(self, domain: str) -> List[str]:
        """Get MX records asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            mx_records = await loop.run_in_executor(
                None, 
                lambda: dns.resolver.resolve(domain, 'MX')
            )
            return [str(mx.exchange).rstrip('.') for mx in sorted(mx_records, key=lambda x: x.preference)]
        except:
            return []
    
    def _get_mx_records(self, domain: str) -> List[str]:
        """Get MX records synchronously"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return [str(mx.exchange).rstrip('.') for mx in sorted(mx_records, key=lambda x: x.preference)]
        except:
            return []
    
    def _select_best_result(self, results: List) -> SMTPResponse:
        """Select the best result from multiple attempts"""
        valid_results = [r for r in results if isinstance(r, SMTPResponse)]
        
        if not valid_results:
            return SMTPResponse(
                result=SMTPResult.UNKNOWN,
                confidence=0.0,
                error="No valid results"
            )
        
        # Sort by confidence, then by result priority
        result_priority = {
            SMTPResult.DELIVERABLE: 5,
            SMTPResult.UNDELIVERABLE: 4,
            SMTPResult.CATCH_ALL: 3,
            SMTPResult.RISKY: 2,
            SMTPResult.GREYLISTED: 1,
            SMTPResult.UNKNOWN: 0
        }
        
        best = max(valid_results, key=lambda r: (r.confidence, result_priority.get(r.result, 0)))
        return best


# Usage example
async def validate_email_enhanced(email: str) -> Dict[str, Any]:
    """
    Enhanced email validation with multi-strategy SMTP
    """
    validator = EnhancedSMTPValidator()
    smtp_result = await validator.verify_email_multi_strategy(email)
    
    return {
        'email': email,
        'smtp_result': smtp_result.result.value,
        'confidence': smtp_result.confidence,
        'deliverable': smtp_result.result == SMTPResult.DELIVERABLE,
        'is_catch_all': smtp_result.is_catch_all,
        'smtp_code': smtp_result.smtp_code,
        'message': smtp_result.message,
        'response_time_ms': smtp_result.response_time_ms,
        'error': smtp_result.error
    }