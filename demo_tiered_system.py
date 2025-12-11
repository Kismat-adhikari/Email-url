#!/usr/bin/env python3
"""
Demo: Tiered Validation System
Shows how confidence scores determine filter application
"""

from emailvalidator_unified import validate_email_tiered

def demo():
    print("=" * 80)
    print("TIERED VALIDATION SYSTEM - CONFIDENCE-BASED FILTERING")
    print("=" * 80)
    print()
    print("CONCEPT: Higher confidence = MORE filters to ensure accuracy")
    print()
    
    # Test different scenarios
    scenarios = [
        {
            'title': 'HIGH CONFIDENCE SCENARIO (90-100%)',
            'description': 'Valid syntax + not disposable + not role-based = 100% confidence',
            'email': 'john.smith@gmail.com',
            'expected_tier': 'high'
        },
        {
            'title': 'MEDIUM CONFIDENCE SCENARIO (60-89%)',
            'description': 'Valid syntax + role-based email = 90% confidence',
            'email': 'info@company.com',
            'expected_tier': 'high'  # Still high because 90%
        },
        {
            'title': 'MEDIUM CONFIDENCE SCENARIO (60-89%)',
            'description': 'Valid syntax + disposable domain = 50% confidence',
            'email': 'test@tempmail.com',
            'expected_tier': 'low'  # Low because <60%
        },
        {
            'title': 'LOW CONFIDENCE SCENARIO (<60%)',
            'description': 'Invalid syntax = 0% confidence',
            'email': 'invalid@@@domain',
            'expected_tier': 'low'
        }
    ]
    
    for scenario in scenarios:
        print("=" * 80)
        print(f"SCENARIO: {scenario['title']}")
        print("=" * 80)
        print(f"Email: {scenario['email']}")
        print(f"Description: {scenario['description']}")
        print()
        
        result = validate_email_tiered(scenario['email'])
        
        print(f"✓ Initial Confidence: {result['initial_confidence']}%")
        print(f"✓ Validation Tier: {result['tier'].upper()}")
        print(f"✓ Final Confidence: {result['confidence_score']}%")
        print(f"✓ Valid: {result['valid']}")
        print()
        
        print("Filters Applied:")
        for filter_name, applied in result['filters_applied'].items():
            status = "✓ YES" if applied else "✗ NO"
            print(f"  {status} - {filter_name}")
        print()
        
        print("Checks Performed:")
        for check_name, check_result in result['checks'].items():
            print(f"  • {check_name}: {check_result}")
        print()
        
        print(f"Result: {result['reason']}")
        print()
    
    print("=" * 80)
    print("SUMMARY: HOW IT WORKS")
    print("=" * 80)
    print()
    print("1. PRELIMINARY CHECK (fast, no network calls):")
    print("   - Validates syntax")
    print("   - Checks if disposable (local lookup)")
    print("   - Checks if role-based (local lookup)")
    print("   - Calculates initial confidence score")
    print()
    print("2. TIER SELECTION based on initial confidence:")
    print("   - 90-100%: HIGH tier → Apply ALL filters")
    print("   - 60-89%:  MEDIUM tier → Apply moderate filters")
    print("   - <60%:    LOW tier → Apply minimal filters")
    print()
    print("3. FULL VALIDATION with selected filters:")
    print("   - HIGH: DNS + MX + disposable + role-based + typo detection")
    print("   - MEDIUM: DNS + MX + disposable")
    print("   - LOW: Syntax only")
    print()
    print("4. FINAL RESULT with updated confidence score")
    print()
    print("=" * 80)
    print("WHY THIS APPROACH?")
    print("=" * 80)
    print()
    print("✓ EFFICIENCY: Don't waste resources on obviously bad emails")
    print("✓ ACCURACY: Be thorough when email looks promising")
    print("✓ COST-EFFECTIVE: Expensive checks (DNS/MX) only when needed")
    print("✓ SCALABLE: Handles large batches intelligently")
    print()


if __name__ == "__main__":
    demo()
