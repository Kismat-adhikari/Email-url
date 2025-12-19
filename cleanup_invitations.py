#!/usr/bin/env python3
"""
Clean up pending invitations
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def cleanup_invitations():
    print("🧹 Cleaning up pending invitations...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Delete all pending invitations
        result = supabase.table('team_invitations').delete().eq('status', 'pending').execute()
        
        print(f"✅ Cleaned up pending invitations")
        print(f"📊 Deleted {len(result.data) if result.data else 0} pending invitations")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    cleanup_invitations()