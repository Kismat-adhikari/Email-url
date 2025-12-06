#!/usr/bin/env python3
"""
Unit Tests for Email Enrichment
Tests domain type detection, geolocation inference, and engagement scoring
"""

import unittest
from email_enrichment import EmailEnrichment, enrich_email


class TestDomainTypeDetection(unittest.TestCase):
    """Test domain type classification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.enricher = EmailEnrichment()
    
    def test_free_provider_detection(self):
        """Test detection of free email providers."""
        free_emails = [
            'user@gmail.com',
            'test@yahoo.com',
            'john@hotmail.com',
            'jane@outlook.com',
            'bob@icloud.com'
        ]
        
        for email in free_emails:
            with self.subTest(email=email):
                result = self.enricher.enrich_email(email)
                self.assertEqual(result['domain_type'], 'free')
                self.assertEqual(result['provider_type'], 'consumer')
                self.assertTrue(result['is_free_provider'])
                self.assertFalse(result['is_corporate'])
    
    def test_corporate_domain_detection(self):
        """Test detection of corporate domains."""
        corporate_emails = [
            'john@acme-corp.com',
            'jane@techsolutions.io',
            'bob@consulting-group.com',
            'alice@enterprise-inc.com'
        ]
        
        for email in corporate_emails:
            with self.subTest(email=email):
                result = self.enricher.enrich_email(email)
                self.assertEqual(result['domain_type'], 'corporate')
                self.assertEqual(result['provider_type'], 'business')
                self.assertTrue(result['is_corporate'])
                self.assertFalse(result['is_free_provider'])
    
    def test_educational_domain_detection(self):
        """Test detection of educational domains."""
        edu_emails = [
            'student@university.edu',
            'prof@college.edu',
            'admin@mit.edu'
        ]
        
        for email in edu_emails:
            with self.subTest(email=email):
                result = self.enricher.enrich_email(email)
                self.assertEqual(result['domain_type'], 'educational')
                self.assertEqual(result['provider_type'], 'education')
                self.assertTrue(result['is_educational'])
    
    def test_government_domain_detection(self):
        """Test detection of government domains."""
        gov_emails = [
            'official@agency.gov',
            'admin@government.gov'
        ]
        
        for email in gov_emails:
            with self.subTest(email=email):
                result = self.enricher.enrich_email(email)
                self.assertEqual(result['domain_type'], 'government')
                self.assertEqual(result['provider_type'], 'government')
                self.assertTrue(result['is_government'])
    
    def test_domain_metadata(self):
        """Test domain metadata extraction."""
        domain = 'acme-corp.com'
        metadata = self.enricher.get_domain_metadata(domain)
        
        self.assertIn('type', metadata)
        self.assertIn('provider_type', metadata)
        self.assertIn('is_free', metadata)
        self.assertIn('is_corporate', metadata)
        self.assertIn('is_educational', metadata)
        self.assertIn('is_government', metadata)


class TestGeolocationInference(unittest.TestCase):
    """Test geolocation inference from domains."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.enricher = EmailEnrichment()
    
    def test_uk_domain_geolocation(self):
        """Test UK domain geolocation."""
        result = self.enricher.infer_geolocation('example.co.uk')
        
        self.assertEqual(result['country'], 'United Kingdom')
        self.assertEqual(result['country_code'], 'UK')
        self.assertEqual(result['region'], 'Europe')
        self.assertEqual(result['confidence'], 'high')
    
    def test_us_domain_geolocation(self):
        """Test US domain geolocation."""
        result = self.enricher.infer_geolocation('example.us')
        
        self.assertEqual(result['country'], 'United States')
        self.assertEqual(result['country_code'], 'US')
        self.assertEqual(result['region'], 'Americas')
        self.assertEqual(result['confidence'], 'high')
    
    def test_german_domain_geolocation(self):
        """Test German domain geolocation."""
        result = self.enricher.infer_geolocation('example.de')
        
        self.assertEqual(result['country'], 'Germany')
        self.assertEqual(result['country_code'], 'DE')
        self.assertEqual(result['region'], 'Europe')
        self.assertEqual(result['confidence'], 'high')
    
    def test_japanese_domain_geolocation(self):
        """Test Japanese domain geolocation."""
        result = self.enricher.infer_geolocation('example.jp')
        
        self.assertEqual(result['country'], 'Japan')
        self.assertEqual(result['country_code'], 'JP')
        self.assertEqual(result['region'], 'Asia')
        self.assertEqual(result['confidence'], 'high')
    
    def test_generic_com_domain(self):
        """Test generic .com domain."""
        result = self.enricher.infer_geolocation('example.com')
        
        self.assertIsNone(result['country'])
        self.assertIsNone(result['country_code'])
        self.assertEqual(result['region'], 'Global/United States')
        self.assertEqual(result['confidence'], 'low')
    
    def test_edu_domain_geolocation(self):
        """Test .edu domain geolocation."""
        result = self.enricher.infer_geolocation('university.edu')
        
        self.assertIsNone(result['country'])
        self.assertEqual(result['region'], 'United States (Education)')
        self.assertEqual(result['confidence'], 'low')
    
    def test_multiple_country_domains(self):
        """Test multiple country domains."""
        test_cases = [
            ('example.fr', 'France', 'FR', 'Europe'),
            ('example.au', 'Australia', 'AU', 'Oceania'),
            ('example.br', 'Brazil', 'BR', 'Americas'),
            ('example.in', 'India', 'IN', 'Asia'),
            ('example.za', 'South Africa', 'ZA', 'Africa')
        ]
        
        for domain, country, code, region in test_cases:
            with self.subTest(domain=domain):
                result = self.enricher.infer_geolocation(domain)
                self.assertEqual(result['country'], country)
                self.assertEqual(result['country_code'], code)
                self.assertEqual(result['region'], region)
    
    def test_unknown_tld(self):
        """Test unknown TLD."""
        result = self.enricher.infer_geolocation('example.xyz')
        
        self.assertIsNone(result['country'])
        self.assertIsNone(result['country_code'])
        self.assertEqual(result['confidence'], 'none')


class TestEngagementScoring(unittest.TestCase):
    """Test engagement score calculation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.enricher = EmailEnrichment()
    
    def test_perfect_engagement_score(self):
        """Test perfect engagement score."""
        domain_metadata = {
            'is_corporate': True,
            'is_free': False
        }
        
        validation_data = {
            'valid': True,
            'confidence_score': 100,
            'bounce_count': 0,
            'is_disposable': False,
            'is_role_based': False
        }
        
        score = self.enricher.calculate_engagement_score(
            'john@company.com',
            domain_metadata,
            validation_data
        )
        
        self.assertEqual(score, 100)
    
    def test_low_engagement_score(self):
        """Test low engagement score."""
        domain_metadata = {
            'is_corporate': False,
            'is_free': True
        }
        
        validation_data = {
            'valid': False,
            'confidence_score': 20,
            'bounce_count': 5,
            'is_disposable': True,
            'is_role_based': True
        }
        
        score = self.enricher.calculate_engagement_score(
            'test@tempmail.com',
            domain_metadata,
            validation_data
        )
        
        self.assertLess(score, 50)
    
    def test_corporate_vs_free_scoring(self):
        """Test corporate domains score higher than free."""
        validation_data = {
            'valid': True,
            'confidence_score': 80,
            'bounce_count': 0,
            'is_disposable': False,
            'is_role_based': False
        }
        
        corporate_score = self.enricher.calculate_engagement_score(
            'john@company.com',
            {'is_corporate': True, 'is_free': False},
            validation_data
        )
        
        free_score = self.enricher.calculate_engagement_score(
            'john@gmail.com',
            {'is_corporate': False, 'is_free': True},
            validation_data
        )
        
        self.assertGreater(corporate_score, free_score)
    
    def test_bounce_penalty(self):
        """Test bounce count reduces score."""
        domain_metadata = {'is_corporate': True}
        
        no_bounce = self.enricher.calculate_engagement_score(
            'john@company.com',
            domain_metadata,
            {'valid': True, 'bounce_count': 0, 'confidence_score': 90}
        )
        
        with_bounce = self.enricher.calculate_engagement_score(
            'john@company.com',
            domain_metadata,
            {'valid': True, 'bounce_count': 3, 'confidence_score': 90}
        )
        
        self.assertGreater(no_bounce, with_bounce)
    
    def test_score_without_validation_data(self):
        """Test scoring without validation data."""
        domain_metadata = {'is_corporate': True}
        
        score = self.enricher.calculate_engagement_score(
            'john@company.com',
            domain_metadata,
            None
        )
        
        # Should still get points for domain type
        self.assertGreater(score, 0)
        self.assertLess(score, 50)


class TestIndustryDetection(unittest.TestCase):
    """Test industry detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.enricher = EmailEnrichment()
    
    def test_technology_industry(self):
        """Test technology industry detection."""
        tech_domains = [
            'techcorp.com',
            'software-solutions.io',
            'cloudservices.com',
            'dataanalytics.com'
        ]
        
        for domain in tech_domains:
            with self.subTest(domain=domain):
                industry = self.enricher.detect_industry(domain)
                self.assertEqual(industry, 'Technology')
    
    def test_finance_industry(self):
        """Test finance industry detection."""
        finance_domains = [
            'bankofamerica.com',
            'capitalinvest.com',
            'insurance-group.com'
        ]
        
        for domain in finance_domains:
            with self.subTest(domain=domain):
                industry = self.enricher.detect_industry(domain)
                self.assertEqual(industry, 'Finance')
    
    def test_healthcare_industry(self):
        """Test healthcare industry detection."""
        healthcare_domains = [
            'healthclinic.com',
            'medical-center.org',
            'pharma-corp.com'
        ]
        
        for domain in healthcare_domains:
            with self.subTest(domain=domain):
                industry = self.enricher.detect_industry(domain)
                self.assertEqual(industry, 'Healthcare')
    
    def test_education_industry(self):
        """Test education industry detection."""
        edu_domains = [
            'university.edu',
            'college-academy.org',
            'learning-center.com'
        ]
        
        for domain in edu_domains:
            with self.subTest(domain=domain):
                industry = self.enricher.detect_industry(domain)
                self.assertEqual(industry, 'Education')
    
    def test_unknown_industry(self):
        """Test unknown industry."""
        industry = self.enricher.detect_industry('randomcompany.com')
        self.assertIsNone(industry)


class TestCompanySizeEstimation(unittest.TestCase):
    """Test company size estimation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.enricher = EmailEnrichment()
    
    def test_individual_size(self):
        """Test individual (free provider) size."""
        metadata = {'is_free': True, 'is_corporate': False}
        size = self.enricher.estimate_company_size('gmail.com', metadata)
        self.assertEqual(size, 'individual')
    
    def test_enterprise_size(self):
        """Test enterprise size detection."""
        metadata = {'is_free': False, 'is_corporate': True}
        
        enterprise_domains = [
            'global-corp.com',
            'international-group.com',
            'worldwide-holdings.com'
        ]
        
        for domain in enterprise_domains:
            with self.subTest(domain=domain):
                size = self.enricher.estimate_company_size(domain, metadata)
                self.assertEqual(size, 'enterprise')
    
    def test_midmarket_size(self):
        """Test mid-market size detection."""
        metadata = {'is_free': False, 'is_corporate': True}
        
        midmarket_domains = [
            'consulting-solutions.com',
            'business-services.com',
            'tech-partners.io'
        ]
        
        for domain in midmarket_domains:
            with self.subTest(domain=domain):
                size = self.enricher.estimate_company_size(domain, metadata)
                self.assertEqual(size, 'mid-market')
    
    def test_small_business_size(self):
        """Test small business size detection."""
        metadata = {'is_free': False, 'is_corporate': True}
        size = self.enricher.estimate_company_size('local-shop.com', metadata)
        self.assertEqual(size, 'small')


class TestFullEnrichment(unittest.TestCase):
    """Test complete enrichment flow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.enricher = EmailEnrichment()
    
    def test_complete_enrichment(self):
        """Test complete email enrichment."""
        result = self.enricher.enrich_email('john@acme-corp.co.uk')
        
        # Check all fields present
        self.assertIn('email', result)
        self.assertIn('domain', result)
        self.assertIn('domain_type', result)
        self.assertIn('provider_type', result)
        self.assertIn('geolocation', result)
        self.assertIn('engagement_score', result)
        self.assertIn('industry', result)
        self.assertIn('company_size', result)
        self.assertIn('enriched_at', result)
        
        # Check geolocation
        self.assertEqual(result['geolocation']['country'], 'United Kingdom')
        
        # Check domain type
        self.assertEqual(result['domain_type'], 'corporate')
    
    def test_enrichment_with_validation_data(self):
        """Test enrichment with validation data."""
        validation_data = {
            'valid': True,
            'confidence_score': 95,
            'bounce_count': 0,
            'is_disposable': False,
            'is_role_based': False
        }
        
        result = self.enricher.enrich_email(
            'john@techcorp.com',
            validation_data
        )
        
        # Should have high engagement score
        self.assertGreater(result['engagement_score'], 80)
    
    def test_batch_enrichment(self):
        """Test batch enrichment."""
        emails = [
            'john@company.com',
            'jane@gmail.com',
            'bob@university.edu'
        ]
        
        results = self.enricher.batch_enrich(emails)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['domain_type'], 'corporate')
        self.assertEqual(results[1]['domain_type'], 'free')
        self.assertEqual(results[2]['domain_type'], 'educational')
    
    def test_invalid_email_format(self):
        """Test enrichment with invalid email."""
        result = self.enricher.enrich_email('invalid-email')
        
        self.assertIn('error', result)
    
    def test_convenience_function(self):
        """Test convenience function."""
        result = enrich_email('user@example.com')
        
        self.assertIn('email', result)
        self.assertIn('domain_type', result)


def run_tests():
    """Run all tests with detailed output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDomainTypeDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestGeolocationInference))
    suite.addTests(loader.loadTestsFromTestCase(TestEngagementScoring))
    suite.addTests(loader.loadTestsFromTestCase(TestIndustryDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestCompanySizeEstimation))
    suite.addTests(loader.loadTestsFromTestCase(TestFullEnrichment))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
