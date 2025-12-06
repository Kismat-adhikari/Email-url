# Quick Start - Risk Scoring

Get email risk scoring running in 5 minutes.

## Step 1: Run Tests

```bash
python test_risk_scoring.py
```

Expected: **19 tests passed** ✅

## Step 2: Start API

```bash
python app_risk_scoring.py
```

Server: `http://localhost:5001`

## Step 3: Test Risk Assessment

### Assess Single Email

```bash
curl -X POST http://localhost:5001/api/risk/assess \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

**Response:**
```json
{
  "email": "user@example.com",
  "risk_score": 45,
  "risk_level": "MEDIUM",
  "risk_factors": ["Previous bounce", "Catch-all domain"],
  "is_spam_trap": false,
  "is_blacklisted": false,
  "recommendations": [
    "⚠️ CAUTION - Moderate risk detected",
    "Consider re-verification before sending"
  ]
}
```

### Get Risk by Email

```bash
curl http://localhost:5001/api/risk/user@example.com
```

### Batch Assessment

```bash
curl -X POST http://localhost:5001/api/risk/batch \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["user1@example.com", "user2@test.com"]
  }'
```

### Generate Report

```bash
curl -X POST http://localhost:5001/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["user1@example.com", "user2@test.com"],
    "format": "text"
  }'
```

### Get Statistics

```bash
curl http://localhost:5001/api/risk/statistics
```

## Python Usage

### Assess Risk

```python
from risk_scoring import assess_email_risk

result = assess_email_risk('user@example.com')
print(f"Risk: {result['risk_level']} ({result['risk_score']}/100)")
```

### Batch Assessment

```python
from risk_scoring import RiskScorer

scorer = RiskScorer()
results = scorer.batch_risk_assessment([
    'user1@example.com',
    'user2@test.com'
])

print(f"High Risk: {results['high_risk']}")
print(f"Safe: {results['low_risk']}")
```

### Generate Report

```python
from risk_scoring import RiskScorer, generate_risk_report

scorer = RiskScorer()

assessments = [
    scorer.get_email_risk_from_db('user1@example.com'),
    scorer.get_email_risk_from_db('user2@test.com')
]

report = generate_risk_report(assessments)
print(report)
```

## Risk Levels

| Score | Level | Icon | Action |
|-------|-------|------|--------|
| 0-39 | LOW | 🟢 | ✅ Safe to send |
| 40-69 | MEDIUM | 🟡 | ⚠️ Review required |
| 70-100 | HIGH | 🔴 | ❌ Do not send |

## Risk Factors

- **Bounce History** - Multiple bounces increase risk
- **Recent Bounce** - Bounces within 7-30 days
- **Spam Trap** - Known honeypot domains
- **Blacklisted** - Domain on blacklist
- **Catch-all** - Cannot verify mailbox
- **Disposable** - Temporary email service
- **Role-based** - Generic addresses (info, admin)
- **Low Confidence** - Poor validation score

## Example Scenarios

### Low Risk Email ✅
```
john@company.com
- No bounces
- High confidence (95)
- Not disposable
→ SAFE TO SEND
```

### Medium Risk Email ⚠️
```
info@company.com
- 1 bounce
- Catch-all domain
- Role-based
→ REVIEW REQUIRED
```

### High Risk Email ❌
```
trap@spamtrap.com
- 5 bounces
- Spam trap detected
- Low confidence (20)
→ DO NOT SEND
```

## Integration Example

```python
from supabase_storage import get_storage
from risk_scoring import RiskScorer

storage = get_storage()
scorer = RiskScorer()

# Get email from database
record = storage.get_record_by_email('user@example.com')

# Assess risk
risk = scorer.calculate_risk_score(record)

# Take action
if risk['risk_level'] == 'HIGH':
    print("❌ Removing from mailing list")
    remove_from_list(record['email'])
elif risk['risk_level'] == 'MEDIUM':
    print("⚠️ Flagging for review")
    flag_for_review(record['email'])
else:
    print("✅ Safe to send")
    add_to_campaign(record['email'])
```

## Next Steps

- Read full docs: `README_RISK_SCORING.md`
- Check API: `http://localhost:5001/api`
- Run tests: `python test_risk_scoring.py`
- Integrate with your app

You're ready to assess email risk! 🚀
