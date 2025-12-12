-- Fix Free Tier API Limits
-- This migration ensures free tier users have proper limits

-- Update the default API limit for free tier users to 10
ALTER TABLE users ALTER COLUMN api_calls_limit SET DEFAULT 10;

-- Update existing free tier users to have the correct limit
UPDATE users 
SET api_calls_limit = 10 
WHERE subscription_tier = 'free' 
AND api_calls_limit > 10;

-- Create a function to set proper limits based on subscription tier
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
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically set limits when subscription tier changes
DROP TRIGGER IF EXISTS trigger_set_user_limits ON users;
CREATE TRIGGER trigger_set_user_limits
    BEFORE INSERT OR UPDATE OF subscription_tier ON users
    FOR EACH ROW
    EXECUTE FUNCTION set_user_limits_by_tier();

-- Add comments for clarity
COMMENT ON COLUMN users.api_calls_limit IS 'API calls limit per month: free=10, pro=10000, enterprise=100000';
COMMENT ON COLUMN users.subscription_tier IS 'Subscription tier: free, pro, enterprise';

-- Verify the changes
SELECT 
    subscription_tier,
    COUNT(*) as user_count,
    AVG(api_calls_limit) as avg_limit,
    MIN(api_calls_limit) as min_limit,
    MAX(api_calls_limit) as max_limit
FROM users 
GROUP BY subscription_tier
ORDER BY subscription_tier;