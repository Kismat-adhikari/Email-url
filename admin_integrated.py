#!/usr/bin/env python3
"""
Integrated Admin System for Email Platform
Combines authentication and dashboard functionality
"""

import os
import jwt
import bcrypt
import secrets
import json
from datetime import datetime, timedelta
from flask import request, jsonify, g
from functools import wraps
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Supabase client
def get_supabase_client():
    """Get Supabase client for database operations"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    
    return create_client(url, key)

class AdminSystem:
    def __init__(self):
        self.secret_key = os.getenv('ADMIN_JWT_SECRET', 'your-super-secret-admin-key-change-this')
        self.token_expiry = timedelta(hours=8)  # 8 hour sessions
    
    # ============================================================================
    # AUTHENTICATION METHODS
    # ============================================================================
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_token(self, admin_id, role, permissions):
        """Generate JWT token for admin"""
        payload = {
            'admin_id': str(admin_id),
            'role': role,
            'permissions': permissions,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow(),
            'type': 'admin'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def login(self, email, password, ip_address=None, user_agent=None):
        """Authenticate admin user"""
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get admin user
                cur.execute("""
                    SELECT id, email, password_hash, role, permissions, 
                           first_name, last_name, is_active
                    FROM admin_users 
                    WHERE email = %s AND is_active = true
                """, (email,))
                
                admin = cur.fetchone()
                if not admin or not self.verify_password(password, admin['password_hash']):
                    # Log failed login attempt
                    self.log_activity(None, 'login_failed', 'admin_auth', None, 
                                    {'email': email, 'reason': 'invalid_credentials'}, 
                                    ip_address, user_agent)
                    return None
                
                # Generate token
                token = self.generate_token(admin['id'], admin['role'], admin['permissions'])
                token_hash = self.hash_token(token)
                
                # Create session
                cur.execute("""
                    INSERT INTO admin_sessions (admin_id, token_hash, expires_at, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    admin['id'],
                    token_hash,
                    datetime.utcnow() + self.token_expiry,
                    ip_address,
                    user_agent
                ))
                
                session_id = cur.fetchone()['id']
                
                # Update last login
                cur.execute("""
                    UPDATE admin_users 
                    SET last_login = NOW() 
                    WHERE id = %s
                """, (admin['id'],))
                
                # Log successful login
                self.log_activity(admin['id'], 'login_success', 'admin_auth', str(session_id),
                                {'email': email}, ip_address, user_agent)
                
                conn.commit()
                
                return {
                    'token': token,
                    'admin': {
                        'id': str(admin['id']),
                        'email': admin['email'],
                        'role': admin['role'],
                        'permissions': admin['permissions'],
                        'first_name': admin['first_name'],
                        'last_name': admin['last_name']
                    }
                }
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def logout(self, token):
        """Logout admin user"""
        payload = self.verify_token(token)
        if not payload:
            return False
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                token_hash = self.hash_token(token)
                
                # Deactivate session
                cur.execute("""
                    UPDATE admin_sessions 
                    SET is_active = false 
                    WHERE token_hash = %s
                """, (token_hash,))
                
                # Log logout
                self.log_activity(payload['admin_id'], 'logout', 'admin_auth', None, {})
                
                conn.commit()
                return True
        
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
        finally:
            conn.close()
    
    def hash_token(self, token):
        """Hash token for storage"""
        return bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def get_admin_by_token(self, token):
        """Get admin info by token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT a.id, a.email, a.role, a.permissions, 
                           a.first_name, a.last_name, a.is_active
                    FROM admin_users a
                    JOIN admin_sessions s ON a.id = s.admin_id
                    WHERE a.id = %s AND a.is_active = true 
                      AND s.is_active = true AND s.expires_at > NOW()
                """, (payload['admin_id'],))
                
                return cur.fetchone()
        
        except Exception as e:
            logger.error(f"Get admin error: {e}")
            return None
        finally:
            conn.close()
    
    def has_permission(self, admin_permissions, required_permission):
        """Check if admin has required permission"""
        if not admin_permissions:
            return False
        
        # Super admin has all permissions
        if '*' in admin_permissions:
            return True
        
        # Check specific permission
        return required_permission in admin_permissions
    
    # ============================================================================
    # DASHBOARD METHODS
    # ============================================================================
    
    def get_dashboard_stats(self):
        """Get main dashboard statistics"""
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get dashboard stats from view
                cur.execute("SELECT * FROM admin_dashboard_stats")
                stats = cur.fetchone()
                
                # Get recent activity
                cur.execute("""
                    SELECT action, resource_type, created_at, 
                           CONCAT(a.first_name, ' ', a.last_name) as admin_name
                    FROM admin_activity_logs al
                    LEFT JOIN admin_users a ON al.admin_id = a.id
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
                recent_activity = cur.fetchall()
                
                # Get user growth (last 30 days)
                cur.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM users
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """)
                user_growth = cur.fetchall()
                
                # Get validation trends (last 7 days)
                cur.execute("""
                    SELECT DATE(validated_at) as date, 
                           COUNT(*) as total,
                           COUNT(CASE WHEN valid THEN 1 END) as valid_count
                    FROM email_validations
                    WHERE validated_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY DATE(validated_at)
                    ORDER BY date
                """)
                validation_trends = cur.fetchall()
                
                return {
                    'stats': dict(stats) if stats else {},
                    'recent_activity': [dict(row) for row in recent_activity],
                    'user_growth': [dict(row) for row in user_growth],
                    'validation_trends': [dict(row) for row in validation_trends]
                }
        
        except Exception as e:
            logger.error(f"Dashboard stats error: {e}")
            return None
        finally:
            conn.close()
    
    def get_users(self, page=1, limit=50, search=None, tier=None, status=None):
        """Get paginated user list with filters"""
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Build WHERE clause
                where_conditions = []
                params = []
                
                if search:
                    where_conditions.append("(email ILIKE %s OR first_name ILIKE %s OR last_name ILIKE %s)")
                    search_param = f"%{search}%"
                    params.extend([search_param, search_param, search_param])
                
                if tier:
                    where_conditions.append("subscription_tier = %s")
                    params.append(tier)
                
                if status == 'active':
                    where_conditions.append("is_active = true AND is_suspended = false")
                elif status == 'suspended':
                    where_conditions.append("is_suspended = true")
                elif status == 'inactive':
                    where_conditions.append("is_active = false")
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM users {where_clause}"
                cur.execute(count_query, params)
                total_count = cur.fetchone()['count']
                
                # Get paginated results
                offset = (page - 1) * limit
                query = f"""
                    SELECT id, email, first_name, last_name, subscription_tier,
                           api_calls_count, api_calls_limit, is_active, is_suspended,
                           created_at, last_login, suspended_at, suspension_reason
                    FROM users 
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                params.extend([limit, offset])
                cur.execute(query, params)
                users = cur.fetchall()
                
                return {
                    'users': [dict(user) for user in users],
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total_count,
                        'pages': (total_count + limit - 1) // limit
                    }
                }
        
        except Exception as e:
            logger.error(f"Get users error: {e}")
            return None
        finally:
            conn.close()
    
    def suspend_user(self, user_id, reason, admin_id):
        """Suspend a user"""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET is_suspended = true, 
                        suspended_at = NOW(),
                        suspended_by = %s,
                        suspension_reason = %s
                    WHERE id = %s
                """, (admin_id, reason, user_id))
                
                # Log activity
                self.log_activity(
                    admin_id, 'user_suspended', 'user', str(user_id),
                    {'reason': reason}
                )
                
                conn.commit()
                return True
        
        except Exception as e:
            logger.error(f"Suspend user error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def unsuspend_user(self, user_id, admin_id):
        """Unsuspend a user"""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET is_suspended = false, 
                        suspended_at = NULL,
                        suspended_by = NULL,
                        suspension_reason = NULL
                    WHERE id = %s
                """, (user_id,))
                
                # Log activity
                self.log_activity(
                    admin_id, 'user_unsuspended', 'user', str(user_id), {}
                )
                
                conn.commit()
                return True
        
        except Exception as e:
            logger.error(f"Unsuspend user error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_user_tier(self, user_id, new_tier, new_limit, admin_id):
        """Update user subscription tier and limits"""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET subscription_tier = %s, 
                        api_calls_limit = %s
                    WHERE id = %s
                """, (new_tier, new_limit, user_id))
                
                # Log activity
                self.log_activity(
                    admin_id, 'user_tier_updated', 'user', str(user_id),
                    {'new_tier': new_tier, 'new_limit': new_limit}
                )
                
                conn.commit()
                return True
        
        except Exception as e:
            logger.error(f"Update user tier error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def log_activity(self, admin_id, action, resource_type, resource_id, details, ip_address=None, user_agent=None):
        """Log admin activity"""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO admin_activity_logs 
                    (admin_id, action, resource_type, resource_id, details, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (admin_id, action, resource_type, resource_id, 
                      details, ip_address, user_agent))
                conn.commit()
        except Exception as e:
            logger.error(f"Activity log error: {e}")
        finally:
            conn.close()

# Global admin system instance
admin_system = AdminSystem()

# ============================================================================
# FLASK DECORATORS
# ============================================================================

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Admin authentication required'}), 401
        
        token = token.split(' ')[1]
        admin = admin_system.get_admin_by_token(token)
        
        if not admin:
            return jsonify({'error': 'Invalid admin token'}), 401
        
        g.admin = admin
        return f(*args, **kwargs)
    
    return decorated_function

def permission_required(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'admin'):
                return jsonify({'error': 'Admin authentication required'}), 401
            
            if not admin_system.has_permission(g.admin['permissions'], permission):
                return jsonify({'error': f'Permission denied: {permission}'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# ADMIN ROUTE HANDLERS
# ============================================================================

def register_admin_routes(app):
    """Register all admin routes with the Flask app"""
    
    @app.route('/admin/auth/login', methods=['POST'])
    def admin_login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        result = admin_system.login(
            email, 
            password, 
            request.remote_addr, 
            request.headers.get('User-Agent')
        )
        
        if result:
            return jsonify({
                'success': True,
                'token': result['token'],
                'admin': result['admin']
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    @app.route('/admin/auth/logout', methods=['POST'])
    @admin_required
    def admin_logout():
        token = request.headers.get('Authorization').split(' ')[1]
        admin_system.logout(token)
        return jsonify({'success': True})
    
    @app.route('/admin/auth/me', methods=['GET'])
    @admin_required
    def admin_me():
        return jsonify({
            'admin': {
                'id': str(g.admin['id']),
                'email': g.admin['email'],
                'role': g.admin['role'],
                'permissions': g.admin['permissions'],
                'first_name': g.admin['first_name'],
                'last_name': g.admin['last_name']
            }
        })
    
    @app.route('/admin/dashboard', methods=['GET'])
    @admin_required
    def get_dashboard():
        stats = admin_system.get_dashboard_stats()
        if stats:
            return jsonify(stats)
        else:
            return jsonify({'error': 'Failed to load dashboard'}), 500
    
    @app.route('/admin/users', methods=['GET'])
    @admin_required
    def get_users():
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search')
        tier = request.args.get('tier')
        status = request.args.get('status')
        
        result = admin_system.get_users(page, limit, search, tier, status)
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to load users'}), 500
    
    @app.route('/admin/users/<user_id>/suspend', methods=['POST'])
    @admin_required
    def suspend_user(user_id):
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        success = admin_system.suspend_user(user_id, reason, g.admin['id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to suspend user'}), 500
    
    @app.route('/admin/users/<user_id>/unsuspend', methods=['POST'])
    @admin_required
    def unsuspend_user(user_id):
        success = admin_system.unsuspend_user(user_id, g.admin['id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to unsuspend user'}), 500
    
    @app.route('/admin/users/<user_id>/tier', methods=['PUT'])
    @admin_required
    def update_user_tier(user_id):
        data = request.get_json()
        new_tier = data.get('tier')
        new_limit = data.get('limit')
        
        if not new_tier or not new_limit:
            return jsonify({'error': 'Tier and limit required'}), 400
        
        success = admin_system.update_user_tier(user_id, new_tier, new_limit, g.admin['id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to update user tier'}), 500