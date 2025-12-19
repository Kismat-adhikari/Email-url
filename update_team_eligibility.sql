-- Update team eligibility function to allow Starter and Pro users
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