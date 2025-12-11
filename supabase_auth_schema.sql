-- User Authentication Schema for EmailValidator
-- This creates the users table and related authentication functions

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- User preferences and limits
    api_key VARCHAR(255) UNIQUE,
    api_calls_count INTEGER DEFAULT 0,
    api_calls_limit INTEGER DEFAULT 1000, -- Monthly limit
    api_calls_reset_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '1 month',
    
    -- Subscription info
    subscription_tier VARCHAR(50) DEFAULT 'free', -- free, pro, enterprise
    subscription_expires TIMESTAMP WITH TIME ZONE,
    
    -- Profile info
    company VARCHAR(255),
    phone VARCHAR(50),
    timezone VARCHAR(100) DEFAULT 'UTC',
    
    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create user sessions table for JWT management
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);

-- Create user_email_validations table to link validations to users
CREATE TABLE IF NOT EXISTS user_email_validations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    is_valid BOOLEAN NOT NULL,
    confidence_score INTEGER DEFAULT 0,
    validation_tier VARCHAR(20), -- premium, high, medium, basic, minimal
    checks JSONB,
    risk_assessment JSONB,
    processing_time FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- API usage tracking
    api_call BOOLEAN DEFAULT FALSE,
    batch_id UUID, -- For grouping batch validations
    
    -- Performance metrics
    dns_cache_hit BOOLEAN DEFAULT FALSE,
    filters_applied JSONB
);

CREATE INDEX IF NOT EXISTS idx_user_validations_user_id ON user_email_validations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_validations_created_at ON user_email_validations(created_at);
CREATE INDEX IF NOT EXISTS idx_user_validations_batch_id ON user_email_validations(batch_id);
CREATE INDEX IF NOT EXISTS idx_user_validations_api_call ON user_email_validations(api_call);

-- Create user_api_usage table for detailed API tracking
CREATE TABLE IF NOT EXISTS user_api_usage (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(100) NOT NULL, -- /api/validate, /api/validate/batch
    method VARCHAR(10) NOT NULL, -- POST, GET
    emails_processed INTEGER DEFAULT 1,
    processing_time FLOAT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Performance tracking
    cache_hit_rate FLOAT,
    tier_distribution JSONB,
    cost_saved FLOAT -- Estimated cost saved through optimizations
);

CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON user_api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON user_api_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON user_api_usage(endpoint);

-- Function to generate API key
CREATE OR REPLACE FUNCTION generate_api_key()
RETURNS VARCHAR(255) AS $$
BEGIN
    RETURN 'ev_' || encode(gen_random_bytes(32), 'hex');
END;
$$ LANGUAGE plpgsql;

-- Function to reset API calls monthly
CREATE OR REPLACE FUNCTION reset_api_calls()
RETURNS VOID AS $$
BEGIN
    UPDATE users 
    SET 
        api_calls_count = 0,
        api_calls_reset_date = NOW() + INTERVAL '1 month'
    WHERE api_calls_reset_date <= NOW();
END;
$$ LANGUAGE plpgsql;

-- Create function to check API rate limits
CREATE OR REPLACE FUNCTION check_api_limit(user_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    current_calls INTEGER;
    call_limit INTEGER;
BEGIN
    SELECT api_calls_count, api_calls_limit 
    INTO current_calls, call_limit
    FROM users 
    WHERE id = user_uuid AND is_active = TRUE AND is_banned = FALSE;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    RETURN current_calls < call_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to increment API usage
CREATE OR REPLACE FUNCTION increment_api_usage(user_uuid UUID, email_count INTEGER DEFAULT 1)
RETURNS VOID AS $$
BEGIN
    UPDATE users 
    SET api_calls_count = api_calls_count + email_count
    WHERE id = user_uuid;
END;
$$ LANGUAGE plpgsql;

-- Create RLS (Row Level Security) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_email_validations ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_api_usage ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Sessions policies
CREATE POLICY "Users can view own sessions" ON user_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own sessions" ON user_sessions
    FOR ALL USING (auth.uid() = user_id);

-- Validations policies
CREATE POLICY "Users can view own validations" ON user_email_validations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own validations" ON user_email_validations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- API usage policies
CREATE POLICY "Users can view own API usage" ON user_api_usage
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "System can insert API usage" ON user_api_usage
    FOR INSERT WITH CHECK (true); -- Allow system to insert

-- Create some sample subscription tiers
INSERT INTO users (email, password_hash, first_name, last_name, subscription_tier, api_calls_limit, api_key) 
VALUES 
    ('demo@emailvalidator.com', '$2b$12$demo_hash', 'Demo', 'User', 'pro', 10000, generate_api_key())
ON CONFLICT (email) DO NOTHING;

-- Create a view for user statistics
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
    COUNT(uev.id) as total_validations,
    COUNT(CASE WHEN uev.is_valid THEN 1 END) as valid_emails,
    COUNT(CASE WHEN NOT uev.is_valid THEN 1 END) as invalid_emails,
    ROUND(AVG(uev.confidence_score)::numeric, 2) as avg_confidence_score,
    
    -- API usage statistics
    COUNT(uau.id) as api_calls_made,
    ROUND(AVG(uau.processing_time)::numeric, 4) as avg_processing_time,
    ROUND(AVG(uau.cache_hit_rate)::numeric, 2) as avg_cache_hit_rate,
    SUM(uau.cost_saved) as total_cost_saved
    
FROM users u
LEFT JOIN user_email_validations uev ON u.id = uev.user_id
LEFT JOIN user_api_usage uau ON u.id = uau.user_id
GROUP BY u.id, u.email, u.first_name, u.last_name, u.subscription_tier, 
         u.api_calls_count, u.api_calls_limit, u.created_at, u.last_login;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON users TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_sessions TO authenticated;
GRANT SELECT, INSERT ON user_email_validations TO authenticated;
GRANT SELECT, INSERT ON user_api_usage TO authenticated;
GRANT SELECT ON user_stats TO authenticated;

-- Grant usage on sequences
GRANT USAGE ON SEQUENCE user_email_validations_id_seq TO authenticated;
GRANT USAGE ON SEQUENCE user_api_usage_id_seq TO authenticated;

COMMENT ON TABLE users IS 'User accounts with authentication and subscription info';
COMMENT ON TABLE user_sessions IS 'Active user sessions for JWT token management';
COMMENT ON TABLE user_email_validations IS 'Email validation history linked to users';
COMMENT ON TABLE user_api_usage IS 'Detailed API usage tracking and analytics';
COMMENT ON VIEW user_stats IS 'Aggregated user statistics for dashboard';