#!/usr/bin/env python3
"""
Simple check of user team status
"""

from supabase_storage import get_storage

def check_user_team():
    """Check user team status"""
    try:
        storage = get_storage()
        
        print("🔍 Checking user team status...")
        
        # Get all users
        users = storage.client.table('users').select('id, email, subscription_tier, team_id, team_role').execute()
        
        print(f"📋 Found {len(users.data)} users:")
        
        for user in users.data:
            print(f"  👤 {user['email']}")
            print(f"     ID: {user['id']}")
            print(f"     Base tier: {user['subscription_tier']}")
            print(f"     Team ID: {user['team_id']}")
            print(f"     Team role: {user['team_role']}")
            
            # Check if user is in team_members table
            if user['team_id']:
                team_member = storage.client.table('team_members').select('team_id, role').eq('user_id', user['id']).execute()
                if team_member.data:
                    print(f"     ✅ Found in team_members: team={team_member.data[0]['team_id']}, role={team_member.data[0]['role']}")
                else:
                    print(f"     ❌ NOT found in team_members table")
            else:
                team_member = storage.client.table('team_members').select('team_id, role').eq('user_id', user['id']).execute()
                if team_member.data:
                    print(f"     ⚠️  Found in team_members but user.team_id is NULL: team={team_member.data[0]['team_id']}, role={team_member.data[0]['role']}")
                    
                    # Fix this user
                    print(f"     🔄 Fixing user team_id...")
                    storage.client.table('users').update({
                        'team_id': team_member.data[0]['team_id'],
                        'team_role': team_member.data[0]['role']
                    }).eq('id', user['id']).execute()
                    print(f"     ✅ Fixed!")
                else:
                    print(f"     ✅ Not in any team")
            
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_user_team()