# Email Validator with SMTP Verification

Advanced email validation system with SMTP-level mailbox verification, catch-all domain detection, and comprehensive validation features.

## Features

### Core Validation
- ✅ **RFC 5321 Syntax Validation** - Strict email format checking
- ✅ **DNS Record Checking** - Verify domain exists
- ✅ **MX Record Verification** - Check mail server configuration
- ✅ **SMTP Mailbox Verification** - Verify mailbox actually exists (NEW)
- ✅ **Catch-all Domain Detection** - Detect domains that accept all emails (NEW)
- ✅ **Disposable Email Detection** - Identify temporary email services
- ✅ **Role-based Email Detection** - Identify generic addresses (admin, info, etc.)
- ✅ **Typo Suggestion** - Suggest corrections for common domain typos
- ✅ **Confidence Scoring** - 0-100 score based on all checks
- ✅ **Batch Processing** - Validate multiple emails efficiently

## Installation

### Requirements
- Python 3.7+
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
flask>=2.0.0
flask-cors>=3.0.0
dnspython>=2.0.0
```

## Quick Start

### 1. Start the API Server

```bash
python app_smtp.py
```

Server will start at `http://localhost:5000`

### 2. Test Basic Validation

```bash
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### 3. Test SMTP Verification

```bash
curl -X POST http://localhost:5000/api/validate/smtp \
  -H "Content-Type: application/json" \
  -d '{"email": "user@gmail.com", "enable_smtp": true}'
```

## API Endpoints

### GET /api
Get API documentation and available endpoints.

**Response:**
```json
{
  "name": "Email Validator API with SMTP",
  "version": "3.0.0",
  "endpoints": {...},
  "features": [...]
}
```

### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "email-validator-smtp",
  "timestamp": 1234567890.123,
  "version": "3.0.0"
}
```

### POST /api/validate
Basic email validation (syntax only, fast).

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "email": "user@example.com",
  "valid": true,
  "processing_time": 0.001,
  "timestamp": 1234567890.123
}
```

### POST /api/validate/smtp
Advanced validation with SMTP verification.

**Request:**
```json
{
  "email": "user@gmail.com",
  "enable_smtp": true,
  "check_dns": true,
  "check_mx": true,
  "check_disposable": true,
  "check_typos": true,
  "check_role_based": true,
  "smtp_timeout": 10
}
```

**Response:**
```json
{
  "email": "user@gmail.com",
  "valid": true,
  "checks": {
    "syntax": true,
    "dns_valid": true,
    "mx_records": true,
    "smtp_verified": true,
    "is_disposable": false,
    "is_role_based": false,
    "is_catch_all": false
  },
  "confidence_score": 100,
  "smtp_details": {
    "smtp_valid": true,
    "smtp_code": 250,
    "smtp_message": "OK",
    "is_catch_all": false,
    "error": null
  },
  "is_catch_all": false,
  "suggestion": null,
  "reason": "Valid email",
  "processing_time": 1.234,
  "timestamp": 1234567890.123
}
```

### POST /api/validate/batch
Validate multiple emails (basic mode for performance).

**Request:**
```json
{
  "emails": ["user@example.com", "test@test.com"],
  "advanced": false
}
```

**Response:**
```json
{
  "total": 2,
  "valid_count": 2,
  "invalid_count": 0,
  "results": [
    {"email": "user@example.com", "valid": true},
    {"email": "test@test.com", "valid": true}
  ],
  "processing_time": 0.123,
  "timestamp": 1234567890.123
}
```

**Note:** SMTP verification is not available in batch mode for performance reasons.

### POST /api/catch-all
Detect if a domain is catch-all (accepts all emails).

**Request:**
```json
{
  "domain": "example.com",
  "timeout": 10
}
```

**Response:**
```json
{
  "domain": "example.com",
  "is_catch_all": false,
  "test_email": "nonexistent-test@example.com",
  "smtp_code": 550,
  "error": null,
  "processing_time": 1.234,
  "timestamp": 1234567890.123
}
```

### GET /api/stats
Get validation statistics and configuration.

**Response:**
```json
{
  "disposable_domains_count": 20,
  "common_domains_count": 19,
  "role_based_prefixes_count": 18,
  "typo_similarity_threshold": 0.85,
  "max_batch_size": 1000,
  "smtp_timeout": 10,
  "features": {...}
}
```

## Python Module Usage

### Basic Validation

```python
from emailvalidator_unified import validate_email

# Simple validation
is_valid = validate_email("user@example.com")
print(is_valid)  # True or False
```

### Advanced Validation

```python
from emailvalidator_unified import validate_email_advanced

result = validate_email_advanced(
    "user@gmail.com",
    check_dns=True,
    check_mx=True,
    check_disposable=True,
    check_typos=True,
    check_role_based=True
)

print(result['valid'])              # True/False
print(result['confidence_score'])   # 0-100
print(result['checks'])             # All validation checks
```

### SMTP Verification

```python
from email_validator_smtp import validate_email_with_smtp

result = validate_email_with_smtp(
    "user@gmail.com",
    enable_smtp=True,
    smtp_timeout=10
)

print(result['valid'])                          # True/False
print(result['confidence_score'])               # 0-100
print(result['smtp_details']['smtp_valid'])     # SMTP verification result
print(result['is_catch_all'])                   # Catch-all detection
```

### Catch-all Detection

```python
from email_validator_smtp import detect_catch_all_domain

result = detect_catch_all_domain("example.com")

print(result['is_catch_all'])   # True/False
print(result['test_email'])     # Email used for testing
print(result['smtp_code'])      # SMTP response code
```

### Batch Validation

```python
from emailvalidator_unified import validate_batch

emails = ["user@example.com", "test@test.com", "invalid@"]

results = validate_batch(emails, advanced=True)

for result in results:
    print(f"{result['email']}: {result['valid']}")
```

## Confidence Scoring

The system calculates a confidence score (0-100) based on multiple checks:

| Check | Points | Description |
|-------|--------|-------------|
| Syntax Valid | 30 | Email follows RFC 5321 format |
| DNS Valid | 15 | Domain has valid DNS records |
| MX Records | 15 | Domain has mail server configuration |
| SMTP Verified | 20 | Mailbox exists (SMTP check) |
| Not Disposable | 10 | Not a temporary email service |
| Not Role-based | 5 | Not a generic address (admin, info) |
| Not Catch-all | 5 | Domain doesn't accept all emails |

**Total: 100 points**

### Score Interpretation

- **90-100**: Highly confident - Valid, deliverable email
- **70-89**: Good confidence - Valid but with minor concerns
- **50-69**: Medium confidence - Valid syntax but delivery uncertain
- **30-49**: Low confidence - Valid syntax only
- **0-29**: Invalid or highly suspicious

## Testing

### Run Unit Tests

```bash
python test_email_validation.py
```

### Test Coverage

The test suite includes:
- ✅ Valid email addresses
- ✅ Invalid email addresses
- ✅ Disposable email detection
- ✅ Role-based email detection
- ✅ SMTP verification success
- ✅ SMTP verification failure (mailbox doesn't exist)
- ✅ SMTP connection errors
- ✅ Catch-all domain detection
- ✅ Non-catch-all domain detection
- ✅ Confidence score calculation
- ✅ Integration tests

### Example Test Output

```
test_valid_email (__main__.TestBasicValidation) ... ok
test_invalid_email (__main__.TestBasicValidation) ... ok
test_disposable_email (__main__.TestDisposableEmailDetection) ... ok
test_smtp_success (__main__.TestSMTPVerification) ... ok
test_catch_all_domain (__main__.TestCatchAllDetection) ... ok
test_perfect_score (__main__.TestConfidenceScoring) ... ok

======================================================================
TEST SUMMARY
======================================================================
Tests run: 20
Successes: 20
Failures: 0
Errors: 0
======================================================================
```

## SMTP Verification Details

### How It Works

1. **Extract Domain** - Get domain from email address
2. **Lookup MX Records** - Find mail server for domain
3. **Connect to SMTP** - Establish connection to mail server
4. **SMTP Handshake** - Perform HELO/EHLO
5. **MAIL FROM** - Specify sender
6. **RCPT TO** - Test recipient (the email being validated)
7. **Analyze Response** - Check SMTP response code
   - `250` = Mailbox exists ✅
   - `550` = Mailbox doesn't exist ❌
   - Other codes = Uncertain

### Catch-all Detection

To detect catch-all domains, the system:
1. Connects to the mail server
2. Tests with an obviously fake email address
3. If the fake email is accepted (250), domain is catch-all

**Why it matters:** Catch-all domains accept all emails, so SMTP verification cannot confirm if a specific mailbox exists.

### Performance Considerations

- **SMTP verification is slow** (~1-3 seconds per email)
- Use only for critical validations (user registration, payment)
- Not recommended for batch processing
- Consider caching results
- Set appropriate timeouts (default: 10 seconds)

### Limitations

- Some mail servers block SMTP verification
- Greylisting may cause temporary failures
- Rate limiting may apply
- Catch-all domains cannot be fully verified
- Some servers return false positives

## Error Handling

The API provides clear error messages:

```json
{
  "error": "Missing email parameter",
  "message": "Please provide an email address in the request body"
}
```

Common errors:
- `400` - Bad request (missing/invalid parameters)
- `404` - Endpoint not found
- `405` - Method not allowed
- `500` - Internal server error

## Best Practices

### When to Use SMTP Verification

✅ **Use SMTP verification for:**
- User registration (prevent fake accounts)
- Payment processing (ensure valid contact)
- Critical communications
- Single email validation

❌ **Don't use SMTP verification for:**
- Batch processing (too slow)
- Real-time form validation (too slow)
- High-volume operations
- Non-critical validations

### Recommended Validation Strategy

1. **Step 1: Syntax** - Always validate syntax first (fast)
2. **Step 2: DNS/MX** - Check domain exists (medium speed)
3. **Step 3: Disposable** - Check if temporary email (fast)
4. **Step 4: SMTP** - Only for critical validations (slow)

### Caching Strategy

```python
# Cache SMTP results to avoid repeated checks
cache = {}

def validate_with_cache(email):
    if email in cache:
        return cache[email]
    
    result = validate_email_with_smtp(email)
    cache[email] = result
    return result
```

## Examples

### Example 1: User Registration

```python
from email_validator_smtp import validate_email_with_smtp

def register_user(email, password):
    # Validate email with SMTP
    result = validate_email_with_smtp(email, enable_smtp=True)
    
    if not result['valid']:
        return {"error": f"Invalid email: {result['reason']}"}
    
    if result['checks']['is_disposable']:
        return {"error": "Disposable emails are not allowed"}
    
    if result['confidence_score'] < 70:
        return {"error": "Email validation confidence too low"}
    
    # Proceed with registration
    create_account(email, password)
    return {"success": True}
```

### Example 2: Email List Cleaning

```python
from emailvalidator_unified import validate_batch

def clean_email_list(emails):
    # Use batch validation (no SMTP for performance)
    results = validate_batch(emails, advanced=True)
    
    valid_emails = []
    for result in results:
        if result['valid'] and not result['checks']['is_disposable']:
            valid_emails.append(result['email'])
    
    return valid_emails
```

### Example 3: API Integration

```javascript
// JavaScript/Node.js example
async function validateEmail(email) {
  const response = await fetch('http://localhost:5000/api/validate/smtp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      enable_smtp: true,
      smtp_timeout: 10
    })
  });
  
  const result = await response.json();
  
  if (result.valid && result.confidence_score >= 80) {
    console.log('Email is valid and deliverable');
  } else {
    console.log('Email validation failed:', result.reason);
  }
  
  return result;
}
```

## Troubleshooting

### SMTP Connection Timeout

**Problem:** SMTP verification times out

**Solutions:**
- Increase timeout: `smtp_timeout: 20`
- Check firewall settings (port 25)
- Some mail servers block verification
- Try without SMTP: `enable_smtp: false`

### False Positives

**Problem:** Valid emails marked as invalid

**Solutions:**
- Check if domain is catch-all
- Disable SMTP: `enable_smtp: false`
- Some servers use greylisting
- Check confidence score instead of binary valid/invalid

### Rate Limiting

**Problem:** Too many requests blocked

**Solutions:**
- Implement caching
- Add delays between requests
- Use batch validation
- Consider using a proxy

## Performance Benchmarks

| Operation | Time | Throughput |
|-----------|------|------------|
| Syntax validation | <1ms | 100,000+/sec |
| DNS/MX check | 10-50ms | 1,000/sec |
| SMTP verification | 1-3s | 1-10/sec |
| Batch (1000 emails) | 5-10s | 100-200/sec |

## License

MIT License - Free to use in your projects

## Contributing

Contributions welcome! Please ensure:
- All tests pass
- Code follows existing style
- Documentation is updated
- New features include tests

## Support

For issues or questions:
- Check the troubleshooting section
- Review API documentation
- Run unit tests to verify setup
- Check server logs for errors

## Changelog

### Version 3.0.0
- ✨ Added SMTP mailbox verification
- ✨ Added catch-all domain detection
- ✨ Enhanced confidence scoring
- ✨ New API endpoints
- 📝 Comprehensive documentation
- ✅ Full test coverage

### Version 2.0.0
- Advanced validation features
- Disposable email detection
- Role-based detection
- Typo suggestions

### Version 1.0.0
- Initial release
- Basic syntax validation
- DNS/MX checking

## Author

Built with production-ready practices and clean code principles.
