"""
Team API Endpoints for Email Validator
Flask routes for team management functionality
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
import os
from team_manager import team_manager
from supabase_storage import get_storage

# Create blueprint
team_bp = Blueprint('team', __name__, url_prefix='/api/team')

def token_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Import the verify function from main app
            from app_anon_history import verify_jwt_token
            payload = verify_jwt_token(token)
            current_user_id = payload.get('user_id')
            
            if not current_user_id:
                return jsonify({'error': 'Invalid token'}), 401
                
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated

# ==================== TEAM CREATION ====================

@team_bp.route('/create', methods=['POST'])
@token_required
def create_team(current_user_id):
    """Create a new team (Pro users only)"""
    try:
        data = request.get_json()
        team_name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not team_name:
            return jsonify({'error': 'Team name is required'}), 400
        
        if len(team_name) < 3:
            return jsonify({'error': 'Team name must be at least 3 characters'}), 400
        
        result = team_manager.create_team(current_user_id, team_name, description)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# ==================== TEAM INFORMATION ====================

@team_bp.route('/info', methods=['GET'])
@token_required
def get_team_info(current_user_id):
    """Get current user's team information"""
    try:
        # Get user's team
        user_team = team_manager.get_user_team(current_user_id)
        
        if not user_team:
            return jsonify({'error': 'You are not in a team'}), 404
        
        team_id = user_team['team']['id']
        result = team_manager.get_team_info(team_id, current_user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@team_bp.route('/usage', methods=['GET'])
@token_required
def get_team_usage(current_user_id):
    """Get team quota usage statistics"""
    try:
        user_team = team_manager.get_user_team(current_user_id)
        
        if not user_team:
            return jsonify({'error': 'You are not in a team'}), 404
        
        team_id = user_team['team']['id']
        result = team_manager.get_team_usage(team_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# ==================== TEAM INVITATIONS ====================

@team_bp.route('/invite', methods=['POST'])
@token_required
def invite_member(current_user_id):
    """Invite a new member to the team"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        message = data.get('message', '').strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Get user's team
        user_team = team_manager.get_user_team(current_user_id)
        if not user_team:
            return jsonify({'error': 'You are not in a team'}), 404
        
        team_id = user_team['team']['id']
        result = team_manager.generate_invitation(team_id, current_user_id, email, message)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@team_bp.route('/invite/<invite_token>', methods=['GET'])
def get_invitation_info(invite_token):
    """Get invitation information (public endpoint)"""
    try:
        storage = get_storage()
        
        # Get invitation details
        result = storage.client.table('team_invitations').select('*').eq('invite_token', invite_token).execute()
        
        if not result.data:
            return jsonify({'error': 'Invalid invitation token'}), 404
        
        invitation = result.data[0]
        
        # Get team details separately
        team_result = storage.client.table('teams').select('name, description').eq('id', invitation['team_id']).execute()
        team_info = team_result.data[0] if team_result.data else {'name': 'Unknown Team', 'description': ''}
        
        # Get inviter details separately  
        inviter_result = storage.client.table('users').select('first_name, last_name, email').eq('id', invitation['invited_by']).execute()
        inviter_info = inviter_result.data[0] if inviter_result.data else {'first_name': 'Unknown', 'last_name': 'User', 'email': 'unknown@example.com'}
        
        # Check if expired
        from datetime import datetime, timezone
        expires_at = datetime.fromisoformat(invitation['expires_at'].replace('Z', '+00:00'))
        now_utc = datetime.now(timezone.utc)
        if expires_at < now_utc:
            return jsonify({'error': 'Invitation has expired'}), 410
        
        # Check if already used
        if invitation['status'] != 'pending':
            return jsonify({'error': 'Invitation has already been used'}), 410
        
        return jsonify({
            'success': True,
            'invitation': {
                'team_name': team_info['name'],
                'team_description': team_info['description'],
                'invited_by': f"{inviter_info['first_name']} {inviter_info['last_name']}",
                'inviter_email': inviter_info['email'],
                'message': invitation['message'],
                'expires_at': invitation['expires_at']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@team_bp.route('/invite/<invite_token>/accept', methods=['POST'])
@token_required
def accept_invitation(current_user_id, invite_token):
    """Accept team invitation"""
    try:
        result = team_manager.accept_invitation(invite_token, current_user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# ==================== TEAM MEMBER MANAGEMENT ====================

@team_bp.route('/members/<member_id>/remove', methods=['DELETE'])
@token_required
def remove_member(current_user_id, member_id):
    """Remove a team member (owner/admin only)"""
    try:
        user_team = team_manager.get_user_team(current_user_id)
        if not user_team:
            return jsonify({'error': 'You are not in a team'}), 404
        
        team_id = user_team['team']['id']
        result = team_manager.remove_team_member(team_id, current_user_id, member_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@team_bp.route('/leave', methods=['POST'])
@token_required
def leave_team(current_user_id):
    """Leave current team"""
    try:
        user_team = team_manager.get_user_team(current_user_id)
        if not user_team:
            return jsonify({'error': 'You are not in a team'}), 404
        
        team_id = user_team['team']['id']
        result = team_manager.leave_team(team_id, current_user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# ==================== TEAM SETTINGS ====================

@team_bp.route('/update', methods=['PUT'])
@token_required
def update_team(current_user_id):
    """Update team settings (owner only)"""
    try:
        data = request.get_json()
        
        user_team = team_manager.get_user_team(current_user_id)
        if not user_team:
            return jsonify({'error': 'You are not in a team'}), 404
        
        if user_team['role'] != 'owner':
            return jsonify({'error': 'Only team owners can update team settings'}), 403
        
        team_id = user_team['team']['id']
        storage = get_storage()
        
        # Update team information
        update_data = {}
        if 'name' in data:
            name = data['name'].strip()
            if len(name) < 3:
                return jsonify({'error': 'Team name must be at least 3 characters'}), 400
            update_data['name'] = name
        
        if 'description' in data:
            update_data['description'] = data['description'].strip()
        
        if 'max_members' in data:
            max_members = int(data['max_members'])
            if max_members < 1 or max_members > 50:
                return jsonify({'error': 'Max members must be between 1 and 50'}), 400
            update_data['max_members'] = max_members
        
        if update_data:
            update_data['updated_at'] = 'now()'
            result = storage.client.table('teams').update(update_data).eq('id', team_id).execute()
            
            if result.data:
                return jsonify({'success': True, 'message': 'Team updated successfully'}), 200
            else:
                return jsonify({'error': 'Failed to update team'}), 400
        
        return jsonify({'error': 'No valid fields to update'}), 400
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# ==================== HELPER ENDPOINTS ====================

@team_bp.route('/status', methods=['GET'])
@token_required
def get_team_status(current_user_id):
    """Get complete team status in a single optimized call"""
    try:
        storage = get_storage()
        
        # Single query to get user info with team data
        user_query = """
        SELECT 
            u.id,
            u.subscription_tier,
            u.team_id,
            u.team_role,
            t.name as team_name,
            t.description as team_description,
            t.quota_used,
            t.quota_limit,
            t.max_members,
            t.owner_id,
            ROUND((t.quota_used::numeric / t.quota_limit::numeric) * 100, 1) as usage_percentage,
            (SELECT COUNT(*) FROM team_members WHERE team_id = t.id AND is_active = true) as member_count
        FROM users u
        LEFT JOIN teams t ON u.team_id = t.id
        WHERE u.id = %s
        """
        
        result = storage.client.rpc('exec_raw_sql', {
            'query': user_query,
            'params': [current_user_id]
        }).execute()
        
        if not result.data or not result.data[0]:
            # Fallback to simple query if raw SQL doesn't work
            user_result = storage.client.table('users').select('subscription_tier, team_id, team_role').eq('id', current_user_id).execute()
            if not user_result.data:
                return jsonify({'error': 'User not found'}), 404
            
            user = user_result.data[0]
            
            response = {
                'can_create_team': user['subscription_tier'] in ['starter', 'pro'] and user['team_id'] is None,
                'subscription_tier': user['subscription_tier'],
                'in_team': user['team_id'] is not None,
                'team_info': None
            }
            
            # If user is in a team, get team info
            if user['team_id']:
                team_info = team_manager.get_team_info(user['team_id'], current_user_id)
                if team_info['success']:
                    response['team_info'] = team_info
            
            return jsonify(response), 200
        
        user_data = result.data[0]
        
        can_create = (
            user_data['subscription_tier'] in ['starter', 'pro'] and 
            user_data['team_id'] is None
        )
        
        response = {
            'can_create_team': can_create,
            'subscription_tier': user_data['subscription_tier'],
            'in_team': user_data['team_id'] is not None,
            'team_info': None
        }
        
        # If user is in a team, include team info
        if user_data['team_id']:
            # Get team members and invitations in parallel
            members_result = storage.client.table('team_member_details').select('*').eq('team_id', user_data['team_id']).execute()
            
            # Only get pending invitations if user is owner/admin
            pending_invites = []
            if user_data['team_role'] in ['owner', 'admin']:
                invites_result = storage.client.table('team_invitations').select('*').eq('team_id', user_data['team_id']).eq('status', 'pending').execute()
                pending_invites = invites_result.data if invites_result.data else []
            
            response['team_info'] = {
                'success': True,
                'team': {
                    'id': user_data['team_id'],
                    'name': user_data['team_name'],
                    'description': user_data['team_description'],
                    'quota_used': user_data['quota_used'],
                    'quota_limit': user_data['quota_limit'],
                    'usage_percentage': user_data['usage_percentage'],
                    'member_count': user_data['member_count'],
                    'max_members': user_data['max_members'],
                    'owner_id': user_data['owner_id']
                },
                'members': members_result.data if members_result.data else [],
                'pending_invitations': pending_invites,
                'user_role': user_data['team_role']
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        # Fallback to original method if optimized query fails
        return check_team_eligibility_fallback(current_user_id)

def check_team_eligibility_fallback(current_user_id):
    """Fallback method for team eligibility check"""
    try:
        storage = get_storage()
        
        # Check user's subscription and team status
        result = storage.client.table('users').select('subscription_tier, team_id').eq('id', current_user_id).execute()
        
        if not result.data:
            return jsonify({'error': 'User not found'}), 404
        
        user = result.data[0]
        
        can_create = (
            user['subscription_tier'] in ['starter', 'pro'] and 
            user['team_id'] is None
        )
        
        response = {
            'can_create_team': can_create,
            'subscription_tier': user['subscription_tier'],
            'in_team': user['team_id'] is not None,
            'team_info': None
        }
        
        # If user is in a team, get team info
        if user['team_id']:
            team_info = team_manager.get_team_info(user['team_id'], current_user_id)
            if team_info['success']:
                response['team_info'] = team_info
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@team_bp.route('/check-eligibility', methods=['GET'])
@token_required
def check_team_eligibility(current_user_id):
    """Legacy endpoint - redirects to optimized status endpoint"""
    return get_team_status(current_user_id)

# Error handlers
@team_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@team_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405