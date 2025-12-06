# Quick Start Guide - Email Validator with SMTP

Get started with email validation including SMTP verification in 5 minutes.

## Installation

```bash
# Install dependencies
pip install -r requirements_smtp.txt
```

## Start the Server

```bash
python app_smtp.py
```

Server runs at: `http://localhost:5000`

## Test the API

### 1. Health Check

```bash
curl http://localhost:5000/api/health
```

### 2. Basic Validation (Fast)

```bash
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

**Response:**
```json
{
  "email": "user@example.com",
  "valid": true,
  "processing_time": 0.001
}
```

### 3. SMTP Verification (Comprehensive)

```bash
curl -X POST http://localhost:5000/api/validate/smtp \
  -H "Content-Type: application/json" \
  -d '{"email": "user@gmail.com", "enable_smtp": true}'
```

**Response:**
```json
{
  "email": "user@gmail.com",
  "valid": true,
  "confidence_score": 100,
  "checks": {
    "syntax": true,
    "dns_valid": true,
    "mx_records": true,
    "smtp_verified": true,
    "is_disposable": false,
    "is_role_based": false,
    "is_catch_all": false
  },
  "smtp_details": {
    "smtp_valid": true,
    "smtp_code": 250,
    "is_catch_all": false
  }
}
```

### 4. Catch-all Detection

```bash
curl -X POST http://localhost:5000/api/catch-all \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com"}'
```

### 5. Batch Validation

```bash
curl -X POST http://localhost:5000/api/validate/batch \
  -H "Content-Type: application/json" \
  -d '{"emails": ["user@example.com", "test@test.com"]}'
```

## Python Usage

### Basic Validation

```python
from emailvalidator_unified import validate_email

is_valid = validate_email("user@example.com")
print(is_valid)  # True
```

### SMTP Verification

```python
from email_validator_smtp import validate_email_with_smtp

result = validate_email_with_smtp("user@gmail.com", enable_smtp=True)

print(f"Valid: {result['valid']}")
print(f"Confidence: {result['confidence_score']}/100")
print(f"SMTP Verified: {result['smtp_details']['smtp_valid']}")
print(f"Catch-all: {result['is_catch_all']}")
```

### Catch-all Detection

```python
from email_validator_smtp import detect_catch_all_domain

result = detect_catch_all_domain("example.com")
print(f"Is catch-all: {result['is_catch_all']}")
```

## Run Tests

```bash
python test_email_validation.py
```

Expected output:
```
Ran 18 tests in 0.3s
OK
```

## Key Features

| Feature | Endpoint | Speed |
|---------|----------|-------|
| Syntax validation | `/api/validate` | <1ms |
| DNS/MX check | `/api/validate/smtp` (dns only) | 10-50ms |
| SMTP verification | `/api/validate/smtp` | 1-3s |
| Catch-all detection | `/api/catch-all` | 1-3s |
| Batch validation | `/api/validate/batch` | Fast |

## When to Use What

### Use Basic Validation (`/api/validate`)
- Real-time form validation
- High-volume operations
- Quick syntax checks

### Use SMTP Verification (`/api/validate/smtp`)
- User registration
- Payment processing
- Critical validations
- When you need high confidence

### Use Batch Validation (`/api/validate/batch`)
- Email list cleaning
- Bulk imports
- Database cleanup

## Common Issues

### SMTP Timeout
```json
{
  "email": "user@example.com",
  "enable_smtp": true,
  "smtp_timeout": 20
}
```

### Disable SMTP for Speed
```json
{
  "email": "user@example.com",
  "enable_smtp": false
}
```

### Check Only Specific Features
```json
{
  "email": "user@example.com",
  "enable_smtp": false,
  "check_dns": true,
  "check_disposable": true,
  "check_role_based": false
}
```

## Next Steps

- Read full documentation: `README_SMTP.md`
- Explore API endpoints: `http://localhost:5000/api`
- Run tests: `python test_email_validation.py`
- Check examples in README

## Support

All tests passing? You're ready to go! 🚀

For detailed documentation, see `README_SMTP.md`
