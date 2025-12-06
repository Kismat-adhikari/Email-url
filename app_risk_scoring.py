#!/usr/bin/env python3
"""
Flask API with Risk Scoring and Reporting
Complete REST API for email risk assessment and batch reporting
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from risk_scoring import RiskScorer, generate_risk_report, assess_email_risk
from supabase_storage import get_storage
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Initialize risk scorer
risk_scorer = RiskScorer()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api')
def api_home():
    """API documentation."""
    return jsonify({
        'name': 'Email Risk Scoring API',
        'version': '1.0.0',
        'description': 'Advanced email risk assessment with blacklist checking and spam trap detection',
        'endpoints': {
            'GET /api': 'API documentation',
            'GET /api/health': 'Health check',
            'POST /api/risk/assess': 'Assess risk for single email',
            'POST /api/risk/batch': 'Assess risk for multiple emails',
            'GET /api/risk/<email>': 'Get risk score for email',
            'POST /api/report/generate': 'Generate risk assessment report',
            'GET /api/risk/statistics': 'Get risk statistics',
            'POST /api/risk/high-risk': 'Get all high-risk emails'
        },
        'features': [
            'Bounce history analysis',
            'Spam trap detection',
            'Blacklist checking',
            'Catch-all domain detection',
            'Risk scoring (0-100)',
            'Batch assessment',
            'Detailed reports'
        ]
    })


@app.route('/api/health')
def health():
    """Health check."""
    return jsonify({
        'status': 'healthy',
        'service': 'email-risk-scoring',
        'timestamp': time.time(),
        'version': '1.0.0'
    })


@app.route('/api/risk/assess', methods=['POST'])
def assess_risk():
    """
    Assess risk for a single email.
    
    Request:
        {
            "email": "user@example.com"
        }
    
    Response:
        {
            "email": "user@example.com",
            "risk_score": 45,
            "risk_level": "MEDIUM",
            "risk_factors": [...],
            "is_spam_trap": false,
            "is_blacklisted": false,
            "recommendations": [...]
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Missing email parameter'}), 400
        
        email = data['email']
        
        # Get risk assessment
        start_time = time.time()
        result = risk_scorer.get_email_risk_from_db(email)
        processing_time = time.time() - start_time
        
        result['processing_time'] = round(processing_time, 4)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/risk/<email>', methods=['GET'])
def get_risk(email):
    """
    Get risk score for an email (GET endpoint).
    
    Example:
        GET /api/risk/user@example.com
    """
    try:
        result = risk_scorer.get_email_risk_from_db(email)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/risk/batch', methods=['POST'])
def assess_batch_risk():
    """
    Assess risk for multiple emails.
    
    Request:
        {
            "emails": ["user1@example.com", "user2@test.com"]
        }
    
    Response:
        {
            "total": 2,
            "high_risk": 0,
            "medium_risk": 1,
            "low_risk": 1,
            "results": [...],
            "summary": {...}
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({'error': 'Missing emails parameter'}), 400
        
        emails = data['emails']
        
        if not isinstance(emails, list) or len(emails) == 0:
            return jsonify({'error': 'emails must be a non-empty array'}), 400
        
        if len(emails) > 1000:
            return jsonify({'error': 'Maximum 1000 emails per request'}), 400
        
        # Assess batch
        start_time = time.time()
        result = risk_scorer.batch_risk_assessment(emails)
        processing_time = time.time() - start_time
        
        result['processing_time'] = round(processing_time, 4)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/report/generate', methods=['POST'])
def generate_report():
    """
    Generate a formatted risk assessment report.
    
    Request:
        {
            "emails": ["user1@example.com", "user2@test.com"],
            "format": "text"  // or "json"
        }
    
    Response:
        Text report or JSON report
    """
    try:
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({'error': 'Missing emails parameter'}), 400
        
        emails = data['emails']
        format_type = data.get('format', 'text')
        
        if not isinstance(emails, list) or len(emails) == 0:
            return jsonify({'error': 'emails must be a non-empty array'}), 400
        
        # Assess all emails
        assessments = []
        for email in emails:
            assessment = risk_scorer.get_email_risk_from_db(email)
            assessments.append(assessment)
        
        if format_type == 'text':
            # Generate text report
            report = generate_risk_report(assessments)
            return Response(report, mimetype='text/plain')
        else:
            # Return JSON report
            return jsonify({
                'report_type': 'risk_assessment',
                'generated_at': datetime.utcnow().isoformat(),
                'total_emails': len(assessments),
                'assessments': assessments
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/risk/statistics', methods=['GET'])
def get_risk_statistics():
    """
    Get overall risk statistics from database.
    
    Response:
        {
            "total_emails": 1000,
            "high_risk_count": 50,
            "medium_risk_count": 200,
            "low_risk_count": 750,
            "spam_trap_count": 5,
            "blacklisted_count": 10,
            "avg_risk_score": 25.5
        }
    """
    try:
        storage = get_storage()
        
        # Get all records
        records = storage.get_all_records(limit=10000)
        
        if not records:
            return jsonify({
                'total_emails': 0,
                'message': 'No emails in database'
            })
        
        # Calculate statistics
        total = len(records)
        high_risk = 0
        medium_risk = 0
        low_risk = 0
        spam_traps = 0
        blacklisted = 0
        total_risk_score = 0
        
        for record in records:
            # Assess risk for each record
            assessment = risk_scorer.calculate_risk_score(record)
            
            if assessment['risk_level'] == 'HIGH':
                high_risk += 1
            elif assessment['risk_level'] == 'MEDIUM':
                medium_risk += 1
            else:
                low_risk += 1
            
            if assessment['is_spam_trap']:
                spam_traps += 1
            
            if assessment['is_blacklisted']:
                blacklisted += 1
            
            total_risk_score += assessment['risk_score']
        
        avg_risk_score = total_risk_score / total if total > 0 else 0
        
        return jsonify({
            'total_emails': total,
            'high_risk_count': high_risk,
            'medium_risk_count': medium_risk,
            'low_risk_count': low_risk,
            'spam_trap_count': spam_traps,
            'blacklisted_count': blacklisted,
            'avg_risk_score': round(avg_risk_score, 2),
            'risk_distribution': {
                'high': round(high_risk / total * 100, 2),
                'medium': round(medium_risk / total * 100, 2),
                'low': round(low_risk / total * 100, 2)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/risk/high-risk', methods=['POST'])
def get_high_risk_emails():
    """
    Get all high-risk emails from database.
    
    Request:
        {
            "limit": 100  // optional
        }
    
    Response:
        {
            "total": 50,
            "emails": [...]
        }
    """
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 100)
        
        storage = get_storage()
        
        # Get records with high bounce count or low confidence
        high_risk_records = storage.search_records(
            max_confidence=50,
            limit=limit
        )
        
        # Also get records with high bounce count
        bounced_records = storage.get_all_records(limit=limit)
        bounced_records = [r for r in bounced_records if r.get('bounce_count', 0) >= 3]
        
        # Combine and assess
        all_records = high_risk_records + bounced_records
        
        high_risk_emails = []
        for record in all_records:
            assessment = risk_scorer.calculate_risk_score(record)
            if assessment['risk_level'] == 'HIGH':
                high_risk_emails.append(assessment)
        
        return jsonify({
            'total': len(high_risk_emails),
            'emails': high_risk_emails
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
    print("Email Risk Scoring API")
    print("=" * 70)
    print("\nEndpoints:")
    print("  Risk Assessment:")
    print("    - POST /api/risk/assess")
    print("    - GET  /api/risk/<email>")
    print("    - POST /api/risk/batch")
    print("\n  Reporting:")
    print("    - POST /api/report/generate")
    print("    - GET  /api/risk/statistics")
    print("    - POST /api/risk/high-risk")
    print("\nFeatures:")
    print("  ✓ Bounce history analysis")
    print("  ✓ Spam trap detection")
    print("  ✓ Blacklist checking")
    print("  ✓ Risk scoring (0-100)")
    print("  ✓ Batch assessment")
    print("  ✓ Detailed reports")
    print("\n" + "=" * 70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5001)
