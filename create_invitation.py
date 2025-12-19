#!/usr/bin/env python3
"""
Create a fresh invitation link for testing
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def create_invitation():
    print("🔗 Creating Fresh Invitation Link...")
    
    # Get Supabase connection
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Find existing team
        teams_response = supabase.table('teams').select('*').limit(1).execute()
        
        if not teams_response.data:
            print("❌ No teams found")
            return
        
        team = teams_response.data[0]
        team_id = team['id']
        
        print(f"✅ Using team: {team['name']} (ID: {team_id})")
        
        # Find team owner
        owner_response = supabase.table('users').select('*').eq('id', team['owner_id']).execute()
        
        if not owner_response.data:
            print("❌ Team owner not found")
            return
        
        owner = owner_response.data[0]
        
        # Create a fresh invitation
        invite_token = f"invite_{secrets.token_urlsafe(32)}"
        
        invitation_data = {
            'team_id': team_id,
            'email': 'newmember@example.com',
            'invite_token': invite_token,
            'invited_by': owner['id'],
            'message': 'Join our team! This is a fresh invitation with timezone fixes.',
            'expires_at': (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        }
        
        invite_response = supabase.table('team_invitations').insert(invitation_data).execute()
        
        if not invite_response.data:
            print("❌ Failed to create invitation")
            return
        
        invitation = invite_response.data[0]
        
        print(f"✅ Fresh invitation created: {invitation['id']}")
        
        # Generate invitation link
        base_url = "http://localhost:3000"
        invite_link = f"{base_url}/invite/{invite_token}"
        
        print(f"\n🔗 FRESH INVITATION LINK (with timezone fixes):")
        print(f"   {invite_link}")
        
        print(f"\n🎯 TEST THIS LINK:")
        print(f"1. Open in different browser/incognito")
        print(f"2. Should show invitation page (no server error)")
        print(f"3. Register new account or login")
        print(f"4. Accept invitation")
        print(f"5. Check if you get Pro access")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_invitation()