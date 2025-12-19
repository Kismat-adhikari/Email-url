# Team Functionality Implementation Guide

## Overview
This implementation adds team collaboration features for Pro users, allowing them to create teams, invite members, and share a monthly quota of 10,000 email validations.

## What Was Created

### 1. Database Schema (`team_functionality_schema.sql`)
Run this SQL script in your Supabase SQL Editor to create:

**Tables:**
- `teams` - Stores team information and quota management
- `team_members` - Tracks team membership and roles
- `team_invitations` - Manages invitation tokens and status

**Key Features:**
- Shared quota system (10,000 validations/month for Pro teams)
- Role-based access (owner, admin, member)
- Automatic quota reset monthly
- Team member limit (default: 10 members)
- Invitation expiry (7 days)

**Helper Functions:**
- `can_create_team()` - Check if user can create a team
- `check_team_quota()` - Verify team has available quota
- `increment_team_quota()` - Use team quota for validations
- `generate_invite_token()` - Create secure invitation tokens

**Views:**
- `team_dashboard` - Complete team overview with statistics
- `team_member_details` - Detailed member information

### 2. Backend Code

#### `team_manager.py`
Core team management logic:
- Create teams (Pro users only)
- Generate and manage invitations
- Add/remove team members
- Check and use team quotas
- Get team statistics

#### `team_api.py`
Flask API endpoints:
- `POST /api/team/create` - Create a new team
- `GET /api/team/info` - Get team information
- `GET /api/team/usage` - Get quota usage
- `POST /api/team/invite` - Invite a member
- `GET /api/team/invite/<token>` - Get invitation details
- `POST /api/team/invite/<token>/accept` - Accept invitation
- `DELETE /api/team/members/<id>/remove` - Remove member
- `POST /api/team/leave` - Leave team
- `PUT /api/team/update` - Update team settings
- `GET /api/team/check-eligibility` - Check if user can create team

### 3. Frontend Components

#### `TeamManagement.js`
React component for team management:
- Create team interface
- Team dashboard with quota visualization
- Member management (invite, remove)
- Pending invitations display
- Leave team functionality

#### `TeamManagement.css`
Responsive styling for team interface

### 4. Integration Changes

#### Modified Files:
- `app_anon_history.py` - Added team routes and quota checking
- `supabase_storage.py` - Added team_id field to validation records

## How It Works

### Team Creation Flow
1. Pro user clicks "Create Team"
2. Enters team name and description
3. System creates team with 10k monthly quota
4. User becomes team owner automatically

### Invitation Flow
1. Team owner/admin enters member email
2. System generates unique invitation token
3. Invitation link sent: `yourapp.com/invite/abc123token`
4. Invitee clicks link
5. If no account → Register first
6. If has account → Join directly
7. Member gets Pro access with shared quota

### Quota Management
1. When team member validates emails:
   - System checks team quota first
   - If available, uses team quota (not individual)
   - Team quota increments
   - All members share same pool
2. When quota exhausted:
   - All team members blocked
   - Resets monthly automatically

### Member Roles
- **Owner**: Created the team, can't be removed, full control
- **Admin**: Can invite/remove members, manage settings
- **Member**: Can use team quota, view team info

## Installation Steps

### 1. Database Setup
```sql
-- Run in Supabase SQL Editor
-- Copy and paste entire content of team_functionality_schema.sql
```

### 2. Backend Setup
```bash
# Files are already created:
# - team_manager.py
# - team_api.py

# The main app (app_anon_history.py) has been updated to:
# - Import team modules
# - Register team routes
# - Check team quotas
# - Store team_id in validations
```

### 3. Frontend Setup
```bash
# Files created:
# - frontend/src/TeamManagement.js
# - frontend/src/TeamManagement.css

# Add to your App.js routing:
import TeamManagement from './TeamManagement';

# Add route:
<Route path="/team" element={<TeamManagement />} />
```

### 4. Restart Services
```bash
# Backend
python app_anon_history.py

# Frontend
cd frontend
npm start
```

## Testing the Feature

### Test Scenario 1: Create Team
1. Login as Pro user
2. Navigate to `/team`
3. Click "Create Team"
4. Enter team name: "Test Startup"
5. Submit
6. Verify team dashboard appears

### Test Scenario 2: Invite Member
1. As team owner, click "Invite Member"
2. Enter email: `member@test.com`
3. Add message (optional)
4. Submit
5. Copy invitation link from response
6. Open link in incognito/different browser
7. Register new account or login
8. Accept invitation
9. Verify member appears in team dashboard

### Test Scenario 3: Shared Quota
1. Login as team owner
2. Validate 5 emails
3. Check quota usage
4. Login as team member
5. Validate 3 emails
6. Check quota usage (should show 8 total)
7. Both users share same quota

### Test Scenario 4: Remove Member
1. As team owner, go to team dashboard
2. Find member in list
3. Click "Remove"
4. Confirm
5. Member loses Pro access
6. Member's validations still counted in team quota

## API Usage Examples

### Create Team
```javascript
const response = await fetch('/api/team/create', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        name: 'My Startup Team',
        description: 'Email validation for our marketing team'
    })
});
```

### Invite Member
```javascript
const response = await fetch('/api/team/invite', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        email: 'colleague@company.com',
        message: 'Join our team!'
    })
});
```

### Get Team Info
```javascript
const response = await fetch('/api/team/info', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

## Business Rules

1. **Only Pro users can create teams**
2. **One team per user** - Users can only be in one team at a time
3. **Team quota overrides individual quota** - When in a team, individual limits don't apply
4. **Owner can't leave** - Must transfer ownership or delete team
5. **Invitations expire in 7 days**
6. **Max 10 members per team** (configurable)
7. **Quota resets monthly** - Automatic on reset date
8. **Shared validation history** - All team validations visible to team

## Security Considerations

1. **Token-based invitations** - Secure random tokens
2. **Role-based access control** - Owner/admin/member permissions
3. **Quota enforcement** - Server-side validation
4. **Email verification** - Invitations sent to verified emails
5. **Audit trail** - All actions logged in admin_activity_logs

## Future Enhancements

Potential additions:
- Team analytics dashboard
- Custom role permissions
- Team-specific API keys
- Billing per team
- Team templates/presets
- Bulk member import
- Team activity feed
- Slack/Discord notifications

## Troubleshooting

### Issue: "Only Pro users can create teams"
**Solution**: Verify user's subscription_tier is 'pro' in users table

### Issue: "Team quota exceeded"
**Solution**: Check team quota_used vs quota_limit, wait for monthly reset

### Issue: "Invitation expired"
**Solution**: Generate new invitation, invitations expire after 7 days

### Issue: "User already in a team"
**Solution**: User must leave current team before joining another

### Issue: Team quota not incrementing
**Solution**: Check team_id is being passed to validation endpoints

## Database Queries for Debugging

```sql
-- Check team info
SELECT * FROM team_dashboard WHERE owner_email = 'user@example.com';

-- Check team members
SELECT * FROM team_member_details WHERE team_id = 'your-team-id';

-- Check pending invitations
SELECT * FROM team_invitations WHERE team_id = 'your-team-id' AND status = 'pending';

-- Check team quota usage
SELECT quota_used, quota_limit, usage_percentage 
FROM teams WHERE id = 'your-team-id';

-- Reset team quota (for testing)
UPDATE teams SET quota_used = 0 WHERE id = 'your-team-id';
```

## Support

For issues or questions:
1. Check error logs in browser console
2. Check backend logs in terminal
3. Verify database schema is correctly applied
4. Test API endpoints with Postman/curl
5. Check user's subscription tier and team status

---

**Status**: ✅ Ready for deployment
**Version**: 1.0.0
**Last Updated**: December 19, 2024