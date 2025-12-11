-- Clear All Email Validation Data
-- This will delete all existing email validation records to start fresh

-- Delete all records from email_validations table
DELETE FROM email_validations;

-- Reset the auto-increment ID counter (if using SERIAL)
-- This makes the next record start from ID 1 again
ALTER SEQUENCE IF EXISTS email_validations_id_seq RESTART WITH 1;

-- Verify the table is empty
SELECT COUNT(*) as remaining_records FROM email_validations;

-- Show table structure to confirm user_id column was added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'email_validations' 
ORDER BY ordinal_position;

-- Optional: Show some sample data structure (will be empty after delete)
SELECT * FROM email_validations LIMIT 5;