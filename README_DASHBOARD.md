# Email Validator Dashboard & Integrations

Complete dashboard system with webhooks, CRM/ESP integrations, CSV export, and React frontend.

## Features

### Dashboard
- ✅ Real-time validation statistics
- ✅ Recent validations display
- ✅ Batch upload and validation
- ✅ Progress tracking
- ✅ Risk assessment integration

### Integrations
- ✅ **Webhooks** - Push results to any endpoint
- ✅ **CRM Systems** - Salesforce, HubSpot, Pipedrive
- ✅ **ESP Systems** - SendGrid, Mailchimp, Mailgun
- ✅ **CSV Export** - Download validation results
- ✅ **HMAC Signatures** - Secure webhook delivery

### Export Formats
- ✅ Basic CSV (email, valid, confidence)
- ✅ Detailed CSV (all validation checks)
- ✅ Risk Report CSV (risk assessments)
- ✅ Statistics CSV (aggregate data)

## Installation

```bash
pip install -r requirements_dashboard.txt
```

**requirements_dashboard.txt:**
```
flask>=2.0.0
flask-cors>=3.0.0
dnspython>=2.0.0
supabase>=2.0.0
python-dotenv>=1.0.0
APScheduler>=3.10.0
requests>=2.28.0
```

## Quick Start

### 1. Start Dashboard API

```bash
python app_dashboard.py
```

Server: `http://localhost:5002`

### 2. Start React Frontend

```bash
cd frontend
npm start
```

Frontend: `http://localhost:3000`

### 3. Test Integration

```bash
# Test webhook
curl -X POST http://localhost:5002/api/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"url": "https://webhook.site/your-unique-url"}'

# Export CSV
curl -X POST http://localhost:5002/api/export/csv \
  -H "Content-Type: application/json" \
  -d '{"emails": ["user@example.com"], "include_details": true}' \
  --output results.csv
```

## API Endpoints

### Dashboard

#### GET /api/dashboard/stats
Get comprehensive statistics.

**Response:**
```json
{
  "total_validations": 1000,
  "valid_count": 850,
  "invalid_count": 150,
  "avg_confidence": 87.5,
  "high_risk_count": 50,
  "disposable_count": 25,
  "role_based_count": 100
}
```

#### GET /api/dashboard/recent
Get recent validations.

**Query Params:**
- `limit`: Number of records (default: 50)

**Response:**
```json
{
  "total": 50,
  "validations": [...]
}
```

#### POST /api/dashboard/validate
Validate email with full dashboard features.

**Request:**
```json
{
  "email": "user@example.com",
  "enable_smtp": false,
  "assess_risk": true,
  "send_webhook": true,
  "webhook_url": "https://example.com/webhook"
}
```

**Response:**
```json
{
  "email": "user@example.com",
  "valid": true,
  "confidence_score": 95,
  "checks": {...},
  "risk_assessment": {...},
  "webhook_sent": true,
  "stored": true,
  "record_id": 123
}
```

#### POST /api/dashboard/batch
Batch validate with progress.

**Request:**
```json
{
  "emails": ["user1@example.com", "user2@test.com"],
  "advanced": true,
  "assess_risk": true
}
```

### CSV Export

#### POST /api/export/csv
Export validation results to CSV.

**Request:**
```json
{
  "emails": ["user1@example.com", "user2@test.com"],
  "include_details": true
}
```

**Response:** CSV file download

#### POST /api/export/risk-csv
Export risk assessments to CSV.

**Request:**
```json
{
  "emails": ["user1@example.com", "user2@test.com"]
}
```

**Response:** CSV file download

#### GET /api/export/stats-csv
Export statistics to CSV.

**Response:** CSV file download

### Webhooks

#### POST /api/webhook/send
Send data to webhook.

**Request:**
```json
{
  "url": "https://example.com/webhook",
  "data": {
    "email": "user@example.com",
    "valid": true,
    "confidence_score": 95
  },
  "secret": "optional-hmac-secret"
}
```

**Response:**
```json
{
  "success": true,
  "status_code": 200,
  "response": {...},
  "sent_at": "2024-01-01T12:00:00"
}
```

#### POST /api/webhook/test
Test webhook connection.

**Request:**
```json
{
  "url": "https://webhook.site/your-unique-url"
}
```

### CRM/ESP Integration

#### POST /api/integration/crm
Update CRM contact.

**Request:**
```json
{
  "email": "user@example.com",
  "crm_type": "salesforce",
  "api_key": "your-api-key",
  "validation_data": {
    "valid": true,
    "confidence_score": 95
  }
}
```

**Supported CRMs:**
- `salesforce`
- `hubspot`
- `pipedrive`
- `generic`

#### POST /api/integration/esp
Update ESP subscriber.

**Request:**
```json
{
  "email": "user@example.com",
  "esp_type": "sendgrid",
  "api_key": "your-api-key",
  "validation_data": {
    "valid": false,
    "confidence_score": 30
  },
  "list_id": "optional-list-id"
}
```

**Supported ESPs:**
- `sendgrid`
- `mailchimp`
- `mailgun`

## Python Module Usage

### Webhooks

```python
from webhook_integration import WebhookManager

# Initialize
manager = WebhookManager(
    webhook_url='https://example.com/webhook',
    secret='your-secret-key'
)

# Send webhook
result = manager.send_webhook({
    'email': 'user@example.com',
    'valid': True,
    'confidence_score': 95
})

print(f"Sent: {result['success']}")
print(f"Status: {result['status_code']}")
```

### CRM Integration

```python
from webhook_integration import CRMIntegration

# Initialize
crm = CRMIntegration(
    crm_type='salesforce',
    api_key='your-api-key'
)

# Update contact
result = crm.update_contact(
    'user@example.com',
    {
        'valid': True,
        'confidence_score': 95
    }
)

print(f"Updated: {result['success']}")
```

### ESP Integration

```python
from webhook_integration import ESPIntegration

# Initialize
esp = ESPIntegration(
    esp_type='sendgrid',
    api_key='your-api-key'
)

# Update subscriber
result = esp.update_subscriber(
    'user@example.com',
    {'valid': False},
    list_id='list-123'
)

# Suppress invalid email
esp.suppress_invalid_email('invalid@example.com')
```

### CSV Export

```python
from csv_export import export_to_csv

results = [
    {
        'email': 'user1@example.com',
        'valid': True,
        'confidence_score': 95,
        'checks': {
            'syntax': True,
            'dns_valid': True,
            'mx_records': True
        }
    },
    {
        'email': 'user2@example.com',
        'valid': False,
        'confidence_score': 0
    }
]

# Export to CSV
csv_data = export_to_csv(results, include_details=True)

# Save to file
with open('results.csv', 'w') as f:
    f.write(csv_data)
```

## Webhook Security

### HMAC Signatures

Webhooks can be signed with HMAC-SHA256:

```python
manager = WebhookManager(
    webhook_url='https://example.com/webhook',
    secret='your-secret-key'
)

# Signature is automatically added to X-Webhook-Signature header
result = manager.send_webhook(data)
```

### Verify Webhook Signature (Receiver Side)

```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    """Verify webhook signature."""
    payload_str = json.dumps(payload, sort_keys=True)
    expected_signature = hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

# In your webhook endpoint
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.get_json()
    
    if verify_webhook(payload, signature, 'your-secret-key'):
        # Process webhook
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Invalid signature'}), 401
```

## CSV Export Formats

### Basic CSV

```csv
email,valid,confidence_score,validated_at,reason
user@example.com,Yes,95,2024-01-01T12:00:00,Valid email
invalid@,No,0,2024-01-01T12:01:00,Invalid syntax
```

### Detailed CSV

```csv
email,valid,confidence_score,syntax,dns_valid,mx_records,is_disposable,is_role_based,is_catch_all,validated_at
user@example.com,Yes,95,Yes,Yes,Yes,No,No,No,2024-01-01T12:00:00
```

### Risk Report CSV

```csv
email,risk_score,risk_level,is_spam_trap,is_blacklisted,bounce_count,risk_factors,recommendations
user@example.com,45,MEDIUM,No,No,1,"Previous bounce; Catch-all domain","Review required"
```

## React Dashboard

### Features

- **Batch Upload** - Upload CSV files or paste emails
- **Real-time Validation** - See results as they process
- **Statistics Dashboard** - Visual charts and metrics
- **Export Options** - Download results in CSV
- **Webhook Configuration** - Set up webhook endpoints
- **Risk Assessment** - View risk scores and recommendations

### Dashboard Components

```
Dashboard/
├── Statistics Panel
│   ├── Total Validations
│   ├── Valid/Invalid Count
│   ├── Average Confidence
│   └── High Risk Count
│
├── Batch Upload
│   ├── File Upload
│   ├── Text Input
│   └── Progress Bar
│
├── Recent Validations
│   ├── Email List
│   ├── Status Indicators
│   └── Risk Levels
│
└── Export & Integration
    ├── CSV Export
    ├── Webhook Config
    └── CRM/ESP Setup
```

## Testing

### Run Unit Tests

```bash
python test_integration.py
```

### Test Coverage

- ✅ Webhook send success/failure
- ✅ Webhook timeout handling
- ✅ HMAC signature generation
- ✅ CRM integration (Salesforce, HubSpot)
- ✅ ESP integration (SendGrid, Mailchimp)
- ✅ CSV export (basic, detailed, risk)
- ✅ Dashboard API data fetching

**Result:** 19/19 tests passed ✅

## Integration Examples

### Example 1: Validate and Push to Webhook

```python
from email_validator_smtp import validate_email_with_smtp
from webhook_integration import WebhookManager

# Validate
result = validate_email_with_smtp('user@example.com')

# Push to webhook
webhook = WebhookManager('https://example.com/webhook')
webhook.send_webhook(result)
```

### Example 2: Batch Validate and Export CSV

```python
from emailvalidator_unified import validate_batch
from csv_export import export_to_csv

# Validate batch
emails = ['user1@example.com', 'user2@test.com']
results = validate_batch(emails, advanced=True)

# Export to CSV
csv_data = export_to_csv(results, include_details=True)

# Save file
with open('batch_results.csv', 'w') as f:
    f.write(csv_data)
```

### Example 3: Validate and Update CRM

```python
from email_validator_smtp import validate_email_with_smtp
from webhook_integration import CRMIntegration

# Validate
result = validate_email_with_smtp('user@example.com')

# Update CRM
crm = CRMIntegration('salesforce', 'your-api-key')
crm.update_contact('user@example.com', result)
```

### Example 4: Suppress Invalid Emails in ESP

```python
from emailvalidator_unified import validate_batch
from webhook_integration import ESPIntegration

# Validate batch
results = validate_batch(emails)

# Suppress invalid emails
esp = ESPIntegration('sendgrid', 'your-api-key')

for result in results:
    if not result['valid']:
        esp.suppress_invalid_email(result['email'])
```

## Environment Variables

Add to `.env`:

```bash
# Webhook Configuration
WEBHOOK_URL=https://example.com/webhook
WEBHOOK_SECRET=your-secret-key

# CRM Configuration
CRM_TYPE=salesforce
CRM_API_KEY=your-crm-api-key
CRM_API_URL=https://api.salesforce.com

# ESP Configuration
ESP_TYPE=sendgrid
ESP_API_KEY=your-esp-api-key
```

## Troubleshooting

### Webhook Not Receiving Data

**Problem:** Webhook endpoint not receiving data

**Solutions:**
- Test webhook URL: `POST /api/webhook/test`
- Check firewall settings
- Verify webhook URL is accessible
- Check webhook logs for errors

### CSV Export Empty

**Problem:** CSV export returns empty file

**Solutions:**
- Verify emails exist in database
- Check email addresses are correct
- Ensure validation has been run first

### CRM/ESP Integration Fails

**Problem:** CRM or ESP update fails

**Solutions:**
- Verify API key is correct
- Check API permissions
- Ensure contact/subscriber exists
- Review CRM/ESP API documentation

## Production Deployment

### Security Checklist

- [ ] Use HTTPS for all webhook URLs
- [ ] Enable HMAC signatures for webhooks
- [ ] Store API keys in environment variables
- [ ] Implement rate limiting
- [ ] Add authentication to dashboard
- [ ] Enable CORS only for trusted domains
- [ ] Use service_role key for Supabase
- [ ] Implement webhook retry logic
- [ ] Add logging and monitoring
- [ ] Set up error tracking

### Performance Optimization

- [ ] Cache validation results
- [ ] Use batch operations
- [ ] Implement pagination
- [ ] Add database indexes
- [ ] Use CDN for frontend
- [ ] Enable gzip compression
- [ ] Optimize CSV generation
- [ ] Use async webhook delivery

## License

MIT License - Free to use in your projects

## Next Steps

1. ✅ Run tests: `python test_integration.py`
2. ✅ Start API: `python app_dashboard.py`
3. ✅ Configure webhooks
4. ✅ Set up CRM/ESP integrations
5. ✅ Test CSV export
6. ✅ Deploy to production

You're ready to integrate! 🚀
