#!/usr/bin/env python3
"""
Admin Authentication System
Handles admin login, session management, and permissions
"""

import os
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, g
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('SUPABASE_HOST', 'localhost'),
        database=os.getenv('SUPABASE_DB', 'postgres'),
        user=os.getenv('SUPABASE_USER', 'postgres'),
        password=os.getenv('SUPABASE_PASSWORD', ''),
        port=os.getenv('SUPABASE_PORT', '5432')
    )

# Admin authentication class
class AdminAuth:
    def __init__(self):
        self.secret_key = os.getenv('ADMIN_JWT_SECRET', 'your-super-secret-admin-key-change-this')
        self.token_expiry = timedelta(hours=8)  # 8 hour sessions
    
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
    
    def has_permission(self, admin_permissions, required_permission):
        """Check if admin has required permission"""
        if not admin_permissions:
            return False
        
        # Super admin has all permissions
        if '*' in admin_permissions:
            return True
        
        # Check specific permission
        return required_permission in admin_permissions

# Flask decorators for admin authentication
admin_auth = AdminAuth()

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Admin authentication required'}), 401
        
        token = token.split(' ')[1]
        admin = admin_auth.get_admin_by_token(token)
        
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
            
            if not admin_auth.has_permission(g.admin['permissions'], permission):
                return jsonify({'error': f'Permission denied: {permission}'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Admin API endpoints
def create_admin_app():
    """Create Flask app for admin API"""
    app = Flask(__name__)
    
    @app.route('/admin/auth/login', methods=['POST'])
    def admin_login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        result = admin_auth.login(
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
        admin_auth.logout(token)
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
    
    return app

if __name__ == '__main__':
    app = create_admin_app()
    app.run(debug=True, port=5001)  # Run on different port from main app