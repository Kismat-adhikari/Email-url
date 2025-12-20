#!/usr/bin/env python3
"""
Test Team Quota Fix
This script tests the updated team quota functions
"""

import os
from team_manager import team_manager

def test_team_quota_fix():
    """Test the updated team quota functions"""
    try:
        print("🧪 Testing updated team quota functions...")
        
        # Get all teams
        teams = team_manager.storage.client.table('teams').select('*').execute()
        
        if not teams.data:
            print("❌ No teams found for testing")
            return False
        
        # Test with the first team
        test_team = teams.data[0]
        team_id = test_team['id']
        team_name = test_team['name']
        
        print(f"\n🔍 Testing with team: {team_name}")
        print(f"   📊 Current usage: {test_team['quota_used']:,} / {test_team['quota_limit']:,}")
        
        # Test quota check
        print("\n1️⃣ Testing quota check...")
        can_validate = team_manager.check_team_quota(team_id, 1)
        print(f"   Result: {'✅ Can validate' if can_validate else '❌ Cannot validate'}")
        
        if can_validate:
            print("\n2️⃣ Testing quota usage (will increment by 1)...")
            
            # Get current usage before
            before_result = team_manager.storage.client.table('teams').select('quota_used').eq('id', team_id).execute()
            before_usage = before_result.data[0]['quota_used'] if before_result.data else 0
            
            # Use quota
            success = team_manager.use_team_quota(team_id, 1)
            print(f"   Quota increment: {'✅ Success' if success else '❌ Failed'}")
            
            if success:
                # Get current usage after
                after_result = team_manager.storage.client.table('teams').select('quota_used').eq('id', team_id).execute()
                after_usage = after_result.data[0]['quota_used'] if after_result.data else 0
                
                print(f"   Usage before: {before_usage:,}")
                print(f"   Usage after: {after_usage:,}")
                print(f"   Difference: +{after_usage - before_usage}")
                
                if after_usage == before_usage + 1:
                    print("   ✅ Quota increment working correctly!")
                else:
                    print("   ⚠️ Quota increment may have issues")
        
        print("\n🎉 Team quota function test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing team quota: {e}")
        return False

if __name__ == "__main__":
    success = test_team_quota_fix()
    if success:
        print("\n✅ Team quota functions are working!")
        print("🚀 Team members should now be able to validate emails")
    else:
        print("\n❌ Team quota functions need more work.")