#!/usr/bin/env python3
"""
Flask Backend for Email Validator
RESTful API with CORS support for React frontend
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from emailvalidator_unified import validate_email, validate_email_advanced, validate_batch
import time
import os
from typing import List, Dict, Any

app = Flask(__name__, static_folder='frontend/build', static_url_path='')
CORS(app)  # Enable CORS for React frontend

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def home():
    """Serve React frontend."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api')
def api_home():
    """API documentation homepage."""
    return jsonify({
        'name': 'Email Validator API',
        'version': '2.0.0',
        'description': 'Advanced email validation with DNS, MX, disposable, and typo detection',
        'endpoints': {
            'GET /api': 'API documentation',
            'GET /api/health': 'Health check',
            'POST /api/validate': 'Validate single email (basic)',
            'POST /api/validate/advanced': 'Validate single email (advanced)',
            'POST /api/validate/batch': 'Validate multiple emails',
            'GET /api/stats': 'Get validation statistics'
        },
        'features': [
            'RFC 5321 syntax validation',
            'DNS record checking',
            'MX record verification',
            'Disposable email detection',
            'Role-based email detection',
            'Typo suggestion',
            'Confidence scoring (0-100)',
            'Batch processing'
        ]
    })


@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'email-validator',
        'timestamp': time.time(),
        'version': '2.0.0'
    })


@app.route('/api/validate', methods=['POST'])
def validate_basic():
    """
    Validate single email - basic mode (fast).
    
    Request body:
        {
            "email": "user@example.com"
        }
    
    Response:
        {
            "email": "user@example.com",
            "valid": true,
            "timestamp": 1234567890.123
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Missing email parameter',
                'message': 'Please provide an email address in the request body'
            }), 400
        
        email = data['email']
        
        if not email or not isinstance(email, str):
            return jsonify({
                'error': 'Invalid email parameter',
                'message': 'Email must be a non-empty string'
            }), 400
        
        # Validate
        start_time = time.time()
        is_valid = validate_email(email)
        processing_time = time.time() - start_time
        
        return jsonify({
            'email': email,
            'valid': is_valid,
            'processing_time': round(processing_time, 4),
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Validation failed',
            'message': str(e)
        }), 500


@app.route('/api/validate/advanced', methods=['POST'])
def validate_advanced():
    """
    Validate single email - advanced mode (comprehensive).
    
    Request body:
        {
            "email": "user@example.com",
            "check_dns": true,          // optional, default: true
            "check_mx": true,           // optional, default: true
            "check_disposable": true,   // optional, default: true
            "check_typos": true,        // optional, default: true
            "check_role_based": true    // optional, default: true
        }
    
    Response:
        {
            "email": "user@example.com",
            "valid": true,
            "checks": {
                "syntax": true,
                "dns_valid": true,
                "mx_records": true,
                "is_disposable": false,
                "is_role_based": false
            },
            "confidence_score": 100,
            "suggestion": null,
            "reason": "Valid email",
            "processing_time": 0.123,
            "timestamp": 1234567890.123
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Missing email parameter',
                'message': 'Please provide an email address in the request body'
            }), 400
        
        email = data['email']
        
        if not email or not isinstance(email, str):
            return jsonify({
                'error': 'Invalid email parameter',
                'message': 'Email must be a non-empty string'
            }), 400
        
        # Get optional parameters
        check_dns = data.get('check_dns', True)
        check_mx = data.get('check_mx', True)
        check_disposable = data.get('check_disposable', True)
        check_typos = data.get('check_typos', True)
        check_role_based = data.get('check_role_based', True)
        
        # Validate
        start_time = time.time()
        result = validate_email_advanced(
            email,
            check_dns=check_dns,
            check_mx=check_mx,
            check_disposable=check_disposable,
            check_typos=check_typos,
            check_role_based=check_role_based
        )
        processing_time = time.time() - start_time
        
        result['processing_time'] = round(processing_time, 4)
        result['timestamp'] = time.time()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': 'Validation failed',
            'message': str(e)
        }), 500


@app.route('/api/validate/batch', methods=['POST'])
def validate_batch_endpoint():
    """
    Validate multiple emails.
    
    Request body:
        {
            "emails": ["user@example.com", "test@test.com"],
            "advanced": false,          // optional, default: false
            "check_dns": true,          // optional for advanced mode
            "check_mx": true,           // optional for advanced mode
            "check_disposable": true,   // optional for advanced mode
            "check_typos": true,        // optional for advanced mode
            "check_role_based": true    // optional for advanced mode
        }
    
    Response:
        {
            "total": 2,
            "valid_count": 1,
            "invalid_count": 1,
            "results": [...],
            "processing_time": 0.123,
            "timestamp": 1234567890.123
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({
                'error': 'Missing emails parameter',
                'message': 'Please provide an array of email addresses'
            }), 400
        
        emails = data['emails']
        
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
        
        # Get mode and options
        advanced = data.get('advanced', False)
        
        # Validate batch
        start_time = time.time()
        
        if advanced:
            # Advanced mode with options
            results = validate_batch(
                emails,
                advanced=True,
                check_dns=data.get('check_dns', True),
                check_mx=data.get('check_mx', True),
                check_disposable=data.get('check_disposable', True),
                check_typos=data.get('check_typos', True),
                check_role_based=data.get('check_role_based', True)
            )
        else:
            # Basic mode
            results = validate_batch(emails)
        
        processing_time = time.time() - start_time
        
        # Count valid/invalid
        valid_count = sum(1 for r in results if r.get('valid', False))
        invalid_count = len(results) - valid_count
        
        return jsonify({
            'total': len(results),
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'results': results,
            'processing_time': round(processing_time, 4),
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Batch validation failed',
            'message': str(e)
        }), 500


@app.route('/api/stats')
def stats():
    """Get validation statistics and configuration."""
    return jsonify({
        'disposable_domains_count': 20,
        'common_domains_count': 19,
        'role_based_prefixes_count': 18,
        'typo_similarity_threshold': 0.85,
        'max_batch_size': 1000,
        'features': {
            'syntax_validation': True,
            'dns_checking': True,
            'mx_verification': True,
            'disposable_detection': True,
            'role_based_detection': True,
            'typo_suggestion': True,
            'confidence_scoring': True,
            'batch_processing': True,
            'parallel_processing': True
        }
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors - serve React app for client-side routing."""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested endpoint does not exist',
            'available_endpoints': [
                'GET /api',
                'GET /api/health',
                'POST /api/validate',
                'POST /api/validate/advanced',
                'POST /api/validate/batch',
                'GET /api/stats'
            ]
        }), 404
    # Serve React app for all other routes
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
    print("=" * 60)
    print("Email Validator API Starting...")
    print("=" * 60)
    print("\nEndpoints:")
    print("  - http://localhost:5000/")
    print("  - http://localhost:5000/api/health")
    print("  - http://localhost:5000/api/validate")
    print("  - http://localhost:5000/api/validate/advanced")
    print("  - http://localhost:5000/api/validate/batch")
    print("  - http://localhost:5000/api/stats")
    print("\nFrontend:")
    print("  - React app will connect to this API")
    print("\n" + "=" * 60)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
