-- Update team quota to 10 million (lifetime)
-- Run this in Supabase SQL Editor

-- Update existing teams to have 10M quota
UPDATE teams 
SET quota_limit = 10000000,  -- 10 million
    quota_reset_date = NULL  -- Remove monthly reset (lifetime quota)
WHERE quota_limit = 10000;   -- Only update teams that currently have 10k

-- Update the default for new teams
ALTER TABLE teams 
ALTER COLUMN quota_limit SET DEFAULT 10000000;  -- 10 million default

-- Update team creation function to use 10M
CREATE OR REPLACE FUNCTION increment_team_quota(team_uuid UUID, email_count INTEGER DEFAULT 1)
RETURNS VOID AS $$
BEGIN
    UPDATE teams 
    SET quota_used = quota_used + email_count,
        updated_at = NOW()
    WHERE id = team_uuid;
    -- No reset logic needed for lifetime quota
END;
$$ LANGUAGE plpgsql;

-- Update quota check function (remove monthly reset)
CREATE OR REPLACE FUNCTION check_team_quota(team_uuid UUID, email_count INTEGER DEFAULT 1)
RETURNS BOOLEAN AS $$
DECLARE
    current_usage INTEGER;
    quota_limit INTEGER;
BEGIN
    SELECT quota_used, quota_limit 
    INTO current_usage, quota_limit
    FROM teams WHERE id = team_uuid AND is_active = TRUE;
    
    -- Simple lifetime quota check (no reset)
    RETURN (current_usage + email_count) <= quota_limit;
END;
$$ LANGUAGE plpgsql;

-- Verify the changes
SELECT 'Team quota updated to 10M lifetime!' as status;
SELECT id, name, quota_used, quota_limit, quota_reset_date 
FROM teams 
ORDER BY created_at DESC;