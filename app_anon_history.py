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
from bounce_tracker import check_bounce_risk
from email_status import determine_email_status
import time
import os
import re
import logging
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


@app.route('/api/validate', methods=['POST'])
@rate_limit
def validate_email():
    """
    Validate single email with anonymous user tracking.
    
    Headers:
        X-User-ID: Anonymous user ID (required)
    
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
        # Extract anonymous user ID
        try:
            anon_user_id = get_anon_user_id()
        except ValueError as e:
            logger.warning(f"Authentication failed: {str(e)}")
            return jsonify({
                'error': 'Authentication required',
                'message': str(e)
            }), 400
        
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
        
        # Bounce history check
        try:
            bounce_risk = check_bounce_risk(email)
            result['bounce_check'] = bounce_risk
            
            # Add bounce warning if exists
            if bounce_risk['bounce_history']['has_bounced']:
                logger.info(f"Bounce history for {email}: {bounce_risk['bounce_history']['total_bounces']} bounces")
                if bounce_risk['risk_level'] in ['critical', 'high']:
                    result['valid'] = False
                    if result.get('reason'):
                        result['reason'] += f"; {bounce_risk['warning']}"
                    else:
                        result['reason'] = bounce_risk['warning']
        except Exception as e:
            logger.error(f"Bounce check failed for {email}: {str(e)}")
        
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
        
        # Store in database with anonymous user ID
        try:
            storage = get_storage()
            record = storage.create_record({
                'anon_user_id': anon_user_id,
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
                
                # Bounce history check
                bounce_risk = check_bounce_risk(email)
                result['bounce_check'] = bounce_risk
                
                if bounce_risk['bounce_history']['has_bounced']:
                    if bounce_risk['risk_level'] in ['critical', 'high']:
                        result['valid'] = False
                        if result.get('reason'):
                            result['reason'] += f"; {bounce_risk['warning']}"
                        else:
                            result['reason'] = bounce_risk['warning']
                
                # Calculate deliverability score
                deliverability = calculate_deliverability_score(email, result)
                result['deliverability'] = deliverability
                
                # Determine email status
                status_info = determine_email_status(result)
                result['status'] = status_info
                
            except Exception as e:
                logger.error(f"Failed to add risk checks for {result.get('email')}: {str(e)}")
        
        processing_time = time.time() - start_time
        
        # Store results with anonymous user ID
        storage = get_storage()
        stored_count = 0
        for result in results:
            try:
                record = storage.create_record({
                    'anon_user_id': anon_user_id,
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
                            
                            # Add bounce check
                            bounce = check_bounce_risk(email)
                            result['bounce_check'] = bounce
                            
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


@app.route('/api/history', methods=['GET'])
def get_history():
    """
    Get validation history for the anonymous user.
    Returns ONLY records belonging to the requesting user.
    
    Headers:
        X-User-ID: Anonymous user ID (required)
    
    Query params:
        - limit: Number of records (default: 100, max: 1000)
        - offset: Pagination offset (default: 0)
    
    Response:
        {
            "total": 50,
            "limit": 100,
            "offset": 0,
            "history": [
                {
                    "id": 123,
                    "email": "user@example.com",
                    "valid": true,
                    "confidence_score": 95,
                    "validated_at": "2024-01-01T12:00:00",
                    ...
                }
            ]
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
        
        # Get pagination params
        limit = min(int(request.args.get('limit', 100)), 1000)
        offset = int(request.args.get('offset', 0))
        
        # Fetch user-specific history
        storage = get_storage()
        history = storage.get_user_history(anon_user_id, limit=limit, offset=offset)
        
        return jsonify({
            'total': len(history),
            'limit': limit,
            'offset': offset,
            'history': history
        })
        
    except Exception as e:
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

if __name__ == '__main__':
    print("=" * 70)
    print("Email Validator API with Anonymous User History")
    print("=" * 70)
    print("\n🔐 Authentication: Anonymous User ID (X-User-ID header)")
    print("📊 Private history without login")
    print("\nEndpoints:")
    print("  - POST /api/validate          - Validate single email")
    print("  - POST /api/validate/batch    - Validate multiple emails")
    print("  - GET  /api/history           - Get user history")
    print("  - DELETE /api/history/:id     - Delete specific record")
    print("  - DELETE /api/history         - Clear all history")
    print("  - GET  /api/analytics         - Get user analytics")
    print("\n" + "=" * 70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
