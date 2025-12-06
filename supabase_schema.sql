-- ============================================================================
-- Supabase Schema for Email Validation Storage
-- Run this SQL in Supabase SQL Editor to create the table and indexes
-- ============================================================================

-- Create email_validations table
CREATE TABLE IF NOT EXISTS email_validations (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,
    
    -- Anonymous User ID (for private history without login)
    anon_user_id VARCHAR(36) NOT NULL,
    
    -- Email information
    email VARCHAR(255) NOT NULL,
    valid BOOLEAN NOT NULL,
    confidence_score INTEGER NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 100),
    
    -- Validation details (stored as JSON)
    checks JSONB DEFAULT '{}',
    smtp_details JSONB,
    
    -- Flags
    is_disposable BOOLEAN DEFAULT FALSE,
    is_role_based BOOLEAN DEFAULT FALSE,
    is_catch_all BOOLEAN DEFAULT FALSE,
    
    -- Bounce tracking
    bounce_count INTEGER DEFAULT 0,
    last_bounce_date TIMESTAMP,
    
    -- Additional information
    notes TEXT DEFAULT '',
    
    -- Timestamps
    validated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Create Indexes for Performance
-- ============================================================================

-- Index for anonymous user ID lookups (CRITICAL for user-specific queries)
CREATE INDEX IF NOT EXISTS idx_anon_user_id ON email_validations(anon_user_id);

-- Composite index for user history queries (user + date) - MOST IMPORTANT
CREATE INDEX IF NOT EXISTS idx_user_validated ON email_validations(anon_user_id, validated_at DESC);

-- Index for email lookups (most common query)
CREATE INDEX IF NOT EXISTS idx_email ON email_validations(email);

-- Index for filtering by validation status
CREATE INDEX IF NOT EXISTS idx_valid ON email_validations(valid);

-- Index for filtering by confidence score
CREATE INDEX IF NOT EXISTS idx_confidence ON email_validations(confidence_score);

-- Index for sorting by validation date (descending)
CREATE INDEX IF NOT EXISTS idx_validated_at ON email_validations(validated_at DESC);

-- Composite index for email history queries (email + date)
CREATE INDEX IF NOT EXISTS idx_email_validated ON email_validations(email, validated_at DESC);

-- ============================================================================
-- Enable Row Level Security (RLS)
-- ============================================================================

ALTER TABLE email_validations ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Create Security Policies
-- ============================================================================

-- Policy 1: Allow all operations (for development/testing)
-- WARNING: This allows anyone to read/write. Adjust for production!
CREATE POLICY "Allow all operations" ON email_validations
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- Alternative Policies (Uncomment for production)
-- ============================================================================

-- Policy 2: Only authenticated users can access (recommended for production)
-- DROP POLICY "Allow all operations" ON email_validations;
-- CREATE POLICY "Authenticated access" ON email_validations
--     FOR ALL
--     USING (auth.role() = 'authenticated')
--     WITH CHECK (auth.role() = 'authenticated');

-- Policy 3: Read-only for anonymous, full access for authenticated
-- DROP POLICY "Allow all operations" ON email_validations;
-- CREATE POLICY "Anonymous read" ON email_validations
--     FOR SELECT
--     USING (true);
-- 
-- CREATE POLICY "Authenticated write" ON email_validations
--     FOR INSERT
--     WITH CHECK (auth.role() = 'authenticated');
-- 
-- CREATE POLICY "Authenticated update" ON email_validations
--     FOR UPDATE
--     USING (auth.role() = 'authenticated')
--     WITH CHECK (auth.role() = 'authenticated');
-- 
-- CREATE POLICY "Authenticated delete" ON email_validations
--     FOR DELETE
--     USING (auth.role() = 'authenticated');

-- ============================================================================
-- Verify Table Creation
-- ============================================================================

-- Check if table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'email_validations'
) AS table_exists;

-- Check indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'email_validations';

-- Check RLS status
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'email_validations';

-- ============================================================================
-- Sample Queries (for testing)
-- ============================================================================

-- Insert sample record
-- INSERT INTO email_validations (email, valid, confidence_score, checks)
-- VALUES ('test@example.com', true, 95, '{"syntax": true, "dns_valid": true}');

-- Query all records
-- SELECT * FROM email_validations ORDER BY validated_at DESC LIMIT 10;

-- Query by email
-- SELECT * FROM email_validations WHERE email = 'test@example.com';

-- Get statistics
-- SELECT 
--     COUNT(*) as total,
--     SUM(CASE WHEN valid THEN 1 ELSE 0 END) as valid_count,
--     AVG(confidence_score) as avg_confidence
-- FROM email_validations;

-- ============================================================================
-- Cleanup (if needed)
-- ============================================================================

-- Drop table (WARNING: This deletes all data!)
-- DROP TABLE IF EXISTS email_validations CASCADE;

-- ============================================================================
-- Notes
-- ============================================================================

-- 1. Run this SQL in Supabase SQL Editor
-- 2. Verify table creation with the verification queries above
-- 3. Adjust RLS policies based on your security requirements
-- 4. For production, use more restrictive policies
-- 5. Consider adding more indexes based on your query patterns
-- 6. Set up database backups in Supabase dashboard

-- ============================================================================
-- End of Schema
-- ============================================================================
