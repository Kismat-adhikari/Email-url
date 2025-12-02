#!/usr/bin/env python3
"""Test script for advanced email validation features."""

from emailvalidator_unified import validate_email, validate_email_advanced, validate_batch
import json

print("=" * 60)
print("ADVANCED EMAIL VALIDATION TESTS")
print("=" * 60)

# Test 1: High confidence email
print("\n1. Test: user@gmail.com (should have high confidence)")
result = validate_email_advanced('user@gmail.com')
print(json.dumps(result, indent=2))

# Test 2: Typo detection
print("\n2. Test: user@gmial.com (should suggest gmail.com)")
result = validate_email_advanced('user@gmial.com')
print(json.dumps(result, indent=2))

# Test 3: Disposable email
print("\n3. Test: test@tempmail.com (should flag as disposable)")
result = validate_email_advanced('test@tempmail.com')
print(json.dumps(result, indent=2))

# Test 4: Role-based email
print("\n4. Test: info@company.com (should flag as role-based)")
result = validate_email_advanced('info@company.com')
print(json.dumps(result, indent=2))

# Test 5: Fake domain
print("\n5. Test: test@fakexyzabc123.com (should fail DNS check)")
result = validate_email_advanced('test@fakexyzabc123.com')
print(json.dumps(result, indent=2))

# Test 6: Backward compatibility
print("\n6. Test: Backward compatibility (existing validate_email)")
print(f"test@test.com: {validate_email('test@test.com')}")
print(f"invalid@: {validate_email('invalid@')}")
print(f"user@example.com: {validate_email('user@example.com')}")

# Test 7: Batch validation with advanced mode
print("\n7. Test: Batch validation with advanced mode")
emails = ['user@gmail.com', 'test@gmial.com', 'info@tempmail.com']
results = validate_batch(emails, advanced=True)
for i, result in enumerate(results, 1):
    print(f"\nEmail {i}: {result['email']}")
    print(f"  Valid: {result['valid']}")
    print(f"  Confidence: {result['confidence_score']}")
    if result['suggestion']:
        print(f"  Suggestion: {result['suggestion']}")
    print(f"  Reason: {result['reason']}")

# Test 8: Batch validation without advanced mode (backward compatibility)
print("\n8. Test: Batch validation (basic mode - backward compatible)")
emails = ['user@example.com', 'invalid@', 'test@test.com']
results = validate_batch(emails)
for result in results:
    print(f"{result['email']}: {result['valid']}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED!")
print("=" * 60)
