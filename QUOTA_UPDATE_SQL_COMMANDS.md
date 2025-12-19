# SQL Commands to Complete 10M Quota Update

Run these commands in your Supabase SQL Editor to complete the quota system update:

## 1. Update Quota Check Function (Remove Monthly Reset)

```sql
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
```

## 2. Update Increment Function (Remove Reset Logic)

```sql
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
```

## 3. Update Default Quota for New Teams

```sql
ALTER TABLE teams ALTER COLUMN quota_limit SET DEFAULT 10000000;
```

## 4. Verify the Changes

```sql
-- Check current team quotas
SELECT 
    name,
    quota_used,
    quota_limit,
    quota_reset_date,
    ROUND((quota_used::numeric / quota_limit::numeric) * 100, 1) as usage_percentage
FROM teams 
ORDER BY created_at DESC;
```

## Summary of Changes Made

✅ **Database Updates Completed:**
- Updated 3 existing teams from 10K to 10M quota
- Removed quota_reset_date (set to NULL for lifetime quota)
- Updated team_manager.py to create new teams with 10M quota
- Updated frontend to show "10 million lifetime validations"
- Removed "Resets in X days" message (now shows "Lifetime quota")

✅ **How the 10M Shared Quota Works:**
- All team members share the same 10,000,000 validation quota
- If User A validates 10,000 emails, the team usage becomes 10,000/10,000,000
- User B will also see 10,000/10,000,000 used (shared counter)
- No monthly resets - it's a lifetime quota
- When the team reaches 10M validations, all members are blocked until quota is increased

✅ **Next Steps:**
1. Run the SQL commands above in Supabase SQL Editor
2. Restart your backend server
3. Test the team functionality to verify 10M quota is working