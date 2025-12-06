#!/usr/bin/env python3
"""
Flask API with Supabase Integration for Email Validation Storage
Complete REST API for managing email validation records
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from email_validator_smtp import validate_email_with_smtp
from emailvalidator_unified import validate_email, validate_batch
from supabase_storage import SupabaseStorage, get_storage
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import time
import os

app = Flask(__name__)
CORS(app)

# Initialize scheduler for re-verification
scheduler = BackgroundScheduler()
scheduler.start()

# ============================================================================
# VALIDATION + STORAGE ENDPOINTS
# ============================================================================

@app.route('/api')
def api_home():
    """API documentation."""
    return jsonify({
        'name': 'Email Validator API with Supabase Storage',
        'version': '4.0.0',
        'description': 'Email validation with persistent storage and history tracking',
        'endpoints': {
            'GET /api': 'API documentation',
            'GET /api/health': 'Health check',
            'POST /api/validate': 'Validate and store email',
            'POST /api/validate/smtp': 'Validate with SMTP and store',
            'POST /api/validate/batch': 'Validate and store multiple emails',
            'GET /api/records': 'Get all records (paginated)',
            'GET /api/records/<email>': 'Get record by email',
            'GET /api/records/id/<id>': 'Get record by ID',
            'GET /api/history/<email>': 'Get validation history',
            'PUT /api/records/<id>': 'Update record',
            'DELETE /api/records/<id>': 'Delete record',
            'POST /api/bounce/<email>': 'Record email bounce',
            'GET /api/statistics': 'Get validation statistics',
            'POST /api/search': 'Search records with filters',
            'POST /api/schedule-reverify': 'Schedule re-verification'
        }
    })


@app.route('/api/health')
def health():
    """Health check with Supabase connection test."""
    try:
        storage = get_storage()
        # Test connection
        storage.get_statistics()
        
        return jsonify({
            'status': 'healthy',
            'service': 'email-validator-supabase',
            'timestamp': time.time(),
            'version': '4.0.0',
            'supabase': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'email-validator-supabase',
            'timestamp': time.time(),
            'error': str(e)
        }), 503


@app.route('/api/validate', methods=['POST'])
def validate_and_store():
    """
    Validate email and store result in Supabase.
    
    Request:
        {
            "email": "user@example.com",
            "store": true  // optional, default: true
        }
    
    Response:
        {
            "email": "user@example.com",
            "valid": true,
            "stored": true,
            "record_id": 123,
            "timestamp": 1234567890.123
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Missing email parameter'}), 400
        
        email = data['email']
        should_store = data.get('store', True)
        
        # Validate email
        start_time = time.time()
        is_valid = validate_email(email)
        processing_time = time.time() - start_time
        
        result = {
            'email': email,
            'valid': is_valid,
            'processing_time': round(processing_time, 4),
            'timestamp': time.time()
        }
        
        # Store in Supabase
        if should_store:
            try:
                storage = get_storage()
                # Get anonymous user ID from header or use default
                anon_user_id = request.headers.get('X-User-ID', 'legacy-user')
                
                record = storage.create_record({
                    'anon_user_id': anon_user_id,
                    'email': email,
                    'valid': is_valid,
                    'confidence_score': 40 if is_valid else 0,
                    'checks': {'syntax': is_valid}
                })
                result['stored'] = True
                result['record_id'] = record['id']
            except Exception as e:
                result['stored'] = False
                result['storage_error'] = str(e)
        else:
            result['stored'] = False
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate/advanced', methods=['POST'])
def validate_advanced_and_store():
    """
    Validate email with advanced checks and store (for React frontend compatibility).
    
    Request:
        {
            "email": "user@example.com",
            "store": true
        }
    
    Response:
        {
            "email": "user@example.com",
            "valid": true,
            "confidence_score": 95,
            "checks": {...},
            "stored": true,
            "record_id": 123
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Missing email parameter'}), 400
        
        email = data['email']
        should_store = data.get('store', True)
        
        # Validate with advanced checks (no SMTP for speed)
        start_time = time.time()
        result = validate_email_with_smtp(
            email,
            enable_smtp=False,  # Disable SMTP for frontend (too slow)
            check_dns=True,
            check_mx=True,
            check_disposable=True,
            check_typos=True,
            check_role_based=True
        )
        processing_time = time.time() - start_time
        
        result['processing_time'] = round(processing_time, 4)
        result['timestamp'] = time.time()
        
        # Store in Supabase
        if should_store:
            try:
                storage = get_storage()
                # Get anonymous user ID from header or use default
                anon_user_id = request.headers.get('X-User-ID', 'legacy-user')
                
                record = storage.create_record({
                    'anon_user_id': anon_user_id,
                    'email': email,
                    'valid': result['valid'],
                    'confidence_score': result['confidence_score'],
                    'checks': result['checks'],
                    'is_disposable': result['checks'].get('is_disposable', False),
                    'is_role_based': result['checks'].get('is_role_based', False),
                    'is_catch_all': result.get('is_catch_all', False)
                })
                result['stored'] = True
                result['record_id'] = record['id']
            except Exception as e:
                result['stored'] = False
                result['storage_error'] = str(e)
        else:
            result['stored'] = False
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate/smtp', methods=['POST'])
def validate_smtp_and_store():
    """
    Validate email with SMTP and store complete result.
    
    Request:
        {
            "email": "user@example.com",
            "enable_smtp": true,
            "store": true
        }
    
    Response:
        {
            "email": "user@example.com",
            "valid": true,
            "confidence_score": 100,
            "checks": {...},
            "smtp_details": {...},
            "stored": true,
            "record_id": 123
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Missing email parameter'}), 400
        
        email = data['email']
        enable_smtp = data.get('enable_smtp', True)
        should_store = data.get('store', True)
        
        # Validate with SMTP
        start_time = time.time()
        result = validate_email_with_smtp(
            email,
            enable_smtp=enable_smtp,
            check_dns=data.get('check_dns', True),
            check_mx=data.get('check_mx', True),
            check_disposable=data.get('check_disposable', True),
            check_typos=data.get('check_typos', True),
            check_role_based=data.get('check_role_based', True),
            smtp_timeout=data.get('smtp_timeout', 10)
        )
        processing_time = time.time() - start_time
        
        result['processing_time'] = round(processing_time, 4)
        result['timestamp'] = time.time()
        
        # Store in Supabase
        if should_store:
            try:
                storage = get_storage()
                record = storage.create_record({
                    'email': email,
                    'valid': result['valid'],
                    'confidence_score': result['confidence_score'],
                    'checks': result['checks'],
                    'smtp_details': result.get('smtp_details'),
                    'is_disposable': result['checks'].get('is_disposable', False),
                    'is_role_based': result['checks'].get('is_role_based', False),
                    'is_catch_all': result.get('is_catch_all', False)
                })
                result['stored'] = True
                result['record_id'] = record['id']
            except Exception as e:
                result['stored'] = False
                result['storage_error'] = str(e)
        else:
            result['stored'] = False
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate/batch', methods=['POST'])
def validate_batch_and_store():
    """
    Validate multiple emails and store results.
    
    Request:
        {
            "emails": ["user1@example.com", "user2@test.com"],
            "advanced": false,
            "store": true
        }
    
    Response:
        {
            "total": 2,
            "valid_count": 2,
            "stored_count": 2,
            "results": [...]
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({'error': 'Missing emails parameter'}), 400
        
        emails = data['emails']
        advanced = data.get('advanced', False)
        should_store = data.get('store', True)
        
        if not isinstance(emails, list) or len(emails) == 0:
            return jsonify({'error': 'emails must be a non-empty array'}), 400
        
        if len(emails) > 1000:
            return jsonify({'error': 'Maximum 1000 emails per request'}), 400
        
        # Validate batch
        start_time = time.time()
        results = validate_batch(emails, advanced=advanced)
        processing_time = time.time() - start_time
        
        # Store results
        stored_count = 0
        if should_store:
            storage = get_storage()
            for result in results:
                try:
                    record = storage.create_record({
                        'email': result['email'],
                        'valid': result['valid'],
                        'confidence_score': result.get('confidence_score', 40 if result['valid'] else 0),
                        'checks': result.get('checks', {'syntax': result['valid']})
                    })
                    result['record_id'] = record['id']
                    stored_count += 1
                except Exception as e:
                    result['storage_error'] = str(e)
        
        valid_count = sum(1 for r in results if r.get('valid', False))
        
        return jsonify({
            'total': len(results),
            'valid_count': valid_count,
            'invalid_count': len(results) - valid_count,
            'stored_count': stored_count,
            'results': results,
            'processing_time': round(processing_time, 4),
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================

@app.route('/api/records', methods=['GET'])
def get_records():
    """
    Get all records with pagination.
    
    Query params:
        - limit: Number of records (default: 100, max: 1000)
        - offset: Skip records (default: 0)
    
    Response:
        {
            "total": 250,
            "limit": 100,
            "offset": 0,
            "records": [...]
        }
    """
    try:
        limit = min(int(request.args.get('limit', 100)), 1000)
        offset = int(request.args.get('offset', 0))
        
        storage = get_storage()
        records = storage.get_all_records(limit=limit, offset=offset)
        
        return jsonify({
            'total': len(records),
            'limit': limit,
            'offset': offset,
            'records': records
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/records/<email>', methods=['GET'])
def get_record_by_email(email):
    """
    Get most recent record for an email.
    
    Response:
        {
            "id": 123,
            "email": "user@example.com",
            "valid": true,
            "confidence_score": 95,
            ...
        }
    """
    try:
        storage = get_storage()
        record = storage.get_record_by_email(email)
        
        if record:
            return jsonify(record)
        else:
            return jsonify({'error': 'Record not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/records/id/<int:record_id>', methods=['GET'])
def get_record_by_id(record_id):
    """Get record by ID."""
    try:
        storage = get_storage()
        record = storage.get_record_by_id(record_id)
        
        if record:
            return jsonify(record)
        else:
            return jsonify({'error': 'Record not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<email>', methods=['GET'])
def get_validation_history(email):
    """
    Get validation history for an email.
    
    Query params:
        - limit: Number of records (default: 10)
    
    Response:
        {
            "email": "user@example.com",
            "total": 5,
            "history": [...]
        }
    """
    try:
        limit = int(request.args.get('limit', 10))
        
        storage = get_storage()
        history = storage.get_validation_history(email, limit=limit)
        
        return jsonify({
            'email': email,
            'total': len(history),
            'history': history
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/records/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    """
    Update a record.
    
    Request:
        {
            "confidence_score": 85,
            "bounce_count": 1,
            "notes": "Updated after bounce"
        }
    
    Response:
        {
            "id": 123,
            "email": "user@example.com",
            "confidence_score": 85,
            ...
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No update data provided'}), 400
        
        storage = get_storage()
        updated_record = storage.update_record(record_id, data)
        
        return jsonify(updated_record)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """
    Delete a record.
    
    Response:
        {
            "success": true,
            "message": "Record deleted",
            "id": 123
        }
    """
    try:
        storage = get_storage()
        storage.delete_record(record_id)
        
        return jsonify({
            'success': True,
            'message': 'Record deleted',
            'id': record_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bounce/<email>', methods=['POST'])
def record_bounce(email):
    """
    Record an email bounce.
    
    Request:
        {
            "notes": "Bounce reason"  // optional
        }
    
    Response:
        {
            "email": "user@example.com",
            "bounce_count": 2,
            "last_bounce_date": "2024-01-01T12:00:00"
        }
    """
    try:
        data = request.get_json() or {}
        
        storage = get_storage()
        record = storage.increment_bounce_count(email)
        
        # Optionally add notes
        if 'notes' in data:
            record = storage.update_record(record['id'], {'notes': data['notes']})
        
        return jsonify({
            'email': email,
            'bounce_count': record['bounce_count'],
            'last_bounce_date': record['last_bounce_date']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Get validation statistics.
    
    Response:
        {
            "total_validations": 1000,
            "valid_count": 850,
            "invalid_count": 150,
            "avg_confidence": 87.5,
            "disposable_count": 50,
            "role_based_count": 100
        }
    """
    try:
        storage = get_storage()
        stats = storage.get_statistics()
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search_records():
    """
    Search records with filters.
    
    Request:
        {
            "valid": true,
            "min_confidence": 80,
            "max_confidence": 100,
            "is_disposable": false,
            "is_role_based": false,
            "limit": 100
        }
    
    Response:
        {
            "total": 50,
            "records": [...]
        }
    """
    try:
        data = request.get_json() or {}
        
        storage = get_storage()
        records = storage.search_records(
            valid=data.get('valid'),
            min_confidence=data.get('min_confidence'),
            max_confidence=data.get('max_confidence'),
            is_disposable=data.get('is_disposable'),
            is_role_based=data.get('is_role_based'),
            limit=data.get('limit', 100)
        )
        
        return jsonify({
            'total': len(records),
            'records': records
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# RE-VERIFICATION SCHEDULING
# ============================================================================

@app.route('/api/schedule-reverify', methods=['POST'])
def schedule_reverification():
    """
    Schedule re-verification for an email.
    
    Request:
        {
            "email": "user@example.com",
            "days": 30  // Re-verify after X days
        }
    
    Response:
        {
            "success": true,
            "email": "user@example.com",
            "scheduled_for": "2024-02-01T12:00:00"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Missing email parameter'}), 400
        
        email = data['email']
        days = data.get('days', 30)
        
        # Schedule re-verification
        run_date = datetime.now() + timedelta(days=days)
        
        scheduler.add_job(
            func=reverify_email,
            trigger='date',
            run_date=run_date,
            args=[email],
            id=f'reverify_{email}_{int(time.time())}',
            replace_existing=False
        )
        
        return jsonify({
            'success': True,
            'email': email,
            'scheduled_for': run_date.isoformat(),
            'days': days
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def reverify_email(email: str):
    """Background task to re-verify an email."""
    try:
        print(f"Re-verifying email: {email}")
        
        # Validate email
        result = validate_email_with_smtp(email, enable_smtp=False)
        
        # Store new validation
        storage = get_storage()
        storage.create_record({
            'email': email,
            'valid': result['valid'],
            'confidence_score': result['confidence_score'],
            'checks': result['checks'],
            'notes': 'Automatic re-verification'
        })
        
        print(f"Re-verification complete for {email}: {result['valid']}")
        
    except Exception as e:
        print(f"Re-verification failed for {email}: {str(e)}")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404


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
    print("Email Validator API with Supabase Storage")
    print("=" * 70)
    print("\nEndpoints:")
    print("  Validation:")
    print("    - POST /api/validate")
    print("    - POST /api/validate/smtp")
    print("    - POST /api/validate/batch")
    print("\n  Records:")
    print("    - GET  /api/records")
    print("    - GET  /api/records/<email>")
    print("    - GET  /api/records/id/<id>")
    print("    - PUT  /api/records/<id>")
    print("    - DELETE /api/records/<id>")
    print("\n  History & Stats:")
    print("    - GET  /api/history/<email>")
    print("    - GET  /api/statistics")
    print("    - POST /api/search")
    print("\n  Bounce Tracking:")
    print("    - POST /api/bounce/<email>")
    print("\n  Scheduling:")
    print("    - POST /api/schedule-reverify")
    print("\n" + "=" * 70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
