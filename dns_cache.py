#!/usr/bin/env python3
"""
DNS Cache Module for Email Validation Performance Optimization

This module provides DNS and MX record caching to dramatically improve
email validation performance for large batches with duplicate domains.

Performance Impact:
- Without cache: 1000 gmail emails = 1000 DNS lookups
- With cache: 1000 gmail emails = 1 DNS lookup + 999 cache hits
- Speed improvement: 10-100x faster for duplicate domains
"""

import socket
import time
from typing import Tuple, Dict, Any
from threading import Lock

# Try to import DNS library
try:
    import dns.resolver
    import dns.exception
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

# Global cache and statistics
_dns_cache: Dict[str, Tuple[bool, bool, float]] = {}
_cache_lock = Lock()
_cache_stats = {
    'hits': 0,
    'misses': 0,
    'total_lookups': 0,
    'cache_size': 0,
    'time_saved': 0.0
}

# Cache configuration
CACHE_TTL = 300  # 5 minutes TTL
MAX_CACHE_SIZE = 10000  # Maximum domains to cache


def check_dns_and_mx_cached(domain: str) -> Tuple[bool, bool]:
    """
    Check DNS and MX records with caching for performance.
    
    Args:
        domain: Domain name to check
        
    Returns:
        Tuple of (dns_valid, mx_valid) as booleans
        
    Performance:
        - First lookup: ~0.1-0.2 seconds (network call)
        - Cached lookup: ~0.001 seconds (memory access)
        - 100-200x faster for cached domains!
    """
    global _dns_cache, _cache_stats
    
    domain = domain.lower().strip()
    current_time = time.time()
    
    with _cache_lock:
        # Check if domain is in cache and not expired
        if domain in _dns_cache:
            dns_valid, mx_valid, cached_time = _dns_cache[domain]
            
            # Check if cache entry is still valid (not expired)
            if current_time - cached_time < CACHE_TTL:
                _cache_stats['hits'] += 1
                _cache_stats['total_lookups'] += 1
                _cache_stats['time_saved'] += 0.15  # Estimated time saved per cache hit
                return dns_valid, mx_valid
            else:
                # Cache expired, remove entry
                del _dns_cache[domain]
        
        # Cache miss - perform actual DNS lookup
        _cache_stats['misses'] += 1
        _cache_stats['total_lookups'] += 1
    
    # Perform actual DNS and MX lookup
    start_time = time.time()
    dns_valid, mx_valid = _perform_dns_lookup(domain)
    lookup_time = time.time() - start_time
    
    with _cache_lock:
        # Clean cache if it's getting too large
        if len(_dns_cache) >= MAX_CACHE_SIZE:
            _cleanup_cache()
        
        # Store result in cache
        _dns_cache[domain] = (dns_valid, mx_valid, current_time)
        _cache_stats['cache_size'] = len(_dns_cache)
    
    return dns_valid, mx_valid


def _perform_dns_lookup(domain: str) -> Tuple[bool, bool]:
    """
    Perform actual DNS and MX record lookup (no caching).
    
    Args:
        domain: Domain name to check
        
    Returns:
        Tuple of (dns_valid, mx_valid) as booleans
    """
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
    if DNS_AVAILABLE and dns_valid:  # Only check MX if DNS is valid
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_valid = len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            mx_valid = False
        except dns.exception.Timeout:
            mx_valid = False
        except Exception:
            mx_valid = False
    
    return dns_valid, mx_valid


def _cleanup_cache():
    """
    Clean up old cache entries when cache gets too large.
    Removes oldest 25% of entries.
    """
    global _dns_cache
    
    if len(_dns_cache) < MAX_CACHE_SIZE:
        return
    
    # Sort by timestamp (oldest first)
    sorted_items = sorted(_dns_cache.items(), key=lambda x: x[1][2])
    
    # Remove oldest 25%
    remove_count = len(sorted_items) // 4
    for domain, _ in sorted_items[:remove_count]:
        del _dns_cache[domain]
    
    print(f"DNS Cache: Cleaned up {remove_count} old entries")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get DNS cache performance statistics.
    
    Returns:
        Dictionary with cache performance metrics
    """
    global _cache_stats
    
    with _cache_lock:
        stats = _cache_stats.copy()
        stats['cache_size'] = len(_dns_cache)
        
        # Calculate hit rate
        if stats['total_lookups'] > 0:
            stats['hit_rate'] = (stats['hits'] / stats['total_lookups']) * 100
        else:
            stats['hit_rate'] = 0.0
        
        # Calculate estimated time saved
        stats['estimated_time_saved_minutes'] = stats['time_saved'] / 60
        
        return stats


def clear_cache():
    """
    Clear all cached DNS results.
    Useful for testing or when you want fresh lookups.
    """
    global _dns_cache, _cache_stats
    
    with _cache_lock:
        _dns_cache.clear()
        _cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_lookups': 0,
            'cache_size': 0,
            'time_saved': 0.0
        }
    
    print("DNS Cache: All entries cleared")


def warm_cache(domains: list):
    """
    Pre-populate cache with common domains for better performance.
    
    Args:
        domains: List of domain names to pre-cache
    """
    print(f"DNS Cache: Warming cache with {len(domains)} domains...")
    
    for domain in domains:
        check_dns_and_mx_cached(domain)
    
    stats = get_cache_stats()
    print(f"DNS Cache: Warmed with {stats['cache_size']} domains")


# Pre-populate cache with common email domains for better performance
COMMON_DOMAINS = [
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com',
    'icloud.com', 'protonmail.com', 'zoho.com', 'yandex.com', 'gmx.com',
    'mail.com', 'live.com', 'msn.com', 'comcast.net', 'verizon.net'
]

# Warm cache on module import (optional)
# warm_cache(COMMON_DOMAINS)