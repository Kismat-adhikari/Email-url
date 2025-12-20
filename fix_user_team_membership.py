#!/usr/bin/env python3
"""
Fix user team membership - sync team_members table with users table
This ensures users have the correct team_id in their user record
"""

from supabase_storage import get_storage

def fix_user_team_membership():
    """Fix user team membership by syncing team_members with users table"""
    try:
        storage = get_storage()
        
        print("🔧 Fixing user team membership...")
        
        # Get all team members
        team_members = storage.client.table('team_members').select('user_id, team_id, role').eq('is_active', True).execute()
        
        if not team_members.data:
            print("❌ No team members found")
            return False
        
        print(f"📋 Found {len(team_members.data)} team members:")
        
        for member in team_members.data:
            user_id = member['user_id']
            team_id = member['team_id']
            role = member['role']
            
            # Get current user data
            user_result = storage.client.table('users').select('id, email, team_id, team_role, subscription_tier').eq('id', user_id).execute()
            
            if user_result.data:
                user = user_result.data[0]
                current_team_id = user.get('team_id')
                current_role = user.get('team_role')
                
                print(f"  👤 {user['email']} (tier: {user['subscription_tier']})")
                print(f"     Current: team_id={current_team_id}, role={current_role}")
                print(f"     Should be: team_id={team_id}, role={role}")
                
                # Update user if team info is missing or incorrect
                if current_team_id != team_id or current_role != role:
                    print(f"     🔄 Updating user team info...")
                    
                    update_result = storage.client.table('users').update({
                        'team_id': team_id,
                        'team_role': role
                    }).eq('id', user_id).execute()
                    
                    if update_result.data:
                        print(f"     ✅ Updated successfully")
                    else:
                        print(f"     ❌ Update failed")
                else:
                    print(f"     ✅ Already correct")
            else:
                print(f"  ❌ User {user_id} not found")
        
        print("\n🔍 Verifying fixes...")
        
        # Verify all team members now have correct user records
        for member in team_members.data:
            user_id = member['user_id']
            team_id = member['team_id']
            
            user_result = storage.client.table('users').select('email, team_id, subscription_tier').eq('id', user_id).execute()
            if user_result.data:
                user = user_result.data[0]
                if user['team_id'] == team_id:
                    print(f"  ✅ {user['email']} - team_id correct, tier: {user['subscription_tier']}")
                else:
                    print(f"  ❌ {user['email']} - team_id still wrong: {user['team_id']} != {team_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing team membership: {e}")
        return False

def test_effective_tier():
    """Test the effective tier calculation for team members"""
    try:
        storage = get_storage()
        
        print("\n🧪 Testing effective tier calculation...")
        
        # Get all users with teams
        users_with_teams = storage.client.table('users').select('id, email, subscription_tier, team_id').not_.is_('team_id', 'null').execute()
        
        if users_with_teams.data:
            for user in users_with_teams.data:
                print(f"  👤 {user['email']}")
                print(f"     Base tier: {user['subscription_tier']}")
                print(f"     Team ID: {user['team_id']}")
                
                # Test effective tier calculation
                from app_anon_history import get_effective_subscription_tier
                effective_tier = get_effective_subscription_tier(user)
                print(f"     Effective tier: {effective_tier}")
                
                if user['team_id'] and effective_tier != 'pro':
                    print(f"     ❌ ERROR: Should be 'pro' but got '{effective_tier}'")
                else:
                    print(f"     ✅ Correct effective tier")
        else:
            print("  ❌ No users with teams found")
        
    except Exception as e:
        print(f"❌ Error testing effective tier: {e}")

if __name__ == "__main__":
    print("🚀 Starting user team membership fix...")
    success = fix_user_team_membership()
    
    if success:
        test_effective_tier()
        print("\n✅ Fix completed!")
        print("🔄 Please restart your backend server to apply changes")
    else:
        print("\n❌ Fix failed. Please check the errors above.")