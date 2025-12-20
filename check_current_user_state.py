#!/usr/bin/env python3
"""
Check current user state in database
"""

from supabase_storage import get_storage

def check_user_state():
    """Check current user state"""
    try:
        storage = get_storage()
        
        # Check the user that's having issues
        user_id = 'd7562a67-300b-4703-ac8d-bc00541a0f6c'  # kismat@gmail.com from debug output
        
        print(f"🔍 Checking current state for user: {user_id}")
        
        # Direct database query
        user_result = storage.client.table('users').select('*').eq('id', user_id).execute()
        
        if not user_result.data:
            print(f"❌ User not found in database")
            return
        
        user = user_result.data[0]
        
        print(f"\n📊 Current database state:")
        print(f"   Email: {user.get('email')}")
        print(f"   Base tier: {user.get('subscription_tier')}")
        print(f"   Team ID: {user.get('team_id')}")
        print(f"   Team role: {user.get('team_role')}")
        print(f"   Updated at: {user.get('updated_at')}")
        
        # Check team_members table
        if user.get('team_id'):
            team_member_result = storage.client.table('team_members').select('*').eq('user_id', user_id).execute()
            if team_member_result.data:
                member = team_member_result.data[0]
                print(f"\n🏢 Team membership:")
                print(f"   Team ID: {member.get('team_id')}")
                print(f"   Role: {member.get('role')}")
                print(f"   Joined at: {member.get('created_at')}")
                
                # Check if team is active
                team_result = storage.client.table('teams').select('*').eq('id', member['team_id']).execute()
                if team_result.data:
                    team = team_result.data[0]
                    print(f"\n🏢 Team details:")
                    print(f"   Name: {team.get('name')}")
                    print(f"   Active: {team.get('is_active')}")
                    print(f"   Quota: {team.get('quota_used')}/{team.get('quota_limit')}")
                else:
                    print(f"\n❌ Team not found: {member['team_id']}")
            else:
                print(f"\n❌ User not found in team_members table")
        
        # Test effective tier calculation
        from app_anon_history import get_effective_subscription_tier
        effective_tier = get_effective_subscription_tier(user)
        print(f"\n🎯 Effective tier calculation: {effective_tier}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_user_state()