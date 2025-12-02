# Quick Reference - Advanced Email Validation

## 🚀 Installation

```bash
pip install -r requirements.txt
```

## 📖 Basic Usage (Unchanged)

```python
from emailvalidator_unified import validate_email

# Simple validation
validate_email("user@example.com")  # True or False
```

## ⚡ Advanced Usage (New!)

```python
from emailvalidator_unified import validate_email_advanced

# Full validation with all checks
result = validate_email_advanced("user@gmail.com")

# Access results
result['valid']              # True/False
result['confidence_score']   # 0-100
result['checks']             # Dict of all checks
result['suggestion']         # Domain suggestion if typo
result['reason']             # Explanation
```

## 🎯 Common Scenarios

### Check if Email is Valid and Not Disposable
```python
result = validate_email_advanced("test@tempmail.com")
if result['valid'] and not result['checks']['is_disposable']:
    print("Good email!")
```

### Get Typo Suggestions
```python
result = validate_email_advanced("user@gmial.com")
if result['suggestion']:
    print(f"Did you mean {result['suggestion']}?")  # gmail.com
```

### Check Confidence Score
```python
result = validate_email_advanced("user@example.com")
if result['confidence_score'] >= 80:
    print("High confidence email")
```

### Disable Specific Checks
```python
result = validate_email_advanced(
    "user@example.com",
    check_dns=False,        # Skip DNS check
    check_disposable=False  # Skip disposable check
)
```

## 📦 Batch Validation

### Basic Batch
```python
from emailvalidator_unified import validate_batch

emails = ["user@example.com", "invalid@"]
results = validate_batch(emails)
```

### Advanced Batch
```python
results = validate_batch(emails, advanced=True)

for result in results:
    print(f"{result['email']}: {result['confidence_score']}")
```

## 🔧 Result Structure

```python
{
    'valid': bool,              # Overall validity
    'email': str,               # Original email
    'checks': {
        'syntax': bool,         # RFC 5321 valid
        'dns_valid': bool,      # Domain exists
        'mx_records': bool,     # Can receive email
        'is_disposable': bool,  # Temp email service
        'is_role_based': bool   # Generic role address
    },
    'confidence_score': int,    # 0-100
    'suggestion': str or None,  # Typo suggestion
    'reason': str               # Explanation
}
```

## 📊 Confidence Scores

- **100**: Perfect email (all checks pass)
- **90**: Valid but disposable or role-based
- **80**: Valid but missing MX records
- **60**: Valid syntax but domain doesn't exist
- **0**: Invalid syntax

## 🎨 Flask Example

```python
from flask import Flask, request, jsonify
from emailvalidator_unified import validate_email_advanced

app = Flask(__name__)

@app.route('/validate', methods=['POST'])
def validate():
    email = request.json.get('email')
    result = validate_email_advanced(email)
    return jsonify(result)
```

## ✅ Test All Features

```bash
python test_advanced.py
```

## 📚 Full Documentation

See `ADVANCED_FEATURES.md` for complete documentation.

## 🔄 Backward Compatibility

All existing code works unchanged:
```python
validate_email("test@test.com")  # Still works!
validate_batch(emails)            # Still works!
```

CLI also unchanged:
```bash
python emailvalidator_unified.py emails.txt --benchmark
```
