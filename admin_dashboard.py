#!/usr/bin/env python3
"""
Admin Dashboard Backend
Handles dashboard metrics, user management, and system monitoring
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify, g
from datetime import datetime, timedelta
import logging
from admin_auth import admin_required, permission_required, admin_auth

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

class AdminDashboard:
    def __init__(self):
        pass
    
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
    
    def get_user_details(self, user_id):
        """Get detailed user information"""
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get user info
                cur.execute("""
                    SELECT * FROM users WHERE id = %s
                """, (user_id,))
                user = cur.fetchone()
                
                if not user:
                    return None
                
                # Get user's validation history (last 100)
                cur.execute("""
                    SELECT email, valid, confidence_score, validated_at
                    FROM email_validations
                    WHERE user_id = %s
                    ORDER BY validated_at DESC
                    LIMIT 100
                """, (user_id,))
                validations = cur.fetchall()
                
                # Get user's API usage over time (last 30 days)
                cur.execute("""
                    SELECT DATE(validated_at) as date, COUNT(*) as count
                    FROM email_validations
                    WHERE user_id = %s AND validated_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(validated_at)
                    ORDER BY date
                """, (user_id,))
                usage_history = cur.fetchall()
                
                return {
                    'user': dict(user),
                    'validations': [dict(v) for v in validations],
                    'usage_history': [dict(u) for u in usage_history]
                }
        
        except Exception as e:
            logger.error(f"Get user details error: {e}")
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
                admin_auth.log_activity(
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
                admin_auth.log_activity(
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
                admin_auth.log_activity(
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

# Create Flask app for admin dashboard
def create_admin_dashboard_app():
    """Create Flask app for admin dashboard API"""
    app = Flask(__name__)
    dashboard = AdminDashboard()
    
    @app.route('/admin/dashboard', methods=['GET'])
    @admin_required
    @permission_required('dashboard.read')
    def get_dashboard():
        stats = dashboard.get_dashboard_stats()
        if stats:
            return jsonify(stats)
        else:
            return jsonify({'error': 'Failed to load dashboard'}), 500
    
    @app.route('/admin/users', methods=['GET'])
    @admin_required
    @permission_required('users.read')
    def get_users():
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search')
        tier = request.args.get('tier')
        status = request.args.get('status')
        
        result = dashboard.get_users(page, limit, search, tier, status)
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to load users'}), 500
    
    @app.route('/admin/users/<user_id>', methods=['GET'])
    @admin_required
    @permission_required('users.read')
    def get_user_details(user_id):
        result = dashboard.get_user_details(user_id)
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'User not found'}), 404
    
    @app.route('/admin/users/<user_id>/suspend', methods=['POST'])
    @admin_required
    @permission_required('users.write')
    def suspend_user(user_id):
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        success = dashboard.suspend_user(user_id, reason, g.admin['id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to suspend user'}), 500
    
    @app.route('/admin/users/<user_id>/unsuspend', methods=['POST'])
    @admin_required
    @permission_required('users.write')
    def unsuspend_user(user_id):
        success = dashboard.unsuspend_user(user_id, g.admin['id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to unsuspend user'}), 500
    
    @app.route('/admin/users/<user_id>/tier', methods=['PUT'])
    @admin_required
    @permission_required('users.write')
    def update_user_tier(user_id):
        data = request.get_json()
        new_tier = data.get('tier')
        new_limit = data.get('limit')
        
        if not new_tier or not new_limit:
            return jsonify({'error': 'Tier and limit required'}), 400
        
        success = dashboard.update_user_tier(user_id, new_tier, new_limit, g.admin['id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to update user tier'}), 500
    
    return app

if __name__ == '__main__':
    app = create_admin_dashboard_app()
    app.run(debug=True, port=5002)  # Run on different port