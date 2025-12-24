#!/usr/bin/env python3
"""
SMTP Intelligence Layer
Adds reputation scoring and pattern learning to SMTP validation
"""

import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib

@dataclass
class SMTPReputation:
    domain: str
    success_rate: float
    total_checks: int
    last_updated: float
    avg_response_time: float
    common_codes: Dict[int, int]  # code -> count
    blocks_smtp: bool = False
    is_catch_all: Optional[bool] = None

class SMTPIntelligence:
    """
    Intelligence layer that learns from SMTP validation patterns
    to improve accuracy over time
    """
    
    def __init__(self, cache_file: str = "smtp_reputation.json"):
        self.cache_file = cache_file
        self.reputation_cache: Dict[str, SMTPReputation] = {}
        self.domain_patterns: Dict[str, Dict] = defaultdict(dict)
        self.load_reputation_cache()
    
    def load_reputation_cache(self):
        """Load reputation data from cache file"""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                for domain, rep_data in data.get('reputations', {}).items():
                    self.reputation_cache[domain] = SMTPReputation(**rep_data)
                self.domain_patterns = data.get('patterns', defaultdict(dict))
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading reputation cache: {e}")
    
    def save_reputation_cache(self):
        """Save reputation data to cache file"""
        try:
            data = {
                'reputations': {
                    domain: asdict(rep) for domain, rep in self.reputation_cache.items()
                },
                'patterns': dict(self.domain_patterns)
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving reputation cache: {e}")
    
    def update_reputation(self, domain: str, smtp_code: Optional[int], 
                         response_time: int, success: bool, is_catch_all: bool = False):
        """Update domain reputation based on SMTP result"""
        
        if domain not in self.reputation_cache:
            self.reputation_cache[domain] = SMTPReputation(
                domain=domain,
                success_rate=0.0,
                total_checks=0,
                last_updated=time.time(),
                avg_response_time=0.0,
                common_codes=defaultdict(int),
                blocks_smtp=False,
                is_catch_all=None
            )
        
        rep = self.reputation_cache[domain]
        
        # Update success rate
        old_total = rep.total_checks
        rep.total_checks += 1
        rep.success_rate = ((rep.success_rate * old_total) + (1 if success else 0)) / rep.total_checks
        
        # Update response time
        rep.avg_response_time = ((rep.avg_response_time * old_total) + response_time) / rep.total_checks
        
        # Update common codes
        if smtp_code:
            rep.common_codes[smtp_code] = rep.common_codes.get(smtp_code, 0) + 1
        
        # Update catch-all detection
        if is_catch_all:
            rep.is_catch_all = True
        
        # Detect if domain blocks SMTP
        if smtp_code in [421, 554, 571] or response_time > 30000:
            rep.blocks_smtp = True
        
        rep.last_updated = time.time()
        
        # Save periodically
        if rep.total_checks % 10 == 0:
            self.save_reputation_cache()
    
    def get_domain_intelligence(self, domain: str) -> Dict[str, Any]:
        """Get intelligence data for a domain"""
        rep = self.reputation_cache.get(domain)
        
        if not rep:
            return {
                'has_data': False,
                'recommendation': 'unknown',
                'confidence': 0.0
            }
        
        # Calculate recommendation based on reputation
        recommendation = 'unknown'
        confidence = 0.5
        
        if rep.total_checks >= 5:  # Enough data
            if rep.success_rate > 0.8:
                recommendation = 'reliable'
                confidence = 0.9
            elif rep.success_rate > 0.5:
                recommendation = 'moderate'
                confidence = 0.7
            elif rep.blocks_smtp:
                recommendation = 'blocks_smtp'
                confidence = 0.8
            else:
                recommendation = 'unreliable'
                confidence = 0.6
        
        return {
            'has_data': True,
            'total_checks': rep.total_checks,
            'success_rate': rep.success_rate,
            'avg_response_time': rep.avg_response_time,
            'blocks_smtp': rep.blocks_smtp,
            'is_catch_all': rep.is_catch_all,
            'most_common_code': max(rep.common_codes.items(), key=lambda x: x[1])[0] if rep.common_codes else None,
            'recommendation': recommendation,
            'confidence': confidence,
            'last_updated': rep.last_updated
        }
    
    def should_skip_smtp(self, domain: str) -> bool:
        """Determine if SMTP check should be skipped for this domain"""
        rep = self.reputation_cache.get(domain)
        
        if not rep or rep.total_checks < 3:
            return False
        
        # Skip if domain consistently blocks SMTP
        if rep.blocks_smtp and rep.success_rate < 0.1:
            return True
        
        # Skip if average response time is too high
        if rep.avg_response_time > 25000:  # 25 seconds
            return True
        
        return False
    
    def get_optimal_strategy(self, domain: str) -> Dict[str, Any]:
        """Get optimal validation strategy for domain"""
        intelligence = self.get_domain_intelligence(domain)
        
        strategy = {
            'use_smtp': True,
            'timeout': 15,
            'retries': 2,
            'delay': 3,
            'use_async': False,
            'priority': 'normal'
        }
        
        if not intelligence['has_data']:
            return strategy
        
        # Adjust strategy based on intelligence
        if intelligence['blocks_smtp']:
            strategy['use_smtp'] = False
            strategy['priority'] = 'dns_only'
        elif intelligence['avg_response_time'] > 20000:
            strategy['timeout'] = 30
            strategy['retries'] = 1
            strategy['use_async'] = True
        elif intelligence['success_rate'] > 0.8:
            strategy['timeout'] = 10
            strategy['retries'] = 1
            strategy['priority'] = 'fast'
        
        return strategy

# Pattern Learning for Email Validation
class EmailPatternLearner:
    """
    Learns patterns from email validation results to improve accuracy
    """
    
    def __init__(self):
        self.patterns = {
            'valid_patterns': defaultdict(int),
            'invalid_patterns': defaultdict(int),
            'domain_patterns': defaultdict(lambda: {'valid': 0, 'invalid': 0})
        }
    
    def learn_from_result(self, email: str, is_valid: bool, confidence: float):
        """Learn patterns from validation results"""
        if confidence < 0.7:  # Only learn from high-confidence results
            return
        
        local_part, domain = email.split('@')
        
        # Learn local part patterns
        local_hash = self._hash_pattern(local_part)
        if is_valid:
            self.patterns['valid_patterns'][local_hash] += 1
        else:
            self.patterns['invalid_patterns'][local_hash] += 1
        
        # Learn domain patterns
        if is_valid:
            self.patterns['domain_patterns'][domain]['valid'] += 1
        else:
            self.patterns['domain_patterns'][domain]['invalid'] += 1
    
    def predict_validity(self, email: str) -> Dict[str, Any]:
        """Predict email validity based on learned patterns"""
        local_part, domain = email.split('@')
        local_hash = self._hash_pattern(local_part)
        
        # Check local part patterns
        valid_count = self.patterns['valid_patterns'].get(local_hash, 0)
        invalid_count = self.patterns['invalid_patterns'].get(local_hash, 0)
        
        # Check domain patterns
        domain_stats = self.patterns['domain_patterns'].get(domain, {'valid': 0, 'invalid': 0})
        
        # Calculate prediction
        total_local = valid_count + invalid_count
        total_domain = domain_stats['valid'] + domain_stats['invalid']
        
        if total_local > 0:
            local_confidence = valid_count / total_local
        else:
            local_confidence = 0.5
        
        if total_domain > 0:
            domain_confidence = domain_stats['valid'] / total_domain
        else:
            domain_confidence = 0.5
        
        # Combine predictions
        overall_confidence = (local_confidence * 0.3) + (domain_confidence * 0.7)
        
        return {
            'predicted_valid': overall_confidence > 0.5,
            'confidence': overall_confidence,
            'local_pattern_matches': total_local,
            'domain_pattern_matches': total_domain,
            'recommendation': 'high_confidence' if overall_confidence > 0.8 or overall_confidence < 0.2 else 'uncertain'
        }
    
    def _hash_pattern(self, local_part: str) -> str:
        """Create a pattern hash for local part"""
        # Create pattern: letters -> L, numbers -> N, special -> S
        pattern = ''
        for char in local_part.lower():
            if char.isalpha():
                pattern += 'L'
            elif char.isdigit():
                pattern += 'N'
            else:
                pattern += 'S'
        
        # Compress similar patterns
        compressed = ''
        prev_char = ''
        count = 0
        
        for char in pattern:
            if char == prev_char:
                count += 1
            else:
                if prev_char:
                    compressed += prev_char + (str(count) if count > 1 else '')
                prev_char = char
                count = 1
        
        if prev_char:
            compressed += prev_char + (str(count) if count > 1 else '')
        
        return compressed[:20]  # Limit length