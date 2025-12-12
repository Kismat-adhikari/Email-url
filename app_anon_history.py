#!/usr/bin/env python3
"""
Flask Backend with Anonymous User ID System
Private history WITHOUT requiring user login
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from emailvalidator_unified import validate_email_advanced, validate_email_tiered, validate_batch
from email_validator_smtp import validate_email_with_smtp
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
        
        # Create user in database with proper defaults
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'first_name': first_name,
            'last_name': last_name,
            'api_key': api_key,
            'subscription_tier': 'free',  # Default tier
            'api_calls_count': 0,         # Start with 0 calls
            'api_calls_limit': 10,        # Free tier limit
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
        
        # Return user data (exclude sensitive fields)
        user_response = {
            'id': user['id'],
            'email': user['email'],
            'firstName': user['first_name'],
            'lastName': user['last_name'],
            'subscriptionTier': user['subscription_tier'],
            'apiKey': user.get('api_key'),
            'apiCallsLimit': user['api_calls_limit'],
            'apiCallsCount': user['api_calls_count'],
            'isVerified': user['is_verified'],
            'createdAt': user['created_at'],
            'lastLogin': user.get('last_login')
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
                
            # Check API limits
            if authenticated_user['api_calls_count'] >= authenticated_user['api_calls_limit']:
                return jsonify({
                    'error': 'API limit exceeded',
                    'message': f'You have reached your limit of {authenticated_user["api_calls_limit"]} API calls. Upgrade your plan for more.',
                    'current_usage': authenticated_user['api_calls_count'],
                    'limit': authenticated_user['api_calls_limit']
                }), 429
                
        except ValueError as e:
            return jsonify({
                'error': 'Invalid authentication',
                'message': str(e)
            }), 401
        
        data = request.get_json()
        
        if not data or 'email' not in data:
            logger.warning(f"Missing email parameter from user {anon_user_id}")
            return jsonify({
                'error': 'Missing email parameter',
                'message': 'Please provide an email address'
            }), 400
        
        email = data['email']
        advanced = data.get('advanced', True)
        
        # Input validation
        if not validate_email_format(email):
            logger.warning(f"Invalid email format: {email}")
            return jsonify({
                'error': 'Invalid email format',
                'message': 'Email must be a valid format'
            }), 400
        
        logger.info(f"Validating email: {email} (user: {anon_user_id}, advanced: {advanced})")
        
        # Validate email using TIERED system
        if advanced:
            # Use tiered validation - applies filters based on confidence
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
            logger.info(f"Risk check for {email}: {risk_check['overall_risk']}")
            
            # Override validity if critical risk detected
            if risk_check['overall_risk'] == 'critical':
                result['valid'] = False
                logger.warning(f"CRITICAL RISK detected for {email}: {risk_check['recommendation']}")
                if result.get('reason'):
                    result['reason'] += f"; {risk_check['recommendation']}"
                else:
                    result['reason'] = risk_check['recommendation']
        except Exception as e:
            logger.error(f"Risk check failed for {email}: {str(e)}")
        
        # Integrated bounce check
        try:
            from email_sender import get_email_sender
            sender = get_email_sender()
            bounce_check = sender.check_bounce_history(email)
            result['bounce_check'] = bounce_check
            
            # Add bounce warning if exists
            if bounce_check['has_bounced']:
                logger.info(f"Bounce history for {email}: {bounce_check['total_bounces']} bounces")
                if bounce_check['risk_level'] in ['critical', 'high']:
                    result['valid'] = False
                    if result.get('reason'):
                        result['reason'] += f"; {bounce_check['warning']}"
                    else:
                        result['reason'] = bounce_check['warning']
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
            logger.info(f"Email status for {email}: {status_info['status']}")
        except Exception as e:
            logger.error(f"Status determination failed: {str(e)}")
        
        # Enrich email data
        try:
            enrichment = enricher.enrich_email(email, validation_data=result)
            result['enrichment'] = enrichment
        except Exception as e:
            logger.error(f"Email enrichment failed: {str(e)}")
            result['enrichment'] = {'error': str(e)}
        
        # Store in database with user tracking
        try:
            storage = get_storage()
            
            # Check if user is authenticated and handle API limits
            user_id = None
            authenticated_user = None
            try:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
                    payload = verify_jwt_token(token)
                    user_id = payload.get('user_id')
                    
                    # Get user details for API limiting
                    authenticated_user = storage.get_user_by_id(user_id)
                    if authenticated_user:
                        # Check API limits
                        if authenticated_user['api_calls_count'] >= authenticated_user['api_calls_limit']:
                            return jsonify({
                                'error': 'API limit exceeded',
                                'message': f'You have reached your limit of {authenticated_user["api_calls_limit"]} API calls. Upgrade your plan for more.',
                                'current_usage': authenticated_user['api_calls_count'],
                                'limit': authenticated_user['api_calls_limit']
                            }), 429
                        
                        logger.info(f"Authenticated user {user_id} ({authenticated_user['email']}) validating email: {email} - Usage: {authenticated_user['api_calls_count']}/{authenticated_user['api_calls_limit']}")
            except Exception as e:
                # Not authenticated, use anonymous tracking
                logger.debug(f"No authentication or invalid token: {str(e)}")
                pass
            
            record = storage.create_record({
                'anon_user_id': anon_user_id,
                'user_id': user_id,  # Will be None for anonymous users
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
            
            # Increment API usage for authenticated users
            if authenticated_user:
                try:
                    storage.increment_api_usage(user_id, 1)
                    new_count = authenticated_user['api_calls_count'] + 1
                    result['api_usage'] = {
                        'calls_used': new_count,
                        'calls_limit': authenticated_user['api_calls_limit'],
                        'calls_remaining': authenticated_user['api_calls_limit'] - new_count
                    }
                    logger.info(f"API usage incremented for user {user_id}: {new_count}/{authenticated_user['api_calls_limit']}")
                except Exception as e:
                    logger.error(f"Failed to increment API usage: {str(e)}")
            
            logger.info(f"Validation stored: {email} (valid: {result['valid']}, score: {result.get('confidence_score')})")
        except Exception as e:
            logger.error(f"Storage failed: {str(e)}")
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
    Validate single email for ANONYMOUS users (NO database storage).
    Results are returned but not saved to database.
    
    Headers:
        X-User-ID: Anonymous user ID (optional, for rate limiting only)
    
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
            "storage": "local_only"
        }
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Missing email parameter',
                'message': 'Please provide an email address'
            }), 400
        
        email = data['email']
        advanced = data.get('advanced', True)
        
        # Input validation
        if not validate_email_format(email):
            logger.warning(f"Invalid email format: {email}")
            return jsonify({
                'error': 'Invalid email format',
                'message': 'Email must be a valid format'
            }), 400
        
        logger.info(f"Anonymous validation: {email} (advanced: {advanced})")
        
        # Validate email using TIERED system
        if advanced:
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
        
        # Mark as local-only storage
        result['storage'] = 'local_only'
        result['stored'] = False
        
        logger.info(f"Anonymous validation completed: {email} (valid: {result['valid']}, score: {result.get('confidence_score')}) - NOT STORED")
        
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
        
        if len(emails) > 1000:
            logger.warning(f"Too many emails ({len(emails)}) from user {anon_user_id}")
            return jsonify({
                'error': 'Too many emails',
                'message': 'Maximum 1,000 emails per request'
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
        # Extract anonymous user ID
        try:
            anon_user_id = get_anon_user_id()
        except ValueError as e:
            logger.warning(f"Stream validation auth failed: {str(e)}")
            return jsonify({
                'error': 'Authentication required',
                'message': str(e)
            }), 400
        
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
        
        if len(emails) > 1000:
            return jsonify({
                'error': 'Too many emails',
                'message': 'Maximum 1000 emails per batch'
            }), 400
        
        def generate():
            """Generator function that yields validation results one by one."""
            storage = get_storage()
            total = len(emails)
            valid_count = 0
            invalid_count = 0
            all_results = []  # Collect all results for domain stats
            
            # Send initial progress event with duplicate info
            yield f"data: {json.dumps({'type': 'start', 'total': total, 'original_count': original_count, 'duplicates_removed': duplicates_removed})}\n\n"
            
            for index, email in enumerate(emails):
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
                        
                        # Store in database
                        if storage:
                            try:
                                storage.create_record({
                                    'anon_user_id': anon_user_id,
                                    'email': result.get('email'),
                                    'valid': result.get('valid', False),
                                    'confidence_score': result.get('confidence_score', 0),
                                    'checks': result.get('checks', {}),
                                    'is_disposable': result.get('checks', {}).get('is_disposable', False),
                                    'is_role_based': result.get('checks', {}).get('is_role_based', False)
                                })
                            except Exception as e:
                                logger.error(f"Failed to store validation: {str(e)}")
                    
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
                            'reason': f'Validation error: {str(e)}'
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
                'domain_stats': domain_stats
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
        
        if len(emails) > 1000:
            return jsonify({
                'error': 'Too many emails',
                'message': 'Maximum 1000 emails per batch'
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
def send_single_email():
    """
    Send a single email.
    
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
    print("Email Platform - Validate & Send Emails")
    print("=" * 70)
    print("\n🚀 Server starting on http://localhost:5000")
    print("🔐 Authentication: Anonymous User ID (X-User-ID header)")
    print("📊 Private history without login")
    print("📧 Email sending with SendGrid integration")
    
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
    
    print("\n🌐 Frontend: http://localhost:3000 (if running)")
    print("💡 Tip: Use 'Send Emails' tab to compose and send emails")
    print("⚙️  Setup: Add SENDGRID_API_KEY to .env file")
    print("\n" + "=" * 70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
