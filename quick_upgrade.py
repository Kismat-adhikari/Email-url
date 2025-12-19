#!/usr/bin/env python3
"""
Quick script to upgrade a user to Pro tier directly in the database
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def upgrade_user_to_pro():
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY in .env file")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Get the most recent user (likely you)
        users_response = supabase.table('users').select('*').order('created_at', desc=True).limit(5).execute()
        
        if not users_response.data:
            print("❌ No users found")
            return
        
        print("📋 Recent users:")
        for i, user in enumerate(users_response.data):
            print(f"{i+1}. {user['email']} - {user['first_name']} {user['last_name']} - {user['subscription_tier']}")
        
        # Ask which user to upgrade
        choice = input("\nEnter the number of the user to upgrade to Pro (or press Enter for #1): ").strip()
        
        if not choice:
            choice = "1"
        
        try:
            user_index = int(choice) - 1
            selected_user = users_response.data[user_index]
        except (ValueError, IndexError):
            print("❌ Invalid choice")
            return
        
        # Upgrade user to Pro
        update_response = supabase.table('users').update({
            'subscription_tier': 'pro',
            'api_calls_limit': 10000000  # 10M for Pro
        }).eq('id', selected_user['id']).execute()
        
        if update_response.data:
            print(f"✅ Successfully upgraded {selected_user['email']} to Pro tier!")
            print("🔄 Now refresh your browser and try the Team tab.")
        else:
            print("❌ Failed to upgrade user")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    upgrade_user_to_pro()