# Quick Start - Supabase Integration

Get your email validator with Supabase storage running in 10 minutes.

## Step 1: Install Dependencies

```bash
pip install -r requirements_supabase.txt
```

## Step 2: Set Up Supabase

### Create Project
1. Go to [https://supabase.com](https://supabase.com)
2. Click "New Project"
3. Fill in project details
4. Wait for project to be ready (~2 minutes)

### Create Table
1. Go to **SQL Editor** in Supabase dashboard
2. Copy and paste this SQL:

```sql
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

CREATE INDEX idx_email ON email_validations(email);
CREATE INDEX idx_validated_at ON email_validations(validated_at DESC);

ALTER TABLE email_validations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations" ON email_validations
    FOR ALL USING (true) WITH CHECK (true);
```

3. Click "Run"

### Get API Credentials
1. Go to **Settings** → **API**
2. Copy **Project URL**
3. Copy **anon public** key

## Step 3: Configure Environment

Create `.env` file:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_TABLE_NAME=email_validations
```

**Note:** Your credentials are already in `.env` file!

## Step 4: Run Tests

```bash
python test_storage.py
```

Expected: **15 tests passed** ✓

## Step 5: Start API Server

```bash
python app_supabase.py
```

Server runs at: `http://localhost:5000`

## Step 6: Test the API

### Validate and Store Email

```bash
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"user@example.com\"}"
```

### Get Validation History

```bash
curl http://localhost:5000/api/history/user@example.com
```

### Get Statistics

```bash
curl http://localhost:5000/api/statistics
```

## Quick Examples

### Python - Store Validation

```python
from supabase_storage import get_storage

storage = get_storage()

# Create record
record = storage.create_record({
    'email': 'user@example.com',
    'valid': True,
    'confidence_score': 95
})

print(f"Stored with ID: {record['id']}")
```

### Python - Get History

```python
from supabase_storage import get_storage

storage = get_storage()

history = storage.get_validation_history('user@example.com')

for record in history:
    print(f"{record['validated_at']}: {record['confidence_score']}")
```

### Python - Track Bounces

```python
from supabase_storage import get_storage

storage = get_storage()

result = storage.increment_bounce_count('user@example.com')
print(f"Bounce count: {result['bounce_count']}")
```

## Verify in Supabase

1. Go to **Table Editor** in Supabase dashboard
2. Select `email_validations` table
3. See your validation records!

## Next Steps

- Read full documentation: `README_SUPABASE.md`
- Explore API endpoints: `http://localhost:5000/api`
- Check validation history in Supabase dashboard
- Set up re-verification scheduling

## Troubleshooting

### Can't connect to Supabase
- Check `.env` file has correct URL and KEY
- Verify Supabase project is active
- Check internet connection

### Table doesn't exist
- Run the SQL in Supabase SQL Editor
- Verify table name is `email_validations`

### Tests failing
- Install all dependencies: `pip install -r requirements_supabase.txt`
- Check `.env` file exists

## You're Ready! 🚀

Your email validator with Supabase storage is now running!

Try validating some emails and check the results in your Supabase dashboard.
