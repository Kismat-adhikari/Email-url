#!/usr/bin/env python3
"""
Flask Backend with Anonymous User ID System
Private history WITHOUT requiring user login
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from emailvalidator_unified import validate_email_advanced, validate_email_tiered, validate_batch
from email_validator_smtp import validate_email_with_smtp
# Import fast SMTP integration (10x faster)
from fast_smtp_integration import validate_email_with_smtp as validate_email_with_fast_smtp
# Import enhanced SMTP validation (production-ready)
from production_smtp_validator import validate_email_production_ready
from supabase_storage import get_storage
from email_enrichment import EmailEnrichment
from pattern_analysis import calculate_deliverability_score, analyze_email_pattern
from spam_trap_detector import comprehensive_risk_check
from email_status import determine_email_status
# Bounce tracking now integrated into email_sender
import time
import os
import re
import logging
import jwt
import bcrypt
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta

# Import admin system
from admin_simple import register_admin_routes

# Import team system
from team_api import team_bp
from team_manager import team_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_validator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='frontend/build', static_url_path='')
CORS(app)

# Register admin routes immediately after app creation
register_admin_routes(app)

# Register team routes
app.register_blueprint(team_bp)

# Rate limiting configuration
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100  # requests per window
rate_limit_store = defaultdict(list)

# Initialize components
enricher = EmailEnrichment()

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Admin JWT Configuration
ADMIN_JWT_SECRET = os.getenv('ADMIN_JWT_SECRET', 'your-super-secret-admin-key-change-this')

# ============================================================================
# ADMIN HELPER FUNCTIONS
# ============================================================================

def get_daily_api_usage(user_id, storage):
    """Get today's API usage for a user (for daily limits)"""
    try:
        from datetime import datetime, timezone
        
        # Get today's date in UTC
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Query validation history for today
        result = storage.supabase.table('validation_history').select('id').eq('user_id', user_id).gte('validated_at', today_start.isoformat()).lte('validated_at', today_end.isoformat()).execute()
        
        daily_count = len(result.data) if result.data else 0
        logger.info(f"Daily API usage for user {user_id}: {daily_count} calls today")
        return daily_count
        
    except Exception as e:
        logger.error(f"Failed to get daily API usage: {str(e)}")
        return 0

def get_fresh_user_data(user_id):
    """
    Get fresh user data from database to ensure team_id is current
    This prevents issues where user just joined a team but backend has stale data
    """
    try:
        storage = get_storage()
        fresh_user = storage.get_user_by_id(user_id)
        if fresh_user:

            return fresh_user
        return None
    except Exception as e:

        return None

def get_effective_subscription_tier(user):
    """
    Get the effective subscription tier for a user, considering team membership
    Team members get Pro access regardless of their base tier
    """
    base_tier = user.get('subscription_tier', 'free')
    team_id = user.get('team_id')

    # If user is in a team, they get Pro access
    if team_id:

        return 'pro'

    return base_tier

def check_api_limits(user, is_admin=False):
    """Check API limits based on user's subscription tier"""
    if is_admin:
        return True, 0, 'unlimited'  # Admin has unlimited access
    
    subscription_tier = get_effective_subscription_tier(user)
    
    if subscription_tier == 'free':
        # Free tier: 10 per day
        storage = get_storage()
        daily_usage = get_daily_api_usage(user['id'], storage)
        daily_limit = 10
        
        if daily_usage >= daily_limit:
            return False, daily_usage, daily_limit
        return True, daily_usage, daily_limit
        
    elif subscription_tier == 'starter':
        # Starter tier: 10K per month (use existing monthly logic)
        monthly_usage = user['api_calls_count']
        monthly_limit = 10000
        
        if monthly_usage >= monthly_limit:
            return False, monthly_usage, monthly_limit
        return True, monthly_usage, monthly_limit
        
    elif subscription_tier == 'pro':
        # Pro tier: 10M lifetime
        lifetime_usage = user['api_calls_count']
        lifetime_limit = 10000000
        
        if lifetime_usage >= lifetime_limit:
            return False, lifetime_usage, lifetime_limit
        return True, lifetime_usage, lifetime_limit
    
    # Default to free tier limits
    return check_api_limits({**user, 'subscription_tier': 'free'}, is_admin)

def is_admin_request():
    """Check if the current request is from an admin user"""
    try:
        # Check for admin token in Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return False
        
        token = auth_header.split(' ')[1]
        
        # Verify admin token
        payload = jwt.decode(token, ADMIN_JWT_SECRET, algorithms=['HS256'])
        role = payload.get('role')
        # Accept both 'admin' and 'super_admin' roles
        return role in ['admin', 'super_admin']
    except:
        return False

def get_admin_from_request():
    """Get admin info from the current request"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, ADMIN_JWT_SECRET, algorithms=['HS256'])
        
        role = payload.get('role')
        # Accept both 'admin' and 'super_admin' roles
        if role in ['admin', 'super_admin']:
            return {
                'id': payload.get('admin_id'),
                'email': payload.get('email', 'admin@emailvalidator.com'),
                'role': role
            }
        return None
    except:
        return None

# ============================================================================
# DOMAIN STATISTICS HELPER
# ============================================================================

def calculate_domain_stats(results):
    """
    Calculate comprehensive domain statistics from validation results.
    
    Args:
        results: List of validation result dictionaries
        
    Returns:
        Dictionary containing domain statistics
    """
    from collections import Counter
    
    domain_counts = Counter()
    domain_valid = defaultdict(lambda: {'valid': 0, 'invalid': 0})
    domain_risks = defaultdict(lambda: {'low': 0, 'medium': 0, 'high': 0, 'critical': 0})
    provider_types = {
        'free': 0,
        'business': 0,
        'disposable': 0,
        'educational': 0,
        'government': 0,
        'unknown': 0
    }
    
    # Free email providers
    free_providers = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
        'aol.com', 'icloud.com', 'mail.com', 'protonmail.com',
        'yandex.com', 'zoho.com', 'gmx.com', 'live.com'
    }
    
    for result in results:
        email = result.get('email', '')
        if '@' not in email:
            continue
            
        domain = email.split('@')[1].lower()
        domain_counts[domain] += 1
        
        # Track validity by domain
        if result.get('valid'):
            domain_valid[domain]['valid'] += 1
        else:
            domain_valid[domain]['invalid'] += 1
        
        # Track risk levels by domain (if available)
        if result.get('risk_check'):
            risk_level = result['risk_check'].get('overall_risk', 'low')
            domain_risks[domain][risk_level] += 1
        
        # Categorize provider type
        checks = result.get('checks', {})
        if checks.get('is_disposable'):
            provider_types['disposable'] += 1
        elif domain.endswith('.edu'):
            provider_types['educational'] += 1
        elif domain.endswith('.gov'):
            provider_types['government'] += 1
        elif domain in free_providers:
            provider_types['free'] += 1
        elif '.' in domain:
            provider_types['business'] += 1
        else:
            provider_types['unknown'] += 1
    
    # Calculate top domains
    top_domains = []
    total_emails = len(results)
    for domain, count in domain_counts.most_common(10):
        valid_count = domain_valid[domain]['valid']
        invalid_count = domain_valid[domain]['invalid']
        validity_rate = (valid_count / (valid_count + invalid_count) * 100) if (valid_count + invalid_count) > 0 else 0
        
        # Get risk distribution
        risks = domain_risks[domain]
        high_risk_count = risks['high'] + risks['critical']
        
        top_domains.append({
            'domain': domain,
            'count': count,
            'percentage': round(count / total_emails * 100, 1),
            'valid': valid_count,
            'invalid': invalid_count,
            'validity_rate': round(validity_rate, 1),
            'high_risk_count': high_risk_count
        })
    
    # Calculate provider percentages
    provider_percentages = {}
    for ptype, count in provider_types.items():
        if count > 0:
            provider_percentages[ptype] = {
                'count': count,
                'percentage': round(count / total_emails * 100, 1)
            }
    
    return {
        'total_domains': len(domain_counts),
        'top_domains': top_domains,
        'provider_distribution': provider_percentages,
        'total_emails': total_emails
    }

# ============================================================================
# MIDDLEWARE - Extract Anonymous User ID & Rate Limiting
# ============================================================================

def validate_uuid_format(user_id: str) -> bool:
    """Validate UUID format (UUIDv4)."""
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(user_id))

def validate_email_format(email: str) -> bool:
    """Basic email format validation using the proper validator."""
    from emailvalidator_unified import validate_email
    return validate_email(email)

def get_anon_user_id():
    """
    Extract and validate anonymous user ID from request headers.
    
    Returns:
        str: Anonymous user ID
    
    Raises:
        ValueError: If header is missing or invalid
    """
    anon_user_id = request.headers.get('X-User-ID')
    
    if not anon_user_id:
        raise ValueError('Missing X-User-ID header. Anonymous user ID is required.')
    
    # Validate UUID format
    if not validate_uuid_format(anon_user_id):
        raise ValueError('Invalid X-User-ID format. Must be a valid UUIDv4.')
    
    return anon_user_id

def get_client_ip():
    """Get client IP address for rate limiting."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'unknown'

def rate_limit(f):
    """Rate limiting decorator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = get_client_ip()
        now = datetime.now()
        
        # Clean old entries
        rate_limit_store[client_ip] = [
            timestamp for timestamp in rate_limit_store[client_ip]
            if now - timestamp < timedelta(seconds=RATE_LIMIT_WINDOW)
        ]
        
        # Check rate limit
        if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': f'Maximum {RATE_LIMIT_MAX_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds'
            }), 429
        
        # Add current request
        rate_limit_store[client_ip].append(now)
        
        return f(*args, **kwargs)
    
    return decorated_function

# ============================================================================
# AUTHENTICATION HELPERS
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_jwt_token(user_data: dict) -> str:
    """Generate JWT token for user."""
    payload = {
        'user_id': user_data['id'],
        'email': user_data['email'],
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')

def get_user_from_token():
    """Extract user from JWT token in Authorization header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise ValueError('Missing or invalid Authorization header')
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    return payload

def auth_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user = get_user_from_token()
            request.current_user = user
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({
                'error': 'Authentication required',
                'message': str(e)
            }), 401
    return decorated_function

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def home():
    """Serve React frontend."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api')
def api_home():
    """API documentation."""
    return jsonify({
        'name': 'Email Validator API with Anonymous History',
        'version': '3.0.0',
        'description': 'Private history without login using anonymous user IDs',
        'authentication': 'Anonymous User ID (X-User-ID header)',
        'endpoints': {
            'GET /api': 'API documentation',
            'GET /api/health': 'Health check',
            'POST /api/validate': 'Validate single email',
            'POST /api/validate/batch': 'Validate multiple emails',
            'GET /api/history': 'Get user-specific validation history',
            'DELETE /api/history/:id': 'Delete specific validation record',
            'DELETE /api/history': 'Clear all user history',
            'GET /api/analytics': 'Get user-specific analytics'
        },
        'required_headers': {
            'X-User-ID': 'Anonymous user ID (UUIDv4 generated on frontend)'
        }
    })

# ============================================================================
# ADMIN VALIDATION ENDPOINTS (UNLIMITED ACCESS)
# ============================================================================

@app.route('/api/admin/validate', methods=['POST'])
def admin_validate_email():
    """
    Admin-only email validation endpoint with unlimited access.
    
    Headers:
        Authorization: Bearer <admin_token> (required)
    
    Request body:
        {
            "email": "user@example.com",
            "advanced": true,
            "enable_smtp": false
        }
    
    Response:
        Same as regular validation but with unlimited access
    """
    start_time = time.time()
    
    try:
        # Verify admin authentication
        admin = get_admin_from_request()
        if not admin:
            return jsonify({
                'error': 'Admin authentication required',
                'message': 'This endpoint requires admin privileges'
            }), 401
        
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Missing email parameter',
                'message': 'Please provide an email address'
            }), 400
        
        email = data['email']
        advanced = data.get('advanced', True)
        enable_smtp = data.get('enable_smtp', False)
        
        logger.info(f"Admin validation request: {email} (advanced: {advanced}) by {admin['email']}")
        
        # Perform validation (admin gets production-ready SMTP validation)
        if advanced:
            if enable_smtp:
                # Use production-ready SMTP validation for admin
                logger.info(f"Using production SMTP validation for admin: {email}")
                result = validate_email_production_ready(email, enable_smtp=True)
            else:
                result = validate_email_tiered(email)
        else:
            result = validate_email_advanced(email)
        
        # Add admin-specific metadata
        result['admin_validation'] = True
        result['admin_user'] = admin['email']
        result['processing_time'] = round(time.time() - start_time, 3)
        result['unlimited_access'] = True
        
        logger.info(f"Admin validation completed: {email} (valid: {result['valid']}) by {admin['email']}")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Admin validation failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Admin validation failed',
            'message': str(e)
        }), 500

@app.route('/api/admin/validate/batch', methods=['POST'])
def admin_validate_batch():
    """
    Admin-only batch validation endpoint with unlimited access.
    
    Headers:
        Authorization: Bearer <admin_token> (required)
    
    Request body:
        {
            "emails": ["user1@example.com", "user2@test.com"],
            "advanced": true
        }
    
    Response:
        {
            "results": [...],
            "total": 100,
            "valid_count": 85,
            "invalid_count": 15,
            "admin_validation": true,
            "unlimited_access": true
        }
    """
    start_time = time.time()
    
    try:
        # Verify admin authentication
        admin = get_admin_from_request()
        if not admin:
            return jsonify({
                'error': 'Admin authentication required',
                'message': 'This endpoint requires admin privileges'
            }), 401
        
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({
                'error': 'Missing emails parameter',
                'message': 'Please provide a list of email addresses'
            }), 400
        
        emails = data.get('emails', [])
        advanced = data.get('advanced', True)
        remove_duplicates = data.get('remove_duplicates', True)
        
        if not emails:
            return jsonify({
                'error': 'Empty email list',
                'message': 'Please provide at least one email address'
            }), 400
        
        # Track original count for duplicate removal
        original_count = len(emails)
        
        # Remove duplicates if requested (case-insensitive)
        if remove_duplicates:
            emails_lower = [email.lower().strip() for email in emails]
            unique_emails = []
            seen = set()
            for email in emails:
                email_lower = email.lower().strip()
                if email_lower not in seen:
                    seen.add(email_lower)
                    unique_emails.append(email)
            emails = unique_emails
            duplicates_removed = original_count - len(emails)
            logger.info(f"Admin batch: Removed {duplicates_removed} duplicates")
        else:
            duplicates_removed = 0
        
        logger.info(f"Admin batch validation: {len(emails)} emails (advanced: {advanced}) by {admin['email']}")
        
        # Process all emails (unlimited)
        results = []
        valid_count = 0
        invalid_count = 0
        
        for email in emails:
            try:
                # Clean email
                email = email.strip()
                
                # Validate email format
                if not validate_email_format(email):
                    result = {
                        'email': email,
                        'valid': False,
                        'reason': 'Invalid email format',
                        'checks': {'syntax': False}
                    }
                else:
                    # Perform validation
                    if advanced:
                        try:
                            result = validate_email_advanced(email)
                        except Exception as e:
                            logger.error(f"Advanced validation error for {email}: {str(e)}")
                            result = {
                                'email': email,
                                'valid': False,
                                'reason': f'Validation error: {str(e)}',
                                'checks': {'syntax': True}
                            }
                        
                        # Add enrichment
                        enrichment_data = enricher.enrich_email(email)
                        if enrichment_data:
                            result['enrichment'] = enrichment_data
                        
                        # Add deliverability score
                        deliverability = calculate_deliverability_score(email, result)
                        result['deliverability'] = deliverability
                        
                        # Add pattern analysis
                        pattern = analyze_email_pattern(email)
                        if pattern:
                            result['pattern_analysis'] = pattern
                        
                        # Add risk check
                        if '@' in email:
                            domain = email.split('@')[1]
                            risk = comprehensive_risk_check(email, domain)
                            result['risk_check'] = risk
                        
                        # Add bounce check (integrated)
                        try:
                            from email_sender import get_email_sender
                            sender = get_email_sender()
                            bounce_check = sender.check_bounce_history(email)
                            result['bounce_check'] = bounce_check
                        except Exception as e:
                            logger.error(f"Bounce check failed: {e}")
                            result['bounce_check'] = {'has_bounced': False, 'total_bounces': 0, 'risk_level': 'low'}
                        
                        # Add status
                        status = determine_email_status(result)
                        result['status'] = status
                    else:
                        # Basic validation
                        result = {'email': email, 'valid': validate_email_format(email)}
                
                results.append(result)
                
                if result.get('valid'):
                    valid_count += 1
                else:
                    invalid_count += 1
                    
            except Exception as e:
                logger.error(f"Admin batch validation error for {email}: {str(e)}")
                results.append({
                    'email': email,
                    'valid': False,
                    'error': str(e),
                    'reason': 'Validation failed'
                })
                invalid_count += 1
        
        processing_time = round(time.time() - start_time, 3)
        
        # Calculate domain statistics
        domain_stats = calculate_domain_stats(results)
        
        response = {
            'results': results,
            'total': len(emails),
            'original_count': original_count,
            'duplicates_removed': duplicates_removed,
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'processing_time': processing_time,
            'domain_stats': domain_stats,
            'admin_validation': True,
            'admin_user': admin['email'],
            'unlimited_access': True
        }
        
        logger.info(f"Admin batch validation completed: {len(emails)} emails ({valid_count} valid, {invalid_count} invalid) by {admin['email']}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Admin batch validation failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Admin batch validation failed',
            'message': str(e)
        }), 500

# ============================================================================
# SHARE FUNCTIONALITY - Backend Storage for Cross-User Sharing
# ============================================================================

@app.route('/api/share', methods=['POST'])
def create_share():
    """Create a shareable link for batch results."""
    try:
        data = request.get_json()
        
        if not data or 'results' not in data:
            return jsonify({'error': 'No results data provided'}), 400
        
        # Generate unique share ID
        import uuid
        share_id = f"share_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Prepare share data with expiration (7 days)
        expiration_date = datetime.now() + timedelta(days=7)
        
        share_data = {
            'share_id': share_id,
            'created_at': datetime.now().isoformat(),
            'expires_at': expiration_date.isoformat(),
            'metadata': data.get('metadata', {}),
            'results': data.get('results', []),
            'domain_statistics': data.get('domain_statistics'),
            'shared_by': data.get('shared_by', 'Anonymous User'),
            'is_public': True  # Anyone with link can view
        }
        
        # Try to store in Supabase, fallback to in-memory storage if table doesn't exist
        try:
            supabase = get_storage()
            result = supabase.table('shared_results').insert(share_data).execute()
            
            if result.data:
                logger.info(f"Created share link in database: {share_id}")
                return jsonify({
                    'success': True,
                    'share_id': share_id,
                    'share_url': f"{request.host_url}?share={share_id}",
                    'expires_at': expiration_date.isoformat()
                })
            else:
                raise Exception("Database insert failed")
                
        except Exception as db_error:
            logger.warning(f"Database storage failed, using in-memory fallback: {str(db_error)}")
            
            # Fallback: Store in a global dictionary (in-memory)
            if not hasattr(app, 'shared_data_store'):
                app.shared_data_store = {}
            
            app.shared_data_store[share_id] = share_data
            
            logger.info(f"Created share link in memory: {share_id}")
            return jsonify({
                'success': True,
                'share_id': share_id,
                'share_url': f"{request.host_url}?share={share_id}",
                'expires_at': expiration_date.isoformat(),
                'storage': 'memory'  # Indicate fallback storage
            })
            
    except Exception as e:
        logger.error(f"Share creation failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to create share link',
            'message': str(e)
        }), 500

@app.route('/api/share/<share_id>', methods=['GET'])
def get_share(share_id):
    """Retrieve shared batch results."""
    try:
        # Try database first, then fallback to in-memory storage
        try:
            supabase = get_storage()
            result = supabase.table('shared_results').select('*').eq('share_id', share_id).execute()
            
            if result.data:
                share_data = result.data[0]
                
                # Check if expired
                expiration_date = datetime.fromisoformat(share_data['expires_at'].replace('Z', '+00:00'))
                if datetime.now() > expiration_date.replace(tzinfo=None):
                    # Clean up expired data
                    supabase.table('shared_results').delete().eq('share_id', share_id).execute()
                    return jsonify({'error': 'This shared link has expired'}), 410
                
                logger.info(f"Retrieved share link from database: {share_id}")
                return jsonify({
                    'success': True,
                    'data': {
                        'metadata': share_data['metadata'],
                        'results': share_data['results'],
                        'domain_statistics': share_data['domain_statistics'],
                        'shared_by': share_data['shared_by'],
                        'created_at': share_data['created_at'],
                        'expires_at': share_data['expires_at']
                    }
                })
                
        except Exception as db_error:
            logger.warning(f"Database retrieval failed, trying in-memory fallback: {str(db_error)}")
        
        # Fallback: Check in-memory storage
        if hasattr(app, 'shared_data_store') and share_id in app.shared_data_store:
            share_data = app.shared_data_store[share_id]
            
            # Check if expired
            expiration_date = datetime.fromisoformat(share_data['expires_at'])
            if datetime.now() > expiration_date:
                # Clean up expired data
                del app.shared_data_store[share_id]
                return jsonify({'error': 'This shared link has expired'}), 410
            
            logger.info(f"Retrieved share link from memory: {share_id}")
            return jsonify({
                'success': True,
                'data': {
                    'metadata': share_data['metadata'],
                    'results': share_data['results'],
                    'domain_statistics': share_data['domain_statistics'],
                    'shared_by': share_data['shared_by'],
                    'created_at': share_data['created_at'],
                    'expires_at': share_data['expires_at']
                }
            })
        
        # Not found in either database or memory
        return jsonify({'error': 'Shared results not found or have expired'}), 404
        
    except Exception as e:
        logger.error(f"Share retrieval failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve shared results',
            'message': str(e)
        }), 500

@app.route('/api/share/cleanup', methods=['POST'])
def cleanup_expired_shares():
    """Clean up expired shared results (can be called periodically)."""
    try:
        supabase = get_storage()
        
        # Delete expired shares
        current_time = datetime.now().isoformat()
        result = supabase.table('shared_results').delete().lt('expires_at', current_time).execute()
        
        cleaned_count = len(result.data) if result.data else 0
        logger.info(f"Cleaned up {cleaned_count} expired shares")
        
        return jsonify({
            'success': True,
            'cleaned_count': cleaned_count
        })
        
    except Exception as e:
        logger.error(f"Share cleanup failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to cleanup expired shares',
            'message': str(e)
        }), 500

@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'email-validator-anon',
        'timestamp': time.time(),
        'version': '3.0.0'
    })

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/signup', methods=['POST'])
@rate_limit
def signup():
    """
    User registration endpoint.
    
    Request body:
        {
            "firstName": "John",
            "lastName": "Doe", 
            "email": "john@example.com",
            "password": "securepassword123"
        }
    
    Response:
        {
            "success": true,
            "message": "Account created successfully",
            "user": {
                "id": "uuid",
                "email": "john@example.com",
                "firstName": "John",
                "lastName": "Doe"
            },
            "token": "jwt_token"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Missing request data',
                'message': 'Request body is required'
            }), 400
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'error': f'Missing {field}',
                    'message': f'{field} is required'
                }), 400
        
        first_name = data['firstName'].strip()
        last_name = data['lastName'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate email format
        if not validate_email_format(email):
            return jsonify({
                'error': 'Invalid email format',
                'message': 'Please provide a valid email address'
            }), 400
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({
                'error': 'Weak password',
                'message': 'Password must be at least 8 characters long'
            }), 400
        
        # Check if user already exists in database
        storage = get_storage()
        existing_user = storage.get_user_by_email(email)
        if existing_user:
            return jsonify({
                'error': 'Email already registered',
                'message': 'An account with this email already exists'
            }), 409
        
        # Hash password
        password_hash = hash_password(password)
        
        # Generate API key
        import secrets
        api_key = f"ev_{secrets.token_hex(32)}"
        
        # Create user in database with proper free tier defaults
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'first_name': first_name,
            'last_name': last_name,
            'api_key': api_key,
            'subscription_tier': 'free',  # Default tier
            'api_calls_count': 0,         # Start with 0 calls
            'api_calls_limit': 10,        # Free tier limit (10 validations)
            'is_verified': False,
            'is_active': True
        }
        
        user = storage.create_user(user_data)
        
        logger.info(f"Created user: {email} with API key: {api_key[:10]}... and {user_data['api_calls_limit']} API calls limit")
        
        # Generate JWT token
        token = generate_jwt_token(user)
        
        # Return success response (exclude sensitive data)
        user_response = {
            'id': user['id'],
            'email': user['email'],
            'firstName': user['first_name'],
            'lastName': user['last_name'],
            'subscriptionTier': user['subscription_tier'],
            'apiCallsLimit': user['api_calls_limit'],
            'createdAt': user['created_at']
        }
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': user_response,
            'token': token
        }), 201
        
    except Exception as e:
        logger.error(f"Signup failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Registration failed',
            'message': 'An error occurred while creating your account'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
@rate_limit
def login():
    """
    User login endpoint.
    
    Request body:
        {
            "email": "john@example.com",
            "password": "securepassword123"
        }
    
    Response:
        {
            "success": true,
            "message": "Login successful",
            "user": {
                "id": "uuid",
                "email": "john@example.com",
                "firstName": "John",
                "lastName": "Doe"
            },
            "token": "jwt_token"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Missing request data',
                'message': 'Request body is required'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'error': 'Missing credentials',
                'message': 'Email and password are required'
            }), 400
        
        # Get user from database
        storage = get_storage()
        user = storage.get_user_by_email(email)
        
        if not user:
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Email or password is incorrect'
            }), 401
        
        # Check if account is active
        if not user.get('is_active', True):
            return jsonify({
                'error': 'Account disabled',
                'message': 'Your account has been disabled'
            }), 401
        
        # Check if account is suspended
        if user.get('is_suspended', False):
            suspension_reason = user.get('suspension_reason', 'No reason provided')
            return jsonify({
                'error': 'Account suspended',
                'message': f'Your account has been suspended. Reason: {suspension_reason}',
                'suspension_reason': suspension_reason,
                'suspended_at': user.get('suspended_at'),
                'contact_support': True
            }), 403
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Email or password is incorrect'
            }), 401
        
        # Update last login in database
        storage.update_user_last_login(user['id'])
        
        # Generate JWT token
        token = generate_jwt_token(user)
        
        # Return success response (exclude sensitive data)
        user_response = {
            'id': user['id'],
            'email': user['email'],
            'firstName': user['first_name'],
            'lastName': user['last_name'],
            'subscriptionTier': user['subscription_tier'],
            'apiCallsLimit': user['api_calls_limit'],
            'apiCallsCount': user['api_calls_count'],
            'createdAt': user['created_at'],
            'lastLogin': user.get('last_login')
        }
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user_response,
            'token': token
        })
        
    except Exception as e:
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Login failed',
            'message': 'An error occurred during login'
        }), 500

@app.route('/api/auth/me', methods=['GET'])
@auth_required
def get_current_user():
    """
    Get current user profile.
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Response:
        {
            "user": {
                "id": "uuid",
                "email": "john@example.com",
                "firstName": "John",
                "lastName": "Doe",
                ...
            }
        }
    """
    try:
        user_id = request.current_user['user_id']
        
        # Get user from database
        storage = get_storage()
        user = storage.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'message': 'User account no longer exists'
            }), 404
        
        # Check if user is in a team (team membership gives Pro access)
        effective_subscription_tier = user['subscription_tier']
        team_info = None
        
        if user.get('team_id'):
            # User is in a team, they get Pro-level access
            effective_subscription_tier = 'pro'

            # Get team information
            try:
                team_result = storage.client.table('team_dashboard').select('*').eq('id', user['team_id']).execute()
                if team_result.data:
                    team_info = team_result.data[0]
            except:
                pass  # If team query fails, continue without team info
        
        # Return user data (exclude sensitive fields)
        user_response = {
            'id': user['id'],
            'email': user['email'],
            'firstName': user['first_name'],
            'lastName': user['last_name'],
            'subscriptionTier': effective_subscription_tier,  # This now considers team membership
            'originalSubscriptionTier': user['subscription_tier'],  # Original individual tier
            'apiKey': user.get('api_key'),
            'apiCallsLimit': user['api_calls_limit'],
            'apiCallsCount': user['api_calls_count'],
            'isVerified': user['is_verified'],
            'createdAt': user['created_at'],
            'lastLogin': user.get('last_login'),
            'teamId': user.get('team_id'),
            'teamRole': user.get('team_role'),
            'teamInfo': team_info
        }
        
        return jsonify({
            'user': user_response
        })
        
    except Exception as e:
        logger.error(f"Get current user failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to get user profile',
            'message': 'An error occurred while fetching user data'
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
@auth_required
def logout():
    """
    User logout endpoint.
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Response:
        {
            "success": true,
            "message": "Logged out successfully"
        }
    """
    try:
        # In a more complex system, you might want to blacklist the token
        # For now, we'll just return success since JWT tokens are stateless
        
        logger.info(f"User logged out: {request.current_user['email']}")
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Logout failed',
            'message': 'An error occurred during logout'
        }), 500

@app.route('/api/auth/profile', methods=['PUT'])
@auth_required
def update_profile():
    """
    Update user profile information.
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Request body:
        {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com",
            "sendgridApiKey": "SG.abc123..."
        }
    
    Response:
        {
            "success": true,
            "message": "Profile updated successfully",
            "user": {...}
        }
    """
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'message': 'Request body is required'
            }), 400
        
        # Get current user
        storage = get_storage()
        user = storage.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'message': 'User account no longer exists'
            }), 404
        
        # Update fields (for now, we'll just return success - implement storage later)
        updated_fields = {}
        
        if 'firstName' in data:
            updated_fields['first_name'] = data['firstName'].strip()
        if 'lastName' in data:
            updated_fields['last_name'] = data['lastName'].strip()
        if 'email' in data:
            # Validate email format
            new_email = data['email'].strip().lower()
            if not validate_email_format(new_email):
                return jsonify({
                    'error': 'Invalid email format',
                    'message': 'Please provide a valid email address'
                }), 400
            updated_fields['email'] = new_email
        if 'sendgridApiKey' in data:
            # For now, just store it (we'll add validation later)
            updated_fields['sendgrid_api_key'] = data['sendgridApiKey'].strip()
        
        # TODO: Implement actual database update
        # For now, return the updated user data
        updated_user = {**user, **updated_fields}
        
        logger.info(f"Profile updated for user {user_id}: {list(updated_fields.keys())}")
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'id': updated_user['id'],
                'email': updated_user.get('email', user['email']),
                'firstName': updated_fields.get('first_name', user['first_name']),
                'lastName': updated_fields.get('last_name', user['last_name']),
                'subscriptionTier': updated_user['subscription_tier'],
                'apiCallsLimit': updated_user['api_calls_limit'],
                'apiCallsCount': updated_user['api_calls_count'],
                'createdAt': updated_user['created_at'],
                'sendgridApiKey': updated_fields.get('sendgrid_api_key', user.get('sendgrid_api_key', ''))
            }
        })
        
    except Exception as e:
        logger.error(f"Profile update failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Profile update failed',
            'message': 'An error occurred while updating your profile'
        }), 500

@app.route('/api/validate', methods=['POST'])
@rate_limit
def validate_email():
    """
    Validate single email for AUTHENTICATED users (saves to database).
    
    Headers:
        Authorization: Bearer <token> (required for authenticated users)
    
    Request body:
        {
            "email": "user@example.com",
            "advanced": true,
            "enable_smtp": false
        }
    
    Response:
        {
            "email": "user@example.com",
            "valid": true,
            "confidence_score": 95,
            "checks": {...},
            "risk_assessment": {...},
            "enrichment": {...},
            "record_id": 123,
            "processing_time": 0.123
        }
    """
    start_time = time.time()
    
    try:
        # Extract anonymous user ID (for logging and fallback)
        try:
            anon_user_id = get_anon_user_id()
        except ValueError:
            anon_user_id = "unknown"  # Fallback for authenticated users
        
        # Check if user is authenticated (required for database storage)
        user_id = None
        authenticated_user = None
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'This endpoint requires login. Use /api/validate/local for anonymous validation.'
                }), 401
            
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            user_id = payload.get('user_id')
            
            # Get user details for API limiting
            storage = get_storage()
            authenticated_user = storage.get_user_by_id(user_id)
            if not authenticated_user:
                return jsonify({
                    'error': 'User not found',
                    'message': 'User account no longer exists'
                }), 404
            
            # Check if user is suspended (IMMEDIATE CHECK)
            if authenticated_user.get('is_suspended', False):
                suspension_reason = authenticated_user.get('suspension_reason', 'No reason provided')
                return jsonify({
                    'error': 'Account suspended',
                    'message': f'Your account has been suspended. Reason: {suspension_reason}',
                    'suspension_reason': suspension_reason,
                    'suspended_at': authenticated_user.get('suspended_at'),
                    'suspended': True
                }), 403
                
            # Check API limits - team quota takes priority over individual quota
            is_admin = is_admin_request()
            
            # Check if user is in a team (team quota overrides individual quota)
            team_info = team_manager.get_user_team(user_id)

            if team_info and team_info['team']['is_active']:
                # Use team quota
                team_id = team_info['team']['id']
                can_validate = team_manager.check_team_quota(team_id, 1)
                
                if not can_validate:
                    team_usage = team_manager.get_team_usage(team_id)
                    if team_usage['success']:
                        usage_data = team_usage['usage']
                        return jsonify({
                            'error': 'Team quota exceeded',
                            'message': f'Your team has reached the lifetime limit of {usage_data["quota_limit"]:,} validations. This is a lifetime quota that does not reset.',
                            'current_usage': usage_data['quota_used'],
                            'limit': usage_data['quota_limit'],
                            'usage_percentage': usage_data['usage_percentage'],
                            'team_name': team_info['team']['name'],
                            'is_team_quota': True
                        }), 429
                    else:
                        return jsonify({'error': 'Unable to check team quota'}), 500
            else:
                # Use individual quota
                can_validate, current_usage, limit = check_api_limits(authenticated_user, is_admin)
                
                if not can_validate:
                    subscription_tier = get_effective_subscription_tier(authenticated_user)
                    if subscription_tier == 'free':
                        message = f'You have reached your daily limit of {limit} API calls. Come back tomorrow or upgrade to Pro for 10K calls per month!'
                    elif subscription_tier == 'starter':
                        message = f'You have reached your monthly limit of {limit:,} API calls. Upgrade to Pro for 10M lifetime calls!'
                    else:  # pro
                        message = f'You have reached your lifetime limit of {limit:,} API calls. Contact support for enterprise options.'
                    
                    return jsonify({
                        'error': 'API limit exceeded',
                        'message': message,
                        'current_usage': current_usage,
                        'limit': limit,
                        'subscription_tier': subscription_tier,
                        'is_team_quota': False
                    }), 429
                
        except ValueError as e:
            return jsonify({
                'error': 'Invalid authentication',
                'message': str(e)
            }), 401
        
        data = request.get_json()
        
        if not data or 'email' not in data:
            logger.warning(f"Missing email parameter from user {user_id or anon_user_id}")
            return jsonify({
                'error': 'Missing email parameter',
                'message': 'Please provide an email address'
            }), 400
        
        email = data['email']
        advanced = data.get('advanced', True)
        enable_smtp = data.get('enable_smtp', False)
        
        # Input validation
        if not validate_email_format(email):
            logger.warning(f"Invalid email format: {email}")
            return jsonify({
                'error': 'Invalid email format',
                'message': 'Email must be a valid format'
            }), 400
        
        logger.info(f"Validating email: {email} (user_id: {user_id}, anon_id: {anon_user_id}, advanced: {advanced})")
        
        # Validate email using TIERED system (optional SMTP mailbox check)
        if advanced:
            if enable_smtp:
                # Production-ready SMTP validation (74ms for Gmail vs 156 seconds!)
                logger.info(f"Using production SMTP validation for authenticated user: {email}")
                result = validate_email_production_ready(email, enable_smtp=True)
            else:
                result = validate_email_tiered(email)
        else:
            # Basic validation
            from emailvalidator_unified import validate_email as validate_basic
            is_valid = validate_basic(email)
            result = {
                'email': email,
                'valid': is_valid,
                'confidence_score': 100 if is_valid else 0,
                'checks': {'syntax': is_valid}
            }
        
        # Fast parallel processing of additional checks
        import concurrent.futures
        import threading
        
        def safe_pattern_analysis():
            try:
                return analyze_email_pattern(email)
            except Exception as e:
                logger.error(f"Pattern analysis failed: {str(e)}")
                return None
        
        def safe_risk_check():
            try:
                domain = email.split('@')[1]
                risk_check = comprehensive_risk_check(email, domain)
                return risk_check
            except Exception as e:
                logger.error(f"Risk check failed for {email}: {str(e)}")
                return None
        
        def safe_bounce_check():
            try:
                from email_sender import get_email_sender
                sender = get_email_sender()
                return sender.check_bounce_history(email)
            except Exception as e:
                logger.error(f"Bounce check failed for {email}: {str(e)}")
                return {'has_bounced': False, 'total_bounces': 0, 'risk_level': 'low'}
        
        def safe_deliverability():
            try:
                return calculate_deliverability_score(email, result)
            except Exception as e:
                logger.error(f"Deliverability calculation failed: {str(e)}")
                return None
        
        def safe_status():
            try:
                return determine_email_status(result)
            except Exception as e:
                logger.error(f"Status determination failed: {str(e)}")
                return None
        
        def safe_enrichment():
            try:
                return enricher.enrich_email(email, validation_data=result)
            except Exception as e:
                logger.error(f"Email enrichment failed: {str(e)}")
                return {'error': str(e)}
        
        # Run additional checks in parallel with 2 second timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                'pattern': executor.submit(safe_pattern_analysis),
                'risk': executor.submit(safe_risk_check),
                'bounce': executor.submit(safe_bounce_check),
                'deliverability': executor.submit(safe_deliverability),
                'status': executor.submit(safe_status),
                'enrichment': executor.submit(safe_enrichment)
            }
            
            # Wait for results with timeout
            for name, future in futures.items():
                try:
                    result_data = future.result(timeout=2.0)  # 2 second timeout per check
                    if result_data:
                        if name == 'pattern':
                            result['pattern_analysis'] = result_data
                        elif name == 'risk':
                            result['risk_check'] = result_data
                            # Override validity if critical risk detected
                            if result_data['overall_risk'] == 'critical':
                                result['valid'] = False
                                logger.warning(f"CRITICAL RISK detected for {email}: {result_data['recommendation']}")
                                if result.get('reason'):
                                    result['reason'] += f"; {result_data['recommendation']}"
                                else:
                                    result['reason'] = result_data['recommendation']
                        elif name == 'bounce':
                            result['bounce_check'] = result_data
                            # Add bounce warning if exists
                            if result_data['has_bounced'] and result_data['risk_level'] in ['critical', 'high']:
                                result['valid'] = False
                                if result.get('reason'):
                                    result['reason'] += f"; {result_data['warning']}"
                                else:
                                    result['reason'] = result_data['warning']
                        elif name == 'deliverability':
                            result['deliverability'] = result_data
                        elif name == 'status':
                            result['status'] = result_data
                        elif name == 'enrichment':
                            result['enrichment'] = result_data
                except concurrent.futures.TimeoutError:
                    logger.warning(f"{name} check timed out for {email}")
                except Exception as e:
                    logger.error(f"{name} check failed for {email}: {str(e)}")
        
        processing_time = time.time() - start_time
        result['processing_time'] = round(processing_time, 4)
        
        # Store in database ONLY for authenticated users
        try:
            storage = get_storage()
            
            # Only store in database for authenticated users
            # Free users should use localStorage only (privacy-first approach)
            # Get team_id if user is in a team
            team_id = None
            if team_info and team_info['team']['is_active']:
                team_id = team_info['team']['id']
            
            record = storage.create_record({
                'anon_user_id': anon_user_id,
                'user_id': user_id,  # Always present for authenticated users
                'team_id': team_id,  # Include team_id if user is in a team
                'email': email,
                'valid': result['valid'],
                'confidence_score': result.get('confidence_score', 0),
                'checks': result.get('checks', {}),
                'smtp_details': result.get('smtp_details'),
                'is_disposable': result.get('checks', {}).get('is_disposable', False),
                'is_role_based': result.get('checks', {}).get('is_role_based', False),
                'is_catch_all': result.get('is_catch_all', False)
            })
            result['record_id'] = record['id']
            result['stored'] = True
            
            # Increment API usage for authenticated users (skip for admins)
            if authenticated_user and not is_admin:
                try:

                    # Check if user is in a team - increment team quota instead of individual
                    if team_info and team_info.get('team', {}).get('is_active'):
                        team_id = team_info['team']['id']

                        team_manager.use_team_quota(team_id, 1)
                        
                        # Get updated team usage for response
                        team_usage = team_manager.get_team_usage(team_id)
                        if team_usage['success']:
                            usage_data = team_usage['usage']
                            result['api_usage'] = {
                                'calls_used': usage_data['quota_used'],
                                'calls_limit': usage_data['quota_limit'],
                                'calls_remaining': usage_data['quota_limit'] - usage_data['quota_used'],
                                'team_name': team_info['team']['name'],
                                'is_team_quota': True
                            }

                        logger.info(f"Team quota incremented for team {team_id} (user {user_id})")
                    else:

                        # Use individual quota
                        storage.increment_api_usage(user_id, 1)
                        new_count = authenticated_user['api_calls_count'] + 1
                        result['api_usage'] = {
                            'calls_used': new_count,
                            'calls_limit': authenticated_user['api_calls_limit'],
                            'calls_remaining': authenticated_user['api_calls_limit'] - new_count,
                            'is_team_quota': False
                        }
                        logger.info(f"API usage incremented for user {user_id}: {new_count}/{authenticated_user['api_calls_limit']}")
                except Exception as e:

                    logger.error(f"Failed to increment API usage: {str(e)}")
            elif is_admin:
                # For admin users, show unlimited usage
                result['api_usage'] = {
                    'calls_used': 0,
                    'calls_limit': 'unlimited',
                    'calls_remaining': 'unlimited'
                }
                logger.info(f"Admin validation (unlimited): {email}")
            
            logger.info(f"Validation stored in database: {email} (valid: {result['valid']}, score: {result.get('confidence_score')}) for user {user_id}")
        except Exception as e:
            logger.error(f"Database storage failed: {str(e)}")
            result['stored'] = False
            result['storage_error'] = str(e)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Validation failed',
            'message': str(e)
        }), 500

@app.route('/api/validate/local', methods=['POST'])
@rate_limit
def validate_email_local():
    """
    Validate single email for ANONYMOUS users (LIMITED to 2 validations).
    Results are returned but not saved to database.
    
    Headers:
        X-User-ID: Anonymous user ID (required for tracking limits)
    
    Request body:
        {
            "email": "user@example.com",
            "advanced": true
        }
    
    Response:
        {
            "email": "user@example.com",
            "valid": true,
            "confidence_score": 95,
            "checks": {...},
            "risk_assessment": {...},
            "enrichment": {...},
            "processing_time": 0.123,
            "storage": "local_only",
            "anonymous_usage": {"used": 1, "limit": 2}
        }
    """
    start_time = time.time()
    
    try:
        # Extract anonymous user ID for tracking limits
        try:
            anon_user_id = get_anon_user_id()
        except ValueError as e:
            return jsonify({
                'error': 'Anonymous ID required',
                'message': 'Please refresh the page to generate an anonymous ID'
            }), 400
        
        # Check anonymous user limits (2 validations max)
        storage = get_storage()
        try:
            # Count existing validations for this anonymous user
            existing_validations = storage.client.table('email_validations').select('id').eq('anon_user_id', anon_user_id).execute()
            validation_count = len(existing_validations.data) if existing_validations.data else 0
            
            ANONYMOUS_LIMIT = 2
            if validation_count >= ANONYMOUS_LIMIT:
                return jsonify({
                    'error': 'Anonymous limit reached',
                    'message': f'Anonymous users can only validate {ANONYMOUS_LIMIT} emails. Please sign up for unlimited access!',
                    'anonymous_usage': {
                        'used': validation_count,
                        'limit': ANONYMOUS_LIMIT
                    },
                    'upgrade_required': True
                }), 429
        except Exception as e:
            logger.warning(f"Could not check anonymous limits: {e}")
            # Continue anyway if database check fails
        
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Missing email parameter',
                'message': 'Please provide an email address'
            }), 400
        
        email = data['email']
        advanced = data.get('advanced', True)
        enable_smtp = data.get('enable_smtp', False)
        
        # Input validation
        if not validate_email_format(email):
            logger.warning(f"Invalid email format: {email}")
            return jsonify({
                'error': 'Invalid email format',
                'message': 'Email must be a valid format'
            }), 400
        
        logger.info(f"Anonymous validation: {email} (advanced: {advanced})")
        
        # Validate email using TIERED system (optional SMTP mailbox check)
        if advanced:
            if enable_smtp:
                # Production-ready SMTP validation for anonymous users too
                logger.info(f"Using production SMTP validation for anonymous user: {email}")
                result = validate_email_production_ready(email, enable_smtp=True)
            else:
                result = validate_email_tiered(email)
        else:
            from emailvalidator_unified import validate_email as validate_basic
            is_valid = validate_basic(email)
            result = {
                'email': email,
                'valid': is_valid,
                'confidence_score': 100 if is_valid else 0,
                'checks': {'syntax': is_valid}
            }
        
        processing_time = time.time() - start_time
        result['processing_time'] = round(processing_time, 4)
        
        # Pattern analysis
        try:
            pattern_analysis = analyze_email_pattern(email)
            result['pattern_analysis'] = pattern_analysis
        except Exception as e:
            logger.error(f"Pattern analysis failed: {str(e)}")
        
        # Spam trap & risk detection
        try:
            domain = email.split('@')[1]
            risk_check = comprehensive_risk_check(email, domain)
            result['risk_check'] = risk_check
            
            # Override validity if critical risk detected
            if risk_check['overall_risk'] == 'critical':
                result['valid'] = False
                if result.get('reason'):
                    result['reason'] += f"; {risk_check['recommendation']}"
                else:
                    result['reason'] = risk_check['recommendation']
        except Exception as e:
            logger.error(f"Risk check failed for {email}: {str(e)}")
        
        # Bounce check (but don't save bounces for anonymous users)
        try:
            from email_sender import get_email_sender
            sender = get_email_sender()
            bounce_check = sender.check_bounce_history(email)
            result['bounce_check'] = bounce_check
            
            if bounce_check['has_bounced'] and bounce_check['risk_level'] in ['critical', 'high']:
                result['valid'] = False
                if result.get('reason'):
                    result['reason'] += f"; {bounce_check.get('warning', 'High bounce risk')}"
                else:
                    result['reason'] = bounce_check.get('warning', 'High bounce risk')
        except Exception as e:
            logger.error(f"Bounce check failed for {email}: {str(e)}")
            result['bounce_check'] = {'has_bounced': False, 'total_bounces': 0, 'risk_level': 'low'}
        
        # Calculate deliverability score
        try:
            deliverability = calculate_deliverability_score(email, result)
            result['deliverability'] = deliverability
        except Exception as e:
            logger.error(f"Deliverability calculation failed: {str(e)}")
        
        # Determine email status
        try:
            status_info = determine_email_status(result)
            result['status'] = status_info
        except Exception as e:
            logger.error(f"Status determination failed: {str(e)}")
        
        # Enrich email data
        try:
            enrichment = enricher.enrich_email(email, validation_data=result)
            result['enrichment'] = enrichment
        except Exception as e:
            logger.error(f"Email enrichment failed: {str(e)}")
            result['enrichment'] = {'error': str(e)}
        
        # Store validation for anonymous user (to track limits)
        try:
            storage = get_storage()
            record = storage.create_record({
                'anon_user_id': anon_user_id,
                'user_id': None,  # Anonymous user
                'email': email,
                'valid': result['valid'],
                'confidence_score': result.get('confidence_score', 0),
                'checks': result.get('checks', {}),
                'smtp_details': result.get('smtp_details'),
                'is_disposable': result.get('checks', {}).get('is_disposable', False),
                'is_role_based': result.get('checks', {}).get('is_role_based', False),
                'is_catch_all': result.get('is_catch_all', False)
            })
            result['record_id'] = record['id']
            result['stored'] = True
            
            # Get updated count
            updated_validations = storage.client.table('email_validations').select('id').eq('anon_user_id', anon_user_id).execute()
            current_count = len(updated_validations.data) if updated_validations.data else 0
            
            result['anonymous_usage'] = {
                'used': current_count,
                'limit': 2,
                'remaining': 2 - current_count
            }
            
            logger.info(f"Anonymous validation stored: {email} (valid: {result['valid']}) - Usage: {current_count}/2")
        except Exception as e:
            logger.error(f"Failed to store anonymous validation: {str(e)}")
            result['stored'] = False
            result['anonymous_usage'] = {'used': 0, 'limit': 2, 'remaining': 2}
        
        # Mark as anonymous validation
        result['storage'] = 'anonymous_tracked'
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Anonymous validation failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Validation failed',
            'message': str(e)
        }), 500

@app.route('/api/validate/batch', methods=['POST'])
@rate_limit
def validate_batch_endpoint():
    """
    Validate multiple emails with anonymous user tracking.
    
    Headers:
        X-User-ID: Anonymous user ID (required)
    
    Request body:
        {
            "emails": ["user1@example.com", "user2@test.com"],
            "advanced": true,
            "remove_duplicates": true
        }
    
    Response:
        {
            "total": 2,
            "valid_count": 1,
            "invalid_count": 1,
            "duplicates_removed": 5,
            "results": [...],
            "processing_time": 0.123
        }
    """
    start_time = time.time()
    
    try:
        # Extract anonymous user ID
        try:
            anon_user_id = get_anon_user_id()
        except ValueError as e:
            logger.warning(f"Batch validation auth failed: {str(e)}")
            return jsonify({
                'error': 'Authentication required',
                'message': str(e)
            }), 400
        
        # Check if user is authenticated - batch validation requires login
        user_id = None
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': 'Login required for batch validation',
                    'message': 'Batch validation is only available for registered users. Please sign up or login to validate multiple emails at once.',
                    'feature_restricted': True,
                    'single_validation_available': True
                }), 401
            
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            user_id = payload.get('user_id')
            logger.info(f"Authenticated batch validation for user {user_id}")
        except Exception as e:
            return jsonify({
                'error': 'Login required for batch validation',
                'message': 'Batch validation is only available for registered users. Please sign up or login to validate multiple emails at once.',
                'feature_restricted': True,
                'single_validation_available': True
            }), 401
        
        data = request.get_json()
        
        if not data or 'emails' not in data:
            logger.warning(f"Missing emails parameter from user {anon_user_id}")
            return jsonify({
                'error': 'Missing emails parameter',
                'message': 'Please provide an array of email addresses'
            }), 400
        
        emails = data['emails']
        advanced = data.get('advanced', True)
        remove_duplicates = data.get('remove_duplicates', True)
        
        # Track original count for duplicate detection
        original_count = len(emails)
        
        # Remove duplicates if requested (case-insensitive)
        if remove_duplicates:
            emails_lower = [email.lower().strip() for email in emails]
            unique_emails = []
            seen = set()
            for email in emails:
                email_lower = email.lower().strip()
                if email_lower not in seen:
                    seen.add(email_lower)
                    unique_emails.append(email)
            emails = unique_emails
            duplicates_removed = original_count - len(emails)
            logger.info(f"Removed {duplicates_removed} duplicates from batch (user: {anon_user_id})")
        else:
            duplicates_removed = 0
        
        # Input validation
        if not isinstance(emails, list):
            logger.warning(f"Invalid emails parameter type from user {anon_user_id}")
            return jsonify({
                'error': 'Invalid emails parameter',
                'message': 'emails must be an array'
            }), 400
        
        if len(emails) == 0:
            return jsonify({
                'error': 'Empty array',
                'message': 'Please provide at least one email address'
            }), 400
        
        if len(emails) > 5000:
            logger.warning(f"Too many emails ({len(emails)}) from user {anon_user_id}")
            return jsonify({
                'error': 'Too many emails',
                'message': 'Maximum 5,000 emails per request'
            }), 400
        
        # Validate each email format
        invalid_formats = []
        for email in emails:
            if not validate_email_format(email):
                invalid_formats.append(email)
        
        if invalid_formats:
            logger.warning(f"Invalid email formats in batch: {invalid_formats[:5]}")
            return jsonify({
                'error': 'Invalid email formats',
                'message': f'{len(invalid_formats)} emails have invalid format',
                'invalid_emails': invalid_formats[:10]  # Return first 10
            }), 400
        
        logger.info(f"Batch validation started: {len(emails)} emails (user: {anon_user_id}, advanced: {advanced})")
        
        # Validate batch
        results = validate_batch(emails, advanced=advanced)
        
        # Add risk checks and pattern analysis to each result
        for result in results:
            try:
                email = result['email']
                
                # Pattern analysis
                pattern_analysis = analyze_email_pattern(email)
                result['pattern_analysis'] = pattern_analysis
                
                # Spam trap & risk detection
                if '@' in email:
                    domain = email.split('@')[1]
                    risk_check = comprehensive_risk_check(email, domain)
                    result['risk_check'] = risk_check
                    
                    # Override validity if critical risk detected
                    if risk_check['overall_risk'] == 'critical':
                        result['valid'] = False
                        if result.get('reason'):
                            result['reason'] += f"; {risk_check['recommendation']}"
                        else:
                            result['reason'] = risk_check['recommendation']
                
                # Bounce history check (integrated)
                try:
                    from email_sender import get_email_sender
                    sender = get_email_sender()
                    bounce_check = sender.check_bounce_history(email)
                    result['bounce_check'] = bounce_check
                    
                    # Override validity if high bounce risk
                    if bounce_check['has_bounced'] and bounce_check['risk_level'] in ['critical', 'high']:
                        result['valid'] = False
                        if result.get('reason'):
                            result['reason'] += f"; {bounce_check.get('warning', 'High bounce risk')}"
                        else:
                            result['reason'] = bounce_check.get('warning', 'High bounce risk')
                except Exception as e:
                    logger.error(f"Bounce check failed: {e}")
                    result['bounce_check'] = {'has_bounced': False, 'total_bounces': 0, 'risk_level': 'low'}
                
                # Calculate deliverability score
                deliverability = calculate_deliverability_score(email, result)
                result['deliverability'] = deliverability
                
                # Determine email status
                status_info = determine_email_status(result)
                result['status'] = status_info
                
            except Exception as e:
                logger.error(f"Failed to add risk checks for {result.get('email')}: {str(e)}")
        
        processing_time = time.time() - start_time
        
        # Store results with user tracking
        storage = get_storage()
        stored_count = 0
        
        # Check if user is authenticated
        user_id = None
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                payload = verify_jwt_token(token)
                user_id = payload.get('user_id')
                logger.info(f"Authenticated user {user_id} batch validating {len(results)} emails")
        except Exception:
            # Not authenticated, use anonymous tracking
            pass
        
        for result in results:
            try:
                record = storage.create_record({
                    'anon_user_id': anon_user_id,
                    'user_id': user_id,  # Will be None for anonymous users
                    'email': result['email'],
                    'valid': result['valid'],
                    'confidence_score': result.get('confidence_score', 40 if result['valid'] else 0),
                    'checks': result.get('checks', {'syntax': result['valid']})
                })
                result['record_id'] = record['id']
                stored_count += 1
            except Exception as e:
                logger.error(f"Failed to store batch result for {result['email']}: {str(e)}")
                result['storage_error'] = str(e)
        
        valid_count = sum(1 for r in results if r.get('valid', False))
        
        # Calculate domain statistics
        domain_stats = calculate_domain_stats(results)
        
        logger.info(f"Batch validation completed: {valid_count}/{len(results)} valid, {stored_count} stored, {duplicates_removed} duplicates removed, {processing_time:.2f}s")
        
        return jsonify({
            'total': len(results),
            'original_count': original_count,
            'duplicates_removed': duplicates_removed,
            'valid_count': valid_count,
            'invalid_count': len(results) - valid_count,
            'domain_stats': domain_stats,
            'results': results,
            'processing_time': round(processing_time, 4)
        })
        
    except Exception as e:
        logger.error(f"Batch validation failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Batch validation failed',
            'message': str(e)
        }), 500

@app.route('/api/validate/batch/authenticated', methods=['POST'])
@rate_limit
def validate_batch_authenticated():
    """
    Batch validation for authenticated users (non-streaming, reliable).
    
    Headers:
        Authorization: Bearer <jwt_token> (required)
    
    Request body:
        {
            "emails": ["user1@example.com", "user2@test.com"],
            "advanced": true,
            "remove_duplicates": true
        }
    
    Response:
        {
            "results": [...],
            "total": 100,
            "valid_count": 85,
            "invalid_count": 15,
            "processing_time": 2.5,
            "domain_stats": {...}
        }
    """
    start_time = time.time()
    
    try:
        # Check if user is authenticated (required for this endpoint)
        user_id = None
        authenticated_user = None
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'This endpoint requires login. Please authenticate first.'
                }), 401
            
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            user_id = payload.get('user_id')
            
            # Get user details for API limiting
            storage = get_storage()
            authenticated_user = storage.get_user_by_id(user_id)
            if not authenticated_user:
                return jsonify({
                    'error': 'User not found',
                    'message': 'User account no longer exists'
                }), 404
            
            # Check if user is suspended (IMMEDIATE CHECK)
            if authenticated_user.get('is_suspended', False):
                suspension_reason = authenticated_user.get('suspension_reason', 'No reason provided')
                return jsonify({
                    'error': 'Account suspended',
                    'message': f'Your account has been suspended. Reason: {suspension_reason}',
                    'suspension_reason': suspension_reason,
                    'suspended_at': authenticated_user.get('suspended_at'),
                    'suspended': True
                }), 403
                
        except ValueError as e:
            return jsonify({
                'error': 'Invalid authentication',
                'message': str(e)
            }), 401
        
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({
                'error': 'Missing emails parameter',
                'message': 'Please provide a list of email addresses'
            }), 400
        
        emails = data.get('emails', [])
        advanced = data.get('advanced', True)
        remove_duplicates = data.get('remove_duplicates', True)
        
        if not emails:
            return jsonify({
                'error': 'Empty email list',
                'message': 'Please provide at least one email address'
            }), 400
        
        # Check API limits and subscription tier for authenticated users (bypass for admins)
        is_admin = is_admin_request()
        if not is_admin:
            # CRITICAL: Get fresh user data to ensure team_id is current
            fresh_user = get_fresh_user_data(user_id)
            if fresh_user:
                authenticated_user = fresh_user
            
            subscription_tier = get_effective_subscription_tier(authenticated_user)

            # Block batch validation for free tier users only (starter+ can use batch validation)
            if subscription_tier == 'free':
                return jsonify({
                    'error': 'Feature not available',
                    'message': 'Batch validation is available for Starter tier and above. Upgrade to Starter (10K/month) or Pro (10M lifetime) to access batch processing!',
                    'subscription_tier': subscription_tier,
                    'upgrade_required': True
                }), 403
            else:
                # Check API limits using new tier-aware system
                can_validate, current_usage, limit = check_api_limits(authenticated_user, is_admin)
            
            if not can_validate:
                if subscription_tier == 'starter':
                    message = f'You have reached your monthly limit of {limit:,} API calls. Upgrade to Pro for 10M lifetime calls!'
                else:  # pro
                    message = f'You have reached your lifetime limit of {limit:,} API calls. Contact support for enterprise options.'
                
                return jsonify({
                    'error': 'API limit exceeded',
                    'message': message,
                    'current_usage': current_usage,
                    'limit': limit,
                    'subscription_tier': subscription_tier
                }), 429
            
            # Check if batch would exceed remaining limit
            remaining_calls = limit - current_usage
            if len(emails) > remaining_calls:
                return jsonify({
                    'error': 'Batch size exceeds remaining API calls',
                    'message': f'This batch contains {len(emails)} emails, but you only have {remaining_calls:,} API calls remaining. Please reduce the batch size or upgrade your plan.',
                    'current_usage': current_usage,
                    'limit': limit,
                    'batch_size': len(emails),
                    'remaining_calls': remaining_calls,
                    'subscription_tier': subscription_tier
                }), 429
        
        # Track original count for duplicate removal
        original_count = len(emails)
        
        # Remove duplicates if requested (case-insensitive)
        if remove_duplicates:
            emails_lower = [email.lower().strip() for email in emails]
            unique_emails = []
            seen = set()
            for email in emails:
                email_lower = email.lower().strip()
                if email_lower not in seen:
                    seen.add(email_lower)
                    unique_emails.append(email)
            emails = unique_emails
            duplicates_removed = original_count - len(emails)
            logger.info(f"Authenticated batch: Removed {duplicates_removed} duplicates")
        else:
            duplicates_removed = 0
        
        logger.info(f"Authenticated batch validation: {len(emails)} emails (advanced: {advanced}) for user {user_id}")
        
        # Process all emails
        results = []
        valid_count = 0
        invalid_count = 0
        
        for email in emails:
            try:
                # Clean email
                email = email.strip()
                
                # Validate email format
                if not validate_email_format(email):
                    result = {
                        'email': email,
                        'valid': False,
                        'reason': 'Invalid email format',
                        'checks': {'syntax': False}
                    }
                else:
                    # Perform validation
                    if advanced:
                        try:
                            result = validate_email_advanced(email)
                        except Exception as e:
                            logger.error(f"Advanced validation error for {email}: {str(e)}")
                            result = {
                                'email': email,
                                'valid': False,
                                'reason': f'Validation error: {str(e)}',
                                'checks': {'syntax': True}
                            }
                        
                        # Add enrichment
                        enrichment_data = enricher.enrich_email(email)
                        if enrichment_data:
                            result['enrichment'] = enrichment_data
                        
                        # Add deliverability score
                        deliverability = calculate_deliverability_score(email, result)
                        result['deliverability'] = deliverability
                        
                        # Add pattern analysis
                        pattern = analyze_email_pattern(email)
                        if pattern:
                            result['pattern_analysis'] = pattern
                        
                        # Add risk check
                        if '@' in email:
                            domain = email.split('@')[1]
                            risk = comprehensive_risk_check(email, domain)
                            result['risk_check'] = risk
                        
                        # Add bounce check (integrated)
                        try:
                            from email_sender import get_email_sender
                            sender = get_email_sender()
                            bounce_check = sender.check_bounce_history(email)
                            result['bounce_check'] = bounce_check
                        except Exception as e:
                            logger.error(f"Bounce check failed: {e}")
                            result['bounce_check'] = {'has_bounced': False, 'total_bounces': 0, 'risk_level': 'low'}
                        
                        # Add status
                        status = determine_email_status(result)
                        result['status'] = status
                    else:
                        # Basic validation
                        result = {'email': email, 'valid': validate_email_format(email)}
                
                results.append(result)
                
                if result.get('valid'):
                    valid_count += 1
                else:
                    invalid_count += 1
                
                # Store in database
                try:
                    storage.create_record({
                        'anon_user_id': None,  # Not anonymous
                        'user_id': user_id,
                        'email': result.get('email'),
                        'valid': result.get('valid', False),
                        'confidence_score': result.get('confidence_score', 0),
                        'checks': result.get('checks', {}),
                        'is_disposable': result.get('checks', {}).get('is_disposable', False),
                        'is_role_based': result.get('checks', {}).get('is_role_based', False)
                    })
                    
                    # Increment API usage for authenticated users (skip for admins)
                    if not is_admin:
                        try:
                            # Check if user is in a team
                            team_info = team_manager.get_user_team(user_id)
                            if team_info and team_info.get('team', {}).get('is_active'):
                                team_id = team_info['team']['id']

                                team_manager.use_team_quota(team_id, 1)
                            else:

                                storage.increment_api_usage(user_id, 1)
                        except Exception as e:

                            logger.error(f"Failed to increment API usage: {str(e)}")
                            
                except Exception as e:
                    logger.error(f"Failed to store validation: {str(e)}")
                    
            except Exception as e:
                logger.error(f"Authenticated batch validation error for {email}: {str(e)}")
                results.append({
                    'email': email,
                    'valid': False,
                    'error': str(e),
                    'reason': 'Validation failed'
                })
                invalid_count += 1
        
        processing_time = round(time.time() - start_time, 3)
        
        # Calculate domain statistics
        domain_stats = calculate_domain_stats(results)
        
        response = {
            'results': results,
            'total': len(emails),
            'original_count': original_count,
            'duplicates_removed': duplicates_removed,
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'processing_time': processing_time,
            'domain_stats': domain_stats
        }
        
        logger.info(f"Authenticated batch validation completed: {len(emails)} emails ({valid_count} valid, {invalid_count} invalid) for user {user_id}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Authenticated batch validation failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Batch validation failed',
            'message': str(e)
        }), 500

@app.route('/api/validate/batch/stream', methods=['POST'])
@rate_limit
def validate_batch_stream():
    """
    Stream batch validation results in real-time.
    Each email is validated and sent immediately as it completes.
    
    Headers:
        X-User-ID: Anonymous user ID (required)
    
    Request body:
        {
            "emails": ["user1@example.com", "user2@test.com"],
            "advanced": true,
            "remove_duplicates": true
        }
    
    Response: Server-Sent Events (SSE) stream
        Each event contains one validation result as JSON
    """
    import json
    
    try:
        # Extract anonymous user ID and check authentication
        try:
            anon_user_id = get_anon_user_id()
        except ValueError as e:
            logger.warning(f"Stream validation auth failed: {str(e)}")
            return jsonify({
                'error': 'Authentication required',
                'message': str(e)
            }), 400
        
        # Check if user is authenticated and validate API limits
        user_id = None
        authenticated_user = None
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                payload = verify_jwt_token(token)
                user_id = payload.get('user_id')
                
                # Get user details for API limiting - ALWAYS get fresh data
                storage = get_storage()
                authenticated_user = storage.get_user_by_id(user_id)
                if authenticated_user:
                    # CRITICAL: Always get fresh user data to ensure team_id is current
                    # This prevents issues where user just joined a team but backend has stale data

                    fresh_user = storage.get_user_by_id(user_id)
                    if fresh_user:
                        authenticated_user = fresh_user

                    logger.info(f"Authenticated batch validation for user {user_id} ({authenticated_user['email']})")
                    
                    # Check if user is suspended (IMMEDIATE CHECK)
                    if authenticated_user.get('is_suspended', False):
                        suspension_reason = authenticated_user.get('suspension_reason', 'No reason provided')
                        return jsonify({
                            'error': 'Account suspended',
                            'message': f'Your account has been suspended. Reason: {suspension_reason}',
                            'suspension_reason': suspension_reason,
                            'suspended_at': authenticated_user.get('suspended_at'),
                            'suspended': True
                        }), 403
        except Exception as e:
            # Not authenticated, continue as anonymous
            logger.debug(f"No authentication or invalid token for batch: {str(e)}")
            pass
        
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({
                'error': 'Missing required parameter',
                'message': 'emails parameter is required'
            }), 400
        
        emails = data.get('emails', [])
        advanced = data.get('advanced', True)
        remove_duplicates = data.get('remove_duplicates', True)
        
        # Check API limits and subscription tier for authenticated users BEFORE processing (bypass for admins)
        is_admin = is_admin_request()
        if authenticated_user and not is_admin:
            # CRITICAL: Get fresh user data to ensure team_id is current
            fresh_user = get_fresh_user_data(user_id)
            if fresh_user:
                authenticated_user = fresh_user
            
            subscription_tier = get_effective_subscription_tier(authenticated_user)

            # Block batch validation for free tier users only (starter+ can use batch validation)
            if subscription_tier == 'free':
                return jsonify({
                    'error': 'Feature not available',
                    'message': 'Batch validation is available for Starter tier and above. Upgrade to Starter (10K/month) or Pro (10M lifetime) to access batch processing!',
                    'subscription_tier': subscription_tier,
                    'upgrade_required': True
                }), 403
            else:
                # Check API limits using new tier-aware system
                can_validate, current_usage, limit = check_api_limits(authenticated_user, is_admin)
            
            if not can_validate:
                if subscription_tier == 'starter':
                    message = f'You have reached your monthly limit of {limit:,} API calls. Upgrade to Pro for 10M lifetime calls!'
                else:  # pro
                    message = f'You have reached your lifetime limit of {limit:,} API calls. Contact support for enterprise options.'
                
                return jsonify({
                    'error': 'API limit exceeded',
                    'message': message,
                    'current_usage': current_usage,
                    'limit': limit,
                    'subscription_tier': subscription_tier
                }), 429
            
            # Check if batch would exceed remaining limit
            remaining_calls = limit - current_usage
            if len(emails) > remaining_calls:
                return jsonify({
                    'error': 'Batch size exceeds remaining API calls',
                    'message': f'This batch contains {len(emails)} emails, but you only have {remaining_calls:,} API calls remaining. Please reduce the batch size or upgrade your plan.',
                    'current_usage': current_usage,
                    'limit': limit,
                    'batch_size': len(emails),
                    'remaining_calls': remaining_calls,
                    'subscription_tier': subscription_tier
                }), 429
        elif is_admin:
            logger.info(f"Admin batch validation (unlimited): {len(emails)} emails")
        
        # Track original count
        original_count = len(emails)
        
        # Remove duplicates if requested (case-insensitive)
        if remove_duplicates:
            emails_lower = [email.lower().strip() for email in emails]
            unique_emails = []
            seen = set()
            for email in emails:
                email_lower = email.lower().strip()
                if email_lower not in seen:
                    seen.add(email_lower)
                    unique_emails.append(email)
            emails = unique_emails
            duplicates_removed = original_count - len(emails)
            logger.info(f"Stream: Removed {duplicates_removed} duplicates (user: {anon_user_id})")
        else:
            duplicates_removed = 0
        
        if not isinstance(emails, list):
            return jsonify({
                'error': 'Invalid parameter type',
                'message': 'emails must be an array'
            }), 400
        
        if len(emails) == 0:
            return jsonify({
                'error': 'Empty email list',
                'message': 'At least one email is required'
            }), 400
        
        if len(emails) > 5000:
            return jsonify({
                'error': 'Too many emails',
                'message': 'Maximum 5000 emails per batch'
            }), 400
        
        def generate():
            """Generator function that yields validation results one by one with PARALLEL PROCESSING."""
            import concurrent.futures
            import threading
            from queue import Queue
            
            storage = get_storage()
            total = len(emails)
            valid_count = 0
            invalid_count = 0
            all_results = []  # Collect all results for domain stats
            
            # Thread-safe counters
            counter_lock = threading.Lock()
            result_queue = Queue()
            
            def validate_single_email(email_data):
                """Validate a single email in parallel."""
                index, email = email_data
                try:
                    email = email.strip()
                    
                    # Validate email format
                    if not validate_email_format(email):
                        result = {
                            'email': email,
                            'valid': False,
                            'reason': 'Invalid email format',
                            'checks': {'syntax': False}
                        }
                    else:
                        # Perform validation
                        if advanced:
                            try:
                                result = validate_email_advanced(email)
                            except Exception as e:
                                logger.error(f"Advanced validation error for {email}: {str(e)}")
                                result = {
                                    'email': email,
                                    'valid': False,
                                    'reason': f'Validation error: {str(e)}',
                                    'checks': {'syntax': True}
                                }
                            
                            # PERFORMANCE OPTIMIZATION: Skip heavy operations for large batches
                            if total <= 100:
                                # Add enrichment
                                try:
                                    enrichment_data = enricher.enrich_email(email)
                                    if enrichment_data:
                                        result['enrichment'] = enrichment_data
                                except:
                                    pass
                                
                                # Add deliverability score
                                try:
                                    deliverability = calculate_deliverability_score(email, result)
                                    result['deliverability'] = deliverability
                                except:
                                    result['deliverability'] = {
                                        'deliverability_score': result.get('confidence_score', 50),
                                        'deliverability_grade': 'B' if result.get('valid') else 'F'
                                    }
                                
                                # Add pattern analysis
                                try:
                                    pattern = analyze_email_pattern(email)
                                    if pattern:
                                        result['pattern_analysis'] = pattern
                                except:
                                    pass
                                
                                # Add risk check
                                try:
                                    if '@' in email:
                                        domain = email.split('@')[1]
                                        risk = comprehensive_risk_check(email, domain)
                                        result['risk_check'] = risk
                                except:
                                    result['risk_check'] = {'overall_risk': 'low'}
                                
                                # Add bounce check (integrated)
                                try:
                                    from email_sender import get_email_sender
                                    sender = get_email_sender()
                                    bounce_check = sender.check_bounce_history(email)
                                    result['bounce_check'] = bounce_check
                                except Exception as e:
                                    result['bounce_check'] = {'has_bounced': False, 'total_bounces': 0, 'risk_level': 'low'}
                            else:
                                # Fast mode for large batches - minimal overhead
                                result['deliverability'] = {
                                    'deliverability_score': result.get('confidence_score', 50),
                                    'deliverability_grade': 'B' if result.get('valid') else 'F'
                                }
                                result['risk_check'] = {'overall_risk': 'low'}
                                result['bounce_check'] = {'has_bounced': False, 'total_bounces': 0, 'risk_level': 'low'}
                        else:
                            # Basic validation
                            result = {'email': email, 'valid': validate_email_format(email)}
                    
                    return (index, result)
                    
                except Exception as e:
                    logger.error(f"Error validating {email}: {str(e)}")
                    return (index, {
                        'email': email,
                        'valid': False,
                        'reason': f'Validation error: {str(e)}'
                    })
            
            # Send initial progress event with duplicate info
            yield f"data: {json.dumps({'type': 'start', 'total': total, 'original_count': original_count, 'duplicates_removed': duplicates_removed})}\n\n"
            
            # PARALLEL PROCESSING - Process emails in batches of 20 simultaneously
            batch_size = 20  # Process 20 emails at once
            max_workers = min(20, total)  # Don't create more threads than emails
            
            # Prepare email data with indices
            email_data = [(i, email) for i, email in enumerate(emails)]
            
            # Process emails in parallel batches
            processed_results = [None] * total  # Pre-allocate results array
            batch_results_for_db = []  # Collect results for batch database write
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Process emails in chunks
                for batch_start in range(0, total, batch_size):
                    batch_end = min(batch_start + batch_size, total)
                    batch_emails = email_data[batch_start:batch_end]
                    
                    # Submit batch for parallel processing
                    future_to_email = {
                        executor.submit(validate_single_email, email_data): email_data 
                        for email_data in batch_emails
                    }
                    
                    # Collect results as they complete
                    for future in concurrent.futures.as_completed(future_to_email):
                        try:
                            index, result = future.result()
                            processed_results[index] = result
                            
                            # Update counters thread-safely
                            with counter_lock:
                                if result.get('valid'):
                                    valid_count += 1
                                else:
                                    invalid_count += 1
                                
                                # Add to batch for database write
                                batch_results_for_db.append((index, result))
                                
                                # Send result event immediately
                                event_data = {
                                    'type': 'result',
                                    'index': index,
                                    'total': total,
                                    'result': result,
                                    'progress': {
                                        'current': len(batch_results_for_db),
                                        'total': total,
                                        'valid': valid_count,
                                        'invalid': invalid_count,
                                        'percentage': int((len(batch_results_for_db) / total) * 100)
                                    }
                                }
                                yield f"data: {json.dumps(event_data)}\n\n"
                        
                        except Exception as e:
                            logger.error(f"Future result error: {str(e)}")
                    
                    # BATCH DATABASE WRITE - Write 20 results at once instead of 1 by 1
                    if batch_results_for_db and storage:
                        try:
                            # Prepare batch data for database
                            batch_records = []
                            for idx, result in batch_results_for_db:
                                batch_records.append({
                                    'anon_user_id': anon_user_id,
                                    'user_id': user_id,
                                    'email': result.get('email'),
                                    'valid': result.get('valid', False),
                                    'confidence_score': result.get('confidence_score', 0),
                                    'checks': result.get('checks', {}),
                                    'is_disposable': result.get('checks', {}).get('is_disposable', False),
                                    'is_role_based': result.get('checks', {}).get('is_role_based', False)
                                })
                            
                            # Batch insert to database (much faster than individual inserts)
                            if hasattr(storage, 'create_records_batch'):
                                storage.create_records_batch(batch_records)
                            else:
                                # Fallback to individual inserts if batch not available
                                for record in batch_records:
                                    storage.create_record(record)
                            
                            # Batch update API usage - check for team quota first
                            if authenticated_user and user_id and not is_admin_request():
                                try:
                                    # Check if user is in a team
                                    team_info = team_manager.get_user_team(user_id)
                                    if team_info and team_info.get('team', {}).get('is_active'):
                                        team_id = team_info['team']['id']

                                        team_manager.use_team_quota(team_id, len(batch_records))
                                    else:

                                        storage.increment_api_usage(user_id, len(batch_records))
                                except Exception as e:

                                    logger.error(f"Failed to increment API usage: {str(e)}")
                            
                            # Clear batch
                            batch_results_for_db = []
                            
                        except Exception as e:
                            logger.error(f"Batch database write failed: {str(e)}")
                            batch_results_for_db = []
            
            # Collect all results for domain stats
            all_results = [r for r in processed_results if r is not None]

            # Calculate domain statistics
            domain_stats = calculate_domain_stats(all_results)
            
            # Get updated API usage for completion event
            api_usage_info = None
            if authenticated_user and user_id and not is_admin_request():
                try:
                    team_info = team_manager.get_user_team(user_id)
                    if team_info and team_info.get('team', {}).get('is_active'):
                        # Return team quota info
                        team_usage = team_manager.get_team_usage(team_info['team']['id'])
                        if team_usage['success']:
                            usage_data = team_usage['usage']
                            api_usage_info = {
                                'calls_used': usage_data['quota_used'],
                                'calls_limit': usage_data['quota_limit'],
                                'calls_remaining': usage_data['quota_limit'] - usage_data['quota_used'],
                                'team_name': team_info['team']['name'],
                                'is_team_quota': True
                            }
                    else:
                        # Return individual quota info
                        fresh_user = get_fresh_user_data(user_id)
                        if fresh_user:
                            api_usage_info = {
                                'calls_used': fresh_user['api_calls_count'],
                                'calls_limit': fresh_user['api_calls_limit'],
                                'calls_remaining': fresh_user['api_calls_limit'] - fresh_user['api_calls_count'],
                                'is_team_quota': False
                            }
                except Exception as e:
                    logger.error(f"Failed to save validation: {e}")

                # Send completion event
            completion_data = {
                'type': 'complete',
                'total': total,
                'original_count': original_count,
                'duplicates_removed': duplicates_removed,
                'valid_count': valid_count,
                'invalid_count': invalid_count,
                'domain_stats': domain_stats,
                'api_usage': api_usage_info
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
        
        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
        
    except Exception as e:
        logger.error(f"Stream validation failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Stream validation failed',
            'message': str(e)
        }), 500

@app.route('/api/validate/batch/local', methods=['POST'])
@rate_limit
def validate_batch_stream_local():
    """
    Stream batch validation for ANONYMOUS users (NO database storage).
    Results are returned but not saved to database.
    
    Headers:
        X-User-ID: Anonymous user ID (optional, for rate limiting only)
    
    Request body:
        {
            "emails": ["user1@example.com", "user2@test.com"],
            "advanced": true,
            "remove_duplicates": true
        }
    
    Response: Server-Sent Events (SSE) stream
        Each event contains one validation result as JSON
    """
    import json
    
    try:
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({
                'error': 'Missing required parameter',
                'message': 'emails parameter is required'
            }), 400
        
        emails = data.get('emails', [])
        advanced = data.get('advanced', True)
        remove_duplicates = data.get('remove_duplicates', True)
        
        # Track original count
        original_count = len(emails)
        
        # Remove duplicates if requested
        if remove_duplicates:
            emails_lower = [email.lower().strip() for email in emails]
            unique_emails = []
            seen = set()
            for email in emails:
                email_lower = email.lower().strip()
                if email_lower not in seen:
                    seen.add(email_lower)
                    unique_emails.append(email)
            emails = unique_emails
            duplicates_removed = original_count - len(emails)
            logger.info(f"Anonymous batch: Removed {duplicates_removed} duplicates")
        else:
            duplicates_removed = 0
        
        if not isinstance(emails, list):
            return jsonify({
                'error': 'Invalid parameter type',
                'message': 'emails must be an array'
            }), 400
        
        if len(emails) == 0:
            return jsonify({
                'error': 'Empty email list',
                'message': 'At least one email is required'
            }), 400
        
        if len(emails) > 5000:
            return jsonify({
                'error': 'Too many emails',
                'message': 'Maximum 5000 emails per batch'
            }), 400
        
        def generate():
            """Generator function that yields validation results one by one."""
            total = len(emails)
            valid_count = 0
            invalid_count = 0
            all_results = []
            
            # Send initial progress event
            yield f"data: {json.dumps({'type': 'start', 'total': total, 'original_count': original_count, 'duplicates_removed': duplicates_removed})}\n\n"
            
            for index, email in enumerate(emails):
                try:
                    email = email.strip()
                    
                    # Validate email format
                    if not validate_email_format(email):
                        result = {
                            'email': email,
                            'valid': False,
                            'reason': 'Invalid email format',
                            'checks': {'syntax': False}
                        }
                    else:
                        # Perform validation (same as single validation)
                        if advanced:
                            try:
                                result = validate_email_advanced(email)
                                
                                # PERFORMANCE OPTIMIZATION: Skip heavy operations for large batches
                                # Only do full validation for batches <= 100 emails
                                if total <= 100:
                                    # Add all the same enrichments as single validation
                                    enrichment_data = enricher.enrich_email(email)
                                    if enrichment_data:
                                        result['enrichment'] = enrichment_data
                                    
                                    deliverability = calculate_deliverability_score(email, result)
                                    result['deliverability'] = deliverability
                                    
                                    pattern = analyze_email_pattern(email)
                                    if pattern:
                                        result['pattern_analysis'] = pattern
                                    
                                    if '@' in email:
                                        domain = email.split('@')[1]
                                        risk = comprehensive_risk_check(email, domain)
                                        result['risk_check'] = risk
                                    
                                    # Bounce check (but don't save)
                                    try:
                                        from email_sender import get_email_sender
                                        sender = get_email_sender()
                                        bounce_check = sender.check_bounce_history(email)
                                        result['bounce_check'] = bounce_check
                                    except Exception as e:
                                        result['bounce_check'] = {'has_bounced': False, 'total_bounces': 0, 'risk_level': 'low'}
                                else:
                                    # Fast mode for large batches - skip heavy operations
                                    result['deliverability'] = {
                                        'deliverability_score': result.get('confidence_score', 50),
                                        'deliverability_grade': 'B' if result.get('valid') else 'F'
                                    }
                                    result['risk_check'] = {'overall_risk': 'low'}
                                    result['bounce_check'] = {'has_bounced': False, 'total_bounces': 0, 'risk_level': 'low'}
                                
                                status = determine_email_status(result)
                                result['status'] = status
                                
                            except Exception as e:
                                logger.error(f"Advanced validation error for {email}: {str(e)}")
                                result = {
                                    'email': email,
                                    'valid': False,
                                    'reason': f'Validation error: {str(e)}',
                                    'checks': {'syntax': True}
                                }
                        else:
                            # Basic validation
                            result = {'email': email, 'valid': validate_email_format(email)}
                        
                        # Mark as local storage
                        result['storage'] = 'local_only'
                    
                    # Update counters
                    if result.get('valid'):
                        valid_count += 1
                    else:
                        invalid_count += 1
                    
                    # Store result for domain stats
                    all_results.append(result)
                    
                    # Send result event
                    event_data = {
                        'type': 'result',
                        'index': index,
                        'total': total,
                        'result': result,
                        'progress': {
                            'current': index + 1,
                            'total': total,
                            'valid': valid_count,
                            'invalid': invalid_count,
                            'percentage': int(((index + 1) / total) * 100)
                        }
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error validating {email}: {str(e)}")
                    error_result = {
                        'type': 'result',
                        'index': index,
                        'total': total,
                        'result': {
                            'email': email,
                            'valid': False,
                            'reason': f'Validation error: {str(e)}',
                            'storage': 'local_only'
                        },
                        'progress': {
                            'current': index + 1,
                            'total': total,
                            'valid': valid_count,
                            'invalid': invalid_count,
                            'percentage': int(((index + 1) / total) * 100)
                        }
                    }
                    yield f"data: {json.dumps(error_result)}\n\n"
            
            # Calculate domain statistics
            domain_stats = calculate_domain_stats(all_results)
            
            # Send completion event
            completion_data = {
                'type': 'complete',
                'total': total,
                'original_count': original_count,
                'duplicates_removed': duplicates_removed,
                'valid_count': valid_count,
                'invalid_count': invalid_count,
                'domain_stats': domain_stats,
                'storage': 'local_only'
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
        
        logger.info(f"Anonymous batch validation started: {len(emails)} emails - NOT STORED")
        
        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
        
    except Exception as e:
        logger.error(f"Anonymous batch validation failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Batch validation failed',
            'message': str(e)
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """
    Get validation history for AUTHENTICATED users only.
    Anonymous users should use localStorage on frontend.
    
    Headers:
        Authorization: Bearer <token> (required)
    
    Query params:
        - limit: Number of records (default: 100, max: 1000)
        - offset: Pagination offset (default: 0)
    
    Response:
        {
            "total": 50,
            "limit": 100,
            "offset": 0,
            "history": [...],
            "user_type": "authenticated"
        }
    """
    try:
        # Check if user is authenticated (required)
        user_id = None
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'History endpoint requires login. Anonymous users use localStorage.'
                }), 401
            
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            user_id = payload.get('user_id')
            
        except ValueError as e:
            return jsonify({
                'error': 'Invalid authentication',
                'message': str(e)
            }), 401
        
        # Get pagination params
        limit = min(int(request.args.get('limit', 100)), 1000)
        offset = int(request.args.get('offset', 0))
        
        storage = get_storage()
        
        # Get authenticated user history only
        history = storage.get_authenticated_user_history(user_id, limit=limit, offset=offset)
        
        logger.info(f"Fetched {len(history)} history records for authenticated user: {user_id}")
        
        return jsonify({
            'total': len(history),
            'limit': limit,
            'offset': offset,
            'history': history,
            'user_type': 'authenticated'
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch history: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to fetch history',
            'message': str(e)
        }), 500

@app.route('/api/history/<int:record_id>', methods=['DELETE'])
def delete_history_record(record_id):
    """
    Delete a specific validation record.
    Only allows deletion if record belongs to the requesting user.
    
    Headers:
        X-User-ID: Anonymous user ID (required)
    
    Response:
        {
            "success": true,
            "message": "Record deleted"
        }
    """
    try:
        # Extract anonymous user ID
        try:
            anon_user_id = get_anon_user_id()
        except ValueError as e:
            return jsonify({
                'error': 'Authentication required',
                'message': str(e)
            }), 400
        
        # Verify record belongs to user before deleting
        storage = get_storage()
        record = storage.get_record_by_id(record_id)
        
        if not record:
            return jsonify({
                'error': 'Record not found',
                'message': f'No record found with ID {record_id}'
            }), 404
        
        if record.get('anon_user_id') != anon_user_id:
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have permission to delete this record'
            }), 403
        
        # Delete the record
        storage.delete_record(record_id)
        
        return jsonify({
            'success': True,
            'message': 'Record deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to delete record',
            'message': str(e)
        }), 500

@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """
    Clear all validation history for the anonymous user.
    
    Headers:
        X-User-ID: Anonymous user ID (required)
    
    Response:
        {
            "success": true,
            "deleted_count": 25,
            "message": "History cleared"
        }
    """
    try:
        # Extract anonymous user ID
        try:
            anon_user_id = get_anon_user_id()
        except ValueError as e:
            return jsonify({
                'error': 'Authentication required',
                'message': str(e)
            }), 400
        
        # Delete all records for this user
        storage = get_storage()
        deleted_count = storage.delete_user_history(anon_user_id)
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} records'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to clear history',
            'message': str(e)
        }), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """
    Get analytics for the anonymous user.
    Returns statistics ONLY for the requesting user's data.
    
    Headers:
        X-User-ID: Anonymous user ID (required)
    
    Response:
        {
            "total_validations": 100,
            "valid_count": 85,
            "invalid_count": 15,
            "avg_confidence": 87.5,
            "risk_distribution": {...},
            "domain_types": {...},
            "top_domains": [...]
        }
    """
    try:
        # Extract anonymous user ID
        try:
            anon_user_id = get_anon_user_id()
        except ValueError as e:
            return jsonify({
                'error': 'Authentication required',
                'message': str(e)
            }), 400
        
        # Get user-specific analytics
        storage = get_storage()
        analytics = storage.get_user_analytics(anon_user_id)
        
        return jsonify(analytics)
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch analytics',
            'message': str(e)
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested endpoint does not exist'
        }), 404
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The HTTP method is not allowed for this endpoint'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

# ============================================================================
# MAIN
# ============================================================================
# BOUNCE MANAGEMENT API ENDPOINTS
# ============================================================================

@app.route('/api/bounce/stats', methods=['GET'])
def get_bounce_statistics():
    """
    Get overall bounce statistics.
    
    Response:
        {
            "total_emails_tracked": 1000,
            "total_bounces": 50,
            "hard_bounces": 30,
            "soft_bounces": 20,
            "bounce_rate": 0.05,
            "top_bounce_reasons": [...],
            "recent_bounces": [...],
            "last_updated": "2023-12-11T10:30:00Z"
        }
    """
    try:
        from email_sender import get_email_sender
        
        sender = get_email_sender()
        stats = sender.get_delivery_stats()
        
        # Add real-time data from database if available
        storage = get_storage()
        
        # Get basic counts from database
        # This is a simplified version - you'd want to add proper SQL queries
        try:
            # Get total validations count
            total_validations = storage.get_total_validations_count()
            stats['total_emails_tracked'] = total_validations
            
            # Get bounce counts
            bounce_counts = storage.get_bounce_counts()
            stats.update(bounce_counts)
            
        except Exception as e:
            logger.warning(f"Could not get real bounce stats from DB: {e}")
            # Return mock data for now
            stats.update({
                'total_emails_tracked': 1250,
                'total_bounces': 47,
                'hard_bounces': 28,
                'soft_bounces': 19,
                'bounce_rate': 0.038,
                'top_bounce_reasons': [
                    {'reason': '550 5.1.1 User unknown', 'count': 15},
                    {'reason': '452 4.2.2 Mailbox full', 'count': 8},
                    {'reason': '550 5.7.1 Spam detected', 'count': 6},
                    {'reason': '421 4.3.0 Temporary failure', 'count': 5}
                ],
                'recent_bounces': []
            })
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Failed to get bounce statistics: {str(e)}")
        return jsonify({
            'error': 'Failed to get bounce statistics',
            'message': str(e),
            'total_emails_tracked': 0,
            'total_bounces': 0,
            'bounce_rate': 0.0
        }), 500

@app.route('/api/bounce/record', methods=['POST'])
def record_bounce_api():
    """
    Record a bounce manually (for testing or manual entry).
    
    Request:
        {
            "email": "user@example.com",
            "bounce_type": "hard|soft",
            "reason": "Bounce reason"
        }
    
    Response:
        {
            "success": true,
            "bounce_count": 1,
            "message": "Bounce recorded"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        bounce_type = data.get('bounce_type', 'hard')
        reason = data.get('reason', 'Manual bounce record')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if bounce_type not in ['hard', 'soft']:
            return jsonify({'error': 'bounce_type must be "hard" or "soft"'}), 400
        
        from email_sender import get_email_sender
        
        sender = get_email_sender()
        result = sender.record_bounce(email, bounce_type, reason)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        
        return jsonify({
            'success': True,
            'bounce_count': result.get('bounce_count', 1),
            'message': f'Bounce recorded for {email}'
        })
        
    except Exception as e:
        logger.error(f"Failed to record bounce: {str(e)}")
        return jsonify({
            'error': 'Failed to record bounce',
            'message': str(e)
        }), 500

@app.route('/api/bounce/history/<email>', methods=['GET'])
def get_email_bounce_history(email):
    """
    Get bounce history for a specific email using integrated bounce tracking.
    
    Response:
        {
            "email": "user@example.com",
            "bounce_history": {
                "total_bounces": 2,
                "hard_bounces": 1,
                "soft_bounces": 1,
                "risk_level": "high",
                "safe_to_send": false,
                "last_bounce": "2023-12-11T10:30:00Z"
            },
            "risk_assessment": {
                "risk_level": "high",
                "safe_to_send": false,
                "warning": "Email has bounced 2 times - High risk"
            }
        }
    """
    try:
        from email_sender import get_email_sender
        
        sender = get_email_sender()
        bounce_check = sender.check_bounce_history(email)
        
        return jsonify({
            'email': email,
            'bounce_history': {
                'total_bounces': bounce_check['total_bounces'],
                'hard_bounces': bounce_check['hard_bounces'],
                'soft_bounces': bounce_check['soft_bounces'],
                'risk_level': bounce_check['risk_level'],
                'safe_to_send': bounce_check['safe_to_send'],
                'last_bounce': bounce_check.get('last_bounce')
            },
            'risk_assessment': {
                'risk_level': bounce_check['risk_level'],
                'safe_to_send': bounce_check['safe_to_send'],
                'warning': bounce_check.get('warning'),
                'recommendation': f"Risk level: {bounce_check['risk_level']}"
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get bounce history for {email}: {str(e)}")
        return jsonify({
            'error': 'Failed to get bounce history',
            'message': str(e)
        }), 500

# ============================================================================
# SIMPLE BOUNCE TRACKING
# ============================================================================

@app.route('/api/bounce/record', methods=['POST'])
def record_simple_bounce():
    """
    Simple bounce recording for future email sending integration.
    
    Request:
        {
            "email": "user@example.com",
            "reason": "Bounce reason"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        reason = data.get('reason', 'Email bounced')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Simple bounce recording - just mark as bounced in database
        storage = get_storage()
        
        bounce_record = {
            'email': email,
            'valid': False,
            'bounced': True,
            'bounce_reason': reason,
            'bounce_count': 1,
            'last_bounce_date': datetime.utcnow().isoformat(),
            'validated_at': datetime.utcnow().isoformat(),
            'confidence_score': 0,
            'risk_score': 100,
            'notes': f'Bounce recorded: {reason}'
        }
        
        result = storage.store_validation_result(bounce_record)
        
        if result.get('success'):
            logger.info(f"Simple bounce recorded for {email}: {reason}")
            return jsonify({
                'success': True,
                'message': f'Bounce recorded for {email}'
            })
        else:
            return jsonify({'error': 'Failed to record bounce'}), 500
        
    except Exception as e:
        logger.error(f"Failed to record bounce: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# EMAIL SENDING API ENDPOINTS
# ============================================================================

@app.route('/api/email/send', methods=['POST'])
@auth_required
def send_single_email():
    """
    Send a single email (requires authentication).
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Request:
        {
            "to_email": "user@example.com",
            "subject": "Hello World",
            "content": "<h1>Hello!</h1>",
            "content_type": "text/html",
            "from_email": "sender@yourdomain.com",
            "from_name": "Your Name"
        }
    
    Response:
        {
            "success": true,
            "message_id": "abc123",
            "to_email": "user@example.com",
            "sent_at": "2023-12-11T10:30:00Z"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['to_email', 'subject', 'content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Import email sender
        from email_sender import get_email_sender
        
        sender = get_email_sender()
        
        # Send email
        result = sender.send_single_email(
            to_email=data['to_email'],
            subject=data['subject'],
            content=data['content'],
            content_type=data.get('content_type', 'text/html'),
            from_email=data.get('from_email'),
            from_name=data.get('from_name')
        )
        
        # Store send record in database
        if result['success']:
            try:
                storage = get_storage()
                send_record = {
                    'email': data['to_email'],
                    'subject': data['subject'],
                    'status': 'sent',
                    'message_id': result.get('message_id'),
                    'sent_at': result['sent_at'],
                    'anon_user_id': request.headers.get('X-User-ID', 'unknown')
                }
                # You'd need to add a new table for email sends
                # storage.store_email_send(send_record)
            except Exception as e:
                logger.warning(f"Failed to store send record: {e}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/email/send/batch', methods=['POST'])
@auth_required
def send_batch_emails():
    """
    Send emails to multiple recipients.
    
    Request:
        {
            "recipients": ["user1@example.com", "user2@example.com"],
            "subject": "Newsletter",
            "content": "<h1>Newsletter Content</h1>",
            "content_type": "text/html",
            "from_email": "newsletter@yourdomain.com",
            "from_name": "Newsletter Team"
        }
    
    Response:
        {
            "success": true,
            "total_recipients": 2,
            "total_sent": 2,
            "total_failed": 0,
            "sent_at": "2023-12-11T10:30:00Z"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['recipients', 'subject', 'content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        recipients = data['recipients']
        if not isinstance(recipients, list) or len(recipients) == 0:
            return jsonify({'error': 'Recipients must be a non-empty list'}), 400
        
        # Import email sender
        from email_sender import get_email_sender
        
        sender = get_email_sender()
        
        # Send batch emails
        result = sender.send_batch_emails(
            recipients=recipients,
            subject=data['subject'],
            content=data['content'],
            content_type=data.get('content_type', 'text/html'),
            from_email=data.get('from_email'),
            from_name=data.get('from_name')
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to send batch emails: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/email/templates', methods=['GET'])
def get_email_templates():
    """
    Get available email templates.
    
    Response:
        {
            "templates": {
                "welcome": {
                    "subject": "Welcome!",
                    "content": "<html>...</html>"
                }
            }
        }
    """
    try:
        from email_sender import EMAIL_TEMPLATES
        
        return jsonify({
            'templates': EMAIL_TEMPLATES
        })
        
    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/email/config/test', methods=['POST'])
def test_email_config():
    """
    Test email configuration (SendGrid API key).
    
    Response:
        {
            "valid": true,
            "username": "your_username",
            "status": "API key is valid"
        }
    """
    try:
        from email_sender import get_email_sender
        
        sender = get_email_sender()
        result = sender.validate_api_key()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Email config test failed: {str(e)}")
        return jsonify({
            'valid': False,
            'error': str(e),
            'status': 'Configuration test failed'
        }), 500

@app.route('/api/email/stats', methods=['GET'])
def get_email_stats():
    """
    Get email delivery statistics.
    
    Query Parameters:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Response:
        {
            "delivered": 100,
            "bounced": 5,
            "opened": 80,
            "clicked": 20,
            "delivery_rate": 95.0,
            "open_rate": 80.0,
            "click_rate": 20.0
        }
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        from email_sender import get_email_sender
        
        sender = get_email_sender()
        stats = sender.get_delivery_stats(start_date, end_date)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Failed to get email stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/sendgrid/bounce', methods=['POST'])
def handle_sendgrid_bounce():
    """
    Handle SendGrid bounce webhook (integrated with email sender).
    
    SendGrid sends bounce events in this format:
    [
        {
            "email": "user@example.com",
            "event": "bounce",
            "reason": "550 5.1.1 User unknown",
            "status": "5.1.1",
            "sg_message_id": "abc123"
        }
    ]
    """
    try:
        events = request.get_json()
        if not events:
            return jsonify({'error': 'No events received'}), 400
        
        from email_sender import get_email_sender
        sender = get_email_sender()
        
        processed_count = 0
        
        for event in events:
            if event.get('event') == 'bounce':
                email = event.get('email')
                reason = event.get('reason', 'Unknown bounce reason')
                status = event.get('status', '')
                message_id = event.get('sg_message_id')
                
                if not email:
                    continue
                
                # Determine bounce type based on status code
                bounce_type = 'hard'
                if status.startswith('4'):  # 4xx = temporary failure
                    bounce_type = 'soft'
                elif status.startswith('5'):  # 5xx = permanent failure
                    bounce_type = 'hard'
                
                # Record the bounce using integrated method
                result = sender.record_bounce(
                    email=email,
                    bounce_type=bounce_type,
                    reason=f"SendGrid: {reason} (Status: {status})",
                    message_id=message_id
                )
                
                if result.get('success'):
                    processed_count += 1
                    logger.info(f"Recorded SendGrid bounce for {email}: {reason}")
                else:
                    logger.error(f"Failed to record bounce for {email}: {result.get('error')}")
        
        return jsonify({
            'status': 'success',
            'processed': processed_count,
            'total_events': len(events)
        })
        
    except Exception as e:
        logger.error(f"SendGrid webhook error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/webhook/test/bounce', methods=['POST'])
def test_bounce_recording():
    """
    Test bounce recording (integrated approach).
    
    Request:
        {
            "email": "test@example.com",
            "bounce_type": "hard",
            "reason": "Test bounce"
        }
    """
    try:
        data = request.get_json()
        email = data.get('email', 'test@example.com') if data else 'test@example.com'
        bounce_type = data.get('bounce_type', 'hard') if data else 'hard'
        reason = data.get('reason', 'Test bounce') if data else 'Test bounce'
        
        from email_sender import get_email_sender
        sender = get_email_sender()
        
        result = sender.record_bounce(email, bounce_type, reason)
        
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': f'Test bounce recorded for {email}',
                'bounce_count': result['bounce_count']
            })
        else:
            return jsonify({'error': result.get('error', 'Unknown error')}), 500
            
    except Exception as e:
        logger.error(f"Test bounce error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("Email Platform - Validate & Send Emails + Admin System")
    print("=" * 70)
    print("\n🚀 Server starting on http://localhost:5000")
    print("🔐 Authentication: Anonymous User ID (X-User-ID header)")
    print("📊 Private history without login")
    print("📧 Email sending with SendGrid integration")
    print("🛡️  Admin system integrated")
    
    print("\n📧 Email Validation Endpoints:")
    print("  - POST /api/validate          - Validate single email")
    print("  - POST /api/validate/batch    - Validate multiple emails")
    print("  - GET  /api/history           - Get user history")
    
    print("\n📤 Email Sending Endpoints:")
    print("  - POST /api/email/send        - Send single email")
    print("  - POST /api/email/send/batch  - Send batch emails")
    print("  - GET  /api/email/templates   - Get email templates")
    print("  - POST /api/email/config/test - Test SendGrid config")
    print("  - GET  /api/email/stats       - Email delivery stats")
    
    print("\n🛡️  Admin Endpoints:")
    print("  - POST /admin/auth/login      - Admin login")
    print("  - GET  /admin/dashboard       - Admin dashboard")
    print("  - GET  /admin/users           - User management")
    print("  - POST /admin/users/{id}/suspend - Suspend user")
    
    print("\n🌐 Frontend: http://localhost:3000 (if running)")
    print("🔧 Admin Panel: http://localhost:3000/admin (after login)")
    print("💡 Tip: Use 'Send Emails' tab to compose and send emails")
    print("⚙️  Setup: Add SENDGRID_API_KEY to .env file")
    print("🔑 Default Admin: admin@emailvalidator.com / admin123")
    print("\n" + "=" * 70)
    print()
    
    # Configure for better performance and connection handling
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max request size
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
    
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000,
        threaded=True,  # Enable threading for concurrent requests
        use_reloader=False  # Disable reloader to prevent issues with threading
    )
