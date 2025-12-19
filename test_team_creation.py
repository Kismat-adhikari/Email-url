#!/usr/bin/env python3
"""
Test script to create a team and generate invitation link
This bypasses the frontend to test the backend directly
"""

import os
import requests
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def test_team_functionality():
    print("🧪 Testing Team Functionality...")
    
    # Get Supabase connection
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # 1. Find your Pro user
        print("\n1️⃣ Finding Pro user...")
        users_response = supabase.table('users').select('*').eq('email', 'kismat@gmail.com').execute()
        
        if not users_response.data:
            print("❌ No Pro users found")
            return
        
        user = users_response.data[0]
        user_id = user['id']
        user_email = user['email']
        
        print(f"✅ Found Pro user: {user_email} (ID: {user_id})")
        print(f"   Subscription: {user['subscription_tier']}")
        print(f"   Current team_id: {user.get('team_id', 'None')}")
        
        # 2. Check if user can create team using the database function
        print("\n2️⃣ Testing can_create_team function...")
        
        function_result = supabase.rpc('can_create_team', {'user_uuid': user_id}).execute()
        can_create = function_result.data
        
        print(f"✅ can_create_team result: {can_create}")
        
        if not can_create:
            print("❌ User cannot create team according to database function")
            
            # Check why
            if user.get('team_id'):
                print(f"   Reason: User is already in team {user['team_id']}")
            else:
                print(f"   Reason: Subscription tier '{user['subscription_tier']}' not allowed")
            return
        
        # 3. Create a team directly in database
        print("\n3️⃣ Creating team directly...")
        
        team_data = {
            'name': 'Test Team from Backend',
            'owner_id': user_id,
            'description': 'Team created by test script',
            'quota_limit': 10000,
            'quota_used': 0
        }
        
        team_response = supabase.table('teams').insert(team_data).execute()
        
        if not team_response.data:
            print("❌ Failed to create team")
            return
        
        team = team_response.data[0]
        team_id = team['id']
        
        print(f"✅ Team created: {team['name']} (ID: {team_id})")
        
        # 4. Add owner as team member
        print("\n4️⃣ Adding owner as team member...")
        
        member_data = {
            'team_id': team_id,
            'user_id': user_id,
            'role': 'owner',
            'invited_by': user_id
        }
        
        member_response = supabase.table('team_members').insert(member_data).execute()
        
        if member_response.data:
            print("✅ Owner added to team")
        else:
            print("❌ Failed to add owner to team")
        
        # 5. Create an invitation
        print("\n5️⃣ Creating invitation...")
        
        import secrets
        invite_token = f"invite_{secrets.token_urlsafe(32)}"
        
        invitation_data = {
            'team_id': team_id,
            'email': 'test-member@example.com',
            'invite_token': invite_token,
            'invited_by': user_id,
            'message': 'Join our test team!'
        }
        
        invite_response = supabase.table('team_invitations').insert(invitation_data).execute()
        
        if not invite_response.data:
            print("❌ Failed to create invitation")
            return
        
        invitation = invite_response.data[0]
        
        print(f"✅ Invitation created: {invitation['id']}")
        
        # 6. Generate invitation link
        base_url = "http://localhost:3000"
        invite_link = f"{base_url}/invite/{invite_token}"
        
        print(f"\n🔗 INVITATION LINK:")
        print(f"   {invite_link}")
        
        # 7. Test API endpoints
        print(f"\n6️⃣ Testing API endpoints...")
        
        # We need a valid JWT token for API testing
        # For now, let's just show the direct database results
        
        # Check team dashboard view
        dashboard_response = supabase.table('team_dashboard').select('*').eq('id', team_id).execute()
        
        if dashboard_response.data:
            dashboard = dashboard_response.data[0]
            print(f"✅ Team Dashboard:")
            print(f"   Name: {dashboard['name']}")
            print(f"   Owner: {dashboard['owner_email']}")
            print(f"   Quota: {dashboard['quota_used']}/{dashboard['quota_limit']}")
            print(f"   Members: {dashboard['member_count']}")
        
        print(f"\n🎯 TESTING INSTRUCTIONS:")
        print(f"1. Open this link in a different browser: {invite_link}")
        print(f"2. You should see the invitation page")
        print(f"3. Register a new account or login")
        print(f"4. Accept the invitation")
        print(f"5. Check if you get Pro access")
        
        print(f"\n📊 CURRENT STATUS:")
        print(f"✅ Team created successfully")
        print(f"✅ Invitation generated")
        print(f"✅ Database functions working")
        print(f"🔗 Test the invitation link above!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_team_functionality()