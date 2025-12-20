# Team Quota System - Fix Summary

## Issues Fixed

### 1. ✅ User Team Synchronization
**Problem:** Users' `team_id` field in the `users` table was NULL even though they were in the `team_members` table. This caused the effective tier calculation to fail.

**Solution:** 
- Updated `team_manager.py` to sync `users.team_id` and `users.team_role` when:
  - Creating a team (owner)
  - Accepting an invitation (member)
  - Leaving a team (clear fields)
  - Removing a member (clear fields)
- Ran `fix_user_team_sync.py` to fix existing users (6 users synced successfully)

**Files Modified:**
- `team_manager.py` - Added user table updates in `create_team()`, `accept_invitation()`, `leave_team()`, `remove_team_member()`
- `fix_user_team_sync.py` - Script to sync existing users

### 2. ✅ Database Function Calls
**Problem:** Team quota functions were being called incorrectly using `execute_function()` which doesn't exist.

**Solution:**
- Fixed all function calls to use Supabase's `rpc()` method with proper parameter format
- Updated `check_team_quota()`, `use_team_quota()`, and `can_create_team()` calls

**Files Modified:**
- `team_manager.py` - Fixed all `execute_function()` calls to use `rpc()`

### 3. ⚠️ Database Functions Need Update
**Problem:** The database functions `check_team_quota` and `increment_team_quota` have SQL errors (ambiguous column references).

**Solution Required:** Run the SQL commands in Supabase SQL Editor

## 🚨 ACTION REQUIRED: Run SQL Commands

You need to run these SQL commands in your **Supabase SQL Editor** to fix the database functions:

### Step 1: Update Quota Check Function

```sql
CREATE OR REPLACE FUNCTION check_team_quota(team_uuid UUID, email_count INTEGER DEFAULT 1)
RETURNS BOOLEAN AS $$
DECLARE
    current_usage INTEGER;
    quota_limit_val INTEGER;
BEGIN
    SELECT quota_used, quota_limit 
    INTO current_usage, quota_limit_val
    FROM teams WHERE id = team_uuid AND is_active = TRUE;
    
    -- Simple lifetime quota check (no reset)
    RETURN (current_usage + email_count) <= quota_limit_val;
END;
$$ LANGUAGE plpgsql;
```

### Step 2: Update Increment Function

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

### Step 3: Update Default Quota for New Teams

```sql
ALTER TABLE teams ALTER COLUMN quota_limit SET DEFAULT 10000000;
```

### Step 4: Verify the Changes

```sql
-- Check current team quotas
SELECT 
    name,
    quota_used,
    quota_limit,
    is_active,
    ROUND((quota_used::numeric / quota_limit::numeric) * 100, 1) as usage_percentage
FROM teams 
ORDER BY created_at DESC;
```

## How to Run SQL Commands

1. Go to your Supabase Dashboard
2. Navigate to **SQL Editor**
3. Create a new query
4. Copy and paste each SQL command above
5. Run each command one by one
6. Verify the results

## Testing After SQL Update

After running the SQL commands, restart your backend and test:

```bash
# Restart backend
python app_anon_history.py

# Test team quota
python test_team_quota_fix.py

# Check team status
python check_team_status.py
```

## Expected Behavior After Fix

### For Team Members:
1. ✅ Team members (even with "free" base tier) get Pro access
2. ✅ Batch validation works for all team members
3. ✅ All team members share the same 10M lifetime quota
4. ✅ Validation counter shows shared team usage (not individual)

### For Team Owners:
1. ✅ Can create teams with 10M lifetime quota
2. ✅ Can generate shareable invitation links
3. ✅ Can see all team members and their usage
4. ✅ Team quota is shared across all members

### Quota Sharing Example:
- Team has 10,000,000 validations
- User A validates 5,000 emails → Team usage: 5,000/10,000,000
- User B validates 3,000 emails → Team usage: 8,000/10,000,000
- Both users see the same counter: 8,000/10,000,000

## Current Status

✅ **Completed:**
- User team synchronization fixed
- Database function calls fixed
- Backend code updated
- Test scripts created

⚠️ **Pending:**
- SQL commands need to be run in Supabase SQL Editor
- Backend needs restart after SQL update
- Testing required after SQL update

## Files Created/Modified

**Modified:**
- `team_manager.py` - Fixed team creation, invitation, and quota functions
- `app_anon_history.py` - Already has correct effective tier logic

**Created:**
- `fix_user_team_sync.py` - Sync existing users with teams
- `test_team_quota_fix.py` - Test team quota functionality
- `check_team_status.py` - Check team status and functions
- `TEAM_QUOTA_FIX_SUMMARY.md` - This file

## Next Steps

1. **Run SQL commands** in Supabase SQL Editor (see above)
2. **Restart backend** server
3. **Test team functionality:**
   - Login as a team member
   - Try batch validation
   - Check if effective tier is "pro"
   - Verify shared quota counter
4. **Verify quota sharing:**
   - User A validates emails
   - User B should see the same usage counter

## Troubleshooting

### If batch validation still fails:
1. Check browser console for debug logs
2. Look for "DEBUG: Batch validation - User X, effective_tier: Y"
3. Verify user's team_id is not NULL in database
4. Check if team is marked as active

### If quota not shared:
1. Verify SQL functions are updated
2. Check team_info is being retrieved correctly
3. Look for "DEBUG: Using team quota for team X" in backend logs
4. Verify team quota is being incremented (not individual quota)

### If effective tier is still "free":
1. Check user's team_id field in users table
2. Run `fix_user_team_sync.py` again
3. Verify `get_effective_subscription_tier()` function logic
4. Check backend logs for tier calculation

## Support

If issues persist after running SQL commands:
1. Check backend logs for errors
2. Run test scripts to identify specific issues
3. Verify database schema matches expected structure
4. Check if all team members have team_id set correctly
