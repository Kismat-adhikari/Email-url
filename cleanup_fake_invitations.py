#!/usr/bin/env python3
"""
Clean up fake invitations from the database
Remove all invitations with @temp.com emails or starting with 'invite-'
"""

from supabase_storage import get_storage

def cleanup_fake_invitations():
    """Remove fake invitations from the database"""
    try:
        storage = get_storage()
        
        print("🧹 Cleaning up fake invitations...")
        
        # Get all invitations
        all_invites_result = storage.client.table('team_invitations').select('*').execute()
        
        # Filter fake invitations
        fake_invites = [inv for inv in all_invites_result.data if '@temp.com' in inv['email'] or inv['email'].startswith('invite-')]
        
        if fake_invites:
            print(f"Found {len(fake_invites)} fake invitations to remove:")
            for invite in fake_invites:
                print(f"  - {invite['email']} (Team: {invite['team_id']})")
            
            # Delete fake invitations one by one
            for invite in fake_invites:
                storage.client.table('team_invitations').delete().eq('id', invite['id']).execute()
            
            print(f"✅ Removed {len(fake_invites.data)} fake invitations")
        else:
            print("✅ No fake invitations found")
        
        # Show remaining real invitations
        remaining_invites_result = storage.client.table('team_invitations').select('*').execute()
        real_invites = [inv for inv in remaining_invites_result.data if '@temp.com' not in inv['email'] and not inv['email'].startswith('invite-')]
        
        if real_invites:
            print(f"\n📧 Remaining real invitations ({len(real_invites)}):")
            for invite in real_invites:
                print(f"  - {invite['email']} (Status: {invite['status']})")
        else:
            print("\n📧 No real invitations found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning up invitations: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting fake invitation cleanup...")
    success = cleanup_fake_invitations()
    
    if success:
        print("\n✅ Cleanup completed successfully!")
    else:
        print("\n❌ Cleanup failed. Please check the errors above.")