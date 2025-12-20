"""
Team Management System for Email Validator
Handles team creation, invitations, and quota management for Pro users
"""

import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from supabase_storage import get_storage

class TeamManager:
    def __init__(self):
        self.storage = get_storage()
        # Simple in-memory cache for team info (expires after 30 seconds)
        self._team_cache = {}
        self._cache_timeout = 30  # seconds
    
    # ==================== CACHE HELPERS ====================
    
    def _get_cache_key(self, team_id: str, user_id: str) -> str:
        """Generate cache key for team info"""
        return f"team_{team_id}_{user_id}"
    
    def _is_cache_valid(self, cache_entry: dict) -> bool:
        """Check if cache entry is still valid"""
        import time
        return time.time() - cache_entry['timestamp'] < self._cache_timeout
    
    def _get_cached_team_info(self, team_id: str, user_id: str) -> dict:
        """Get team info from cache if valid"""
        cache_key = self._get_cache_key(team_id, user_id)
        if cache_key in self._team_cache:
            cache_entry = self._team_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                return cache_entry['data']
        return None
    
    def _cache_team_info(self, team_id: str, user_id: str, data: dict):
        """Cache team info with timestamp"""
        import time
        cache_key = self._get_cache_key(team_id, user_id)
        self._team_cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        
        # Clean old cache entries (simple cleanup)
        current_time = time.time()
        keys_to_remove = []
        for key, entry in self._team_cache.items():
            if current_time - entry['timestamp'] > self._cache_timeout * 2:  # Remove entries older than 2x timeout
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._team_cache[key]
    
    def _invalidate_team_cache(self, team_id: str):
        """Invalidate all cache entries for a specific team"""
        keys_to_remove = []
        for key in self._team_cache.keys():
            if key.startswith(f"team_{team_id}_"):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._team_cache[key]

    # ==================== TEAM CREATION ====================
    
    def create_team(self, owner_id: str, team_name: str, description: str = "") -> Dict:
        """Create a new team (Pro users only)"""
        try:
            # Check if user can create team (must be Pro and not in a team)
            can_create = self.storage.client.rpc('can_create_team', {'user_uuid': owner_id}).execute()
            if not can_create.data:
                return {"success": False, "error": "Only Starter/Pro users who aren't in a team can create teams"}
            
            # Create the team
            team_data = {
                'name': team_name,
                'owner_id': owner_id,
                'description': description,
                'quota_limit': 10000000,  # Pro tier gets 10M lifetime validations
                'quota_used': 0
            }
            
            result = self.storage.client.table('teams').insert(team_data).execute()
            if not result.data:
                return {"success": False, "error": "Failed to create team"}
            
            team = result.data[0]
            team_id = team['id']
            
            # Add owner as team member with 'owner' role
            member_data = {
                'team_id': team_id,
                'user_id': owner_id,
                'role': 'owner',
                'invited_by': owner_id
            }
            
            self.storage.client.table('team_members').insert(member_data).execute()
            
            # CRITICAL: Update users table with team_id and team_role for owner
            # This ensures effective tier calculation works correctly
            self.storage.client.table('users').update({
                'team_id': team_id,
                'team_role': 'owner'
            }).eq('id', owner_id).execute()
            
            # Invalidate cache since team structure changed
            self._invalidate_team_cache(team_id)
            
            return {
                "success": True,
                "team": team,
                "message": f"Team '{team_name}' created successfully!"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error creating team: {str(e)}"}
    
    # ==================== TEAM INVITATIONS ====================
    
    def generate_invitation(self, team_id: str, inviter_id: str, email: str, message: str = "") -> Dict:
        """Generate team invitation link"""
        try:
            # Check if inviter has permission (owner or admin)
            member_check = self.storage.client.table('team_members').select('role').eq('team_id', team_id).eq('user_id', inviter_id).execute()
            if not member_check.data or member_check.data[0]['role'] not in ['owner', 'admin']:
                return {"success": False, "error": "Only team owners and admins can invite members"}
            
            # Check team member limit
            team_info = self.storage.client.table('team_dashboard').select('member_count, max_members').eq('id', team_id).execute()
            if team_info.data and team_info.data[0]['member_count'] >= team_info.data[0]['max_members']:
                return {"success": False, "error": "Team has reached maximum member limit"}
            
            # Check if email is already invited or is a member
            existing_invite = self.storage.client.table('team_invitations').select('id').eq('team_id', team_id).eq('email', email).eq('status', 'pending').execute()
            if existing_invite.data:
                return {"success": False, "error": "User already has a pending invitation"}
            
            # Check if user is already a team member
            existing_user = self.storage.client.table('users').select('id, team_id').eq('email', email).execute()
            if existing_user.data and existing_user.data[0]['team_id']:
                return {"success": False, "error": "User is already in a team"}
            
            # Generate invitation
            invite_token = self.generate_invite_token()
            invitation_data = {
                'team_id': team_id,
                'email': email,
                'invite_token': invite_token,
                'invited_by': inviter_id,
                'message': message,
                'expires_at': (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
            }
            
            result = self.storage.client.table('team_invitations').insert(invitation_data).execute()
            if not result.data:
                return {"success": False, "error": "Failed to create invitation"}
            
            invitation = result.data[0]
            
            # Generate invitation link
            base_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            invite_link = f"{base_url}/invite/{invite_token}"
            
            # Generate invitation link only (no email sending)
            return {
                "success": True,
                "invitation": invitation,
                "invite_link": invite_link,
                "message": f"Invitation link created for {email}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error creating invitation: {str(e)}"}
    
    def accept_invitation(self, invite_token: str, user_id: str) -> Dict:
        """Accept team invitation"""
        try:
            # Get invitation details
            invite_result = self.storage.client.table('team_invitations').select('*').eq('invite_token', invite_token).eq('status', 'pending').execute()
            if not invite_result.data:
                return {"success": False, "error": "Invalid or expired invitation"}
            
            invitation = invite_result.data[0]
            
            # Check if invitation is expired
            from datetime import timezone
            expires_at = datetime.fromisoformat(invitation['expires_at'].replace('Z', '+00:00'))
            now_utc = datetime.now(timezone.utc)
            if expires_at < now_utc:
                return {"success": False, "error": "Invitation has expired"}
            
            # Check if user is already in a team
            user_check = self.storage.client.table('users').select('team_id').eq('id', user_id).execute()
            if user_check.data and user_check.data[0]['team_id']:
                return {"success": False, "error": "You are already in a team"}
            
            # Add user to team
            member_data = {
                'team_id': invitation['team_id'],
                'user_id': user_id,
                'role': 'member',
                'invited_by': invitation['invited_by']
            }
            
            self.storage.client.table('team_members').insert(member_data).execute()
            
            # CRITICAL: Update users table with team_id and team_role
            # This ensures effective tier calculation works correctly
            self.storage.client.table('users').update({
                'team_id': invitation['team_id'],
                'team_role': 'member'
            }).eq('id', user_id).execute()
            
            # Mark invitation as accepted
            self.storage.client.table('team_invitations').update({
                'status': 'accepted',
                'used_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', invitation['id']).execute()
            
            # Invalidate cache since team membership changed
            self._invalidate_team_cache(invitation['team_id'])
            
            return {
                "success": True,
                "team_id": invitation['team_id'],
                "message": "Successfully joined the team!"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error accepting invitation: {str(e)}"}
    
    # ==================== TEAM MANAGEMENT ====================
    
    def get_team_info(self, team_id: str, user_id: str) -> Dict:
        """Get team information for a member - optimized with caching and parallel queries"""
        try:
            # Check cache first for faster response
            cached_data = self._get_cached_team_info(team_id, user_id)
            if cached_data:

                return cached_data
            
            # First, quickly check if user is a team member
            user_role_result = self.storage.client.table('team_members').select('role').eq('team_id', team_id).eq('user_id', user_id).execute()
            if not user_role_result.data:
                return {"success": False, "error": "You are not a member of this team"}
            
            user_role = user_role_result.data[0]['role']
            
            # OPTIMIZED: Use concurrent.futures for truly parallel database queries
            import concurrent.futures
            import threading
            
            def get_team_dashboard():
                return self.storage.client.table('team_dashboard').select('*').eq('id', team_id).execute()
            
            def get_team_members():
                return self.storage.client.table('team_member_details').select('*').eq('team_id', team_id).execute()
            
            def get_pending_invitations():
                if user_role in ['owner', 'admin']:
                    return self.storage.client.table('team_invitations').select('id, email, created_at, expires_at, message').eq('team_id', team_id).eq('status', 'pending').execute()
                return None
            
            # Execute all queries in parallel using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # Submit all queries simultaneously
                team_future = executor.submit(get_team_dashboard)
                members_future = executor.submit(get_team_members)
                invites_future = executor.submit(get_pending_invitations)
                
                # Wait for all results
                team_info = team_future.result()
                members = members_future.result()
                invites = invites_future.result()
            
            # Validate team exists
            if not team_info.data:
                return {"success": False, "error": "Team not found"}
            
            # Process invitations
            pending_invites = []
            if invites and invites.data:
                pending_invites = invites.data
            
            result = {
                "success": True,
                "team": team_info.data[0],
                "members": members.data if members.data else [],
                "pending_invitations": pending_invites,
                "user_role": user_role
            }
            
            # Cache the result for faster future access
            self._cache_team_info(team_id, user_id, result)

            return result
            
        except Exception as e:
            return {"success": False, "error": f"Error getting team info: {str(e)}"}
    
    def remove_team_member(self, team_id: str, remover_id: str, member_id: str) -> Dict:
        """Remove a member from team (owner/admin only)"""
        try:
            # Check if remover has permission
            remover_check = self.storage.client.table('team_members').select('role').eq('team_id', team_id).eq('user_id', remover_id).execute()
            if not remover_check.data or remover_check.data[0]['role'] not in ['owner', 'admin']:
                return {"success": False, "error": "Only team owners and admins can remove members"}
            
            # Check if trying to remove owner
            member_check = self.storage.client.table('team_members').select('role').eq('team_id', team_id).eq('user_id', member_id).execute()
            if member_check.data and member_check.data[0]['role'] == 'owner':
                return {"success": False, "error": "Cannot remove team owner"}
            
            # Remove member from team_members table
            result = self.storage.client.table('team_members').delete().eq('team_id', team_id).eq('user_id', member_id).execute()
            
            # CRITICAL: Clear team_id and team_role from users table
            # This ensures effective tier calculation reverts to individual tier
            self.storage.client.table('users').update({
                'team_id': None,
                'team_role': None
            }).eq('id', member_id).execute()
            
            # Invalidate cache since team membership changed
            self._invalidate_team_cache(team_id)
            
            return {
                "success": True,
                "message": "Member removed successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error removing member: {str(e)}"}
    
    def leave_team(self, team_id: str, user_id: str) -> Dict:
        """Leave team (members only, owners cannot leave)"""
        try:
            # Check if user is team member
            member_check = self.storage.client.table('team_members').select('role').eq('team_id', team_id).eq('user_id', user_id).execute()
            if not member_check.data:
                return {"success": False, "error": "You are not a member of this team"}
            
            # Owners cannot leave, they must transfer ownership or delete team
            if member_check.data[0]['role'] == 'owner':
                return {"success": False, "error": "Team owners cannot leave. Transfer ownership or delete the team."}
            
            # Remove member from team_members table
            self.storage.client.table('team_members').delete().eq('team_id', team_id).eq('user_id', user_id).execute()
            
            # CRITICAL: Clear team_id and team_role from users table
            # This ensures effective tier calculation reverts to individual tier
            self.storage.client.table('users').update({
                'team_id': None,
                'team_role': None
            }).eq('id', user_id).execute()
            
            # Invalidate cache since team membership changed
            self._invalidate_team_cache(team_id)
            
            return {
                "success": True,
                "message": "Successfully left the team"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error leaving team: {str(e)}"}
    
    # ==================== QUOTA MANAGEMENT ====================
    
    def check_team_quota(self, team_id: str, email_count: int = 1) -> bool:
        """Check if team has enough quota for validation - Python implementation"""
        try:
            # Direct database query to avoid function issues
            result = self.storage.client.table('teams').select('quota_used, quota_limit').eq('id', team_id).eq('is_active', True).execute()
            
            if not result.data:
                return False
            
            team = result.data[0]
            current_usage = team['quota_used'] or 0
            quota_limit = team['quota_limit'] or 0
            
            # Simple lifetime quota check (no reset)
            can_validate = (current_usage + email_count) <= quota_limit
            
            print(f"🔍 Team quota check: {current_usage:,} + {email_count} <= {quota_limit:,} = {can_validate}")
            
            return can_validate
            
        except Exception as e:
            print(f"❌ Team quota check error: {e}")
            return False
    
    def use_team_quota(self, team_id: str, email_count: int = 1) -> bool:
        """Use team quota for validation - Direct SQL implementation"""
        try:
            # Get current usage first
            current_result = self.storage.client.table('teams').select('quota_used').eq('id', team_id).execute()
            
            if not current_result.data:
                print(f"❌ Team {team_id} not found")
                return False
            
            current_usage = current_result.data[0]['quota_used'] or 0
            new_usage = current_usage + email_count
            
            # Direct update
            update_result = self.storage.client.table('teams').update({
                'quota_used': new_usage,
                'updated_at': 'now()'
            }).eq('id', team_id).execute()
            
            if update_result.data:
                print(f"✅ Team quota incremented: {current_usage:,} → {new_usage:,} (+{email_count})")
                return True
            else:
                print(f"❌ Failed to update team quota")
                return False
            
        except Exception as e:
            print(f"❌ Team quota increment error: {e}")
            return False
    
    def get_team_usage(self, team_id: str) -> Dict:
        """Get team quota usage statistics - Direct from teams table"""
        try:
            # Get data directly from teams table instead of team_dashboard view
            result = self.storage.client.table('teams').select('quota_used, quota_limit, name').eq('id', team_id).eq('is_active', True).execute()
            
            if result.data:
                team = result.data[0]
                quota_used = team['quota_used'] or 0
                quota_limit = team['quota_limit'] or 0
                
                # Calculate usage percentage
                usage_percentage = (quota_used / quota_limit * 100) if quota_limit > 0 else 0
                
                usage_data = {
                    'quota_used': quota_used,
                    'quota_limit': quota_limit,
                    'usage_percentage': round(usage_percentage, 2),
                    'remaining': quota_limit - quota_used,
                    'team_name': team['name']
                    # Note: No 'days_until_reset' because this is lifetime quota
                }
                
                return {"success": True, "usage": usage_data}
            
            return {"success": False, "error": "Team not found"}
            
        except Exception as e:
            print(f"❌ Error getting team usage: {e}")
            return {"success": False, "error": f"Error getting usage: {str(e)}"}
    
    # ==================== HELPER METHODS ====================
    
    def generate_invite_token(self) -> str:
        """Generate secure invitation token"""
        return f"invite_{secrets.token_urlsafe(32)}"
    
    def get_user_team(self, user_id: str) -> Optional[Dict]:
        """Get user's current team information"""
        try:
            result = self.storage.client.table('users').select('team_id, team_role').eq('id', user_id).execute()
            if result.data and result.data[0]['team_id']:
                team_info = self.storage.client.table('team_dashboard').select('*').eq('id', result.data[0]['team_id']).execute()
                if team_info.data:
                    return {
                        "team": team_info.data[0],
                        "role": result.data[0]['team_role']
                    }
            return None
        except:
            return None

# Global instance
team_manager = TeamManager()
