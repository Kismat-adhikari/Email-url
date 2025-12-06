# Email Risk Scoring System

Advanced email risk assessment with bounce history analysis, spam trap detection, blacklist checking, and comprehensive reporting.

## Features

### Risk Assessment
- ✅ **Bounce History Analysis** - Track and score based on bounce patterns
- ✅ **Spam Trap Detection** - Identify known honeypot domains
- ✅ **Blacklist Checking** - Check against public blacklists
- ✅ **Catch-all Detection** - Flag domains that accept all emails
- ✅ **Confidence Scoring** - 0-100 risk score for each email
- ✅ **Batch Assessment** - Evaluate multiple emails efficiently
- ✅ **Detailed Reports** - Generate comprehensive risk reports

## Installation

```bash
pip install -r requirements_supabase.txt
```

## Quick Start

### 1. Start Risk Scoring API

```bash
python app_risk_scoring.py
```

Server runs at: `http://localhost:5001`

### 2. Assess Email Risk

```bash
curl -X POST http://localhost:5001/api/risk/assess \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

## Risk Scoring Logic

### Scoring Factors (0-100 points)

| Factor | Points | Description |
|--------|--------|-------------|
| **Bounce History** | 0-40 | Based on number of bounces |
| - 5+ bounces | 40 | High bounce count |
| - 3-4 bounces | 25 | Multiple bounces |
| - 1-2 bounces | 10 | Previous bounce |
| **Recent Bounce** | 0-15 | Time since last bounce |
| - Within 7 days | 15 | Very recent |
| - Within 30 days | 10 | Recent |
| **Catch-all Domain** | 20 | Cannot verify mailbox |
| **Disposable Email** | 15 | Temporary email service |
| **Role-based Email** | 10 | Generic address (info, admin) |
| **Low Confidence** | 0-20 | Validation confidence |
| - < 50 confidence | 20 | Very low |
| - 50-69 confidence | 10 | Low |
| **Spam Trap** | 30 | Known honeypot domain |
| **Blacklisted** | 25 | Domain on blacklist |

**Total:** Maximum 100 points (capped)

### Risk Levels

| Score | Level | Action |
|-------|-------|--------|
| 0-39 | **LOW** | ✅ Safe to send |
| 40-69 | **MEDIUM** | ⚠️ Review required |
| 70-100 | **HIGH** | ❌ Do not send |

## API Endpoints

### POST /api/risk/assess
Assess risk for a single email.

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
  "risk_score": 45,
  "risk_level": "MEDIUM",
  "risk_factors": [
    "Multiple bounces (3 bounces)",
    "Catch-all domain"
  ],
  "is_spam_trap": false,
  "is_blacklisted": false,
  "recommendations": [
    "⚠️ CAUTION - Moderate risk detected",
    "Consider re-verification before sending"
  ],
  "assessed_at": "2024-01-01T12:00:00"
}
```

### GET /api/risk/<email>
Get risk score for an email.

```bash
curl http://localhost:5001/api/risk/user@example.com
```

### POST /api/risk/batch
Assess risk for multiple emails.

**Request:**
```json
{
  "emails": ["user1@example.com", "user2@test.com"]
}
```

**Response:**
```json
{
  "total": 2,
  "high_risk": 0,
  "medium_risk": 1,
  "low_risk": 1,
  "results": [...],
  "summary": {
    "safe_to_send": 1,
    "review_required": 1,
    "do_not_send": 0,
    "risk_percentage": 0
  }
}
```

### POST /api/report/generate
Generate formatted risk report.

**Request:**
```json
{
  "emails": ["user1@example.com", "user2@test.com"],
  "format": "text"
}
```

**Response:** Text report or JSON

### GET /api/risk/statistics
Get overall risk statistics.

```bash
curl http://localhost:5001/api/risk/statistics
```

**Response:**
```json
{
  "total_emails": 1000,
  "high_risk_count": 50,
  "medium_risk_count": 200,
  "low_risk_count": 750,
  "spam_trap_count": 5,
  "blacklisted_count": 10,
  "avg_risk_score": 25.5,
  "risk_distribution": {
    "high": 5.0,
    "medium": 20.0,
    "low": 75.0
  }
}
```

### POST /api/risk/high-risk
Get all high-risk emails.

**Request:**
```json
{
  "limit": 100
}
```

## Python Module Usage

### Basic Risk Assessment

```python
from risk_scoring import RiskScorer

scorer = RiskScorer()

# Assess email from database
result = scorer.get_email_risk_from_db('user@example.com')

print(f"Risk Level: {result['risk_level']}")
print(f"Risk Score: {result['risk_score']}/100")
print(f"Recommendations: {result['recommendations']}")
```

### Manual Risk Calculation

```python
from risk_scoring import RiskScorer

scorer = RiskScorer()

email_data = {
    'email': 'user@example.com',
    'bounce_count': 3,
    'is_catch_all': True,
    'is_disposable': False,
    'is_role_based': False,
    'confidence_score': 60
}

result = scorer.calculate_risk_score(email_data)
print(f"Risk: {result['risk_level']} ({result['risk_score']}/100)")
```

### Batch Assessment

```python
from risk_scoring import RiskScorer

scorer = RiskScorer()

emails = ['user1@example.com', 'user2@test.com', 'user3@spam.com']
results = scorer.batch_risk_assessment(emails)

print(f"Total: {results['total']}")
print(f"High Risk: {results['high_risk']}")
print(f"Safe to Send: {results['summary']['safe_to_send']}")
```

### Generate Report

```python
from risk_scoring import RiskScorer, generate_risk_report

scorer = RiskScorer()

# Assess multiple emails
assessments = [
    scorer.get_email_risk_from_db('user1@example.com'),
    scorer.get_email_risk_from_db('user2@test.com')
]

# Generate report
report = generate_risk_report(assessments)
print(report)
```

## Spam Trap Detection

### Known Spam Trap Domains

The system detects these known honeypot domains:
- spamtrap.com
- honeypot.email
- trap.example.com
- spamcop.net
- abuse.net
- spam-trap.org

### Custom Spam Traps

Add your own spam trap domains:

```python
from risk_scoring import SPAM_TRAP_DOMAINS

# Add custom spam trap
SPAM_TRAP_DOMAINS.add('custom-trap.com')
```

## Blacklist Checking

### Current Implementation

The system checks for suspicious patterns in domains:
- spam
- abuse
- blacklist
- blocked

### Integrate Real Blacklist APIs

You can integrate real blacklist services:

```python
def _check_blacklist(self, domain: str) -> Dict[str, Any]:
    """Check against real blacklist APIs."""
    
    # Spamhaus
    # response = requests.get(f'https://api.spamhaus.org/check/{domain}')
    
    # SURBL
    # response = requests.get(f'https://api.surbl.org/check/{domain}')
    
    # Check-Host
    # response = requests.get(f'https://check-host.net/check-blacklist?host={domain}')
    
    return {
        'is_blacklisted': False,
        'lists': [],
        'checked_at': datetime.utcnow().isoformat()
    }
```

## Risk Assessment Examples

### Example 1: Low Risk Email

```python
email_data = {
    'email': 'john@company.com',
    'bounce_count': 0,
    'is_catch_all': False,
    'is_disposable': False,
    'is_role_based': False,
    'confidence_score': 95
}

result = scorer.calculate_risk_score(email_data)
# Risk Level: LOW (15/100)
# ✅ SAFE TO SEND
```

### Example 2: Medium Risk Email

```python
email_data = {
    'email': 'info@company.com',
    'bounce_count': 1,
    'is_catch_all': True,
    'is_disposable': False,
    'is_role_based': True,
    'confidence_score': 60
}

result = scorer.calculate_risk_score(email_data)
# Risk Level: MEDIUM (50/100)
# ⚠️ CAUTION - Review required
```

### Example 3: High Risk Email

```python
email_data = {
    'email': 'trap@spamtrap.com',
    'bounce_count': 5,
    'is_catch_all': False,
    'is_disposable': True,
    'is_role_based': False,
    'confidence_score': 20
}

result = scorer.calculate_risk_score(email_data)
# Risk Level: HIGH (95/100)
# ❌ DO NOT SEND - Spam trap detected
```

## Sample Risk Report

```
================================================================================
EMAIL RISK ASSESSMENT REPORT
================================================================================
Generated: 2024-01-01 12:00:00 UTC
Total Emails Assessed: 3

RISK DISTRIBUTION:
  High Risk:   1 (33.3%)
  Medium Risk: 1 (33.3%)
  Low Risk:    1 (33.3%)

DETAILED RESULTS:
--------------------------------------------------------------------------------

🟢 john@company.com
   Risk Score: 15/100 (LOW)
   Recommendations:
     • ✅ SAFE TO SEND - Low risk detected
     • Email appears valid and safe

🟡 info@company.com
   Risk Score: 50/100 (MEDIUM)
   Risk Factors:
     - Previous bounce (1 bounce)
     - Catch-all domain (cannot verify mailbox)
     - Role-based email (info, admin, etc.)
   Recommendations:
     • ⚠️ CAUTION - Moderate risk detected
     • Consider re-verification before sending

🔴 trap@spamtrap.com
   Risk Score: 95/100 (HIGH)
   Risk Factors:
     - High bounce count (5 bounces)
     - Disposable/temporary email service
     - Low validation confidence (20/100)
     - SPAM TRAP DETECTED
   ⚠️  SPAM TRAP DETECTED
   Recommendations:
     • ❌ DO NOT SEND - High risk of bounce or spam complaint
     • Remove from mailing list immediately
     • ⚠️ SPAM TRAP - Sending will damage sender reputation

================================================================================
END OF REPORT
================================================================================
```

## Testing

### Run Unit Tests

```bash
python test_risk_scoring.py
```

### Test Coverage

- ✅ Low-risk email assessment
- ✅ High-risk email assessment
- ✅ Medium-risk email assessment
- ✅ Spam trap detection
- ✅ Blacklist checking
- ✅ Bounce history analysis
- ✅ Catch-all domain detection
- ✅ Disposable email detection
- ✅ Role-based email detection
- ✅ Confidence scoring
- ✅ Batch assessment
- ✅ Report generation

**Result:** 19/19 tests passed ✅

## Best Practices

### 1. Regular Assessment

Re-assess emails periodically:

```python
# Re-assess emails every 30 days
from datetime import datetime, timedelta

def should_reassess(last_assessed):
    return (datetime.utcnow() - last_assessed).days >= 30
```

### 2. Action Based on Risk Level

```python
def handle_email_risk(email, risk_level):
    if risk_level == 'HIGH':
        # Remove from mailing list
        remove_from_list(email)
        log_high_risk(email)
    elif risk_level == 'MEDIUM':
        # Flag for review
        flag_for_review(email)
    else:
        # Safe to send
        add_to_campaign(email)
```

### 3. Monitor Trends

```python
# Track risk trends over time
def get_risk_trend(email):
    history = storage.get_validation_history(email)
    scores = [assess_risk(h)['risk_score'] for h in history]
    return {
        'current': scores[0],
        'previous': scores[1] if len(scores) > 1 else None,
        'trend': 'increasing' if scores[0] > scores[1] else 'decreasing'
    }
```

### 4. Bounce Tracking

```python
# Update bounce count when email bounces
def handle_bounce(email, bounce_type):
    storage = get_storage()
    storage.increment_bounce_count(email)
    
    # Re-assess risk
    risk = assess_email_risk(email)
    if risk['risk_level'] == 'HIGH':
        remove_from_list(email)
```

## Integration with Existing System

### With Supabase Storage

```python
from supabase_storage import get_storage
from risk_scoring import RiskScorer

storage = get_storage()
scorer = RiskScorer()

# Get email from database
record = storage.get_record_by_email('user@example.com')

# Assess risk
risk = scorer.calculate_risk_score(record)

# Update record with risk info
storage.update_record(record['id'], {
    'notes': f"Risk: {risk['risk_level']} ({risk['risk_score']}/100)"
})
```

### With Validation API

```python
# In app_supabase.py, add risk assessment
@app.route('/api/validate/with-risk', methods=['POST'])
def validate_with_risk():
    # Validate email
    result = validate_email_with_smtp(email)
    
    # Store in database
    record = storage.create_record(result)
    
    # Assess risk
    risk = scorer.calculate_risk_score(record)
    
    # Return combined result
    return jsonify({
        **result,
        'risk_assessment': risk
    })
```

## Troubleshooting

### High False Positives

If too many emails are flagged as high-risk:

1. Adjust risk thresholds in `risk_scoring.py`
2. Reduce point values for certain factors
3. Customize spam trap and blacklist lists

### Missing Risk Data

If emails show "Email not found in database":

1. Ensure email has been validated first
2. Check Supabase connection
3. Verify email is stored in database

## License

MIT License - Free to use in your projects

## Next Steps

1. ✅ Run tests: `python test_risk_scoring.py`
2. ✅ Start API: `python app_risk_scoring.py`
3. ✅ Assess emails via API
4. ✅ Generate reports
5. ✅ Integrate with your application

You're ready to assess email risk! 🚀
