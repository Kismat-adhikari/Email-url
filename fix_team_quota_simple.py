#!/usr/bin/env python3
"""
Fix Team Quota to Lifetime - Simple Version
This script updates team quota settings directly
"""

import os
from supabase_storage import get_storage

def fix_team_quota_simple():
    """Update team quota settings directly"""
    try:
        storage = get_storage()
        
        print("🔧 Fixing team quota settings...")
        
        # 1. Update all teams to have 10M quota limit
        print("📊 Updating team quota limits to 10M...")
        
        teams_result = storage.client.table('teams').select('*').execute()
        
        if teams_result.data:
            for team in teams_result.data:
                # Update each team to have 10M quota
                update_result = storage.client.table('teams').update({
                    'quota_limit': 10000000,  # 10M lifetime validations
                    'updated_at': 'now()'
                }).eq('id', team['id']).execute()
                
                print(f"   ✅ Updated team '{team['name']}' to 10M quota")
        
        # 2. Verify the changes
        print("\n📊 Verifying team quota settings...")
        
        teams_result = storage.client.table('teams').select('id, name, quota_used, quota_limit, created_at').execute()
        
        if teams_result.data:
            print(f"\n🏆 Found {len(teams_result.data)} team(s):")
            for team in teams_result.data:
                usage_pct = (team['quota_used'] / team['quota_limit']) * 100 if team['quota_limit'] > 0 else 0
                remaining = team['quota_limit'] - team['quota_used']
                print(f"   📋 {team['name']}")
                print(f"      💾 Usage: {team['quota_used']:,} / {team['quota_limit']:,} ({usage_pct:.3f}%)")
                print(f"      🔄 Remaining: {remaining:,} validations")
                print(f"      📅 Created: {team['created_at']}")
                
                if team['quota_limit'] == 10000000:
                    print(f"      ✅ Quota correctly set to 10M")
                else:
                    print(f"      ❌ Quota incorrect: {team['quota_limit']}")
                print()
        else:
            print("   ℹ️ No teams found")
        
        print("🎉 Team quota update completed!")
        print("📝 All teams now have 10M lifetime validations")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing team quota: {e}")
        return False

if __name__ == "__main__":
    success = fix_team_quota_simple()
    if success:
        print("\n✅ Team quota has been fixed!")
        print("🚀 Team members can now use the full 10M shared quota")
        print("💡 The error message has also been updated to show 'lifetime' instead of 'monthly'")
    else:
        print("\n❌ Failed to fix team quota. Please check the error above.")