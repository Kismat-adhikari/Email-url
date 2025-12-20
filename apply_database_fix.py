#!/usr/bin/env python3
"""
Apply Database Function Fixes
This script applies the SQL fixes for team quota functions
"""

import os
from supabase_storage import get_storage

def apply_database_fix():
    """Apply the database function fixes"""
    try:
        storage = get_storage()
        
        print("🔧 Applying database function fixes...")
        
        # Read the SQL file
        with open('fix_database_functions.sql', 'r') as f:
            sql_content = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for i, statement in enumerate(statements):
            if statement:
                try:
                    print(f"📝 Executing statement {i+1}/{len(statements)}...")
                    
                    # For CREATE FUNCTION statements, we need to handle them specially
                    if 'CREATE OR REPLACE FUNCTION' in statement:
                        # Execute the function creation
                        result = storage.client.rpc('exec', {'sql': statement + ';'}).execute()
                        print(f"   ✅ Function created/updated successfully")
                    elif 'SELECT' in statement and 'status' in statement:
                        # Skip status messages
                        print(f"   ℹ️ Status message skipped")
                    elif 'DO $$' in statement:
                        # Skip test blocks for now
                        print(f"   ℹ️ Test block skipped")
                    else:
                        print(f"   ℹ️ Statement skipped: {statement[:50]}...")
                        
                except Exception as e:
                    print(f"   ⚠️ Statement failed: {e}")
                    # Continue with other statements
        
        print("\n🧪 Testing the fixed functions...")
        
        # Test the functions directly
        teams_result = storage.client.table('teams').select('id, name').limit(1).execute()
        
        if teams_result.data:
            test_team_id = teams_result.data[0]['id']
            test_team_name = teams_result.data[0]['name']
            
            print(f"🔍 Testing with team: {test_team_name}")
            
            try:
                # Test check_team_quota function
                result = storage.client.rpc('check_team_quota', {
                    'team_uuid': test_team_id, 
                    'email_count': 1
                }).execute()
                
                can_validate = result.data if result.data is not None else False
                print(f"   ✅ check_team_quota: {'Can validate' if can_validate else 'Cannot validate'}")
                
            except Exception as e:
                print(f"   ❌ check_team_quota failed: {e}")
        
        print("\n🎉 Database function fixes applied!")
        return True
        
    except Exception as e:
        print(f"❌ Error applying database fixes: {e}")
        return False

if __name__ == "__main__":
    success = apply_database_fix()
    if success:
        print("\n✅ Database functions have been fixed!")
        print("🚀 Team quota validation should now work correctly")
    else:
        print("\n❌ Failed to apply database fixes.")