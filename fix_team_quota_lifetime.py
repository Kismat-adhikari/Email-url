#!/usr/bin/env python3
"""
Fix Team Quota to Lifetime (No Monthly Reset)
This script updates the database functions to use lifetime quota instead of monthly reset
"""

import os
from supabase_storage import get_storage

def fix_team_quota():
    """Update team quota to lifetime (remove monthly reset)"""
    try:
        storage = get_storage()
        
        print("🔧 Fixing team quota to lifetime (removing monthly reset)...")
        
        # 1. Update the check_team_quota function to remove monthly reset
        check_quota_sql = """
        CREATE OR REPLACE FUNCTION check_team_quota(team_uuid UUID, email_count INTEGER DEFAULT 1)
        RETURNS BOOLEAN AS $$
        DECLARE
            current_usage INTEGER;
            quota_limit INTEGER;
        BEGIN
            SELECT quota_used, quota_limit 
            INTO current_usage, quota_limit
            FROM teams WHERE id = team_uuid AND is_active = TRUE;
            
            -- Simple lifetime quota check (no reset)
            RETURN (current_usage + email_count) <= quota_limit;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        result = storage.client.rpc('exec_sql', {'sql': check_quota_sql}).execute()
        print("✅ Updated check_team_quota function (removed monthly reset)")
        
        # 2. Update increment_team_quota function to remove reset logic
        increment_quota_sql = """
        CREATE OR REPLACE FUNCTION increment_team_quota(team_uuid UUID, email_count INTEGER DEFAULT 1)
        RETURNS VOID AS $$
        DECLARE
            current_usage INTEGER;
            quota_limit INTEGER;
        BEGIN
            SELECT quota_used, quota_limit 
            INTO current_usage, quota_limit
            FROM teams WHERE id = team_uuid AND is_active = TRUE;
            
            -- Simple increment (no reset logic)
            UPDATE teams 
            SET quota_used = quota_used + email_count,
                updated_at = NOW()
            WHERE id = team_uuid AND is_active = TRUE;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        result = storage.client.rpc('exec_sql', {'sql': increment_quota_sql}).execute()
        print("✅ Updated increment_team_quota function (removed monthly reset)")
        
        # 3. Ensure all teams have 10M quota limit
        update_limits_sql = """
        UPDATE teams 
        SET quota_limit = 10000000,
            updated_at = NOW()
        WHERE quota_limit != 10000000;
        """
        
        result = storage.client.rpc('exec_sql', {'sql': update_limits_sql}).execute()
        print("✅ Updated all teams to 10M lifetime quota")
        
        # 4. Verify the changes
        print("\n📊 Verifying team quota settings...")
        
        teams_result = storage.client.table('teams').select('id, name, quota_used, quota_limit, created_at').execute()
        
        if teams_result.data:
            print(f"\n🏆 Found {len(teams_result.data)} team(s):")
            for team in teams_result.data:
                usage_pct = (team['quota_used'] / team['quota_limit']) * 100 if team['quota_limit'] > 0 else 0
                print(f"   📋 {team['name']}")
                print(f"      💾 Usage: {team['quota_used']:,} / {team['quota_limit']:,} ({usage_pct:.3f}%)")
                print(f"      📅 Created: {team['created_at']}")
                print()
        else:
            print("   ℹ️ No teams found")
        
        print("🎉 Team quota fix completed successfully!")
        print("📝 Teams now have 10M lifetime validations (no monthly reset)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing team quota: {e}")
        return False

if __name__ == "__main__":
    success = fix_team_quota()
    if success:
        print("\n✅ All team quota issues have been resolved!")
        print("🚀 Team members can now use the full 10M shared quota")
    else:
        print("\n❌ Failed to fix team quota. Please check the error above.")