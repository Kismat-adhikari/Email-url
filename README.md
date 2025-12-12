# 📧 Email Validator - Full Stack Application

A production-ready email validation platform with React frontend and Flask backend, featuring anonymous user history, risk scoring, and email enrichment.

## 🌟 Features

### Validation
- ✅ **RFC 5321 Syntax Validation** - Comprehensive email format checking
- ✅ **DNS/MX Record Verification** - Check if domain exists and accepts mail
- ✅ **SMTP Mailbox Verification** - Verify actual mailbox existence
- ✅ **Disposable Email Detection** - Identify temporary email services
- ✅ **Role-based Email Detection** - Flag generic addresses (info@, admin@)
- ✅ **Typo Suggestions** - Smart corrections for common domain typos
- ✅ **Catch-all Domain Detection** - Identify domains that accept all emails

### Intelligence & Risk Management
- 🎯 **Risk Scoring (0-100)** - Assess email deliverability risk
- 📊 **Email Enrichment** - Domain classification, geolocation, engagement scoring
- 📈 **Confidence Scoring** - Multi-factor validation confidence rating
- 🚫 **Advanced Bounce Tracking** - Real-time bounce monitoring and history
- ⚠️ **Bounce Risk Assessment** - Automatic risk categorization (low/medium/high/critical)
- 📡 **Webhook Integration** - SendGrid, Mailgun, and custom ESP support
- 🔄 **Automated Bounce Recording** - Seamless integration with email service providers

### User Experience
- 🔐 **Anonymous User History** - Private history without login (localStorage UUID)
- 📱 **Modern React Dashboard** - Clean, responsive UI with dark mode
- 📦 **Batch Processing** - Validate multiple emails at once
- 📁 **File Upload Support** - Upload .txt files for bulk validation
- 💾 **Supabase Integration** - Persistent storage with analytics
- 🎛️ **Bounce Management Dashboard** - Monitor and manage bounce activity

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### 2. Configure Supabase

Create a `.env` file:

```bash
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
SUPABASE_TABLE_NAME=email_validations
```

### 3. Setup Database

Run the SQL schema in your Supabase project:

```sql
-- See supabase_schema.sql for complete schema
-- Then run supabase_migration_anon_id.sql for anonymous user support
```

### 4. Start the Application

**Option A: Complete System (Recommended)**
```bash
# Starts main API + bounce service + frontend
start_complete_system.bat
```

**Option B: Individual Services**
```bash
# Terminal 1 - Main API
python app_anon_history.py

# Terminal 2 - Frontend (if developing)
cd frontend && npm start

# Terminal 3 - Frontend
cd frontend
npm start
```

**Option C: Legacy (Main API only)**
```bash
START_ANON_HISTORY.bat
```

### 5. Open Your Browser

- **Frontend**: http://localhost:3000
- **Main API**: http://localhost:5000  
- **Bounce Service**: http://localhost:5001

## 🎯 API Endpoints

### Email Validation
```bash
# Single email validation
POST /api/validate
Body: { "email": "test@example.com" }

# Advanced validation with all checks
POST /api/validate/advanced  
Body: { "email": "test@example.com" }

# Batch validation
POST /api/validate/batch
Body: { "emails": ["email1@test.com", "email2@test.com"] }

# Get validation history
GET /api/history
Headers: X-User-ID: <anonymous_user_id>
```

### Bounce Management
```bash
# Get bounce statistics
GET /api/bounce/stats

# Record bounce manually
POST /api/bounce/record
Body: { "email": "user@example.com", "bounce_type": "hard", "reason": "Domain not found" }

# Get bounce history for email
GET /api/bounce/history/<email>
```

### Bounce Webhooks (Port 5001)
```bash
# SendGrid bounce webhook
POST /webhook/sendgrid/bounce

# Mailgun bounce webhook  
POST /webhook/mailgun/bounce

# Generic bounce webhook
POST /webhook/generic/bounce
Body: { "email": "user@example.com", "bounce_type": "hard", "reason": "550 User unknown" }

# Test bounce webhook
POST /webhook/test
Body: { "email": "test@example.com", "bounce_type": "hard", "reason": "Test bounce" }

# Webhook service stats
GET /webhook/stats
```

## 📁 Project Structure

```
email-validator/
├── app_anon_history.py          # Main Flask API with anonymous history
├── emailvalidator_unified.py    # Core validation engine
├── email_validator_smtp.py      # SMTP verification
├── email_sender.py              # Email sending with integrated bounce tracking (NEW)
├── risk_scoring.py              # Risk assessment engine
├── email_enrichment.py          # Domain enrichment
├── supabase_storage.py          # Database operations
├── start_complete_system.bat    # Complete system startup (NEW)
├── start_bounce_service.bat     # Bounce service startup (NEW)
├── BOUNCE_TRACKING_GUIDE.md     # Bounce tracking documentation (NEW)
├── .env                         # Configuration (create this)
├── requirements.txt             # Python dependencies
├── supabase_schema.sql          # Database schema
├── supabase_migration_anon_id.sql  # Anonymous user migration
├── README.md                    # This file
└── frontend/                    # React application
    ├── src/
    │   ├── App.js              # Main React component
    │   ├── BounceManager.js    # Bounce management dashboard (NEW)
    │   ├── BounceManager.css   # Bounce dashboard styling (NEW)
    │   └── App.css             # Styling
    ├── public/
    └── package.json
```

## 🚫 Bounce Tracking System

### Quick Start
```bash
# Test integrated bounce tracking
curl -X POST http://localhost:5000/webhook/test/bounce \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "bounce_type": "hard", "reason": "Test bounce"}'
python manage_bounces.py record test@invalid.com --type hard --reason "Domain not found"

# Check bounce history
python manage_bounces.py history test@invalid.com

# View bounce statistics
python manage_bounces.py stats
```

### Webhook Integration
Configure your email service provider to send bounce notifications:

**SendGrid**: `POST http://yourdomain.com/webhook/sendgrid/bounce`
**Mailgun**: `POST http://yourdomain.com/webhook/mailgun/bounce`
**Custom ESP**: `POST http://yourdomain.com/webhook/generic/bounce`

### Management Dashboard
Access the bounce management dashboard at http://localhost:3000 → "Bounce Manager" tab

## 🎯 API Endpoints

### Validation
```bash
# Single email validation
POST /api/validate
Body: { "email": "test@example.com" }

# Advanced validation
POST /api/validate/advanced
Body: { "email": "test@example.com

1. **Input Handler** - File loading with comprehensive error handling
2. **Validator Logic** - Pure functions with modular validation rules
3. **Output Reporter** - Clean terminal output with summary statistics

## Error Handling

The validator provides clear, actionable error messages:

- Missing file
- Permission denied
- Invalid encoding
- Empty file
- Missing arguments

## Limitations

This is an **intermediate-level** validator that intentionally does not support:

- Unicode/international characters (ASCII-only)
- Quoted strings in local part
- IP addresses in domain part
- Comments in email addresses
- DNS/MX record validation
- Deliverability checking

These limitations are by design for simplicity, performance, and maintainability.

## Examples

### Valid Emails

```
user@example.com
john.doe@company.co.uk
alice_smith@test-domain.org
bob+filter@mail.example.com
admin@subdomain.example.com
test123@numbers456.com
a@bc.de
```

### Invalid Emails

```
user@example              # No TLD
.user@example.com         # Leading dot
user..name@example.com    # Consecutive dots
user name@example.com     # Space in email
user@-example.com         # Hyphen at start of label
user@@example.com         # Multiple @ symbols
```

## Contributing

Contributions are welcome! Please ensure:

- Code follows existing style and architecture
- All test cases pass
- New features include test cases
- Documentation is updated

## License

MIT License - feel free to use in your projects!

## Author

Kismat Adhikari

## Acknowledgments

Built with clean code principles and production-ready practices.
