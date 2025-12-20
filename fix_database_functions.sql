-- Fix Team Quota Database Functions
-- This script fixes the ambiguous column reference errors and removes monthly reset logic

-- 1. Fix check_team_quota function (remove ambiguous references and monthly reset)
CREATE OR REPLACE FUNCTION check_team_quota(team_uuid UUID, email_count INTEGER DEFAULT 1)
RETURNS BOOLEAN AS $$
DECLARE
    current_usage INTEGER;
    team_quota_limit INTEGER;
BEGIN
    SELECT t.quota_used, t.quota_limit 
    INTO current_usage, team_quota_limit
    FROM teams t 
    WHERE t.id = team_uuid AND t.is_active = TRUE;
    
    -- If team not found, return false
    IF current_usage IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Simple lifetime quota check (no reset)
    RETURN (current_usage + email_count) <= team_quota_limit;
END;
$$ LANGUAGE plpgsql;

-- 2. Fix increment_team_quota function (remove ambiguous references and monthly reset)
CREATE OR REPLACE FUNCTION increment_team_quota(team_uuid UUID, email_count INTEGER DEFAULT 1)
RETURNS VOID AS $$
BEGIN
    UPDATE teams 
    SET quota_used = quota_used + email_count,
        updated_at = NOW()
    WHERE id = team_uuid AND is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- 3. Verify the functions work
SELECT 'Database functions updated successfully!' as status;

-- Test the functions
DO $$
DECLARE
    test_team_id UUID;
    can_validate BOOLEAN;
BEGIN
    -- Get a test team ID
    SELECT id INTO test_team_id FROM teams LIMIT 1;
    
    IF test_team_id IS NOT NULL THEN
        -- Test quota check
        SELECT check_team_quota(test_team_id, 1) INTO can_validate;
        RAISE NOTICE 'Test quota check for team %: %', test_team_id, can_validate;
    ELSE
        RAISE NOTICE 'No teams found for testing';
    END IF;
END;
$$;