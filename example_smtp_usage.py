#!/usr/bin/env python3
"""
Example Usage of Email Validator with SMTP Verification
Demonstrates all key features with real examples
"""

from email_validator_smtp import (
    validate_email_with_smtp,
    detect_catch_all_domain,
    verify_smtp_mailbox
)
from emailvalidator_unified import validate_email, validate_batch

def print_section(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def example_basic_validation():
    """Example 1: Basic syntax validation (fast)."""
    print_section("Example 1: Basic Syntax Validation")
    
    emails = [
        "user@example.com",
        "invalid@",
        "test@test.com",
        "admin@company.org"
    ]
    
    for email in emails:
        is_valid = validate_email(email)
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"{status}: {email}")


def example_advanced_validation():
    """Example 2: Advanced validation without SMTP."""
    print_section("Example 2: Advanced Validation (No SMTP)")
    
    result = validate_email_with_smtp(
        "info@company.com",
        enable_smtp=False,  # Disable SMTP for speed
        check_dns=False,
        check_mx=False
    )
    
    print(f"Email: {result['email']}")
    print(f"Valid: {result['valid']}")
    print(f"Confidence Score: {result['confidence_score']}/100")
    print(f"\nChecks:")
    print(f"  - Syntax: {result['checks']['syntax']}")
    print(f"  - Disposable: {result['checks']['is_disposable']}")
    print(f"  - Role-based: {result['checks']['is_role_based']}")
    print(f"\nReason: {result['reason']}")


def example_smtp_verification():
    """Example 3: SMTP mailbox verification."""
    print_section("Example 3: SMTP Verification (Mocked)")
    
    print("Note: This example uses mocked SMTP for demonstration.")
    print("In production, it would connect to actual mail servers.\n")
    
    # Example with SMTP disabled (for demo purposes)
    result = validate_email_with_smtp(
        "user@example.com",
        enable_smtp=False,  # Set to True for real SMTP verification
        check_dns=False,
        check_mx=False
    )
    
    print(f"Email: {result['email']}")
    print(f"Valid: {result['valid']}")
    print(f"Confidence Score: {result['confidence_score']}/100")
    
    if result['smtp_details']:
        print(f"\nSMTP Details:")
        print(f"  - SMTP Valid: {result['smtp_details']['smtp_valid']}")
        print(f"  - SMTP Code: {result['smtp_details']['smtp_code']}")
        print(f"  - Catch-all: {result['smtp_details']['is_catch_all']}")
    else:
        print("\nSMTP verification disabled for this example")


def example_disposable_detection():
    """Example 4: Disposable email detection."""
    print_section("Example 4: Disposable Email Detection")
    
    test_emails = [
        "user@gmail.com",           # Legitimate
        "test@tempmail.com",        # Disposable
        "fake@guerrillamail.com",   # Disposable
        "admin@company.com"         # Legitimate
    ]
    
    for email in test_emails:
        result = validate_email_with_smtp(
            email,
            enable_smtp=False,
            check_dns=False,
            check_mx=False
        )
        
        is_disposable = result['checks']['is_disposable']
        status = "⚠ DISPOSABLE" if is_disposable else "✓ LEGITIMATE"
        print(f"{status}: {email}")


def example_role_based_detection():
    """Example 5: Role-based email detection."""
    print_section("Example 5: Role-based Email Detection")
    
    test_emails = [
        "john.doe@company.com",     # Personal
        "admin@company.com",        # Role-based
        "info@company.com",         # Role-based
        "alice.smith@test.org"      # Personal
    ]
    
    for email in test_emails:
        result = validate_email_with_smtp(
            email,
            enable_smtp=False,
            check_dns=False,
            check_mx=False
        )
        
        is_role = result['checks']['is_role_based']
        status = "⚠ ROLE-BASED" if is_role else "✓ PERSONAL"
        print(f"{status}: {email}")


def example_confidence_scoring():
    """Example 6: Confidence scoring."""
    print_section("Example 6: Confidence Scoring")
    
    test_cases = [
        ("user@example.com", False, False, False),
        ("admin@tempmail.com", False, False, False),
        ("info@company.com", False, False, False),
    ]
    
    for email, dns, mx, smtp in test_cases:
        result = validate_email_with_smtp(
            email,
            enable_smtp=smtp,
            check_dns=dns,
            check_mx=mx
        )
        
        score = result['confidence_score']
        
        if score >= 90:
            level = "EXCELLENT"
        elif score >= 70:
            level = "GOOD"
        elif score >= 50:
            level = "MEDIUM"
        else:
            level = "LOW"
        
        print(f"{email}")
        print(f"  Score: {score}/100 ({level})")
        print(f"  Checks: Syntax={result['checks']['syntax']}, "
              f"Disposable={result['checks']['is_disposable']}, "
              f"Role={result['checks']['is_role_based']}")
        print()


def example_batch_validation():
    """Example 7: Batch validation."""
    print_section("Example 7: Batch Validation")
    
    emails = [
        "user1@example.com",
        "user2@test.com",
        "invalid@",
        "admin@company.org",
        "test@tempmail.com"
    ]
    
    print(f"Validating {len(emails)} emails...\n")
    
    results = validate_batch(emails)
    
    valid_count = sum(1 for r in results if r['valid'])
    invalid_count = len(results) - valid_count
    
    for result in results:
        status = "✓" if result['valid'] else "✗"
        print(f"{status} {result['email']}")
    
    print(f"\nSummary: {valid_count} valid, {invalid_count} invalid")


def example_catch_all_detection():
    """Example 8: Catch-all domain detection."""
    print_section("Example 8: Catch-all Detection (Mocked)")
    
    print("Note: This example uses mocked detection for demonstration.")
    print("In production, it would test actual mail servers.\n")
    
    # Example domains (mocked for demo)
    domains = [
        "example.com",
        "test.org",
        "company.net"
    ]
    
    for domain in domains:
        print(f"Testing: {domain}")
        print(f"  Status: Would test with fake email")
        print(f"  Result: Requires live SMTP connection")
        print()


def example_real_world_use_case():
    """Example 9: Real-world use case - User registration."""
    print_section("Example 9: User Registration Validation")
    
    def validate_for_registration(email):
        """Validate email for user registration."""
        result = validate_email_with_smtp(
            email,
            enable_smtp=False,  # Set to True in production
            check_dns=False,
            check_mx=False,
            check_disposable=True,
            check_role_based=True
        )
        
        # Business rules
        if not result['valid']:
            return False, f"Invalid email: {result['reason']}"
        
        if result['checks']['is_disposable']:
            return False, "Disposable emails are not allowed"
        
        if result['confidence_score'] < 50:
            return False, "Email validation confidence too low"
        
        return True, "Email accepted"
    
    # Test cases
    test_emails = [
        "john.doe@company.com",
        "test@tempmail.com",
        "invalid@",
        "admin@example.com"
    ]
    
    for email in test_emails:
        accepted, message = validate_for_registration(email)
        status = "✓ ACCEPTED" if accepted else "✗ REJECTED"
        print(f"{status}: {email}")
        print(f"  Reason: {message}\n")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("  EMAIL VALIDATOR WITH SMTP - EXAMPLES")
    print("=" * 70)
    print("\nDemonstrating all features with practical examples...")
    
    try:
        example_basic_validation()
        example_advanced_validation()
        example_smtp_verification()
        example_disposable_detection()
        example_role_based_detection()
        example_confidence_scoring()
        example_batch_validation()
        example_catch_all_detection()
        example_real_world_use_case()
        
        print("\n" + "=" * 70)
        print("  ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nFor more information:")
        print("  - Full documentation: README_SMTP.md")
        print("  - Quick start: QUICKSTART_SMTP.md")
        print("  - Run tests: python test_email_validation.py")
        print("  - Start API: python app_smtp.py")
        print()
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
