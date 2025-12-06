# Email Validator with Supabase Storage

Complete email validation system with persistent storage using Supabase. Store validation results, track bounce history, and manage email validation records via REST API.

## Features

### Validation Features
- ✅ RFC 5321 syntax validation
- ✅ DNS/MX record checking
- ✅ SMTP mailbox verification
- ✅ Catch-all domain detection
- ✅ Disposable email detection
- ✅ Role-based email detection
- ✅ Confidence scoring (0-100)

### Storage Features
- ✅ Persistent validation records in Supabase
- ✅ Validation history tracking
- ✅ Bounce count tracking
- ✅ CRUD operations via REST API
- ✅ Search and filter records
- ✅ Statistics and analytics
- ✅ Automatic re-verification scheduling

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements_supabase.txt
```

**requirements_supabase.txt:**
```
flask>=2.0.0
flask-cors>=3.0.0
dnspython>=2.0.0
supabase>=2.0.0
python-dotenv>=1.0.0
APScheduler>=3.10.0
```

### 2. Supabase Setup

#### Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Create a new project
3. Note your **Project URL** and **API Key**

#### Create Database Table

Run this SQL in Supabase SQL Editor:

```sql
-- Create email_validations table
CREATE TABLE email_validations (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    valid BOOLEAN NOT NULL,
    confidence_score INTEGER NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 100),
    checks JSONB DEFAULT '{}',
    smtp_details JSONB,
    is_disposable BOOLEAN DEFAULT FALSE,
    is_role_based BOOLEAN DEFAULT FALSE,
    is_catch_all BOOLEAN DEFAULT FALSE,
    bounce_count INTEGER DEFAULT 0,
    last_bounce_date TIMESTAMP,
    notes TEXT DEFAULT '',
    validated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_email ON email_validations(email);
CREATE INDEX idx_valid ON email_validations(valid);
CREATE INDEX idx_confidence ON email_validations(confidence_score);
CREATE INDEX idx_validated_at ON email_validations(validated_at DESC);
CREATE INDEX idx_email_validated ON email_validations(email, validated_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE email_validations ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust based on your security needs)
CREATE POLICY "Allow all operations" ON email_validations
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Optional: Create policy for authenticated users only
-- CREATE POLICY "Allow authenticated users" ON email_validations
--     FOR ALL
--     USING (auth.role() = 'authenticated')
--     WITH CHECK (auth.role() = 'authenticated');
```

#### Get API Credentials

1. Go to **Settings** → **API**
2. Copy your **Project URL**: `https://xxxxx.supabase.co`
3. Copy your **anon/public key** (for client-side) or **service_role key** (for server-side)

### 3. Environment Configuration

Create `.env` file in project root:

```bash
# Supabase Configuration
SUPABASE_URL=https://yhvfpkwrzgdgkgbdzxlp.supabase.co
SUPABASE_KEY=your-api-key-here
SUPABASE_TABLE_NAME=email_validations
```

**Security Note:** 
- Use **anon key** for client-side applications
- Use **service_role key** for server-side applications (more permissions)
- Never commit `.env` to version control
- Add `.env` to `.gitignore`

## Quick Start

### 1. Start the API Server

```bash
python app_supabase.py
```

Server runs at: `http://localhost:5000`

### 2. Test the API

#### Validate and Store Email

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
  "stored": true,
  "record_id": 1,
  "timestamp": 1234567890.123
}
```

#### Get Validation History

```bash
curl http://localhost:5000/api/history/user@example.com
```

**Response:**
```json
{
  "email": "user@example.com",
  "total": 3,
  "history": [
    {
      "id": 3,
      "email": "user@example.com",
      "valid": true,
      "confidence_score": 95,
      "validated_at": "2024-01-03T12:00:00"
    },
    {
      "id": 2,
      "email": "user@example.com",
      "valid": true,
      "confidence_score": 90,
      "validated_at": "2024-01-02T12:00:00"
    }
  ]
}
```

## API Endpoints

### Validation + Storage

#### POST /api/validate
Validate email and store result (basic validation).

**Request:**
```json
{
  "email": "user@example.com",
  "store": true
}
```

**Response:**
```json
{
  "email": "user@example.com",
  "valid": true,
  "stored": true,
  "record_id": 123,
  "processing_time": 0.001
}
```

#### POST /api/validate/smtp
Validate with SMTP and store complete result.

**Request:**
```json
{
  "email": "user@gmail.com",
  "enable_smtp": true,
  "store": true
}
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
  "stored": true,
  "record_id": 123
}
```

#### POST /api/validate/batch
Validate and store multiple emails.

**Request:**
```json
{
  "emails": ["user1@example.com", "user2@test.com"],
  "advanced": false,
  "store": true
}
```

**Response:**
```json
{
  "total": 2,
  "valid_count": 2,
  "stored_count": 2,
  "results": [...]
}
```

### CRUD Operations

#### GET /api/records
Get all records with pagination.

**Query Parameters:**
- `limit`: Number of records (default: 100, max: 1000)
- `offset`: Skip records (default: 0)

```bash
curl "http://localhost:5000/api/records?limit=50&offset=0"
```

#### GET /api/records/<email>
Get most recent record for an email.

```bash
curl http://localhost:5000/api/records/user@example.com
```

#### GET /api/records/id/<id>
Get specific record by ID.

```bash
curl http://localhost:5000/api/records/id/123
```

#### PUT /api/records/<id>
Update a record.

**Request:**
```json
{
  "confidence_score": 85,
  "bounce_count": 1,
  "notes": "Updated after bounce"
}
```

```bash
curl -X PUT http://localhost:5000/api/records/123 \
  -H "Content-Type: application/json" \
  -d '{"confidence_score": 85}'
```

#### DELETE /api/records/<id>
Delete a record.

```bash
curl -X DELETE http://localhost:5000/api/records/123
```

### History & Analytics

#### GET /api/history/<email>
Get validation history for an email.

**Query Parameters:**
- `limit`: Number of records (default: 10)

```bash
curl "http://localhost:5000/api/history/user@example.com?limit=5"
```

#### GET /api/statistics
Get validation statistics.

```bash
curl http://localhost:5000/api/statistics
```

**Response:**
```json
{
  "total_validations": 1000,
  "valid_count": 850,
  "invalid_count": 150,
  "avg_confidence": 87.5,
  "disposable_count": 50,
  "role_based_count": 100
}
```

#### POST /api/search
Search records with filters.

**Request:**
```json
{
  "valid": true,
  "min_confidence": 80,
  "max_confidence": 100,
  "is_disposable": false,
  "limit": 100
}
```

### Bounce Tracking

#### POST /api/bounce/<email>
Record an email bounce.

**Request:**
```json
{
  "notes": "Hard bounce - mailbox full"
}
```

**Response:**
```json
{
  "email": "user@example.com",
  "bounce_count": 2,
  "last_bounce_date": "2024-01-01T12:00:00"
}
```

### Re-verification Scheduling

#### POST /api/schedule-reverify
Schedule automatic re-verification.

**Request:**
```json
{
  "email": "user@example.com",
  "days": 30
}
```

**Response:**
```json
{
  "success": true,
  "email": "user@example.com",
  "scheduled_for": "2024-02-01T12:00:00",
  "days": 30
}
```

## Python Module Usage

### Basic Storage Operations

```python
from supabase_storage import SupabaseStorage

# Initialize storage
storage = SupabaseStorage()

# Create record
record = storage.create_record({
    'email': 'user@example.com',
    'valid': True,
    'confidence_score': 95,
    'checks': {'syntax': True, 'dns_valid': True}
})
print(f"Created record ID: {record['id']}")

# Get record
record = storage.get_record_by_email('user@example.com')
print(f"Confidence: {record['confidence_score']}")

# Update record
updated = storage.update_record(record['id'], {
    'confidence_score': 85,
    'notes': 'Updated'
})

# Delete record
storage.delete_record(record['id'])
```

### Validation History

```python
from supabase_storage import SupabaseStorage

storage = SupabaseStorage()

# Get history
history = storage.get_validation_history('user@example.com', limit=10)

for record in history:
    print(f"{record['validated_at']}: Score {record['confidence_score']}")
```

### Bounce Tracking

```python
from supabase_storage import SupabaseStorage

storage = SupabaseStorage()

# Increment bounce count
result = storage.increment_bounce_count('user@example.com')
print(f"Bounce count: {result['bounce_count']}")
print(f"Last bounce: {result['last_bounce_date']}")
```

### Search and Filter

```python
from supabase_storage import SupabaseStorage

storage = SupabaseStorage()

# Find all valid emails with high confidence
records = storage.search_records(
    valid=True,
    min_confidence=80,
    is_disposable=False
)

print(f"Found {len(records)} high-quality emails")
```

### Statistics

```python
from supabase_storage import SupabaseStorage

storage = SupabaseStorage()

stats = storage.get_statistics()
print(f"Total validations: {stats['total_validations']}")
print(f"Valid: {stats['valid_count']}")
print(f"Average confidence: {stats['avg_confidence']}")
```

## Database Schema

### Table: email_validations

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Primary key |
| email | VARCHAR(255) | Email address (indexed) |
| valid | BOOLEAN | Validation status |
| confidence_score | INTEGER | Score 0-100 |
| checks | JSONB | Validation checks details |
| smtp_details | JSONB | SMTP verification details |
| is_disposable | BOOLEAN | Disposable email flag |
| is_role_based | BOOLEAN | Role-based email flag |
| is_catch_all | BOOLEAN | Catch-all domain flag |
| bounce_count | INTEGER | Number of bounces |
| last_bounce_date | TIMESTAMP | Last bounce timestamp |
| notes | TEXT | Additional notes |
| validated_at | TIMESTAMP | Validation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| created_at | TIMESTAMP | Record creation timestamp |

### Indexes

- `idx_email` - Fast email lookups
- `idx_valid` - Filter by validation status
- `idx_confidence` - Filter by confidence score
- `idx_validated_at` - Sort by validation date
- `idx_email_validated` - Composite index for history queries

## Testing

### Run Unit Tests

```bash
python test_storage.py
```

### Test Coverage

The test suite includes:
- ✅ Insert email record
- ✅ Update confidence score
- ✅ Fetch validation history
- ✅ Delete record
- ✅ Bounce count tracking
- ✅ Search and filter
- ✅ Statistics calculation
- ✅ Error handling
- ✅ Full CRUD cycle

### Example Test Output

```
test_create_record ... ok
test_get_record_by_email ... ok
test_get_validation_history ... ok
test_update_record ... ok
test_increment_bounce_count ... ok
test_delete_record ... ok
test_get_statistics ... ok
test_search_records_by_valid ... ok

======================================================================
TEST SUMMARY
======================================================================
Tests run: 16
Successes: 16
Failures: 0
Errors: 0
======================================================================
```

## Security Best Practices

### 1. Environment Variables

Never hardcode credentials:

```python
# ❌ Bad
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# ✅ Good
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
```

### 2. Row Level Security (RLS)

Enable RLS in Supabase:

```sql
ALTER TABLE email_validations ENABLE ROW LEVEL SECURITY;

-- Only authenticated users can access
CREATE POLICY "Authenticated access" ON email_validations
    FOR ALL
    USING (auth.role() = 'authenticated');
```

### 3. API Key Types

- **anon key**: Client-side, limited permissions
- **service_role key**: Server-side, full permissions

Use service_role key for backend applications.

### 4. Rate Limiting

Implement rate limiting in production:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/validate', methods=['POST'])
@limiter.limit("100 per hour")
def validate_and_store():
    # ...
```

## Re-verification Scheduling

### Automatic Re-verification

Schedule emails for automatic re-verification:

```python
from app_supabase import scheduler, reverify_email
from datetime import datetime, timedelta

# Schedule re-verification in 30 days
run_date = datetime.now() + timedelta(days=30)
scheduler.add_job(
    func=reverify_email,
    trigger='date',
    run_date=run_date,
    args=['user@example.com']
)
```

### Via API

```bash
curl -X POST http://localhost:5000/api/schedule-reverify \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "days": 30}'
```

### Cron-based Re-verification

Use Supabase Edge Functions or external cron:

```sql
-- Find emails that need re-verification (validated > 30 days ago)
SELECT email
FROM email_validations
WHERE validated_at < NOW() - INTERVAL '30 days'
AND valid = true
GROUP BY email;
```

## Performance Optimization

### 1. Batch Operations

Use batch validation for multiple emails:

```python
emails = ["user1@example.com", "user2@example.com", ...]
results = validate_batch(emails, store=True)
```

### 2. Caching

Cache validation results:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_validation(email):
    storage = get_storage()
    return storage.get_record_by_email(email)
```

### 3. Pagination

Always use pagination for large datasets:

```python
# Get records in batches
limit = 100
offset = 0

while True:
    records = storage.get_all_records(limit=limit, offset=offset)
    if not records:
        break
    
    process_records(records)
    offset += limit
```

### 4. Indexes

Ensure proper indexes exist (already created in setup SQL).

## Troubleshooting

### Connection Error

**Problem:** `Failed to connect to Supabase`

**Solutions:**
- Check `SUPABASE_URL` is correct
- Check `SUPABASE_KEY` is valid
- Verify network connectivity
- Check Supabase project is active

### Missing Table

**Problem:** `relation "email_validations" does not exist`

**Solution:**
- Run the table creation SQL in Supabase SQL Editor
- Verify table name matches `SUPABASE_TABLE_NAME` in `.env`

### Permission Denied

**Problem:** `new row violates row-level security policy`

**Solution:**
- Check RLS policies in Supabase
- Use service_role key for backend operations
- Adjust policies based on your security needs

### Rate Limiting

**Problem:** Too many requests

**Solution:**
- Implement caching
- Use batch operations
- Add rate limiting
- Upgrade Supabase plan

## Examples

### Example 1: User Registration

```python
from email_validator_smtp import validate_email_with_smtp
from supabase_storage import get_storage

def register_user(email, password):
    # Validate email
    result = validate_email_with_smtp(email, enable_smtp=True)
    
    if not result['valid']:
        return {"error": f"Invalid email: {result['reason']}"}
    
    if result['checks']['is_disposable']:
        return {"error": "Disposable emails not allowed"}
    
    # Store validation
    storage = get_storage()
    storage.create_record({
        'email': email,
        'valid': result['valid'],
        'confidence_score': result['confidence_score'],
        'checks': result['checks']
    })
    
    # Create account
    create_account(email, password)
    return {"success": True}
```

### Example 2: Email Bounce Handler

```python
from supabase_storage import get_storage

def handle_bounce(email, bounce_type):
    storage = get_storage()
    
    # Increment bounce count
    result = storage.increment_bounce_count(email)
    
    # If too many bounces, mark as invalid
    if result['bounce_count'] >= 3:
        storage.update_by_email(email, {
            'valid': False,
            'confidence_score': 0,
            'notes': f'Disabled after {result["bounce_count"]} bounces'
        })
        
        # Remove from mailing list
        remove_from_list(email)
```

### Example 3: Email List Cleaning

```python
from supabase_storage import get_storage

def clean_email_list():
    storage = get_storage()
    
    # Find low-quality emails
    bad_emails = storage.search_records(
        valid=False,
        limit=1000
    )
    
    # Find high bounce count
    bounced = storage.search_records(
        min_confidence=0,
        max_confidence=50,
        limit=1000
    )
    
    # Remove from mailing list
    for record in bad_emails + bounced:
        remove_from_list(record['email'])
    
    print(f"Cleaned {len(bad_emails) + len(bounced)} emails")
```

## Deployment

### Environment Variables

Set these in your production environment:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_TABLE_NAME=email_validations
```

### Production Checklist

- [ ] Use service_role key (not anon key)
- [ ] Enable RLS with proper policies
- [ ] Set up database backups
- [ ] Implement rate limiting
- [ ] Add monitoring and logging
- [ ] Use HTTPS for API
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Configure CORS properly
- [ ] Add API authentication
- [ ] Set up CI/CD pipeline

## License

MIT License - Free to use in your projects

## Support

For issues or questions:
- Check troubleshooting section
- Review API documentation
- Run unit tests
- Check Supabase logs

## Changelog

### Version 4.0.0
- ✨ Added Supabase integration
- ✨ Persistent storage for validation results
- ✨ Validation history tracking
- ✨ Bounce count tracking
- ✨ CRUD REST API
- ✨ Search and filter capabilities
- ✨ Statistics and analytics
- ✨ Re-verification scheduling
- ✅ Complete test coverage
- 📝 Comprehensive documentation

## Next Steps

1. ✅ Set up Supabase project
2. ✅ Create database table
3. ✅ Configure environment variables
4. ✅ Run tests
5. ✅ Start API server
6. ✅ Test endpoints
7. ✅ Deploy to production

You're ready to go! 🚀
