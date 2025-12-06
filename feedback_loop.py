#!/usr/bin/env python3
"""
Email Feedback Loop System
Accept bounce/delivery feedback and automatically update confidence/risk scores
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from supabase_storage import get_storage
from risk_scoring import RiskScorer
from email_validator_smtp import validate_email_with_smtp
from apscheduler.schedulers.background import BackgroundScheduler
import time


class FeedbackLoop:
    """
    Email feedback loop manager.
    
    Handles:
    - Bounce feedback (hard/soft bounces)
    - Delivery feedback (successful deliveries)
    - Complaint feedback (spam complaints)
    - Automatic score updates
    - Scheduled re-verification
    """
    
    def __init__(self):
        """Initialize feedback loop."""
        self.storage = None
        try:
            self.storage = get_storage()
        except:
            pass
        
        self.risk_scorer = RiskScorer()
        self.scheduler = BackgroundScheduler()
    
    def process_bounce(
        self,
        email: str,
        bounce_type: str,
        bounce_reason: str = None,
        timestamp: str = None
    ) -> Dict[str, Any]:
        """
        Process bounce feedback.
        
        Args:
            email: Email address that bounced
            bounce_type: 'hard' or 'soft'
            bounce_reason: Reason for bounce (optional)
            timestamp: Bounce timestamp (optional)
        
        Returns:
            Dictionary with:
                - success: bool
                - email: str
                - bounce_count: int
                - confidence_score: int (updated)
                - risk_score: int (updated)
                - action_taken: str
        
        Example:
            >>> loop = FeedbackLoop()
            >>> result = loop.process_bounce(
            ...     'user@example.com',
            ...     'hard',
            ...     'Mailbox does not exist'
            ... )
            >>> print(result['action_taken'])
            'Marked as invalid'
        """
        if not self.storage:
            return {
                'success': False,
                'error': 'Storage not available'
            }
        
        try:
            # Get current record
            record = self.storage.get_record_by_email(email)
            
            if not record:
                return {
                    'success': False,
                    'error': 'Email not found in database',
                    'email': email,
                    'recommendation': 'Validate email first'
                }
            
            # Increment bounce count
            updated_record = self.storage.increment_bounce_count(email)
            bounce_count = updated_record['bounce_count']
            
            # Determine action based on bounce type and count
            action_taken = None
            new_confidence = record.get('confidence_score', 50)
            mark_invalid = False
            
            if bounce_type == 'hard':
                # Hard bounce = mailbox doesn't exist
                new_confidence = 0
                mark_invalid = True
                action_taken = 'Marked as invalid (hard bounce)'
            elif bounce_type == 'soft':
                # Soft bounce = temporary issue
                if bounce_count >= 3:
                    # Too many soft bounces
                    new_confidence = max(0, new_confidence - 30)
                    mark_invalid = True
                    action_taken = 'Marked as invalid (repeated soft bounces)'
                else:
                    # Reduce confidence
                    new_confidence = max(0, new_confidence - 15)
                    action_taken = f'Reduced confidence (soft bounce #{bounce_count})'
            
            # Update record
            updates = {
                'confidence_score': new_confidence,
                'notes': f"{bounce_type.upper()} BOUNCE: {bounce_reason or 'No reason provided'}"
            }
            
            if mark_invalid:
                updates['valid'] = False
            
            self.storage.update_record(record['id'], updates)
            
            # Recalculate risk score
            updated_record = self.storage.get_record_by_email(email)
            risk_assessment = self.risk_scorer.calculate_risk_score(updated_record)
            
            return {
                'success': True,
                'email': email,
                'bounce_type': bounce_type,
                'bounce_count': bounce_count,
                'confidence_score': new_confidence,
                'risk_score': risk_assessment['risk_score'],
                'risk_level': risk_assessment['risk_level'],
                'action_taken': action_taken,
                'marked_invalid': mark_invalid,
                'processed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'email': email
            }
    
    def process_delivery(
        self,
        email: str,
        delivery_status: str = 'delivered',
        timestamp: str = None
    ) -> Dict[str, Any]:
        """
        Process successful delivery feedback.
        
        Args:
            email: Email address that was delivered
            delivery_status: 'delivered', 'opened', 'clicked'
            timestamp: Delivery timestamp (optional)
        
        Returns:
            Dictionary with processing result
        
        Example:
            >>> loop = FeedbackLoop()
            >>> result = loop.process_delivery('user@example.com', 'delivered')
            >>> print(result['action_taken'])
            'Increased confidence'
        """
        if not self.storage:
            return {
                'success': False,
                'error': 'Storage not available'
            }
        
        try:
            # Get current record
            record = self.storage.get_record_by_email(email)
            
            if not record:
                return {
                    'success': False,
                    'error': 'Email not found in database',
                    'email': email
                }
            
            # Increase confidence based on delivery status
            current_confidence = record.get('confidence_score', 50)
            
            if delivery_status == 'delivered':
                new_confidence = min(100, current_confidence + 5)
                action = 'Increased confidence (delivery confirmed)'
            elif delivery_status == 'opened':
                new_confidence = min(100, current_confidence + 10)
                action = 'Increased confidence (email opened)'
            elif delivery_status == 'clicked':
                new_confidence = min(100, current_confidence + 15)
                action = 'Increased confidence (link clicked)'
            else:
                new_confidence = current_confidence
                action = 'No change'
            
            # Update record
            updates = {
                'confidence_score': new_confidence,
                'valid': True,  # Confirmed valid
                'notes': f"DELIVERY: {delivery_status}"
            }
            
            self.storage.update_record(record['id'], updates)
            
            return {
                'success': True,
                'email': email,
                'delivery_status': delivery_status,
                'confidence_score': new_confidence,
                'action_taken': action,
                'processed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'email': email
            }
    
    def process_complaint(
        self,
        email: str,
        complaint_type: str = 'spam',
        timestamp: str = None
    ) -> Dict[str, Any]:
        """
        Process spam complaint feedback.
        
        Args:
            email: Email address that complained
            complaint_type: 'spam', 'abuse', 'other'
            timestamp: Complaint timestamp (optional)
        
        Returns:
            Dictionary with processing result
        """
        if not self.storage:
            return {
                'success': False,
                'error': 'Storage not available'
            }
        
        try:
            # Get current record
            record = self.storage.get_record_by_email(email)
            
            if not record:
                return {
                    'success': False,
                    'error': 'Email not found in database',
                    'email': email
                }
            
            # Severely reduce confidence
            new_confidence = 0
            
            # Update record
            updates = {
                'confidence_score': new_confidence,
                'notes': f"COMPLAINT: {complaint_type} - Remove from all lists"
            }
            
            self.storage.update_record(record['id'], updates)
            
            return {
                'success': True,
                'email': email,
                'complaint_type': complaint_type,
                'confidence_score': new_confidence,
                'action_taken': 'Marked for removal (spam complaint)',
                'processed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'email': email
            }
    
    def batch_process_feedback(
        self,
        feedback_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process multiple feedback events.
        
        Args:
            feedback_list: List of feedback dictionaries with:
                - email: str
                - type: 'bounce', 'delivery', 'complaint'
                - bounce_type: str (for bounces)
                - delivery_status: str (for deliveries)
                - complaint_type: str (for complaints)
        
        Returns:
            Dictionary with batch processing results
        
        Example:
            >>> feedback = [
            ...     {'email': 'user1@example.com', 'type': 'bounce', 'bounce_type': 'hard'},
            ...     {'email': 'user2@example.com', 'type': 'delivery', 'delivery_status': 'delivered'}
            ... ]
            >>> result = loop.batch_process_feedback(feedback)
        """
        results = {
            'total': len(feedback_list),
            'processed': 0,
            'bounces': 0,
            'deliveries': 0,
            'complaints': 0,
            'errors': 0,
            'results': []
        }
        
        for feedback in feedback_list:
            email = feedback.get('email')
            feedback_type = feedback.get('type')
            
            if feedback_type == 'bounce':
                result = self.process_bounce(
                    email,
                    feedback.get('bounce_type', 'soft'),
                    feedback.get('bounce_reason')
                )
                if result['success']:
                    results['bounces'] += 1
            elif feedback_type == 'delivery':
                result = self.process_delivery(
                    email,
                    feedback.get('delivery_status', 'delivered')
                )
                if result['success']:
                    results['deliveries'] += 1
            elif feedback_type == 'complaint':
                result = self.process_complaint(
                    email,
                    feedback.get('complaint_type', 'spam')
                )
                if result['success']:
                    results['complaints'] += 1
            else:
                result = {
                    'success': False,
                    'error': f'Unknown feedback type: {feedback_type}',
                    'email': email
                }
            
            if result['success']:
                results['processed'] += 1
            else:
                results['errors'] += 1
            
            results['results'].append(result)
        
        return results
    
    def schedule_reverification(
        self,
        days_old: int = 30,
        max_emails: int = 100
    ) -> Dict[str, Any]:
        """
        Schedule re-verification of old emails.
        
        Args:
            days_old: Re-verify emails older than this many days
            max_emails: Maximum emails to re-verify per run
        
        Returns:
            Dictionary with scheduling result
        """
        if not self.storage:
            return {
                'success': False,
                'error': 'Storage not available'
            }
        
        try:
            # Get old records
            all_records = self.storage.get_all_records(limit=1000)
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_records = []
            for record in all_records:
                validated_at = record.get('validated_at')
                if validated_at:
                    try:
                        validated_date = datetime.fromisoformat(validated_at.replace('Z', '+00:00'))
                        if validated_date < cutoff_date:
                            old_records.append(record)
                    except:
                        pass
            
            # Limit to max_emails
            emails_to_reverify = old_records[:max_emails]
            
            return {
                'success': True,
                'total_old_emails': len(old_records),
                'scheduled_for_reverification': len(emails_to_reverify),
                'emails': [r['email'] for r in emails_to_reverify],
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def reverify_email(self, email: str) -> Dict[str, Any]:
        """
        Re-verify a single email and update scores.
        
        Args:
            email: Email to re-verify
        
        Returns:
            Dictionary with re-verification result
        """
        try:
            # Re-validate email
            validation_result = validate_email_with_smtp(
                email,
                enable_smtp=False,  # Disable SMTP for speed
                check_dns=True,
                check_mx=True
            )
            
            # Store new validation
            if self.storage:
                record = self.storage.create_record({
                    'email': email,
                    'valid': validation_result['valid'],
                    'confidence_score': validation_result['confidence_score'],
                    'checks': validation_result['checks'],
                    'notes': 'Automatic re-verification'
                })
                
                return {
                    'success': True,
                    'email': email,
                    'valid': validation_result['valid'],
                    'confidence_score': validation_result['confidence_score'],
                    'reverified_at': datetime.utcnow().isoformat()
                }
            else:
                return validation_result
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'email': email
            }
    
    def batch_reverify(
        self,
        emails: List[str],
        delay_seconds: int = 1
    ) -> Dict[str, Any]:
        """
        Re-verify multiple emails with delay between requests.
        
        Args:
            emails: List of emails to re-verify
            delay_seconds: Delay between verifications
        
        Returns:
            Dictionary with batch re-verification results
        """
        results = {
            'total': len(emails),
            'successful': 0,
            'failed': 0,
            'results': []
        }
        
        for email in emails:
            result = self.reverify_email(email)
            
            if result.get('success', result.get('valid', False)):
                results['successful'] += 1
            else:
                results['failed'] += 1
            
            results['results'].append(result)
            
            # Delay to avoid rate limiting
            if delay_seconds > 0:
                time.sleep(delay_seconds)
        
        return results
    
    def start_scheduled_reverification(
        self,
        interval_hours: int = 24,
        days_old: int = 30,
        max_emails: int = 100
    ):
        """
        Start scheduled automatic re-verification.
        
        Args:
            interval_hours: Run every X hours
            days_old: Re-verify emails older than X days
            max_emails: Max emails per run
        """
        def reverify_job():
            """Background job for re-verification."""
            print(f"[{datetime.utcnow()}] Starting scheduled re-verification...")
            
            # Get emails to re-verify
            schedule_result = self.schedule_reverification(days_old, max_emails)
            
            if schedule_result['success']:
                emails = schedule_result['emails']
                print(f"Re-verifying {len(emails)} emails...")
                
                # Re-verify
                reverify_result = self.batch_reverify(emails, delay_seconds=2)
                
                print(f"Re-verification complete: {reverify_result['successful']} successful, {reverify_result['failed']} failed")
            else:
                print(f"Failed to schedule re-verification: {schedule_result.get('error')}")
        
        # Schedule job
        self.scheduler.add_job(
            reverify_job,
            'interval',
            hours=interval_hours,
            id='reverification_job',
            replace_existing=True
        )
        
        if not self.scheduler.running:
            self.scheduler.start()
        
        print(f"Scheduled re-verification: every {interval_hours} hours, emails older than {days_old} days")
    
    def stop_scheduled_reverification(self):
        """Stop scheduled re-verification."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("Stopped scheduled re-verification")


# Convenience functions
def process_bounce(email: str, bounce_type: str, reason: str = None) -> Dict[str, Any]:
    """Quick bounce processing."""
    loop = FeedbackLoop()
    return loop.process_bounce(email, bounce_type, reason)


def process_delivery(email: str, status: str = 'delivered') -> Dict[str, Any]:
    """Quick delivery processing."""
    loop = FeedbackLoop()
    return loop.process_delivery(email, status)
