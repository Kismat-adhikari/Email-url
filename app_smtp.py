#!/usr/bin/env python3
"""
Enhanced Flask API with SMTP Verification and Catch-all Detection
Extends app.py with SMTP-level mailbox verification
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from email_validator_smtp import validate_email_with_smtp, detect_catch_all_domain
from emailvalidator_unified import validate_email, validate_batch
import time

app = Flask(__name__)
CORS(app)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api')
def api_home():
    """API documentation."""
    return jsonify({
        'name': 'Email Validator API with SMTP',
        'version': '3.0.0',
        'description': 'Advanced email validation with SMTP verification and catch-all detection',
        'endpoints': {
            'GET /api': 'API documentation',
            'GET /api/health': 'Health check',
            'POST /api/validate': 'Validate single email (basic)',
            'POST /api/validate/smtp': 'Validate with SMTP verification',
            'POST /api/validate/batch': 'Validate multiple emails',
            'POST /api/catch-all': 'Detect catch-all domain',
            'GET /api/stats': 'Get validation statistics'
        },
        'features': [
            'RFC 5321 syntax validation',
            'DNS record checking',
            'MX record verification',
            'SMTP mailbox verification',
            'Catch-all domain detection',
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
        'service': 'email-validator-smtp',
        'timestamp': time.time(),
        'version': '3.0.0'
    })


@app.route('/api/validate', methods=['POST'])
def validate_basic():
    """
    Validate single email - basic mode (fast, syntax only).
    
    Request:
        {
            "email": "user@example.com"
        }
    
    Response:
        {
            "email": "user@example.com",
            "valid": true,
            "processing_time": 0.001,
            "timestamp": 1234567890.123
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Missing email parameter'
            }), 400
        
        email = data['email']
        
        if not email or not isinstance(email, str):
            return jsonify({
                'error': 'Invalid email parameter'
            }), 400
        
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


@app.route('/api/validate/smtp', methods=['POST'])
def validate_with_smtp():
    """
    Validate single email with SMTP verification.
    
    Request:
        {
            "email": "user@example.com",
            "enable_smtp": true,        // optional, default: true
            "check_dns": true,          // optional, default: true
            "check_mx": true,           // optional, default: true
            "check_disposable": true,   // optional, default: true
            "check_typos": true,        // optional, default: true
            "check_role_based": true,   // optional, default: true
            "smtp_timeout": 10          // optional, default: 10 seconds
        }
    
    Response:
        {
            "email": "user@example.com",
            "valid": true,
            "checks": {
                "syntax": true,
                "dns_valid": true,
                "mx_records": true,
                "smtp_verified": true,
                "is_disposable": false,
                "is_role_based": false,
                "is_catch_all": false
            },
            "confidence_score": 100,
            "smtp_details": {
                "smtp_valid": true,
                "smtp_code": 250,
                "smtp_message": "OK",
                "is_catch_all": false,
                "error": null
            },
            "is_catch_all": false,
            "suggestion": null,
            "reason": "Valid email",
            "processing_time": 1.234,
            "timestamp": 1234567890.123
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Missing email parameter'
            }), 400
        
        email = data['email']
        
        if not email or not isinstance(email, str):
            return jsonify({
                'error': 'Invalid email parameter'
            }), 400
        
        # Get optional parameters
        enable_smtp = data.get('enable_smtp', True)
        check_dns = data.get('check_dns', True)
        check_mx = data.get('check_mx', True)
        check_disposable = data.get('check_disposable', True)
        check_typos = data.get('check_typos', True)
        check_role_based = data.get('check_role_based', True)
        smtp_timeout = data.get('smtp_timeout', 10)
        
        # Validate
        start_time = time.time()
        result = validate_email_with_smtp(
            email,
            enable_smtp=enable_smtp,
            check_dns=check_dns,
            check_mx=check_mx,
            check_disposable=check_disposable,
            check_typos=check_typos,
            check_role_based=check_role_based,
            smtp_timeout=smtp_timeout
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
    Validate multiple emails (basic mode only for performance).
    
    Request:
        {
            "emails": ["user@example.com", "test@test.com"],
            "advanced": false
        }
    
    Response:
        {
            "total": 2,
            "valid_count": 2,
            "invalid_count": 0,
            "results": [...],
            "processing_time": 0.123,
            "timestamp": 1234567890.123
        }
    
    Note: SMTP verification is not available in batch mode for performance reasons.
    """
    try:
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({
                'error': 'Missing emails parameter'
            }), 400
        
        emails = data['emails']
        
        if not isinstance(emails, list):
            return jsonify({
                'error': 'emails must be an array'
            }), 400
        
        if len(emails) == 0:
            return jsonify({
                'error': 'Empty array'
            }), 400
        
        if len(emails) > 1000:
            return jsonify({
                'error': 'Too many emails (max 1000)'
            }), 400
        
        advanced = data.get('advanced', False)
        
        start_time = time.time()
        results = validate_batch(emails, advanced=advanced)
        processing_time = time.time() - start_time
        
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


@app.route('/api/catch-all', methods=['POST'])
def check_catch_all():
    """
    Detect if a domain is catch-all (accepts all emails).
    
    Request:
        {
            "domain": "example.com",
            "timeout": 10  // optional, default: 10 seconds
        }
    
    Response:
        {
            "domain": "example.com",
            "is_catch_all": false,
            "test_email": "nonexistent-test@example.com",
            "smtp_code": 550,
            "error": null,
            "processing_time": 1.234,
            "timestamp": 1234567890.123
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'domain' not in data:
            return jsonify({
                'error': 'Missing domain parameter'
            }), 400
        
        domain = data['domain']
        timeout = data.get('timeout', 10)
        
        if not domain or not isinstance(domain, str):
            return jsonify({
                'error': 'Invalid domain parameter'
            }), 400
        
        start_time = time.time()
        result = detect_catch_all_domain(domain, timeout=timeout)
        processing_time = time.time() - start_time
        
        result['domain'] = domain
        result['processing_time'] = round(processing_time, 4)
        result['timestamp'] = time.time()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': 'Catch-all detection failed',
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
        'smtp_timeout': 10,
        'features': {
            'syntax_validation': True,
            'dns_checking': True,
            'mx_verification': True,
            'smtp_verification': True,
            'catch_all_detection': True,
            'disposable_detection': True,
            'role_based_detection': True,
            'typo_suggestion': True,
            'confidence_scoring': True,
            'batch_processing': True
        }
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist',
        'available_endpoints': [
            'GET /api',
            'GET /api/health',
            'POST /api/validate',
            'POST /api/validate/smtp',
            'POST /api/validate/batch',
            'POST /api/catch-all',
            'GET /api/stats'
        ]
    }), 404


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
    print("Email Validator API with SMTP Verification")
    print("=" * 70)
    print("\nEndpoints:")
    print("  - http://localhost:5000/api")
    print("  - http://localhost:5000/api/health")
    print("  - http://localhost:5000/api/validate")
    print("  - http://localhost:5000/api/validate/smtp")
    print("  - http://localhost:5000/api/validate/batch")
    print("  - http://localhost:5000/api/catch-all")
    print("  - http://localhost:5000/api/stats")
    print("\nFeatures:")
    print("  ✓ SMTP mailbox verification")
    print("  ✓ Catch-all domain detection")
    print("  ✓ Disposable email detection")
    print("  ✓ Role-based email detection")
    print("  ✓ Confidence scoring (0-100)")
    print("  ✓ Batch processing")
    print("\n" + "=" * 70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
