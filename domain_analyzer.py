#!/usr/bin/env python3
"""
Domain Analyzer for Bulk Email Validation
Pre-analyzes domains in email batches to optimize validation.
"""

from typing import List, Dict, Set, Tuple
from collections import Counter
import logging
from dns_cache import check_dns_and_mx_cached

logger = logging.getLogger(__name__)

class DomainAnalyzer:
    """
    Analyzes domains in email batches for optimization.
    Pre-checks unique domains to avoid redundant validation.
    """
    
    def __init__(self):
        self.domain_cache = {}
        self.stats = {
            'domains_analyzed': 0,
            'emails_processed': 0,
            'cache_hits': 0,
            'dns_queries_saved': 0
        }
    
    def extract_domains(self, emails: List[str]) -> Dict[str, List[str]]:
        """
        Extract unique domains and group emails by domain.
        
        Args:
            emails: List of email addresses
            
        Returns:
            Dictionary mapping domains to lists of emails
        """
        domain_groups = {}
        
        for email in emails:
            try:
                if '@' in email:
                    local, domain = email.split('@', 1)
                    domain = domain.lower().strip()
                    
                    if domain not in domain_groups:
                        domain_groups[domain] = []
                    domain_groups[domain].append(email)
                else:
                    # Invalid email format - group under special key
                    if '_invalid_format' not in domain_groups:
                        domain_groups['_invalid_format'] = []
                    domain_groups['_invalid_format'].append(email)
            except Exception:
                # Handle any parsing errors
                if '_parse_error' not in domain_groups:
                    domain_groups['_parse_error'] = []
                domain_groups['_parse_error'].append(email)
        
        return domain_groups
    
    def analyze_domains(self, domain_groups: Dict[str, List[str]]) -> Dict[str, Dict]:
        """
        Pre-analyze all unique domains in the batch.
        
        Args:
            domain_groups: Dictionary mapping domains to email lists
            
        Returns:
            Dictionary mapping domains to their validation results
        """
        domain_results = {}
        
        for domain, emails in domain_groups.items():
            # Skip special invalid format groups
            if domain.startswith('_'):
                domain_results[domain] = {
                    'dns_valid': False,
                    'mx_valid': False,
                    'email_count': len(emails),
                    'status': 'invalid_format'
                }
                continue
            
            # Check if we already analyzed this domain
            if domain in self.domain_cache:
                result = self.domain_cache[domain].copy()
                result['email_count'] = len(emails)
                result['status'] = 'cached'
                domain_results[domain] = result
                self.stats['cache_hits'] += 1
                self.stats['dns_queries_saved'] += 1
                continue
            
            # Perform DNS/MX check for new domain
            try:
                dns_valid, mx_valid = check_dns_and_mx_cached(domain)
                
                result = {
                    'dns_valid': dns_valid,
                    'mx_valid': mx_valid,
                    'email_count': len(emails),
                    'status': 'analyzed'
                }
                
                # Cache the result
                self.domain_cache[domain] = {
                    'dns_valid': dns_valid,
                    'mx_valid': mx_valid
                }
                
                domain_results[domain] = result
                self.stats['domains_analyzed'] += 1
                
            except Exception as e:
                logger.error(f"Error analyzing domain {domain}: {e}")
                domain_results[domain] = {
                    'dns_valid': False,
                    'mx_valid': False,
                    'email_count': len(emails),
                    'status': 'error',
                    'error': str(e)
                }
        
        return domain_results
    
    def get_domain_stats(self, domain_results: Dict[str, Dict]) -> Dict:
        """
        Generate statistics about domain analysis.
        
        Args:
            domain_results: Results from analyze_domains()
            
        Returns:
            Dictionary with domain statistics
        """
        total_domains = len(domain_results)
        valid_domains = sum(1 for r in domain_results.values() if r.get('dns_valid', False))
        mx_domains = sum(1 for r in domain_results.values() if r.get('mx_valid', False))
        total_emails = sum(r.get('email_count', 0) for r in domain_results.values())
        
        # Top domains by email count
        top_domains = sorted(
            [(domain, result['email_count']) for domain, result in domain_results.items() 
             if not domain.startswith('_')],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_domains': total_domains,
            'valid_domains': valid_domains,
            'mx_domains': mx_domains,
            'total_emails': total_emails,
            'domain_validity_rate': round(valid_domains / total_domains * 100, 2) if total_domains > 0 else 0,
            'mx_rate': round(mx_domains / total_domains * 100, 2) if total_domains > 0 else 0,
            'top_domains': top_domains,
            'analysis_stats': self.stats.copy()
        }
    
    def optimize_email_order(self, emails: List[str], domain_results: Dict[str, Dict]) -> List[str]:
        """
        Reorder emails for optimal processing based on domain analysis.
        Put emails from invalid domains first for faster rejection.
        
        Args:
            emails: Original email list
            domain_results: Results from domain analysis
            
        Returns:
            Reordered email list
        """
        def get_domain_priority(email: str) -> int:
            try:
                if '@' not in email:
                    return 0  # Invalid format - process first
                
                domain = email.split('@', 1)[1].lower().strip()
                result = domain_results.get(domain, {})
                
                # Priority order (lower number = process first):
                # 0: Invalid format
                # 1: Invalid DNS (fast rejection)
                # 2: Valid DNS but no MX
                # 3: Valid DNS and MX
                
                if not result.get('dns_valid', False):
                    return 1  # Invalid DNS - fast rejection
                elif not result.get('mx_valid', False):
                    return 2  # No MX records
                else:
                    return 3  # Valid domain - process last
                    
            except Exception:
                return 0  # Error parsing - process first
        
        # Sort emails by domain priority
        return sorted(emails, key=get_domain_priority)
    
    def clear_cache(self):
        """Clear the domain cache."""
        self.domain_cache.clear()
        self.stats = {
            'domains_analyzed': 0,
            'emails_processed': 0,
            'cache_hits': 0,
            'dns_queries_saved': 0
        }

def analyze_email_batch(emails: List[str]) -> Tuple[Dict[str, Dict], Dict]:
    """
    Convenience function to analyze a batch of emails.
    
    Args:
        emails: List of email addresses
        
    Returns:
        Tuple of (domain_results, statistics)
    """
    analyzer = DomainAnalyzer()
    
    # Extract domains
    domain_groups = analyzer.extract_domains(emails)
    
    # Analyze domains
    domain_results = analyzer.analyze_domains(domain_groups)
    
    # Generate statistics
    stats = analyzer.get_domain_stats(domain_results)
    
    return domain_results, stats

def optimize_batch_order(emails: List[str]) -> Tuple[List[str], Dict]:
    """
    Optimize email batch order for faster processing.
    
    Args:
        emails: Original email list
        
    Returns:
        Tuple of (optimized_emails, analysis_stats)
    """
    domain_results, stats = analyze_email_batch(emails)
    
    analyzer = DomainAnalyzer()
    optimized_emails = analyzer.optimize_email_order(emails, domain_results)
    
    return optimized_emails, stats


# Example usage and testing
if __name__ == "__main__":
    # Test domain analyzer
    print("Testing Domain Analyzer")
    print("=" * 40)
    
    test_emails = [
        'user1@gmail.com',
        'user2@gmail.com',
        'user3@gmail.com',
        'test@yahoo.com',
        'invalid@nonexistent12345.com',
        'another@nonexistent12345.com',
        'info@outlook.com',
        'invalid@@@',
        'no-at-sign.com',
        'admin@tempmail.com'
    ]
    
    print(f"Analyzing {len(test_emails)} emails...")
    
    domain_results, stats = analyze_email_batch(test_emails)
    
    print("\nDomain Analysis Results:")
    for domain, result in domain_results.items():
        print(f"  {domain}: DNS={result.get('dns_valid')}, MX={result.get('mx_valid')}, "
              f"Emails={result.get('email_count')}, Status={result.get('status')}")
    
    print("\nStatistics:")
    for key, value in stats.items():
        if key != 'top_domains':
            print(f"  {key}: {value}")
    
    print("\nTop Domains:")
    for domain, count in stats['top_domains']:
        print(f"  {domain}: {count} emails")
    
    # Test optimization
    print("\nOptimizing batch order...")
    optimized_emails, opt_stats = optimize_batch_order(test_emails)
    
    print("Original order:")
    for i, email in enumerate(test_emails[:5]):
        print(f"  {i+1}. {email}")
    
    print("Optimized order:")
    for i, email in enumerate(optimized_emails[:5]):
        print(f"  {i+1}. {email}")