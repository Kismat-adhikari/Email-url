#!/usr/bin/env python3
"""
Check team status and quota functions
"""

from supabase_storage import get_storage

def check_team_status():
    """Check team status"""
    try:
        storage = get_storage()
        
        print("🔍 Checking team status...")
        
        # Get all teams
        teams = storage.client.table('teams').select('id, name, is_active, quota_used, quota_limit').execute()
        
        if not teams.data:
            print("❌ No teams found")
            return False
        
        print(f"📋 Found {len(teams.data)} teams:")
        
        for team in teams.data:
            print(f"\n🏢 {team['name']}")
            print(f"   ID: {team['id']}")
            print(f"   Active: {team['is_active']}")
            print(f"   Quota: {team['quota_used']:,}/{team['quota_limit']:,}")
            
            # Test quota check function directly
            try:
                result = storage.client.rpc('check_team_quota', {'team_uuid': team['id'], 'email_count': 1}).execute()
                can_validate = result.data if result.data else False
                print(f"   🔍 Function check_team_quota: {'✅ Yes' if can_validate else '❌ No'}")
            except Exception as e:
                print(f"   ❌ Function error: {e}")
        
        print("\n✅ Team status check completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_team_status()