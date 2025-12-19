#!/usr/bin/env python3
"""
Check if the new user is actually in the team
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def check_user_team():
    print("🔍 Checking User Team Status...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Get the most recent user (likely the one you just created)
        users_response = supabase.table('users').select('*').order('created_at', desc=True).limit(3).execute()
        
        print("📋 Recent users:")
        for i, user in enumerate(users_response.data, 1):
            team_status = f"Team: {user.get('team_id', 'None')}" if user.get('team_id') else "No team"
            print(f"{i}. {user['email']} - {user['subscription_tier']} - {team_status}")
        
        # Check team members
        print("\n👥 Team members:")
        team_members = supabase.table('team_member_details').select('*').execute()
        
        for member in team_members.data:
            print(f"- {member['email']} ({member['role']}) in team '{member['team_name']}'")
        
        # Check recent invitations
        print("\n📨 Recent invitations:")
        invitations = supabase.table('team_invitations').select('*').order('created_at', desc=True).limit(3).execute()
        
        for invite in invitations.data:
            print(f"- {invite['email']} - Status: {invite['status']} - Token: {invite['invite_token'][:20]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_user_team()