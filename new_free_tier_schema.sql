-- ============================================================================
-- PERFECT FREE TIER SCHEMA FOR EMAIL VALIDATOR
-- Run this AFTER the reset script
-- ============================================================================

-- 1. CREATE USERS TABLE WITH PROPER FREE TIER DEFAULTS
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    
    -- SUBSCRIPTION & LIMITS (Free tier focused)
    subscription_tier VARCHAR(50) DEFAULT 'free', -- free, pro, enterprise
    api_calls_count INTEGER DEFAULT 0,
    api_calls_limit INTEGER DEFAULT 10, -- FREE TIER GETS 10 CALLS!
    api_calls_reset_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '1 month',
    
    -- API & ACCOUNT INFO
    api_key VARCHAR(255) UNIQUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    
    -- TIMESTAMPS
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- PROFILE INFO (optional)
    company VARCHAR(255),
    phone VARCHAR(50),
    timezone VARCHAR(100) DEFAULT 'UTC'
);

-- 2. CREATE EMAIL VALIDATIONS TABLE
CREATE TABLE email_validations (
    id SERIAL PRIMARY KEY,
    
    -- USER TRACKING (supports both anonymous and authenticated)
    anon_user_id VARCHAR(36), -- For anonymous users (UUID format)
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- For authenticated users
    
    -- EMAIL DATA
    email VARCHAR(255) NOT NULL,
    valid BOOLEAN NOT NULL,
    confidence_score INTEGER DEFAULT 0,
    
    -- VALIDATION DETAILS
    checks JSONB DEFAULT '{}',
    smtp_details JSONB,
    is_disposable BOOLEAN DEFAULT FALSE,
    is_role_based BOOLEAN DEFAULT FALSE,
    is_catch_all BOOLEAN DEFAULT FALSE,
    
    -- BOUNCE TRACKING
    bounce_count INTEGER DEFAULT 0,
    last_bounce_date TIMESTAMP WITH TIME ZONE,
    
    -- METADATA
    notes TEXT DEFAULT '',
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- PERFORMANCE TRACKING
    processing_time_ms INTEGER DEFAULT 0,
    validation_tier VARCHAR(20) DEFAULT 'basic' -- basic, advanced, premium
);

-- 3. CREATE USER SESSIONS TABLE (JWT management)
CREATE TABLE user_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- 4. CREATE PERFORMANCE INDEXES
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_api_key ON users(api_key);
CREATE INDEX idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Email validations indexes (CRITICAL for performance)
CREATE INDEX idx_email_validations_anon_user ON email_validations(anon_user_id);
CREATE INDEX idx_email_validations_user_id ON email_validations(user_id);
CREATE INDEX idx_email_validations_email ON email_validations(email);
CREATE INDEX idx_email_validations_validated_at ON email_validations(validated_at DESC);
CREATE INDEX idx_user_validations_date ON email_validations(user_id, validated_at DESC);

-- Session indexes
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);

-- 5. CREATE HELPER FUNCTIONS

-- Generate API key
CREATE OR REPLACE FUNCTION generate_api_key()
RETURNS VARCHAR(255) AS $$
BEGIN
    RETURN 'ev_' || encode(gen_random_bytes(32), 'hex');
END;
$$ LANGUAGE plpgsql;

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Set proper API limits based on subscription tier
CREATE OR REPLACE FUNCTION set_user_limits_by_tier()
RETURNS TRIGGER AS $$
BEGIN
    -- Set API limits based on subscription tier
    IF NEW.subscription_tier = 'free' THEN
        NEW.api_calls_limit = 10;
    ELSIF NEW.subscription_tier = 'pro' THEN
        NEW.api_calls_limit = 10000;
    ELSIF NEW.subscription_tier = 'enterprise' THEN
        NEW.api_calls_limit = 100000;
    END IF;
    
    -- Reset API calls when tier changes (optional)
    IF OLD.subscription_tier IS DISTINCT FROM NEW.subscription_tier THEN
        NEW.api_calls_count = 0;
        NEW.api_calls_reset_date = NOW() + INTERVAL '1 month';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Check if user can make API calls
CREATE OR REPLACE FUNCTION check_api_limit(user_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    current_calls INTEGER;
    call_limit INTEGER;
BEGIN
    SELECT api_calls_count, api_calls_limit 
    INTO current_calls, call_limit
    FROM users 
    WHERE id = user_uuid;
    
    RETURN current_calls < call_limit;
END;
$$ LANGUAGE plpgsql;

-- Increment API usage
CREATE OR REPLACE FUNCTION increment_api_usage(user_uuid UUID, email_count INTEGER DEFAULT 1)
RETURNS VOID AS $$
BEGIN
    UPDATE users 
    SET api_calls_count = api_calls_count + email_count
    WHERE id = user_uuid;
END;
$$ LANGUAGE plpgsql;

-- 6. CREATE TRIGGERS

-- Update timestamp trigger
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Automatic tier limit management
CREATE TRIGGER trigger_set_user_limits
    BEFORE INSERT OR UPDATE OF subscription_tier ON users
    FOR EACH ROW
    EXECUTE FUNCTION set_user_limits_by_tier();

-- 7. DISABLE RLS FOR SIMPLICITY (Enable later if needed)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE email_validations DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions DISABLE ROW LEVEL SECURITY;

-- 8. GRANT PERMISSIONS
GRANT ALL ON users TO anon;
GRANT ALL ON users TO authenticated;
GRANT ALL ON email_validations TO anon;
GRANT ALL ON email_validations TO authenticated;
GRANT ALL ON user_sessions TO anon;
GRANT ALL ON user_sessions TO authenticated;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- 9. CREATE USEFUL VIEWS

-- User statistics view
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.subscription_tier,
    u.api_calls_count,
    u.api_calls_limit,
    u.created_at,
    u.last_login,
    -- Validation statistics
    COUNT(ev.id) as total_validations,
    COUNT(CASE WHEN ev.valid THEN 1 END) as valid_emails,
    COUNT(CASE WHEN NOT ev.valid THEN 1 END) as invalid_emails,
    ROUND(AVG(ev.confidence_score)::numeric, 2) as avg_confidence_score,
    -- Usage percentage
    ROUND((u.api_calls_count::numeric / u.api_calls_limit::numeric) * 100, 1) as usage_percentage
FROM users u
LEFT JOIN email_validations ev ON u.id = ev.user_id
GROUP BY u.id, u.email, u.first_name, u.last_name, u.subscription_tier, 
         u.api_calls_count, u.api_calls_limit, u.created_at, u.last_login;

-- Free tier users view (for admin monitoring)
CREATE OR REPLACE VIEW free_tier_users AS
SELECT 
    u.*,
    us.usage_percentage,
    us.total_validations
FROM users u
JOIN user_stats us ON u.id = us.id
WHERE u.subscription_tier = 'free'
ORDER BY u.created_at DESC;

-- Grant view permissions
GRANT SELECT ON user_stats TO anon;
GRANT SELECT ON user_stats TO authenticated;
GRANT SELECT ON free_tier_users TO anon;
GRANT SELECT ON free_tier_users TO authenticated;

-- 10. INSERT SAMPLE DATA

-- Create a demo pro user
INSERT INTO users (
    email, 
    password_hash, 
    first_name, 
    last_name, 
    subscription_tier, 
    api_calls_limit, 
    api_key
) VALUES (
    'demo@emailvalidator.com', 
    '$2b$12$demo_hash_placeholder', 
    'Demo', 
    'User', 
    'pro', 
    10000, 
    generate_api_key()
) ON CONFLICT (email) DO NOTHING;

-- Create a demo free user for testing
INSERT INTO users (
    email, 
    password_hash, 
    first_name, 
    last_name, 
    subscription_tier, 
    api_calls_limit, 
    api_key
) VALUES (
    'free@emailvalidator.com', 
    '$2b$12$demo_hash_placeholder', 
    'Free', 
    'User', 
    'free', 
    10, 
    generate_api_key()
) ON CONFLICT (email) DO NOTHING;

-- 11. ADD HELPFUL COMMENTS
COMMENT ON TABLE users IS 'User accounts with proper free tier limits (10 API calls)';
COMMENT ON TABLE email_validations IS 'Email validation records - supports both anonymous and authenticated users';
COMMENT ON TABLE user_sessions IS 'Active user sessions for JWT token management';
COMMENT ON VIEW user_stats IS 'Aggregated user statistics with usage percentages';
COMMENT ON VIEW free_tier_users IS 'Free tier users for admin monitoring';

COMMENT ON COLUMN users.api_calls_limit IS 'API calls limit per month: free=10, pro=10000, enterprise=100000';
COMMENT ON COLUMN users.subscription_tier IS 'Subscription tier: free (10 calls), pro (10k calls), enterprise (100k calls)';

-- 12. VERIFICATION AND SUMMARY
SELECT 'FREE TIER SCHEMA SETUP COMPLETE!' as status;

-- Show table structure
SELECT 
    table_name, 
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE t.table_schema = 'public' 
AND t.table_name IN ('users', 'email_validations', 'user_sessions')
ORDER BY t.table_name;

-- Show subscription tier limits
SELECT 
    'Subscription Tier Limits:' as info,
    'free = 10 calls, pro = 10,000 calls, enterprise = 100,000 calls' as limits;

-- Show sample users
SELECT 
    email,
    subscription_tier,
    api_calls_count,
    api_calls_limit,
    'Sample user for testing' as note
FROM users 
WHERE email IN ('demo@emailvalidator.com', 'free@emailvalidator.com');

SELECT 'Ready for free tier testing! 🚀' as message;