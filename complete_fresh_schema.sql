-- ============================================================================
-- COMPLETE FRESH SCHEMA FOR EMAIL VALIDATOR WITH USER AUTHENTICATION
-- Run this in your new Supabase database
-- ============================================================================

-- 1. CREATE USERS TABLE (Authentication)
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    api_calls_count INTEGER DEFAULT 0,
    api_calls_limit INTEGER DEFAULT 1000,
    api_key VARCHAR(255) UNIQUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- 2. CREATE EMAIL VALIDATIONS TABLE (Main validation storage)
CREATE TABLE email_validations (
    id SERIAL PRIMARY KEY,
    anon_user_id VARCHAR(36), -- For anonymous users
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- For authenticated users
    email VARCHAR(255) NOT NULL,
    valid BOOLEAN NOT NULL,
    confidence_score INTEGER DEFAULT 0,
    checks JSONB DEFAULT '{}',
    smtp_details JSONB,
    is_disposable BOOLEAN DEFAULT FALSE,
    is_role_based BOOLEAN DEFAULT FALSE,
    is_catch_all BOOLEAN DEFAULT FALSE,
    bounce_count INTEGER DEFAULT 0,
    last_bounce_date TIMESTAMP WITH TIME ZONE,
    notes TEXT DEFAULT '',
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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

-- 4. CREATE INDEXES FOR PERFORMANCE
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_api_key ON users(api_key);
CREATE INDEX idx_users_created_at ON users(created_at);

CREATE INDEX idx_email_validations_anon_user ON email_validations(anon_user_id);
CREATE INDEX idx_email_validations_user_id ON email_validations(user_id);
CREATE INDEX idx_email_validations_email ON email_validations(email);
CREATE INDEX idx_email_validations_validated_at ON email_validations(validated_at DESC);
CREATE INDEX idx_user_validations_date ON email_validations(user_id, validated_at DESC);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);

-- 5. CREATE HELPER FUNCTIONS
CREATE OR REPLACE FUNCTION generate_api_key()
RETURNS VARCHAR(255) AS $$
BEGIN
    RETURN 'ev_' || encode(gen_random_bytes(32), 'hex');
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6. CREATE TRIGGERS
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

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
    ROUND(AVG(ev.confidence_score)::numeric, 2) as avg_confidence_score
    
FROM users u
LEFT JOIN email_validations ev ON u.id = ev.user_id
GROUP BY u.id, u.email, u.first_name, u.last_name, u.subscription_tier, 
         u.api_calls_count, u.api_calls_limit, u.created_at, u.last_login;

-- Grant view permissions
GRANT SELECT ON user_stats TO anon;
GRANT SELECT ON user_stats TO authenticated;

-- 10. INSERT SAMPLE DATA (Optional)
INSERT INTO users (email, password_hash, first_name, last_name, subscription_tier, api_calls_limit, api_key) 
VALUES 
    ('demo@emailvalidator.com', '$2b$12$demo_hash_placeholder', 'Demo', 'User', 'pro', 10000, generate_api_key())
ON CONFLICT (email) DO NOTHING;

-- 11. ADD COMMENTS
COMMENT ON TABLE users IS 'User accounts with authentication and subscription info';
COMMENT ON TABLE email_validations IS 'Email validation records - supports both anonymous and authenticated users';
COMMENT ON TABLE user_sessions IS 'Active user sessions for JWT token management';
COMMENT ON VIEW user_stats IS 'Aggregated user statistics for dashboard';

-- 12. VERIFICATION QUERIES
SELECT 'Tables created successfully!' as status;

SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE t.table_schema = 'public' 
AND t.table_name IN ('users', 'email_validations', 'user_sessions')
ORDER BY t.table_name;

SELECT 'Schema setup complete! Ready for authentication and email validation.' as message;