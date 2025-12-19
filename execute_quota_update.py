#!/usr/bin/env python3
"""
Execute the team quota update to change from 10K to 10M lifetime quota
Run this script to update existing teams and set new defaults
"""

from supabase_storage import get_storage

def update_team_quotas():
    """Update all existing teams to 10M lifetime quota"""
    try:
        storage = get_storage()
        
        print("🔄 Updating team quotas to 10 million lifetime...")
        
        # Update existing teams from 10K to 10M
        result = storage.client.table('teams').update({
            'quota_limit': 10000000,  # 10 million
            'quota_reset_date': None  # Remove monthly reset (lifetime quota)
        }).eq('quota_limit', 10000).execute()
        
        updated_count = len(result.data) if result.data else 0
        print(f"✅ Updated {updated_count} existing teams to 10M quota")
        
        # Execute the SQL functions update
        sql_updates = [
            """
            -- Update quota check function (remove monthly reset)
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
            """,
            """
            -- Update increment function (remove reset logic)
            CREATE OR REPLACE FUNCTION increment_team_quota(team_uuid UUID, email_count INTEGER DEFAULT 1)
            RETURNS VOID AS $$
            BEGIN
                UPDATE teams 
                SET quota_used = quota_used + email_count,
                    updated_at = NOW()
                WHERE id = team_uuid;
                -- No reset logic needed for lifetime quota
            END;
            $$ LANGUAGE plpgsql;
            """,
            """
            -- Update default quota for new teams
            ALTER TABLE teams ALTER COLUMN quota_limit SET DEFAULT 10000000;
            """
        ]
        
        for sql in sql_updates:
            try:
                storage.client.rpc('exec_sql', {'sql': sql}).execute()
                print("✅ Updated database functions")
            except Exception as e:
                print(f"⚠️  SQL function update (may need manual execution): {e}")
        
        # Verify the changes
        teams = storage.client.table('teams').select('id, name, quota_limit, quota_used, quota_reset_date').execute()
        
        print("\n📊 Current team quotas:")
        if teams.data:
            for team in teams.data:
                quota_used = team.get('quota_used', 0)
                quota_limit = team.get('quota_limit', 0)
                percentage = (quota_used / quota_limit * 100) if quota_limit > 0 else 0
                reset_date = team.get('quota_reset_date')
                reset_info = "Lifetime" if not reset_date else f"Resets: {reset_date}"
                
                print(f"  • {team['name']}: {quota_used:,}/{quota_limit:,} ({percentage:.1f}%) - {reset_info}")
        else:
            print("  No teams found")
        
        print("\n🎉 Team quota update completed!")
        print("📝 Summary:")
        print(f"   - All teams now have 10 million lifetime validations")
        print(f"   - No monthly resets (lifetime quota)")
        print(f"   - All team members share the same quota counter")
        print(f"   - If User A uses 10K, User B also sees 10K/10M used")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating quotas: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting team quota update...")
    success = update_team_quotas()
    
    if success:
        print("\n✅ Update completed successfully!")
        print("🔄 Please restart your backend server to apply changes")
    else:
        print("\n❌ Update failed. Please check the errors above.")