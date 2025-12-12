-- Check current users and their limits
SELECT 
    email,
    subscription_tier,
    api_calls_count,
    api_calls_limit,
    created_at
FROM users 
ORDER BY created_at DESC
LIMIT 10;

-- Check how many users have wrong limits
SELECT 
    subscription_tier,
    COUNT(*) as user_count,
    AVG(api_calls_limit) as avg_limit,
    MIN(api_calls_limit) as min_limit,
    MAX(api_calls_limit) as max_limit
FROM users 
GROUP BY subscription_tier;