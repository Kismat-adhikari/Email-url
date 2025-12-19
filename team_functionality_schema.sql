-- ============================================================================
-- TEAM FUNCTIONALITY FOR PRO USERS - EMAIL VALIDATOR
-- Run this AFTER your existing schemas are set up
-- This adds team collaboration with shared quotas for Pro users
-- ============================================================================

-- 1. CREATE TEAMS TABLE
CREATE TABLE teams (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- QUOTA MANAGEMENT (shared among all team members)
    quota_limit INTEGER DEFAULT 10000000, -- Pro tier gets 10M lifetime validations
    quota_used INTEGER DEFAULT 0,
    quota_reset_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '1 month',
    
    -- TEAM SETTINGS
    max_members INTEGER DEFAULT 10, -- Limit team size
    is_active BOOLEAN DEFAULT TRUE,
    
    -- METADATA
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. CREATE TEAM MEMBERS TABLE
CREATE TABLE team_members (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- MEMBER ROLE & STATUS
    role VARCHAR(50) DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- INVITATION TRACKING
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- UNIQUE CONSTRAINT: User can only be in one team at a time (business rule)
    UNIQUE(user_id)
);

-- 3. CREATE TEAM INVITATIONS TABLE
CREATE TABLE team_invitations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    
    -- INVITATION DETAILS
    email VARCHAR(255) NOT NULL,
    invite_token VARCHAR(255) UNIQUE NOT NULL,
    
    -- INVITATION METADATA
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    message TEXT, -- Optional personal message
    
    -- STATUS & TIMING
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired', 'cancelled')),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '7 days',
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. ADD TEAM FIELDS TO EXISTING TABLES

-- Add team tracking to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS team_role VARCHAR(50) DEFAULT NULL;

-- Add team tracking to email_validations table
ALTER TABLE email_validations ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

-- 5. CREATE PERFORMANCE INDEXES
CREATE INDEX idx_teams_owner_id ON teams(owner_id);
CREATE INDEX idx_teams_active ON teams(is_active);
CREATE INDEX idx_teams_quota_reset ON teams(quota_reset_date);

CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
CREATE INDEX idx_team_members_active ON team_members(is_active);

CREATE INDEX idx_team_invitations_token ON team_invitations(invite_token);
CREATE INDEX idx_team_invitations_email ON team_invitations(email);
CREATE INDEX idx_team_invitations_team_id ON team_invitations(team_id);
CREATE INDEX idx_team_invitations_status ON team_invitations(status);
CREATE INDEX idx_team_invitations_expires ON team_invitations(expires_at);

CREATE INDEX idx_users_team_id ON users(team_id);
CREATE INDEX idx_email_validations_team_id ON email_validations(team_id);

-- 6. CREATE HELPER FUNCTIONS

-- Generate secure invite token
CREATE OR REPLACE FUNCTION generate_invite_token()
RETURNS VARCHAR(255) AS $$
BEGIN
    RETURN 'invite_' || encode(gen_random_bytes(32), 'hex');
END;
$$ LANGUAGE plpgsql;

-- Check if user can create a team (must be Pro)
CREATE OR REPLACE FUNCTION can_create_team(user_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    user_tier VARCHAR(50);
    existing_team_id UUID;
BEGIN
    SELECT subscription_tier, team_id INTO user_tier, existing_team_id
    FROM users WHERE id = user_uuid;
    
    -- Must be Starter or Pro tier and not already in a team
    RETURN user_tier IN ('starter', 'pro') AND existing_team_id IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Check team quota before validation
CREATE OR REPLACE FUNCTION check_team_quota(team_uuid UUID, email_count INTEGER DEFAULT 1)
RETURNS BOOLEAN AS $$
DECLARE
    current_usage INTEGER;
    quota_limit INTEGER;
    reset_date TIMESTAMP WITH TIME ZONE;
BEGIN
    SELECT quota_used, quota_limit, quota_reset_date 
    INTO current_usage, quota_limit, reset_date
    FROM teams WHERE id = team_uuid AND is_active = TRUE;
    
    -- Reset quota if month has passed
    IF reset_date <= NOW() THEN
        UPDATE teams 
        SET quota_used = 0, quota_reset_date = NOW() + INTERVAL '1 month'
        WHERE id = team_uuid;
        current_usage = 0;
    END IF;
    
    RETURN (current_usage + email_count) <= quota_limit;
END;
$$ LANGUAGE plpgsql;

-- Increment team quota usage
CREATE OR REPLACE FUNCTION increment_team_quota(team_uuid UUID, email_count INTEGER DEFAULT 1)
RETURNS VOID AS $$
BEGIN
    UPDATE teams 
    SET quota_used = quota_used + email_count,
        updated_at = NOW()
    WHERE id = team_uuid;
END;
$$ LANGUAGE plpgsql;

-- Auto-assign team info when user joins
CREATE OR REPLACE FUNCTION sync_user_team_info()
RETURNS TRIGGER AS $$
BEGIN
    -- When user joins a team, update their team_id and role
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE users 
        SET team_id = NEW.team_id,
            team_role = NEW.role,
            updated_at = NOW()
        WHERE id = NEW.user_id;
    END IF;
    
    -- When user leaves a team, clear their team info
    IF TG_OP = 'DELETE' THEN
        UPDATE users 
        SET team_id = NULL,
            team_role = NULL,
            updated_at = NOW()
        WHERE id = OLD.user_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 7. CREATE TRIGGERS

-- Update timestamp trigger for teams
CREATE TRIGGER update_teams_updated_at 
    BEFORE UPDATE ON teams 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Sync user team info when team membership changes
CREATE TRIGGER sync_user_team_info_trigger
    AFTER INSERT OR UPDATE OR DELETE ON team_members
    FOR EACH ROW
    EXECUTE FUNCTION sync_user_team_info();

-- 8. CREATE USEFUL VIEWS

-- Team dashboard view
CREATE OR REPLACE VIEW team_dashboard AS
SELECT 
    t.id,
    t.name,
    t.owner_id,
    u.email as owner_email,
    u.first_name || ' ' || u.last_name as owner_name,
    t.quota_limit,
    t.quota_used,
    t.quota_reset_date,
    t.max_members,
    t.is_active,
    t.created_at,
    
    -- Team statistics
    COUNT(tm.id) as member_count,
    COUNT(CASE WHEN tm.is_active THEN 1 END) as active_members,
    
    -- Usage percentage
    ROUND((t.quota_used::numeric / t.quota_limit::numeric) * 100, 1) as usage_percentage,
    
    -- Days until quota reset
    EXTRACT(DAY FROM t.quota_reset_date - NOW()) as days_until_reset
    
FROM teams t
JOIN users u ON t.owner_id = u.id
LEFT JOIN team_members tm ON t.id = tm.team_id
GROUP BY t.id, t.name, t.owner_id, u.email, u.first_name, u.last_name, 
         t.quota_limit, t.quota_used, t.quota_reset_date, t.max_members, 
         t.is_active, t.created_at;

-- Team member details view
CREATE OR REPLACE VIEW team_member_details AS
SELECT 
    tm.id,
    tm.team_id,
    t.name as team_name,
    tm.user_id,
    u.email,
    u.first_name || ' ' || u.last_name as full_name,
    tm.role,
    tm.is_active,
    tm.joined_at,
    
    -- Invitation details
    inviter.email as invited_by_email,
    inviter.first_name || ' ' || inviter.last_name as invited_by_name,
    
    -- User validation stats in this team
    COUNT(ev.id) as validations_count,
    COUNT(CASE WHEN ev.valid THEN 1 END) as valid_emails,
    COUNT(CASE WHEN ev.valid = FALSE THEN 1 END) as invalid_emails
    
FROM team_members tm
JOIN teams t ON tm.team_id = t.id
JOIN users u ON tm.user_id = u.id
LEFT JOIN users inviter ON tm.invited_by = inviter.id
LEFT JOIN email_validations ev ON u.id = ev.user_id AND ev.team_id = tm.team_id
GROUP BY tm.id, tm.team_id, t.name, tm.user_id, u.email, u.first_name, u.last_name,
         tm.role, tm.is_active, tm.joined_at, inviter.email, inviter.first_name, inviter.last_name;

-- 9. DISABLE RLS FOR SIMPLICITY (Enable later if needed)
ALTER TABLE teams DISABLE ROW LEVEL SECURITY;
ALTER TABLE team_members DISABLE ROW LEVEL SECURITY;
ALTER TABLE team_invitations DISABLE ROW LEVEL SECURITY;

-- 10. GRANT PERMISSIONS
GRANT ALL ON teams TO anon;
GRANT ALL ON teams TO authenticated;
GRANT ALL ON team_members TO anon;
GRANT ALL ON team_members TO authenticated;
GRANT ALL ON team_invitations TO anon;
GRANT ALL ON team_invitations TO authenticated;

-- Grant view permissions
GRANT SELECT ON team_dashboard TO anon;
GRANT SELECT ON team_dashboard TO authenticated;
GRANT SELECT ON team_member_details TO anon;
GRANT SELECT ON team_member_details TO authenticated;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- 11. ADD HELPFUL COMMENTS
COMMENT ON TABLE teams IS 'Teams for Pro users - shared quota system';
COMMENT ON TABLE team_members IS 'Team membership tracking with roles';
COMMENT ON TABLE team_invitations IS 'Team invitation system with tokens';
COMMENT ON VIEW team_dashboard IS 'Complete team overview with statistics';
COMMENT ON VIEW team_member_details IS 'Detailed team member information';

-- 12. SAMPLE DATA FOR TESTING
-- Create a sample Pro user and team (for testing)
INSERT INTO users (email, password_hash, first_name, last_name, subscription_tier, api_calls_limit) 
VALUES ('teamowner@test.com', '$2b$12$demo_hash', 'Team', 'Owner', 'pro', 10000)
ON CONFLICT (email) DO NOTHING;

-- Get the user ID and create a team
DO $$
DECLARE
    owner_uuid UUID;
    team_uuid UUID;
BEGIN
    SELECT id INTO owner_uuid FROM users WHERE email = 'teamowner@test.com';
    
    IF owner_uuid IS NOT NULL THEN
        INSERT INTO teams (name, owner_id, description) 
        VALUES ('Test Startup Team', owner_uuid, 'Sample team for testing team functionality')
        RETURNING id INTO team_uuid;
        
        -- Add owner as team member
        INSERT INTO team_members (team_id, user_id, role, invited_by)
        VALUES (team_uuid, owner_uuid, 'owner', owner_uuid);
    END IF;
END $$;

-- 13. VERIFICATION AND SUMMARY
SELECT 'TEAM FUNCTIONALITY SETUP COMPLETE!' as status;

-- Show new tables
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE t.table_schema = 'public' 
  AND t.table_name IN ('teams', 'team_members', 'team_invitations')
ORDER BY t.table_name;

-- Show sample team
SELECT 'Sample team created for testing:' as info;
SELECT t.name, u.email as owner_email, t.quota_limit, t.member_count
FROM team_dashboard t
JOIN users u ON t.owner_id = u.id
WHERE u.email = 'teamowner@test.com';

SELECT 'Ready for team collaboration! 🚀' as message;
SELECT 'Pro users can now create teams and invite members!' as feature_info;