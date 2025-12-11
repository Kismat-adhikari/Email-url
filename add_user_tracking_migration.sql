-- Migration: Add User Tracking to Email Validations
-- This links email validations to actual user accounts when logged in

-- Add user_id column to link validations to actual users
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'email_validations' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE email_validations ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE SET NULL;
        COMMENT ON COLUMN email_validations.user_id IS 'Links validation to authenticated user account (NULL for anonymous users)';
    END IF;
END $$;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_email_validations_user_id ON email_validations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_validations_date ON email_validations(user_id, validated_at DESC);

-- Create a view for user validation statistics
CREATE OR REPLACE VIEW user_validation_stats AS
SELECT 
    u.id as user_id,
    u.email as user_email,
    u.first_name,
    u.last_name,
    u.subscription_tier,
    
    -- Validation counts
    COUNT(ev.id) as total_validations,
    COUNT(CASE WHEN ev.valid THEN 1 END) as valid_emails,
    COUNT(CASE WHEN NOT ev.valid THEN 1 END) as invalid_emails,
    
    -- Confidence and quality metrics
    ROUND(AVG(ev.confidence_score)::numeric, 2) as avg_confidence_score,
    COUNT(CASE WHEN ev.is_disposable THEN 1 END) as disposable_count,
    COUNT(CASE WHEN ev.is_role_based THEN 1 END) as role_based_count,
    
    -- Date ranges
    MIN(ev.validated_at) as first_validation,
    MAX(ev.validated_at) as last_validation,
    
    -- Recent activity (last 30 days)
    COUNT(CASE WHEN ev.validated_at >= NOW() - INTERVAL '30 days' THEN 1 END) as validations_last_30_days
    
FROM users u
LEFT JOIN email_validations ev ON u.id = ev.user_id
GROUP BY u.id, u.email, u.first_name, u.last_name, u.subscription_tier;

-- Grant permissions
GRANT SELECT ON user_validation_stats TO authenticated;

-- Add comments
COMMENT ON VIEW user_validation_stats IS 'Aggregated validation statistics per authenticated user';

-- Example queries you can run after migration:

-- 1. Get all validations for a specific user
-- SELECT * FROM email_validations WHERE user_id = 'your-user-uuid' ORDER BY validated_at DESC;

-- 2. Get user validation statistics
-- SELECT * FROM user_validation_stats WHERE user_id = 'your-user-uuid';

-- 3. Find users with high validation activity
-- SELECT user_email, total_validations, avg_confidence_score 
-- FROM user_validation_stats 
-- WHERE total_validations > 100 
-- ORDER BY total_validations DESC;

-- 4. Get anonymous vs authenticated validation split
-- SELECT 
--   COUNT(CASE WHEN user_id IS NOT NULL THEN 1 END) as authenticated_validations,
--   COUNT(CASE WHEN user_id IS NULL THEN 1 END) as anonymous_validations,
--   COUNT(*) as total_validations
-- FROM email_validations;

COMMENT ON TABLE email_validations IS 'Email validation records - supports both anonymous (anon_user_id) and authenticated (user_id) users';