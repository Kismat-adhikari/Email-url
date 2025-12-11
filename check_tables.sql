-- Check if all required tables exist
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'email_validations', 'user_sessions', 'user_email_validations', 'user_api_usage')
ORDER BY table_name;

-- Check users table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;

-- Check if users table has any data
SELECT COUNT(*) as user_count FROM users;

-- Check email_validations table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'email_validations' 
ORDER BY ordinal_position;