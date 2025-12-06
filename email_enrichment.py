#!/usr/bin/env python3
"""
Email Enrichment Module
Add domain metadata, geolocation, and engagement scoring to email validation
"""

import re
import socket
from typing import Dict, Any, Optional, List
from datetime import datetime

# Domain provider classifications
FREE_EMAIL_PROVIDERS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com',
    'icloud.com', 'mail.com', 'protonmail.com', 'zoho.com', 'gmx.com',
    'yandex.com', 'live.com', 'msn.com', 'me.com', 'mac.com',
    'yahoo.co.uk', 'googlemail.com', 'hotmail.co.uk', 'outlook.co.uk',
    'inbox.com', 'fastmail.com', 'tutanota.com', 'mailfence.com'
}

CORPORATE_INDICATORS = {
    'company', 'corp', 'inc', 'ltd', 'llc', 'group', 'enterprise',
    'solutions', 'tech', 'consulting', 'services', 'industries'
}

# Country TLD mapping (top-level domains)
COUNTRY_TLD_MAP = {
    'uk': 'United Kingdom',
    'us': 'United States',
    'ca': 'Canada',
    'au': 'Australia',
    'de': 'Germany',
    'fr': 'France',
    'it': 'Italy',
    'es': 'Spain',
    'nl': 'Netherlands',
    'be': 'Belgium',
    'ch': 'Switzerland',
    'at': 'Austria',
    'se': 'Sweden',
    'no': 'Norway',
    'dk': 'Denmark',
    'fi': 'Finland',
    'pl': 'Poland',
    'cz': 'Czech Republic',
    'ie': 'Ireland',
    'pt': 'Portugal',
    'gr': 'Greece',
    'ru': 'Russia',
    'jp': 'Japan',
    'cn': 'China',
    'in': 'India',
    'br': 'Brazil',
    'mx': 'Mexico',
    'ar': 'Argentina',
    'cl': 'Chile',
    'co': 'Colombia',
    'za': 'South Africa',
    'nz': 'New Zealand',
    'sg': 'Singapore',
    'hk': 'Hong Kong',
    'kr': 'South Korea',
    'tw': 'Taiwan',
    'th': 'Thailand',
    'my': 'Malaysia',
    'id': 'Indonesia',
    'ph': 'Philippines',
    'vn': 'Vietnam',
    'ae': 'United Arab Emirates',
    'sa': 'Saudi Arabia',
    'il': 'Israel',
    'tr': 'Turkey',
    'eg': 'Egypt'
}

# Generic TLD to region mapping
GENERIC_TLD_REGIONS = {
    'com': 'Global/United States',
    'net': 'Global',
    'org': 'Global',
    'edu': 'United States (Education)',
    'gov': 'United States (Government)',
    'mil': 'United States (Military)',
    'int': 'International'
}


class EmailEnrichment:
    """
    Email enrichment engine.
    
    Provides:
    - Domain type classification (corporate/free/educational/government)
    - Geolocation inference from domain
    - Engagement/segmentation scoring
    - Industry detection
    - Company size estimation
    """
    
    def __init__(self):
        """Initialize enrichment engine."""
        pass
    
    def enrich_email(self, email: str, validation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enrich email with metadata and scoring.
        
        Args:
            email: Email address
            validation_data: Optional validation results
        
        Returns:
            Dictionary with enrichment data:
                - email: Email address
                - domain: Domain name
                - domain_type: Type classification
                - provider_type: Provider category
                - geolocation: Location data
                - engagement_score: Score 0-100
                - industry: Detected industry
                - company_size: Estimated size
                - enriched_at: Timestamp
        
        Example:
            >>> enricher = EmailEnrichment()
            >>> result = enricher.enrich_email('john@acme-corp.com')
            >>> print(result['domain_type'])
            'corporate'
            >>> print(result['engagement_score'])
            85
        """
        if '@' not in email:
            return {
                'error': 'Invalid email format',
                'email': email
            }
        
        local_part, domain = email.split('@', 1)
        domain = domain.lower()
        
        # Get domain metadata
        domain_metadata = self.get_domain_metadata(domain)
        
        # Get geolocation
        geolocation = self.infer_geolocation(domain)
        
        # Calculate engagement score
        engagement_score = self.calculate_engagement_score(
            email,
            domain_metadata,
            validation_data
        )
        
        # Detect industry
        industry = self.detect_industry(domain)
        
        # Estimate company size
        company_size = self.estimate_company_size(domain, domain_metadata)
        
        return {
            'email': email,
            'domain': domain,
            'local_part': local_part,
            'domain_type': domain_metadata['type'],
            'provider_type': domain_metadata['provider_type'],
            'is_free_provider': domain_metadata['is_free'],
            'is_corporate': domain_metadata['is_corporate'],
            'is_educational': domain_metadata['is_educational'],
            'is_government': domain_metadata['is_government'],
            'geolocation': geolocation,
            'engagement_score': engagement_score,
            'industry': industry,
            'company_size': company_size,
            'enriched_at': datetime.utcnow().isoformat()
        }
    
    def get_domain_metadata(self, domain: str) -> Dict[str, Any]:
        """
        Get domain type and provider classification.
        
        Args:
            domain: Domain name
        
        Returns:
            Dictionary with domain metadata
        """
        domain_lower = domain.lower()
        
        # Check if free provider
        is_free = domain_lower in FREE_EMAIL_PROVIDERS
        
        # Check if educational
        is_educational = domain_lower.endswith('.edu') or 'university' in domain_lower or 'college' in domain_lower
        
        # Check if government
        is_government = domain_lower.endswith('.gov') or 'government' in domain_lower
        
        # Check if corporate
        is_corporate = not is_free and not is_educational and not is_government
        
        # Check for corporate indicators
        has_corporate_indicator = any(indicator in domain_lower for indicator in CORPORATE_INDICATORS)
        
        # Determine primary type
        if is_free:
            domain_type = 'free'
            provider_type = 'consumer'
        elif is_educational:
            domain_type = 'educational'
            provider_type = 'education'
        elif is_government:
            domain_type = 'government'
            provider_type = 'government'
        elif is_corporate or has_corporate_indicator:
            domain_type = 'corporate'
            provider_type = 'business'
        else:
            domain_type = 'unknown'
            provider_type = 'unknown'
        
        return {
            'type': domain_type,
            'provider_type': provider_type,
            'is_free': is_free,
            'is_corporate': is_corporate,
            'is_educational': is_educational,
            'is_government': is_government,
            'has_corporate_indicator': has_corporate_indicator
        }
    
    def infer_geolocation(self, domain: str) -> Dict[str, Any]:
        """
        Infer geolocation from domain TLD and other indicators.
        
        Args:
            domain: Domain name
        
        Returns:
            Dictionary with geolocation data:
                - country: Country name
                - country_code: ISO country code
                - region: Geographic region
                - confidence: Confidence level (low/medium/high)
        
        Example:
            >>> enricher = EmailEnrichment()
            >>> geo = enricher.infer_geolocation('example.co.uk')
            >>> print(geo['country'])
            'United Kingdom'
        """
        parts = domain.split('.')
        
        if len(parts) < 2:
            return {
                'country': None,
                'country_code': None,
                'region': None,
                'confidence': 'none'
            }
        
        tld = parts[-1].lower()
        
        # Check for country-specific TLD
        if tld in COUNTRY_TLD_MAP:
            return {
                'country': COUNTRY_TLD_MAP[tld],
                'country_code': tld.upper(),
                'region': self._get_region_from_country(tld),
                'confidence': 'high'
            }
        
        # Check for second-level country domains (e.g., .co.uk)
        if len(parts) >= 3:
            second_level = parts[-2].lower()
            if second_level == 'co' and tld in COUNTRY_TLD_MAP:
                return {
                    'country': COUNTRY_TLD_MAP[tld],
                    'country_code': tld.upper(),
                    'region': self._get_region_from_country(tld),
                    'confidence': 'high'
                }
        
        # Check generic TLDs
        if tld in GENERIC_TLD_REGIONS:
            return {
                'country': None,
                'country_code': None,
                'region': GENERIC_TLD_REGIONS[tld],
                'confidence': 'low'
            }
        
        # Unknown TLD
        return {
            'country': None,
            'country_code': None,
            'region': 'Unknown',
            'confidence': 'none'
        }
    
    def _get_region_from_country(self, country_code: str) -> str:
        """Get geographic region from country code."""
        europe = ['uk', 'de', 'fr', 'it', 'es', 'nl', 'be', 'ch', 'at', 'se', 'no', 'dk', 'fi', 'pl', 'cz', 'ie', 'pt', 'gr']
        asia = ['jp', 'cn', 'in', 'kr', 'tw', 'th', 'my', 'id', 'ph', 'vn', 'sg', 'hk']
        americas = ['us', 'ca', 'br', 'mx', 'ar', 'cl', 'co']
        oceania = ['au', 'nz']
        middle_east = ['ae', 'sa', 'il', 'tr']
        africa = ['za', 'eg']
        
        if country_code in europe:
            return 'Europe'
        elif country_code in asia:
            return 'Asia'
        elif country_code in americas:
            return 'Americas'
        elif country_code in oceania:
            return 'Oceania'
        elif country_code in middle_east:
            return 'Middle East'
        elif country_code in africa:
            return 'Africa'
        else:
            return 'Unknown'
    
    def calculate_engagement_score(
        self,
        email: str,
        domain_metadata: Dict[str, Any],
        validation_data: Dict[str, Any] = None
    ) -> int:
        """
        Calculate engagement/segmentation score (0-100).
        
        Scoring factors:
        - Email validity: 30 points
        - Domain type: 20 points (corporate > free)
        - Confidence score: 20 points
        - No bounces: 15 points
        - Not disposable: 10 points
        - Not role-based: 5 points
        
        Args:
            email: Email address
            domain_metadata: Domain metadata
            validation_data: Validation results
        
        Returns:
            Engagement score 0-100
        
        Example:
            >>> enricher = EmailEnrichment()
            >>> score = enricher.calculate_engagement_score(
            ...     'john@company.com',
            ...     {'is_corporate': True},
            ...     {'valid': True, 'confidence_score': 95}
            ... )
            >>> print(score)
            95
        """
        score = 0
        
        # Factor 1: Email validity (30 points)
        if validation_data and validation_data.get('valid'):
            score += 30
        
        # Factor 2: Domain type (20 points)
        if domain_metadata.get('is_corporate'):
            score += 20
        elif domain_metadata.get('is_educational'):
            score += 15
        elif domain_metadata.get('is_free'):
            score += 10
        
        # Factor 3: Validation confidence (20 points)
        if validation_data:
            confidence = validation_data.get('confidence_score', 0)
            score += int(confidence * 0.2)  # Scale to 20 points
        
        # Factor 4: No bounces (15 points)
        if validation_data:
            bounce_count = validation_data.get('bounce_count', 0)
            if bounce_count == 0:
                score += 15
            elif bounce_count == 1:
                score += 10
            elif bounce_count == 2:
                score += 5
        
        # Factor 5: Not disposable (10 points)
        if validation_data and not validation_data.get('is_disposable', False):
            score += 10
        
        # Factor 6: Not role-based (5 points)
        if validation_data and not validation_data.get('is_role_based', False):
            score += 5
        
        return min(score, 100)
    
    def detect_industry(self, domain: str) -> Optional[str]:
        """
        Detect industry from domain name.
        
        Args:
            domain: Domain name
        
        Returns:
            Industry name or None
        """
        domain_lower = domain.lower()
        
        # Industry keywords (order matters - check specific before generic)
        industries = [
            ('Education', ['university', 'college', 'school', 'academy', 'learning', '.edu']),
            ('Finance', ['bank', 'finance', 'capital', 'invest', 'insurance', 'credit']),
            ('Healthcare', ['health', 'medical', 'pharma', 'clinic', 'hospital', 'care']),
            ('Government', ['.gov', 'government', 'public']),
            ('Legal', ['law', 'legal', 'attorney', 'lawyer']),
            ('Real Estate', ['realty', 'property', 'real-estate', 'homes']),
            ('Manufacturing', ['manufacturing', 'industrial', 'factory', 'production']),
            ('Retail', ['shop', 'store', 'retail', 'market', 'ecommerce']),
            ('Marketing', ['marketing', 'advertising', 'media', 'creative']),
            ('Non-Profit', ['.org', 'foundation', 'charity', 'nonprofit']),
            ('Consulting', ['consulting', 'advisory']),
            ('Technology', ['tech', 'software', 'digital', 'cloud', 'data', 'ai', 'cyber', 'it', 'solutions', 'services'])
        ]
        
        for industry, keywords in industries:
            if any(keyword in domain_lower for keyword in keywords):
                return industry
        
        return None
    
    def estimate_company_size(
        self,
        domain: str,
        domain_metadata: Dict[str, Any]
    ) -> str:
        """
        Estimate company size from domain characteristics.
        
        Args:
            domain: Domain name
            domain_metadata: Domain metadata
        
        Returns:
            Size category: 'enterprise', 'mid-market', 'small', 'individual', 'unknown'
        """
        domain_lower = domain.lower()
        
        # Free providers = individual
        if domain_metadata.get('is_free'):
            return 'individual'
        
        # Educational/Government = varies
        if domain_metadata.get('is_educational') or domain_metadata.get('is_government'):
            return 'large-organization'
        
        # Enterprise indicators
        enterprise_indicators = ['global', 'international', 'worldwide', 'group', 'holdings', 'corporation']
        if any(indicator in domain_lower for indicator in enterprise_indicators):
            return 'enterprise'
        
        # Mid-market indicators
        midmarket_indicators = ['solutions', 'services', 'consulting', 'partners']
        if any(indicator in domain_lower for indicator in midmarket_indicators):
            return 'mid-market'
        
        # Small business indicators
        small_indicators = ['local', 'shop', 'studio']
        if any(indicator in domain_lower for indicator in small_indicators):
            return 'small'
        
        # Default for corporate
        if domain_metadata.get('is_corporate'):
            return 'small-to-mid'
        
        return 'unknown'
    
    def batch_enrich(
        self,
        emails: List[str],
        validation_results: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Enrich multiple emails.
        
        Args:
            emails: List of email addresses
            validation_results: Optional list of validation results
        
        Returns:
            List of enrichment results
        """
        results = []
        
        for i, email in enumerate(emails):
            validation_data = None
            if validation_results and i < len(validation_results):
                validation_data = validation_results[i]
            
            enrichment = self.enrich_email(email, validation_data)
            results.append(enrichment)
        
        return results


# Convenience function
def enrich_email(email: str, validation_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Quick email enrichment.
    
    Args:
        email: Email address
        validation_data: Optional validation results
    
    Returns:
        Enrichment data
    """
    enricher = EmailEnrichment()
    return enricher.enrich_email(email, validation_data)
