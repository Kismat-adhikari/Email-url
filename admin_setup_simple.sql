-- ============================================================================
-- ADMIN CONTROL SYSTEM - SIMPLE SETUP FOR SUPABASE
-- Copy and paste this entire script into Supabase SQL Editor
-- ============================================================================

-- 1. Create admin_users table
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin' CHECK (role IN ('super_admin', 'admin', 'moderator')),
    permissions JSONB DEFAULT '[]',
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES admin_users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- 2. Create admin_sessions table
CREATE TABLE IF NOT EXISTS admin_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    admin_id UUID REFERENCES admin_users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- 3. Create admin_activity_logs table
CREATE TABLE IF NOT EXISTS admin_activity_logs (
    id SERIAL PRIMARY KEY,
    admin_id UUID REFERENCES admin_users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create system_metrics table
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value DECIMAL(15,4) NOT NULL,
    unit VARCHAR(20),
    metadata JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Add admin fields to users table (if not exists)
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_suspended BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended_by UUID REFERENCES admin_users(id) ON DELETE SET NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS suspension_reason TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_notes TEXT;

-- 6. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);
CREATE INDEX IF NOT EXISTS idx_admin_users_active ON admin_users(is_active);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_admin_id ON admin_sessions(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_token ON admin_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires ON admin_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_admin_activity_admin_id ON admin_activity_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_activity_action ON admin_activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_admin_activity_created ON admin_activity_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type, metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded ON system_metrics(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_suspended ON users(is_suspended);

-- 7. Create dashboard view for admin statistics
CREATE OR REPLACE VIEW admin_dashboard_stats AS
SELECT 
    -- User Statistics
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE) as users_today,
    (SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as users_this_week,
    (SELECT COUNT(*) FROM users WHERE subscription_tier = 'free') as free_users,
    (SELECT COUNT(*) FROM users WHERE subscription_tier != 'free') as paid_users,
    (SELECT COUNT(*) FROM users WHERE is_suspended = true) as suspended_users,
    
    -- Validation Statistics
    (SELECT COUNT(*) FROM email_validations) as total_validations,
    (SELECT COUNT(*) FROM email_validations WHERE validated_at >= CURRENT_DATE) as validations_today,
    (SELECT COUNT(*) FROM email_validations WHERE valid = true) as valid_emails,
    (SELECT COUNT(*) FROM email_validations WHERE valid = false) as invalid_emails,
    
    -- System Health
    (SELECT COUNT(*) FROM admin_activity_logs WHERE created_at >= CURRENT_DATE) as admin_actions_today,
    (SELECT COUNT(DISTINCT admin_id) FROM admin_sessions WHERE is_active = true) as active_admins;

-- 8. Insert default super admin user (password: admin123)
-- IMPORTANT: Change this password immediately after first login!
INSERT INTO admin_users (
    email, 
    password_hash, 
    role, 
    first_name, 
    last_name, 
    permissions
) VALUES (
    'admin@emailvalidator.com',
    '$2b$12$LQv3c1yqBwEHFl5aysHdsOecr0Cz/qt6NzHElYos.RSUuu9OVShxC', -- admin123
    'super_admin',
    'Super',
    'Admin',
    '["*"]'::jsonb
) ON CONFLICT (email) DO NOTHING;

-- 9. Disable RLS for admin tables (we'll handle security in the application layer)
ALTER TABLE admin_users DISABLE ROW LEVEL SECURITY;
ALTER TABLE admin_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE admin_activity_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE system_metrics DISABLE ROW LEVEL SECURITY;

-- 10. Grant necessary permissions
GRANT ALL ON admin_users TO anon;
GRANT ALL ON admin_users TO authenticated;
GRANT ALL ON admin_sessions TO anon;
GRANT ALL ON admin_sessions TO authenticated;
GRANT ALL ON admin_activity_logs TO anon;
GRANT ALL ON admin_activity_logs TO authenticated;
GRANT ALL ON system_metrics TO anon;
GRANT ALL ON system_metrics TO authenticated;
GRANT SELECT ON admin_dashboard_stats TO anon;
GRANT SELECT ON admin_dashboard_stats TO authenticated;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Success message
SELECT 'Admin Control System setup completed successfully!' as status;
SELECT 'Default admin: admin@emailvalidator.com / admin123' as login_info;
SELECT 'IMPORTANT: Change the default password immediately!' as security_warning;