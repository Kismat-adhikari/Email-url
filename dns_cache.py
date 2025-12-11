#!/usr/bin/env python3
"""
DNS Cache System for Email Validation
Caches DNS and MX record lookups to avoid redundant queries.
"""

import time
import socket
from typing import Dict, Tuple, Optional, Set
from threading import Lock
import logging

# Optional DNS checking - gracefully handle if not installed
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

logger = logging.getLogger(__name__)

class DNSCache:
    """
    In-memory DNS cache with TTL support.
    Caches DNS and MX record results to avoid redundant lookups.
    """
    
    def __init__(self, default_ttl: int = 3600):  # 1 hour default TTL
        self.cache: Dict[str, Dict] = {}
        self.default_ttl = default_ttl
        self.lock = Lock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'total_queries': 0
        }
        
        # Pre-populate with common domains
        self._populate_common_domains()
    
    def _populate_common_domains(self):
        """Pre-populate cache with common email domains."""
        common_domains = {
            'gmail.com': {'dns_valid': True, 'mx_valid': True},
            'yahoo.com': {'dns_valid': True, 'mx_valid': True},
            'hotmail.com': {'dns_valid': True, 'mx_valid': True},
            'outlook.com': {'dns_valid': True, 'mx_valid': True},
            'icloud.com': {'dns_valid': True, 'mx_valid': True},
            'aol.com': {'dns_valid': True, 'mx_valid': True},
            'protonmail.com': {'dns_valid': True, 'mx_valid': True},
            'mail.com': {'dns_valid': True, 'mx_valid': True},
            'zoho.com': {'dns_valid': True, 'mx_valid': True},
            'gmx.com': {'dns_valid': True, 'mx_valid': True},
            'yandex.com': {'dns_valid': True, 'mx_valid': True},
            'live.com': {'dns_valid': True, 'mx_valid': True},
            'msn.com': {'dns_valid': True, 'mx_valid': True},
            'me.com': {'dns_valid': True, 'mx_valid': True},
            'mac.com': {'dns_valid': True, 'mx_valid': True},
        }
        
        current_time = time.time()
        for domain, results in common_domains.items():
            self.cache[domain] = {
                'dns_valid': results['dns_valid'],
                'mx_valid': results['mx_valid'],
                'timestamp': current_time,
                'ttl': 86400,  # 24 hours for common domains
                'source': 'preloaded'
            }
        
        logger.info(f"Pre-populated DNS cache with {len(common_domains)} common domains")
    
    def _is_expired(self, entry: Dict) -> bool:
        """Check if cache entry is expired."""
        return time.time() - entry['timestamp'] > entry['ttl']
    
    def get(self, domain: str) -> Optional[Tuple[bool, bool]]:
        """
        Get cached DNS/MX results for domain.
        
        Args:
            domain: Domain name to lookup
            
        Returns:
            Tuple of (dns_valid, mx_valid) or None if not cached/expired
        """
        with self.lock:
            self.stats['total_queries'] += 1
            
            if domain in self.cache:
                entry = self.cache[domain]
                if not self._is_expired(entry):
                    self.stats['hits'] += 1
                    logger.debug(f"DNS cache HIT for {domain}")
                    return (entry['dns_valid'], entry['mx_valid'])
                else:
                    # Remove expired entry
                    del self.cache[domain]
                    logger.debug(f"DNS cache EXPIRED for {domain}")
            
            self.stats['misses'] += 1
            logger.debug(f"DNS cache MISS for {domain}")
            return None
    
    def set(self, domain: str, dns_valid: bool, mx_valid: bool, ttl: Optional[int] = None):
        """
        Cache DNS/MX results for domain.
        
        Args:
            domain: Domain name
            dns_valid: Whether DNS lookup succeeded
            mx_valid: Whether MX records exist
            ttl: Time to live in seconds (uses default if None)
        """
        with self.lock:
            self.cache[domain] = {
                'dns_valid': dns_valid,
                'mx_valid': mx_valid,
                'timestamp': time.time(),
                'ttl': ttl or self.default_ttl,
                'source': 'lookup'
            }
            logger.debug(f"DNS cache SET for {domain}: dns={dns_valid}, mx={mx_valid}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        with self.lock:
            total = self.stats['total_queries']
            hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
            
            return {
                'total_queries': total,
                'cache_hits': self.stats['hits'],
                'cache_misses': self.stats['misses'],
                'hit_rate_percent': round(hit_rate, 2),
                'cached_domains': len(self.cache),
                'cache_size_kb': len(str(self.cache)) / 1024
            }
    
    def clear_expired(self):
        """Remove expired entries from cache."""
        with self.lock:
            current_time = time.time()
            expired_domains = [
                domain for domain, entry in self.cache.items()
                if current_time - entry['timestamp'] > entry['ttl']
            ]
            
            for domain in expired_domains:
                del self.cache[domain]
            
            if expired_domains:
                logger.info(f"Cleared {len(expired_domains)} expired DNS cache entries")
    
    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.stats = {'hits': 0, 'misses': 0, 'total_queries': 0}
            logger.info("DNS cache cleared")


# Global DNS cache instance
_dns_cache = DNSCache()

def get_dns_cache() -> DNSCache:
    """Get the global DNS cache instance."""
    return _dns_cache

def check_dns_and_mx_cached(domain: str) -> Tuple[bool, bool]:
    """
    Check DNS and MX records with caching.
    
    Args:
        domain: Domain name to check
        
    Returns:
        Tuple of (dns_valid, mx_valid) as booleans
    """
    cache = get_dns_cache()
    
    # Try cache first
    cached_result = cache.get(domain)
    if cached_result is not None:
        return cached_result
    
    # Cache miss - perform actual lookup
    dns_valid = False
    mx_valid = False
    
    # Check DNS resolution
    try:
        socket.gethostbyname(domain)
        dns_valid = True
    except (socket.gaierror, socket.herror, socket.timeout, OSError):
        dns_valid = False
    except Exception:
        dns_valid = False
    
    # Check MX records (only if DNS library is available)
    if DNS_AVAILABLE and dns_valid:
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_valid = len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            mx_valid = False
        except dns.exception.Timeout:
            mx_valid = False
        except Exception:
            mx_valid = False
    
    # Cache the result
    cache.set(domain, dns_valid, mx_valid)
    
    return dns_valid, mx_valid

def get_cache_stats() -> Dict:
    """Get DNS cache statistics."""
    return get_dns_cache().get_stats()

def clear_dns_cache():
    """Clear the DNS cache."""
    get_dns_cache().clear()

def cleanup_expired_cache():
    """Remove expired entries from cache."""
    get_dns_cache().clear_expired()


# Example usage and testing
if __name__ == "__main__":
    # Test the DNS cache
    print("Testing DNS Cache System")
    print("=" * 40)
    
    test_domains = [
        'gmail.com',
        'yahoo.com', 
        'nonexistentdomain12345.com',
        'gmail.com',  # Should hit cache
        'outlook.com'
    ]
    
    for domain in test_domains:
        start_time = time.time()
        dns_valid, mx_valid = check_dns_and_mx_cached(domain)
        elapsed = time.time() - start_time
        
        print(f"{domain}: DNS={dns_valid}, MX={mx_valid} ({elapsed:.3f}s)")
    
    print("\nCache Statistics:")
    stats = get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")