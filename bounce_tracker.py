#!/usr/bin/env python3
"""
Bounce Tracking System
Track which emails bounce and build historical data
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from supabase_storage import get_storage

def record_bounce(email: str, bounce_type: str = 'hard', reason: str = None) -> Dict[str, Any]:
    """
    Record an email bounce.
    
    Args:
        email: Email address that bounced
        bounce_type: 'hard' (permanent) or 'soft' (temporary)
        reason: Reason for bounce
    
    Returns:
        Dictionary with bounce record
    """
    try:
        storage = get_storage()
        
        # Get existing bounce count
        history = storage.get_email_history(email)
        bounce_count = len([h for h in history if h.get('bounced', False)])
        
        # Create bounce record
        bounce_record = {
            'email': email,
            'bounced': True,
            'bounce_type': bounce_type,
            'bounce_reason': reason,
            'bounce_count': bounce_count + 1,
            'bounced_at': datetime.utcnow().isoformat()
        }
        
        return bounce_record
    except Exception as e:
        return {'error': str(e)}


def get_bounce_history(email: str) -> Dict[str, Any]:
    """
    Get bounce history for an email.
    
    Args:
        email: Email address
    
    Returns:
        Dictionary with:
            - total_bounces: int
            - hard_bounces: int
            - soft_bounces: int
            - last_bounce: datetime or None
            - bounce_rate: float (0-1)
            - status: str (safe/warning/danger)
    """
    try:
        storage = get_storage()
        history = storage.get_email_history(email)
        
        bounces = [h for h in history if h.get('bounced', False)]
        hard_bounces = [b for b in bounces if b.get('bounce_type') == 'hard']
        soft_bounces = [b for b in bounces if b.get('bounce_type') == 'soft']
        
        total_validations = len(history)
        total_bounces = len(bounces)
        
        bounce_rate = total_bounces / total_validations if total_validations > 0 else 0
        
        # Determine status
        if len(hard_bounces) > 0:
            status = 'danger'
        elif total_bounces >= 3:
            status = 'danger'
        elif total_bounces >= 1:
            status = 'warning'
        else:
            status = 'safe'
        
        last_bounce = None
        if bounces:
            last_bounce = bounces[-1].get('bounced_at')
        
        return {
            'total_bounces': total_bounces,
            'hard_bounces': len(hard_bounces),
            'soft_bounces': len(soft_bounces),
            'last_bounce': last_bounce,
            'bounce_rate': round(bounce_rate, 2),
            'status': status,
            'has_bounced': total_bounces > 0
        }
    except Exception as e:
        return {
            'total_bounces': 0,
            'hard_bounces': 0,
            'soft_bounces': 0,
            'last_bounce': None,
            'bounce_rate': 0,
            'status': 'unknown',
            'has_bounced': False,
            'error': str(e)
        }


def check_bounce_risk(email: str) -> Dict[str, Any]:
    """
    Check if email has bounce history and assess risk.
    
    Args:
        email: Email address
    
    Returns:
        Dictionary with risk assessment
    """
    bounce_history = get_bounce_history(email)
    
    total_bounces = bounce_history['total_bounces']
    hard_bounces = bounce_history['hard_bounces']
    status = bounce_history['status']
    
    # Assess risk
    if hard_bounces > 0:
        risk_level = 'critical'
        warning = f'Email has {hard_bounces} hard bounce(s) - DO NOT SEND'
        safe_to_send = False
    elif total_bounces >= 3:
        risk_level = 'high'
        warning = f'Email has bounced {total_bounces} times - High risk'
        safe_to_send = False
    elif total_bounces >= 1:
        risk_level = 'medium'
        warning = f'Email has bounced {total_bounces} time(s) - Use caution'
        safe_to_send = True
    else:
        risk_level = 'low'
        warning = None
        safe_to_send = True
    
    return {
        'bounce_history': bounce_history,
        'risk_level': risk_level,
        'warning': warning,
        'safe_to_send': safe_to_send,
        'recommendation': 'Do not send' if not safe_to_send else 'Safe to send'
    }
