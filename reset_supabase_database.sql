-- ============================================================================
-- COMPLETE DATABASE RESET - DELETE EVERYTHING
-- ⚠️  WARNING: This will delete ALL data in your database!
-- Run this in Supabase SQL Editor to start fresh
-- ============================================================================

-- 1. DROP ALL VIEWS FIRST (they depend on tables)
DROP VIEW IF EXISTS user_stats CASCADE;

-- 2. DROP ALL TRIGGERS
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS trigger_set_user_limits ON users;

-- 3. DROP ALL FUNCTIONS
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS generate_api_key() CASCADE;
DROP FUNCTION IF EXISTS set_user_limits_by_tier() CASCADE;

-- 4. DROP ALL TABLES (in correct order to avoid foreign key issues)
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS email_validations CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 5. DROP ALL SEQUENCES (if any remain)
DROP SEQUENCE IF EXISTS email_validations_id_seq CASCADE;

-- 6. CLEAN UP ANY REMAINING OBJECTS
-- Drop any custom types
DROP TYPE IF EXISTS subscription_tier_type CASCADE;

-- 7. VERIFY EVERYTHING IS GONE
SELECT 
    'All tables deleted!' as status,
    COUNT(*) as remaining_tables
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'email_validations', 'user_sessions');

-- 8. SHOW WHAT'S LEFT (should be empty or only system tables)
SELECT table_name, table_type
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

SELECT 'Database reset complete! Ready for fresh setup.' as message;