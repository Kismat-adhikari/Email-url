-- ============================================================================
-- Supabase Migration: Add Anonymous User ID Support
-- Run this to upgrade existing email_validations table
-- ============================================================================

-- Step 1: Add anon_user_id column
-- ============================================================================
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'email_validations' 
        AND column_name = 'anon_user_id'
    ) THEN
        ALTER TABLE email_validations 
        ADD COLUMN anon_user_id VARCHAR(36);
        
        RAISE NOTICE 'Added anon_user_id column';
    ELSE
        RAISE NOTICE 'anon_user_id column already exists';
    END IF;
END $$;

-- Step 2: Populate existing records with default/random IDs
-- ============================================================================
-- Option A: Use a single 'legacy' ID for all existing records
-- UPDATE email_validations 
-- SET anon_user_id = 'legacy-user-00000000-0000-0000-0000-000000000000'
-- WHERE anon_user_id IS NULL;

-- Option B: Generate unique random IDs for existing records (RECOMMENDED)
UPDATE email_validations 
SET anon_user_id = gen_random_uuid()::text 
WHERE anon_user_id IS NULL;

-- Step 3: Make column NOT NULL (after populating existing records)
-- ============================================================================
ALTER TABLE email_validations 
ALTER COLUMN anon_user_id SET NOT NULL;

-- Step 4: Create indexes for performance
-- ============================================================================

-- Index for anonymous user ID lookups (CRITICAL)
CREATE INDEX IF NOT EXISTS idx_anon_user_id 
ON email_validations(anon_user_id);

-- Composite index for user history queries (MOST IMPORTANT)
CREATE INDEX IF NOT EXISTS idx_user_validated 
ON email_validations(anon_user_id, validated_at DESC);

-- Step 5: Verify migration
-- ============================================================================

-- Check column exists
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'email_validations' 
AND column_name = 'anon_user_id';

-- Check indexes
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'email_validations'
AND indexname LIKE '%anon%';

-- Count records with anon_user_id
SELECT 
    COUNT(*) as total_records,
    COUNT(anon_user_id) as records_with_anon_id,
    COUNT(DISTINCT anon_user_id) as unique_users
FROM email_validations;

-- Sample data
SELECT 
    id,
    anon_user_id,
    email,
    valid,
    validated_at
FROM email_validations
ORDER BY validated_at DESC
LIMIT 5;

-- ============================================================================
-- Rollback (if needed)
-- ============================================================================

-- WARNING: This will remove the anon_user_id column and all user associations!
-- Uncomment only if you need to rollback the migration

-- DROP INDEX IF EXISTS idx_anon_user_id;
-- DROP INDEX IF EXISTS idx_user_validated;
-- ALTER TABLE email_validations DROP COLUMN IF EXISTS anon_user_id;

-- ============================================================================
-- Performance Analysis
-- ============================================================================

-- Analyze table for query optimization
ANALYZE email_validations;

-- Check table size
SELECT 
    pg_size_pretty(pg_total_relation_size('email_validations')) as total_size,
    pg_size_pretty(pg_relation_size('email_validations')) as table_size,
    pg_size_pretty(pg_indexes_size('email_validations')) as indexes_size;

-- ============================================================================
-- Test Queries
-- ============================================================================

-- Test user-specific query (should use idx_user_validated)
EXPLAIN ANALYZE
SELECT * FROM email_validations
WHERE anon_user_id = 'test-user-id'
ORDER BY validated_at DESC
LIMIT 100;

-- Test user count query
SELECT 
    anon_user_id,
    COUNT(*) as validation_count,
    MAX(validated_at) as last_validation
FROM email_validations
GROUP BY anon_user_id
ORDER BY validation_count DESC
LIMIT 10;

-- ============================================================================
-- Notes
-- ============================================================================

-- 1. This migration is safe to run multiple times (idempotent)
-- 2. Existing records will get random UUIDs assigned
-- 3. New records MUST include anon_user_id
-- 4. Indexes are created for optimal query performance
-- 5. Run ANALYZE after migration for query optimization

-- ============================================================================
-- End of Migration
-- ============================================================================
