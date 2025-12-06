#!/usr/bin/env python3
"""
Flask Backend with Anonymous User ID System
Private history WITHOUT requiring user login
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from emailvalidator_unified import validate_email_advanced, validate_batch
from supabase_storage import get_storage
from risk_scoring import RiskScorer
from email_enrichment import EmailEnricher
import time
import os

app = Flask(__name__, static_folder='frontend/build', static_url_path='')
CORS(app)

# Initialize components
risk_scorer = RiskScorer()
enricher = EmailEnricher()

# ============================================================================
# MIDDLEWARE - Extract Anonymous User ID
# ============================================================================

def get_anon_user_id():
    """
    Extract anonymous user ID from request headers.
    
    Returns:
        str: Anonymous user ID
    
    Raises:
        ValueError: If header is missing or invalid
    """
    anon_user_id = request.headers.get('X-User-ID')
    
    if not anon_user_id:
        raise ValueError('Missing X-User-ID header. Anonymous user ID is required.')
    
    # Basic validation - should be a UUID-like string
    if len(anon_user_id) < 10 or len(anon_user_id) > 50:
        raise ValueError('Invalid X-User-ID format')
    
    return anon_user_id


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
def validate_email():
    """
    Validate single email with anonymous user tracking.
    
    Headers:
        X-User-ID: Anonymous user ID (required)
    
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
            "record_id": 123,
            "processing_time": 0.123
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
        
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Missing email parameter',
                'message': 'Please provide an email address'
            }), 400
        
        email = data['email']
        advanced = data.get('advanced', True)
        
        if not email or not isinstance(email, str):
            return jsonify({
                'error': 'Invalid email parameter',
                'message': 'Email must be a non-empty string'
            }), 400
        
        # Validate email
        start_time = time.time()
        
        if advanced:
            result = validate_email_advanced(
                email,
                check_dns=True,
                check_mx=True,
                check_disposable=True,
                check_typos=True,
                check_role_based=True
            )
        else:
            from emailvalidator_unified import validate_email as validate_basic
            is_valid = validate_basic(email)
            result = {
                'email': email,
                'valid': is_valid,
                'confidence_score': 100 if is_valid else 0
            }
        
        processing_time = time.time() - start_time
        result['processing_time'] = round(processing_time, 4)
        
        # Assess risk
        try:
            risk_assessment = risk_scorer.calculate_risk_score({
                'email': email,
                'bounce_count': 0,
                'confidence_score': result.get('confidence_score', 0),
                **(result.get('checks', {}))
            })
            result['risk_assessment'] = risk_assessment
            result['risk_score'] = risk_assessment['risk_score']
            result['risk_level'] = risk_assessment['risk_level']
            result['risk_factors'] = risk_assessment['risk_factors']
        except Exception as e:
            result['risk_assessment'] = {'error': str(e)}
        
        # Enrich email data
        try:
            enrichment = enricher.enrich_email(email)
            result['enrichment'] = enrichment
        except Exception as e:
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
                'is_disposable': result.get('checks', {}).get('is_disposable', False),
                'is_role_based': result.get('checks', {}).get('is_role_based', False),
                'is_catch_all': result.get('is_catch_all', False)
            })
            result['record_id'] = record['id']
            result['stored'] = True
        except Exception as e:
            result['stored'] = False
            result['storage_error'] = str(e)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': 'Validation failed',
            'message': str(e)
        }), 500


@app.route('/api/validate/batch', methods=['POST'])
def validate_batch_endpoint():
    """
    Validate multiple emails with anonymous user tracking.
    
    Headers:
        X-User-ID: Anonymous user ID (required)
    
    Request body:
        {
            "emails": ["user1@example.com", "user2@test.com"],
            "advanced": true
        }
    
    Response:
        {
            "total": 2,
            "valid_count": 1,
            "invalid_count": 1,
            "results": [...],
            "processing_time": 0.123
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
        
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({
                'error': 'Missing emails parameter',
                'message': 'Please provide an array of email addresses'
            }), 400
        
        emails = data['emails']
        advanced = data.get('advanced', True)
        
        if not isinstance(emails, list):
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
            return jsonify({
                'error': 'Too many emails',
                'message': 'Maximum 1,000 emails per request'
            }), 400
        
        # Validate batch
        start_time = time.time()
        results = validate_batch(emails, advanced=advanced)
        processing_time = time.time() - start_time
        
        # Store results with anonymous user ID
        storage = get_storage()
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
            except Exception as e:
                result['storage_error'] = str(e)
        
        valid_count = sum(1 for r in results if r.get('valid', False))
        
        return jsonify({
            'total': len(results),
            'valid_count': valid_count,
            'invalid_count': len(results) - valid_count,
            'results': results,
            'processing_time': round(processing_time, 4)
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Batch validation failed',
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
