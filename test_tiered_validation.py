#!/usr/bin/env python3
"""
Test script for tiered validation system.
Demonstrates how confidence scores determine which filters are applied.
"""

from emailvalidator_unified import validate_email_tiered

def test_tiered_validation():
    """Test the tiered validation system with different confidence levels."""
    
    print("=" * 70)
    print("TIERED VALIDATION SYSTEM TEST")
    print("=" * 70)
    print()
    
    # Test cases with different expected confidence levels
    test_cases = [
        # High confidence emails (should get full validation)
        ("user@gmail.com", "High confidence - common domain"),
        ("john.doe@outlook.com", "High confidence - valid format"),
        
        # Medium confidence emails
        ("test@example.com", "Medium confidence - generic domain"),
        ("admin@company.co", "Medium confidence - short TLD"),
        
        # Low confidence emails (syntax issues)
        ("invalid@", "Low confidence - incomplete"),
        ("no-at-sign.com", "Low confidence - missing @"),
        ("multiple@@at.com", "Low confidence - multiple @"),
    ]
    
    for email, description in test_cases:
        print(f"\nTesting: {email}")
        print(f"Description: {description}")
        print("-" * 70)
        
        result = validate_email_tiered(email)
        
        print(f"Valid: {result['valid']}")
        print(f"Confidence Score: {result['confidence_score']}%")
        print(f"Validation Tier: {result['tier'].upper()}")
        print(f"Filters Applied: {result['filters_applied']}")
        print(f"Checks Performed: {result['checks']}")
        if result.get('suggestion'):
            print(f"Suggestion: {result['suggestion']}")
        print(f"Reason: {result['reason']}")
        print()
    
    print("=" * 70)
    print("EXPLANATION OF TIERS:")
    print("=" * 70)
    print()
    print("HIGH TIER (90-100% confidence):")
    print("  → Applies ALL filters: DNS, MX, disposable, role-based, typo detection")
    print("  → Used when we're confident the email is valid")
    print("  → Ensures maximum accuracy before marking as 'verified'")
    print()
    print("MEDIUM TIER (60-89% confidence):")
    print("  → Applies moderate filters: DNS, MX, disposable checks")
    print("  → Skips expensive typo detection and role-based checks")
    print("  → Balances thoroughness with performance")
    print()
    print("LOW TIER (<60% confidence):")
    print("  → Applies minimal filters: syntax validation only")
    print("  → Doesn't waste resources on likely invalid emails")
    print("  → Fast rejection of obviously bad emails")
    print()


if __name__ == "__main__":
    test_tiered_validation()
