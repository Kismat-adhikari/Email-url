#!/usr/bin/env python3
"""
Flask API for Dashboard with Webhooks, CSV Export, and Integrations
Complete backend for React dashboard
"""

from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
from email_validator_smtp import validate_email_with_smtp
from emailvalidator_unified import validate_batch
from supabase_storage import get_storage
from risk_scoring import RiskScorer
from webhook_integration import WebhookManager, CRMIntegration, ESPIntegration
from csv_export import export_to_csv, export_risk_report_csv, export_statistics_csv
import time
import io
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Initialize components
risk_scorer = RiskScorer()

# ============================================================================
# DASHBOARD API ENDPOINTS
# ============================================================================

@app.route('/api/dashboard')
def dashboard_home():
    """Dashboard API documentation."""
    return jsonify({
        'name': 'Email Validator Dashboard API',
        'version': '1.0.0',
        'description': 'Complete dashboard with webhooks, CSV export, and integrations',
        'endpoints': {
            'Dashboard': {
                'GET /api/dashboard/stats': 'Get dashboard statistics',
                'GET /api/dashboard/recent': 'Get recent validations',
                'POST /api/dashboard/validate': 'Validate and store email',
                'POST /api/dashboard/batch': 'Batch validate with progress'
            },
            'Export': {
                'POST /api/export/csv': 'Export results to CSV',
                'POST /api/export/risk-csv': 'Export risk report to CSV',
                'GET /api/export/stats-csv': 'Export statistics to CSV'
            },
            'Webhooks': {
                'POST /api/webhook/send': 'Send to webhook',
                'POST /api/webhook/configure': 'Configure webhook',
                'GET /api/webhook/test': 'Test webhook connection'
            },
            'Integrations': {
                'POST /api/integration/crm': 'Update CRM contact',
                'POST /api/integration/esp': 'Update ESP subscriber',
                'GET /api/integration/status': 'Get integration status'
            }
        }
    })


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Get comprehensive dashboard statistics.
    
    Response:
        {
            "total_validations": 1000,
            "valid_count": 850,
            "invalid_count": 150,
            "avg_confidence": 87.5,
            "high_risk_count": 50,
            "recent_validations": 25,
            "today_validations": 100
        }
    """
    try:
        storage = get_storage()
        
        # Get all records
        all_records = storage.get_all_records(limit=10000)
        
        if not all_records:
            return jsonify({
                'total_validations': 0,
                'valid_count': 0,
                'invalid_count': 0,
                'message': 'No data available'
            })
        
        # Calculate statistics
        total = len(all_records)
        valid_count = sum(1 for r in all_records if r.get('valid'))
        invalid_count = total - valid_count
        
        # Calculate average confidence
        total_confidence = sum(r.get('confidence_score', 0) for r in all_records)
        avg_confidence = total_confidence / total if total > 0 else 0
        
        # Count high-risk emails
        high_risk = 0
        for record in all_records[:100]:  # Sample for performance
            assessment = risk_scorer.calculate_risk_score(record)
            if assessment['risk_level'] == 'HIGH':
                high_risk += 1
        
        # Recent validations (last hour)
        recent_count = len([r for r in all_records[:100] if r.get('validated_at')])
        
        return jsonify({
            'total_validations': total,
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'avg_confidence': round(avg_confidence, 2),
            'high_risk_count': high_risk,
            'recent_validations': recent_count,
            'disposable_count': sum(1 for r in all_records if r.get('is_disposable')),
            'role_based_count': sum(1 for r in all_records if r.get('is_role_based')),
            'catch_all_count': sum(1 for r in all_records if r.get('is_catch_all'))
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/recent', methods=['GET'])
def get_recent_validations():
    """
    Get recent validation results.
    
    Query params:
        - limit: Number of records (default: 50)
    
    Response:
        {
            "total": 50,
            "validations": [...]
        }
    """
    try:
        limit = int(request.args.get('limit', 50))
        
        storage = get_storage()
        records = storage.get_all_records(limit=limit)
        
        return jsonify({
            'total': len(records),
            'validations': records
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/validate', methods=['POST'])
def dashboard_validate():
    """
    Validate email with full details for dashboard.
    
    Request:
        {
            "email": "user@example.com",
            "enable_smtp": false,
            "assess_risk": true,
            "send_webhook": false,
            "webhook_url": "https://example.com/webhook"
        }
    
    Response:
        {
            "email": "user@example.com",
            "valid": true,
            "confidence_score": 95,
            "checks": {...},
            "risk_assessment": {...},
            "webhook_sent": false,
            "stored": true
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Missing email parameter'}), 400
        
        email = data['email']
        enable_smtp = data.get('enable_smtp', False)
        assess_risk = data.get('assess_risk', True)
        send_webhook = data.get('send_webhook', False)
        webhook_url = data.get('webhook_url')
        
        # Validate email
        start_time = time.time()
        result = validate_email_with_smtp(
            email,
            enable_smtp=enable_smtp,
            check_dns=True,
            check_mx=True,
            check_disposable=True,
            check_typos=True,
            check_role_based=True
        )
        processing_time = time.time() - start_time
        
        result['processing_time'] = round(processing_time, 4)
        
        # Store in database
        try:
            storage = get_storage()
            record = storage.create_record({
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
        
        # Assess risk
        if assess_risk:
            try:
                risk_assessment = risk_scorer.calculate_risk_score(record if result['stored'] else {
                    'email': email,
                    'bounce_count': 0,
                    'confidence_score': result['confidence_score'],
                    **result['checks']
                })
                result['risk_assessment'] = risk_assessment
            except Exception as e:
                result['risk_assessment'] = {'error': str(e)}
        
        # Send webhook
        if send_webhook and webhook_url:
            try:
                webhook_manager = WebhookManager(webhook_url)
                webhook_result = webhook_manager.send_webhook(result)
                result['webhook_sent'] = webhook_result['success']
                result['webhook_response'] = webhook_result
            except Exception as e:
                result['webhook_sent'] = False
                result['webhook_error'] = str(e)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/batch', methods=['POST'])
def dashboard_batch_validate():
    """
    Batch validate with progress tracking.
    
    Request:
        {
            "emails": ["user1@example.com", "user2@test.com"],
            "advanced": true,
            "assess_risk": true,
            "send_webhook": false
        }
    
    Response:
        {
            "total": 2,
            "valid_count": 2,
            "results": [...],
            "processing_time": 1.234
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({'error': 'Missing emails parameter'}), 400
        
        emails = data['emails']
        advanced = data.get('advanced', True)
        assess_risk = data.get('assess_risk', False)
        
        if not isinstance(emails, list) or len(emails) == 0:
            return jsonify({'error': 'emails must be a non-empty array'}), 400
        
        if len(emails) > 1000:
            return jsonify({'error': 'Maximum 1000 emails per request'}), 400
        
        # Validate batch
        start_time = time.time()
        results = validate_batch(emails, advanced=advanced)
        
        # Store results
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
                
                # Assess risk if requested
                if assess_risk:
                    risk_assessment = risk_scorer.calculate_risk_score(record)
                    result['risk_assessment'] = risk_assessment
                    
            except Exception as e:
                result['storage_error'] = str(e)
        
        processing_time = time.time() - start_time
        
        valid_count = sum(1 for r in results if r.get('valid'))
        
        return jsonify({
            'total': len(results),
            'valid_count': valid_count,
            'invalid_count': len(results) - valid_count,
            'results': results,
            'processing_time': round(processing_time, 4)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# CSV EXPORT ENDPOINTS
# ============================================================================

@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    """
    Export validation results to CSV.
    
    Request:
        {
            "emails": ["user1@example.com", "user2@test.com"],
            "include_details": true
        }
    
    Response:
        CSV file download
    """
    try:
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({'error': 'Missing emails parameter'}), 400
        
        emails = data['emails']
        include_details = data.get('include_details', True)
        
        # Get validation results
        storage = get_storage()
        results = []
        
        for email in emails:
            record = storage.get_record_by_email(email)
            if record:
                results.append(record)
        
        # Generate CSV
        csv_data = export_to_csv(results, include_details=include_details)
        
        # Return as file download
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=email_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/risk-csv', methods=['POST'])
def export_risk_csv():
    """Export risk assessments to CSV."""
    try:
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({'error': 'Missing emails parameter'}), 400
        
        emails = data['emails']
        
        # Get risk assessments
        assessments = []
        for email in emails:
            assessment = risk_scorer.get_email_risk_from_db(email)
            assessments.append(assessment)
        
        # Generate CSV
        csv_data = export_risk_report_csv(assessments)
        
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=risk_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/stats-csv', methods=['GET'])
def export_stats_csv():
    """Export statistics to CSV."""
    try:
        storage = get_storage()
        stats = storage.get_statistics()
        
        csv_data = export_statistics_csv(stats)
        
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=statistics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@app.route('/api/webhook/send', methods=['POST'])
def send_webhook():
    """
    Send data to webhook.
    
    Request:
        {
            "url": "https://example.com/webhook",
            "data": {...},
            "secret": "optional-secret"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'url' not in data or 'data' not in data:
            return jsonify({'error': 'Missing url or data parameter'}), 400
        
        url = data['url']
        payload = data['data']
        secret = data.get('secret')
        
        webhook_manager = WebhookManager(url, secret)
        result = webhook_manager.send_webhook(payload)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/webhook/test', methods=['POST'])
def test_webhook():
    """Test webhook connection."""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing url parameter'}), 400
        
        url = data['url']
        
        webhook_manager = WebhookManager(url)
        result = webhook_manager.send_webhook({
            'test': True,
            'message': 'Webhook test from Email Validator'
        })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# INTEGRATION ENDPOINTS
# ============================================================================

@app.route('/api/integration/crm', methods=['POST'])
def update_crm():
    """
    Update CRM contact.
    
    Request:
        {
            "email": "user@example.com",
            "crm_type": "salesforce",
            "api_key": "your-api-key",
            "validation_data": {...}
        }
    """
    try:
        data = request.get_json()
        
        required = ['email', 'crm_type', 'api_key', 'validation_data']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        crm = CRMIntegration(data['crm_type'], data['api_key'])
        result = crm.update_contact(data['email'], data['validation_data'])
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integration/esp', methods=['POST'])
def update_esp():
    """
    Update ESP subscriber.
    
    Request:
        {
            "email": "user@example.com",
            "esp_type": "sendgrid",
            "api_key": "your-api-key",
            "validation_data": {...},
            "list_id": "optional-list-id"
        }
    """
    try:
        data = request.get_json()
        
        required = ['email', 'esp_type', 'api_key', 'validation_data']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        esp = ESPIntegration(data['esp_type'], data['api_key'])
        result = esp.update_subscriber(
            data['email'],
            data['validation_data'],
            data.get('list_id')
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("Email Validator Dashboard API")
    print("=" * 70)
    print("\nEndpoints:")
    print("  Dashboard:")
    print("    - GET  /api/dashboard/stats")
    print("    - GET  /api/dashboard/recent")
    print("    - POST /api/dashboard/validate")
    print("    - POST /api/dashboard/batch")
    print("\n  Export:")
    print("    - POST /api/export/csv")
    print("    - POST /api/export/risk-csv")
    print("    - GET  /api/export/stats-csv")
    print("\n  Webhooks:")
    print("    - POST /api/webhook/send")
    print("    - POST /api/webhook/test")
    print("\n  Integrations:")
    print("    - POST /api/integration/crm")
    print("    - POST /api/integration/esp")
    print("\n" + "=" * 70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5002)
