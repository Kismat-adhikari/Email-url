#!/usr/bin/env python3
"""
Check Team Table Structure
"""

from supabase_storage import get_storage

def check_team_structure():
    """Check the actual structure of teams table"""
    try:
        storage = get_storage()
        
        # Get one team to see the structure
        result = storage.client.table('teams').select('*').limit(1).execute()
        
        if result.data:
            team = result.data[0]
            print("Team table structure:")
            for key, value in team.items():
                print(f"  {key}: {value} ({type(value).__name__})")
        else:
            print("No teams found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_team_structure()