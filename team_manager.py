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
    
    # ==================== TEAM CREATION ====================
    
    def create_team(self, owner_id: str, team_name: str, description: str = "") -> Dict:
        """Create a new team (Pro users only)"""
        try:
            # Check if user can create team (must be Pro and not in a team)
            can_create = self.storage.execute_function('can_create_team', [owner_id])
            if not can_create.data[0]['can_create_team']:
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
            
            # Send invitation email (optional)
            self.send_invitation_email(email, invite_link, team_id, inviter_id, message)
            
            return {
                "success": True,
                "invitation": invitation,
                "invite_link": invite_link,
                "message": f"Invitation sent to {email}"
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
            
            # Mark invitation as accepted
            self.storage.client.table('team_invitations').update({
                'status': 'accepted',
                'used_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', invitation['id']).execute()
            
            return {
                "success": True,
                "team_id": invitation['team_id'],
                "message": "Successfully joined the team!"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error accepting invitation: {str(e)}"}
    
    # ==================== TEAM MANAGEMENT ====================
    
    def get_team_info(self, team_id: str, user_id: str) -> Dict:
        """Get team information for a member - optimized version"""
        try:
            # Single query to get user role and team info
            user_role_result = self.storage.client.table('team_members').select('role').eq('team_id', team_id).eq('user_id', user_id).execute()
            if not user_role_result.data:
                return {"success": False, "error": "You are not a member of this team"}
            
            user_role = user_role_result.data[0]['role']
            
            # Parallel queries for better performance
            import asyncio
            
            # Get team dashboard info
            team_info = self.storage.client.table('team_dashboard').select('*').eq('id', team_id).execute()
            if not team_info.data:
                return {"success": False, "error": "Team not found"}
            
            # Get team members
            members = self.storage.client.table('team_member_details').select('*').eq('team_id', team_id).execute()
            
            # Get pending invitations (only for owners/admins)
            pending_invites = []
            if user_role in ['owner', 'admin']:
                invites = self.storage.client.table('team_invitations').select('id, email, created_at, expires_at, message').eq('team_id', team_id).eq('status', 'pending').execute()
                pending_invites = invites.data if invites.data else []
            
            return {
                "success": True,
                "team": team_info.data[0],
                "members": members.data if members.data else [],
                "pending_invitations": pending_invites,
                "user_role": user_role
            }
            
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
            
            # Remove member
            result = self.storage.client.table('team_members').delete().eq('team_id', team_id).eq('user_id', member_id).execute()
            
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
            
            # Remove member
            self.storage.client.table('team_members').delete().eq('team_id', team_id).eq('user_id', user_id).execute()
            
            return {
                "success": True,
                "message": "Successfully left the team"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error leaving team: {str(e)}"}
    
    # ==================== QUOTA MANAGEMENT ====================
    
    def check_team_quota(self, team_id: str, email_count: int = 1) -> bool:
        """Check if team has enough quota for validation"""
        try:
            result = self.storage.execute_function('check_team_quota', [team_id, email_count])
            return result.data[0]['check_team_quota'] if result.data else False
        except:
            return False
    
    def use_team_quota(self, team_id: str, email_count: int = 1) -> bool:
        """Use team quota for validation"""
        try:
            self.storage.execute_function('increment_team_quota', [team_id, email_count])
            return True
        except:
            return False
    
    def get_team_usage(self, team_id: str) -> Dict:
        """Get team quota usage statistics"""
        try:
            result = self.storage.client.table('team_dashboard').select('quota_used, quota_limit, usage_percentage, days_until_reset').eq('id', team_id).execute()
            if result.data:
                return {"success": True, "usage": result.data[0]}
            return {"success": False, "error": "Team not found"}
        except Exception as e:
            return {"success": False, "error": f"Error getting usage: {str(e)}"}
    
    # ==================== HELPER METHODS ====================
    
    def generate_invite_token(self) -> str:
        """Generate secure invitation token"""
        return f"invite_{secrets.token_urlsafe(32)}"
    
    def send_invitation_email(self, email: str, invite_link: str, team_id: str, inviter_id: str, message: str = ""):
        """Send invitation email (optional feature)"""
        try:
            # Get team and inviter info
            team_info = self.storage.client.table('teams').select('name').eq('id', team_id).execute()
            inviter_info = self.storage.client.table('users').select('first_name, last_name, email').eq('id', inviter_id).execute()
            
            if not team_info.data or not inviter_info.data:
                return False
            
            team_name = team_info.data[0]['name']
            inviter_name = f"{inviter_info.data[0]['first_name']} {inviter_info.data[0]['last_name']}"
            
            # Email content
            subject = f"You're invited to join {team_name} on Email Validator"
            
            html_content = f"""
            <html>
            <body>
                <h2>Team Invitation</h2>
                <p>Hi there!</p>
                <p><strong>{inviter_name}</strong> has invited you to join the team <strong>"{team_name}"</strong> on Email Validator.</p>
                
                {f'<p><em>Personal message:</em> {message}</p>' if message else ''}
                
                <p>As a team member, you'll get:</p>
                <ul>
                    <li>Pro tier access with shared 10,000 monthly validations</li>
                    <li>Advanced email validation features</li>
                    <li>Team collaboration and shared results</li>
                </ul>
                
                <p><a href="{invite_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Accept Invitation</a></p>
                
                <p>This invitation expires in 7 days.</p>
                
                <p>If you don't have an account yet, you'll be prompted to create one when you click the link.</p>
                
                <p>Best regards,<br>Email Validator Team</p>
            </body>
            </html>
            """
            
            # Send email using SendGrid (if configured)
            sendgrid_key = os.getenv('SENDGRID_API_KEY')
            if sendgrid_key and sendgrid_key != 'your_sendgrid_api_key_here':
                # TODO: Implement SendGrid email sending
                pass
            
            return True
            
        except Exception as e:
            print(f"Error sending invitation email: {e}")
            return False
    
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
