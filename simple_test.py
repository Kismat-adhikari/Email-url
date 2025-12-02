#!/usr/bin/env python3
"""Simple test to verify everything works."""

print("Testing Email Validator...")
print("=" * 50)

# Test 1: Import
try:
    from emailvalidator_unified import validate_email, validate_email_advanced
    print("✓ Imports work")
except Exception as e:
    print(f"✗ Import failed: {e}")
    exit(1)

# Test 2: Basic validation
try:
    assert validate_email("user@example.com") == True
    assert validate_email("invalid@") == False
    print("✓ Basic validation works")
except Exception as e:
    print(f"✗ Basic validation failed: {e}")
    exit(1)

# Test 3: Advanced validation
try:
    result = validate_email_advanced("user@gmail.com")
    assert result['valid'] == True
    assert result['confidence_score'] > 0
    print("✓ Advanced validation works")
except Exception as e:
    print(f"✗ Advanced validation failed: {e}")
    exit(1)

# Test 4: Typo detection
try:
    result = validate_email_advanced("user@gmial.com")
    assert result['suggestion'] == "gmail.com"
    print("✓ Typo detection works")
except Exception as e:
    print(f"✗ Typo detection failed: {e}")
    exit(1)

# Test 5: Disposable detection
try:
    result = validate_email_advanced("test@tempmail.com")
    assert result['checks']['is_disposable'] == True
    print("✓ Disposable detection works")
except Exception as e:
    print(f"✗ Disposable detection failed: {e}")
    exit(1)

print("=" * 50)
print("✅ ALL TESTS PASSED!")
print("\nYour email validator is working perfectly!")
