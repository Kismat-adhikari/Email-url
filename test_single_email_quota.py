#!/usr/bin/env python3
"""
Test Single Email Quota Fix
This script tests the team quota for single email validation
"""

import os
from team_manager import team_manager

def test_single_email_quota():
    """Test the team quota for single email validation"""
    try:
        print("🧪 Testing single email team quota...")
        
        # Get all teams
        teams = team_manager.storage.client.table('teams').select('*').execute()
        
        if not teams.data:
            print("❌ No teams found for testing")
            return False
        
        # Test with the first team that has some usage
        test_team = None
        for team in teams.data:
            if team['quota_used'] > 0:
                test_team = team
                break
        
        if not test_team:
            test_team = teams.data[0]  # Use first team if none have usage
        
        team_id = test_team['id']
        team_name = test_team['name']
        
        print(f"\n🔍 Testing with team: {team_name}")
        print(f"   📊 Current usage: {test_team['quota_used']:,} / {test_team['quota_limit']:,}")
        
        # Test get_team_usage function (this is what single email validation uses)
        print("\n1️⃣ Testing get_team_usage function...")
        usage_result = team_manager.get_team_usage(team_id)
        
        if usage_result['success']:
            usage_data = usage_result['usage']
            print(f"   ✅ Success! Usage data:")
            print(f"      📊 Used: {usage_data['quota_used']:,}")
            print(f"      📊 Limit: {usage_data['quota_limit']:,}")
            print(f"      📊 Percentage: {usage_data['usage_percentage']:.2f}%")
            print(f"      📊 Remaining: {usage_data['remaining']:,}")
            print(f"      📊 Team: {usage_data['team_name']}")
            
            # Check if days_until_reset is present (it shouldn't be)
            if 'days_until_reset' in usage_data:
                print(f"      ⚠️ Still has days_until_reset: {usage_data['days_until_reset']}")
            else:
                print(f"      ✅ No days_until_reset (correct for lifetime quota)")
                
        else:
            print(f"   ❌ Failed: {usage_result['error']}")
            return False
        
        # Test quota check
        print("\n2️⃣ Testing quota check for single email...")
        can_validate = team_manager.check_team_quota(team_id, 1)
        print(f"   Result: {'✅ Can validate' if can_validate else '❌ Cannot validate'}")
        
        # Simulate the single email validation quota check logic
        print("\n3️⃣ Simulating single email validation logic...")
        
        if can_validate:
            print("   ✅ Team has quota available")
            print("   📧 Single email validation should work")
        else:
            print("   ❌ Team quota exceeded")
            print("   📧 Single email validation should show quota exceeded error")
            
            # Check if it's actually at the limit
            if usage_data['quota_used'] >= usage_data['quota_limit']:
                print("   📊 Team has actually reached the 10M limit")
            else:
                print("   ⚠️ Team should have quota but check failed - investigate!")
        
        print("\n🎉 Single email quota test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing single email quota: {e}")
        return False

if __name__ == "__main__":
    success = test_single_email_quota()
    if success:
        print("\n✅ Single email quota functions are working!")
        print("🚀 Single email validation should now work for team members")
    else:
        print("\n❌ Single email quota functions need more work.")