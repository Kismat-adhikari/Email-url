#!/usr/bin/env python3
"""
Check team_dashboard table to see what data is being returned
"""

from supabase_storage import get_storage

def check_team_dashboard():
    """Check team dashboard data"""
    try:
        storage = get_storage()
        
        print("🔍 Checking team_dashboard table...")
        
        # Get all team dashboard data
        dashboard_result = storage.client.table('team_dashboard').select('*').execute()
        
        if not dashboard_result.data:
            print("❌ No data in team_dashboard table")
            return False
        
        print(f"📋 Found {len(dashboard_result.data)} teams in dashboard:")
        
        for team in dashboard_result.data:
            print(f"\n🏢 Team: {team.get('name')}")
            print(f"   ID: {team.get('id')}")
            print(f"   Quota Used: {team.get('quota_used')}")
            print(f"   Quota Limit: {team.get('quota_limit')}")
            print(f"   Usage %: {team.get('usage_percentage')}")
            print(f"   Is Active: {team.get('is_active')}")
            print(f"   Member Count: {team.get('member_count')}")
        
        # Also check the actual teams table for comparison
        print(f"\n🔍 Checking actual teams table for comparison...")
        teams_result = storage.client.table('teams').select('id, name, quota_used, quota_limit, is_active').execute()
        
        if teams_result.data:
            print(f"📋 Found {len(teams_result.data)} teams in teams table:")
            
            for team in teams_result.data:
                print(f"\n🏢 Team: {team.get('name')}")
                print(f"   ID: {team.get('id')}")
                print(f"   Quota Used: {team.get('quota_used')}")
                print(f"   Quota Limit: {team.get('quota_limit')}")
                print(f"   Is Active: {team.get('is_active')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_team_dashboard()