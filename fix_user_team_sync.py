#!/usr/bin/env python3
"""
Fix user team synchronization - ensure users.team_id matches team_members table
"""

from supabase_storage import get_storage

def fix_user_team_sync():
    """Fix user team synchronization"""
    try:
        storage = get_storage()
        
        print("🔄 Fixing user team synchronization...")
        
        # Get all team members
        team_members = storage.client.table('team_members').select('user_id, team_id, role').execute()
        
        if not team_members.data:
            print("✅ No team members found")
            return True
        
        print(f"📋 Found {len(team_members.data)} team memberships to sync:")
        
        for member in team_members.data:
            user_id = member['user_id']
            team_id = member['team_id']
            role = member['role']
            
            print(f"  🔄 Syncing user {user_id} -> team {team_id} (role: {role})")
            
            # Update users table with team info
            result = storage.client.table('users').update({
                'team_id': team_id,
                'team_role': role
            }).eq('id', user_id).execute()
            
            if result.data:
                print(f"    ✅ Updated user {user_id}")
            else:
                print(f"    ❌ Failed to update user {user_id}")
        
        print("✅ Team synchronization completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    fix_user_team_sync()