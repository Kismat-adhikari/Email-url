#!/usr/bin/env python3
"""
Bounce Webhook Handler
Receives bounce notifications from email service providers (SendGrid, Mailgun, etc.)
and records them in the bounce tracking system.
"""

from flask import Flask, request, jsonify
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from bounce_tracker import record_bounce
from supabase_storage import get_storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Webhook security tokens (add these to your .env file)
SENDGRID_WEBHOOK_SECRET = None  # Set in .env: SENDGRID_WEBHOOK_SECRET=your_secret
MAILGUN_WEBHOOK_SECRET = None   # Set in .env: MAILGUN_WEBHOOK_SECRET=your_secret

def verify_sendgrid_signature(payload: str, signature: str) -> bool:
    """
    Verify SendGrid webhook signature for security.
    
    Args:
        payload: Raw request body
        signature: X-Twilio-Email-Event-Webhook-Signature header
    
    Returns:
        bool: True if signature is valid
    """
    if not SENDGRID_WEBHOOK_SECRET:
        logger.warning("SendGrid webhook secret not configured - skipping verification")
        return True
    
    try:
        import hmac
        import hashlib
        import base64
        
        expected_signature = base64.b64encode(
            hmac.new(
                SENDGRID_WEBHOOK_SECRET.encode(),
                payload.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"SendGrid signature verification failed: {e}")
        return False


def verify_mailgun_signature(token: str, timestamp: str, signature: str) -> bool:
    """
    Verify Mailgun webhook signature for security.
    
    Args:
        token: Mailgun token
        timestamp: Request timestamp
        signature: Mailgun signature
    
    Returns:
        bool: True if signature is valid
    """
    if not MAILGUN_WEBHOOK_SECRET:
        logger.warning("Mailgun webhook secret not configured - skipping verification")
        return True
    
    try:
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            MAILGUN_WEBHOOK_SECRET.encode(),
            f"{timestamp}{token}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Mailgun signature verification failed: {e}")
        return False


@app.route('/webhook/sendgrid/bounce', methods=['POST'])
def handle_sendgrid_bounce():
    """
    Handle SendGrid bounce webhook.
    
    SendGrid sends bounce events in this format:
    [
        {
            "email": "user@example.com",
            "event": "bounce",
            "reason": "550 5.1.1 User unknown",
            "status": "5.1.1",
            "type": "bounce",
            "timestamp": 1513299569
        }
    ]
    """
    try:
        # Verify signature (optional but recommended)
        signature = request.headers.get('X-Twilio-Email-Event-Webhook-Signature')
        if signature and not verify_sendgrid_signature(request.get_data(as_text=True), signature):
            logger.warning("Invalid SendGrid signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        events = request.get_json()
        if not events:
            return jsonify({'error': 'No events received'}), 400
        
        processed_count = 0
        
        for event in events:
            if event.get('event') == 'bounce':
                email = event.get('email')
                reason = event.get('reason', 'Unknown bounce reason')
                status = event.get('status', '')
                
                if not email:
                    continue
                
                # Determine bounce type based on status code
                bounce_type = 'hard'
                if status.startswith('4'):  # 4xx = temporary failure
                    bounce_type = 'soft'
                elif status.startswith('5'):  # 5xx = permanent failure
                    bounce_type = 'hard'
                
                # Record the bounce
                bounce_record = record_bounce(
                    email=email,
                    bounce_type=bounce_type,
                    reason=f"SendGrid: {reason} (Status: {status})"
                )
                
                if 'error' not in bounce_record:
                    processed_count += 1
                    logger.info(f"Recorded SendGrid bounce for {email}: {reason}")
                else:
                    logger.error(f"Failed to record bounce for {email}: {bounce_record['error']}")
        
        return jsonify({
            'status': 'success',
            'processed': processed_count,
            'total_events': len(events)
        })
        
    except Exception as e:
        logger.error(f"SendGrid webhook error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/webhook/mailgun/bounce', methods=['POST'])
def handle_mailgun_bounce():
    """
    Handle Mailgun bounce webhook.
    
    Mailgun sends bounce events in this format:
    {
        "signature": {
            "token": "token",
            "timestamp": "timestamp",
            "signature": "signature"
        },
        "event-data": {
            "event": "failed",
            "severity": "permanent",
            "reason": "bounce",
            "recipient": "user@example.com",
            "delivery-status": {
                "message": "550 5.1.1 User unknown",
                "code": 550
            }
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Verify signature (optional but recommended)
        signature_data = data.get('signature', {})
        if signature_data:
            token = signature_data.get('token')
            timestamp = signature_data.get('timestamp')
            signature = signature_data.get('signature')
            
            if not verify_mailgun_signature(token, timestamp, signature):
                logger.warning("Invalid Mailgun signature")
                return jsonify({'error': 'Invalid signature'}), 401
        
        event_data = data.get('event-data', {})
        event_type = event_data.get('event')
        
        if event_type == 'failed' and event_data.get('reason') == 'bounce':
            email = event_data.get('recipient')
            severity = event_data.get('severity', 'permanent')
            delivery_status = event_data.get('delivery-status', {})
            message = delivery_status.get('message', 'Unknown bounce reason')
            code = delivery_status.get('code', 0)
            
            if not email:
                return jsonify({'error': 'No recipient email found'}), 400
            
            # Determine bounce type
            bounce_type = 'hard' if severity == 'permanent' else 'soft'
            
            # Record the bounce
            bounce_record = record_bounce(
                email=email,
                bounce_type=bounce_type,
                reason=f"Mailgun: {message} (Code: {code})"
            )
            
            if 'error' not in bounce_record:
                logger.info(f"Recorded Mailgun bounce for {email}: {message}")
                return jsonify({'status': 'success'})
            else:
                logger.error(f"Failed to record bounce for {email}: {bounce_record['error']}")
                return jsonify({'error': 'Failed to record bounce'}), 500
        
        # Not a bounce event, ignore
        return jsonify({'status': 'ignored', 'reason': 'Not a bounce event'})
        
    except Exception as e:
        logger.error(f"Mailgun webhook error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/webhook/generic/bounce', methods=['POST'])
def handle_generic_bounce():
    """
    Handle generic bounce webhook for custom integrations.
    
    Expected format:
    {
        "email": "user@example.com",
        "bounce_type": "hard|soft",
        "reason": "Bounce reason",
        "provider": "Custom ESP",
        "timestamp": "2023-12-11T10:00:00Z"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        email = data.get('email')
        bounce_type = data.get('bounce_type', 'hard')
        reason = data.get('reason', 'Generic bounce')
        provider = data.get('provider', 'Unknown')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if bounce_type not in ['hard', 'soft']:
            bounce_type = 'hard'
        
        # Record the bounce
        bounce_record = record_bounce(
            email=email,
            bounce_type=bounce_type,
            reason=f"{provider}: {reason}"
        )
        
        if 'error' not in bounce_record:
            logger.info(f"Recorded generic bounce for {email}: {reason}")
            return jsonify({'status': 'success'})
        else:
            logger.error(f"Failed to record bounce for {email}: {bounce_record['error']}")
            return jsonify({'error': 'Failed to record bounce'}), 500
        
    except Exception as e:
        logger.error(f"Generic webhook error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/webhook/test', methods=['POST'])
def test_webhook():
    """
    Test endpoint to manually record a bounce for testing.
    
    Usage:
    curl -X POST http://localhost:5000/webhook/test \
         -H "Content-Type: application/json" \
         -d '{"email": "test@example.com", "bounce_type": "hard", "reason": "Test bounce"}'
    """
    try:
        data = request.get_json()
        email = data.get('email', 'test@example.com')
        bounce_type = data.get('bounce_type', 'hard')
        reason = data.get('reason', 'Test bounce for development')
        
        bounce_record = record_bounce(email, bounce_type, reason)
        
        if 'error' not in bounce_record:
            return jsonify({
                'status': 'success',
                'message': f'Test bounce recorded for {email}',
                'bounce_record': bounce_record
            })
        else:
            return jsonify({'error': bounce_record['error']}), 500
            
    except Exception as e:
        logger.error(f"Test webhook error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/webhook/stats', methods=['GET'])
def webhook_stats():
    """
    Get bounce statistics for monitoring.
    """
    try:
        storage = get_storage()
        
        # Get recent bounce statistics
        # This would need to be implemented in supabase_storage.py
        stats = {
            'status': 'Bounce webhook service is running',
            'endpoints': [
                '/webhook/sendgrid/bounce',
                '/webhook/mailgun/bounce', 
                '/webhook/generic/bounce',
                '/webhook/test'
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Load environment variables
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    global SENDGRID_WEBHOOK_SECRET, MAILGUN_WEBHOOK_SECRET
    SENDGRID_WEBHOOK_SECRET = os.getenv('SENDGRID_WEBHOOK_SECRET')
    MAILGUN_WEBHOOK_SECRET = os.getenv('MAILGUN_WEBHOOK_SECRET')
    
    print("🚀 Bounce Webhook Service Starting...")
    print("📧 Endpoints available:")
    print("   POST /webhook/sendgrid/bounce  - SendGrid bounces")
    print("   POST /webhook/mailgun/bounce   - Mailgun bounces") 
    print("   POST /webhook/generic/bounce   - Generic bounces")
    print("   POST /webhook/test             - Test endpoint")
    print("   GET  /webhook/stats            - Service stats")
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=True)