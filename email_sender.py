#!/usr/bin/env python3
"""
Email Sending Service
Handles email composition and delivery through SendGrid
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
import base64
import logging

logger = logging.getLogger(__name__)

class EmailSender:
    """
    Email sending service using SendGrid.
    
    Features:
    - Single and batch email sending
    - HTML and plain text content
    - File attachments
    - Delivery tracking
    - Template support
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize SendGrid client.
        
        Args:
            api_key: SendGrid API key (defaults to env variable)
        """
        self.api_key = api_key or os.getenv('SENDGRID_API_KEY')
        
        if not self.api_key:
            raise ValueError("SendGrid API key is required. Set SENDGRID_API_KEY environment variable.")
        
        self.sg = SendGridAPIClient(api_key=self.api_key)
        
        # Default sender info
        self.default_from_email = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com')
        self.default_from_name = os.getenv('DEFAULT_FROM_NAME', 'Email Platform')
    
    def send_single_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        content_type: str = 'text/html',
        from_email: str = None,
        from_name: str = None,
        attachments: List[Dict] = None,
        track_bounces: bool = True
    ) -> Dict[str, Any]:
        """
        Send a single email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email content (HTML or plain text)
            content_type: 'text/html' or 'text/plain'
            from_email: Sender email (optional)
            from_name: Sender name (optional)
            attachments: List of attachment dicts (optional)
        
        Returns:
            Dictionary with send result
        
        Example:
            >>> sender = EmailSender()
            >>> result = sender.send_single_email(
            ...     to_email="user@example.com",
            ...     subject="Welcome!",
            ...     content="<h1>Hello World!</h1>"
            ... )
            >>> print(result['success'])
            True
        """
        try:
            # Set sender info
            from_email = from_email or self.default_from_email
            from_name = from_name or self.default_from_name
            
            # Create email
            message = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content(content_type, content)
            )
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    self._add_attachment(message, attachment)
            
            # Send email
            response = self.sg.send(message)
            
            # Log success
            logger.info(f"Email sent successfully to {to_email}. Status: {response.status_code}")
            
            # Return success result
            return {
                'success': True,
                'message_id': response.headers.get('X-Message-Id'),
                'status_code': response.status_code,
                'to_email': to_email,
                'subject': subject,
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'to_email': to_email,
                'subject': subject,
                'failed_at': datetime.utcnow().isoformat()
            }
    
    def send_batch_emails(
        self,
        recipients: List[str],
        subject: str,
        content: str,
        content_type: str = 'text/html',
        from_email: str = None,
        from_name: str = None,
        max_batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Send emails to multiple recipients.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            content: Email content
            content_type: 'text/html' or 'text/plain'
            from_email: Sender email (optional)
            from_name: Sender name (optional)
            max_batch_size: Maximum emails per batch (SendGrid limit: 1000)
        
        Returns:
            Dictionary with batch send results
        """
        try:
            # Validate recipients
            if not recipients:
                return {
                    'success': False,
                    'error': 'No recipients provided',
                    'total_recipients': 0
                }
            
            # Set sender info
            from_email = from_email or self.default_from_email
            from_name = from_name or self.default_from_name
            
            # Split into batches if needed
            batches = [recipients[i:i + max_batch_size] 
                      for i in range(0, len(recipients), max_batch_size)]
            
            total_sent = 0
            total_failed = 0
            batch_results = []
            
            for batch_num, batch_recipients in enumerate(batches, 1):
                try:
                    # Create batch message
                    message = Mail(
                        from_email=Email(from_email, from_name),
                        to_emails=[To(email) for email in batch_recipients],
                        subject=subject,
                        html_content=Content(content_type, content)
                    )
                    
                    # Send batch
                    response = self.sg.send(message)
                    
                    batch_result = {
                        'batch_number': batch_num,
                        'recipients_count': len(batch_recipients),
                        'status_code': response.status_code,
                        'message_id': response.headers.get('X-Message-Id'),
                        'success': True
                    }
                    
                    total_sent += len(batch_recipients)
                    logger.info(f"Batch {batch_num} sent successfully: {len(batch_recipients)} emails")
                    
                except Exception as batch_error:
                    batch_result = {
                        'batch_number': batch_num,
                        'recipients_count': len(batch_recipients),
                        'error': str(batch_error),
                        'success': False
                    }
                    
                    total_failed += len(batch_recipients)
                    logger.error(f"Batch {batch_num} failed: {str(batch_error)}")
                
                batch_results.append(batch_result)
            
            return {
                'success': total_sent > 0,
                'total_recipients': len(recipients),
                'total_sent': total_sent,
                'total_failed': total_failed,
                'batches_processed': len(batches),
                'batch_results': batch_results,
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch email sending failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total_recipients': len(recipients) if recipients else 0,
                'failed_at': datetime.utcnow().isoformat()
            }
    
    def _add_attachment(self, message: Mail, attachment_info: Dict):
        """
        Add attachment to email message.
        
        Args:
            message: SendGrid Mail object
            attachment_info: Dict with 'content', 'filename', 'type'
        """
        try:
            attachment = Attachment(
                FileContent(attachment_info['content']),
                FileName(attachment_info['filename']),
                FileType(attachment_info.get('type', 'application/octet-stream')),
                Disposition('attachment')
            )
            message.attachment = attachment
            
        except Exception as e:
            logger.warning(f"Failed to add attachment: {str(e)}")
    
    def _record_email_send(self, email: str, subject: str, message_id: str):
        """
        Record email send for bounce tracking.
        
        Args:
            email: Recipient email
            subject: Email subject
            message_id: SendGrid message ID
        """
        try:
            from supabase_storage import get_storage
            
            storage = get_storage()
            
            send_record = {
                'email': email,
                'subject': subject,
                'message_id': message_id,
                'status': 'sent',
                'sent_at': datetime.utcnow().isoformat(),
                'bounce_count': 0,
                'bounced': False
            }
            
            # Store in email_sends table (we'll create this)
            # For now, we can store in the main validation table
            storage.store_validation_result(send_record)
            
        except Exception as e:
            logger.warning(f"Failed to record email send: {e}")
    
    def record_bounce(self, email: str, bounce_type: str, reason: str, message_id: str = None):
        """
        Record a bounce for an email that was sent.
        
        Args:
            email: Email that bounced
            bounce_type: 'hard' or 'soft'
            reason: Bounce reason
            message_id: Original message ID (optional)
        """
        try:
            from supabase_storage import get_storage
            
            storage = get_storage()
            
            # Get existing bounce count
            history = storage.get_email_history(email)
            existing_bounces = len([h for h in history if h.get('bounced', False)])
            
            bounce_record = {
                'email': email,
                'valid': False,  # Bounced emails are invalid
                'bounced': True,
                'bounce_type': bounce_type,
                'bounce_reason': reason,
                'bounce_count': existing_bounces + 1,
                'last_bounce_date': datetime.utcnow().isoformat(),
                'message_id': message_id,
                'validated_at': datetime.utcnow().isoformat(),
                'confidence_score': 0,
                'risk_score': 100 if bounce_type == 'hard' else 75
            }
            
            result = storage.store_validation_result(bounce_record)
            
            if result.get('success'):
                logger.info(f"Bounce recorded: {email} ({bounce_type}) - {reason}")
                return {
                    'success': True,
                    'bounce_count': existing_bounces + 1,
                    'email': email,
                    'bounce_type': bounce_type
                }
            else:
                return {'success': False, 'error': 'Failed to store bounce'}
                
        except Exception as e:
            logger.error(f"Failed to record bounce: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_bounce_history(self, email: str) -> Dict[str, Any]:
        """
        Check bounce history for an email before sending.
        
        Args:
            email: Email to check
            
        Returns:
            Dictionary with bounce history and risk assessment
        """
        try:
            from supabase_storage import get_storage
            
            storage = get_storage()
            history = storage.get_email_history(email)
            
            bounces = [h for h in history if h.get('bounced', False)]
            hard_bounces = [b for b in bounces if b.get('bounce_type') == 'hard']
            
            total_bounces = len(bounces)
            hard_bounce_count = len(hard_bounces)
            
            # Determine risk level
            if hard_bounce_count > 0:
                risk_level = 'critical'
                safe_to_send = False
                warning = f'Email has {hard_bounce_count} hard bounce(s) - DO NOT SEND'
            elif total_bounces >= 3:
                risk_level = 'high'
                safe_to_send = False
                warning = f'Email has bounced {total_bounces} times - High risk'
            elif total_bounces >= 1:
                risk_level = 'medium'
                safe_to_send = True
                warning = f'Email has bounced {total_bounces} time(s) - Use caution'
            else:
                risk_level = 'low'
                safe_to_send = True
                warning = None
            
            return {
                'total_bounces': total_bounces,
                'hard_bounces': hard_bounce_count,
                'soft_bounces': total_bounces - hard_bounce_count,
                'risk_level': risk_level,
                'safe_to_send': safe_to_send,
                'warning': warning,
                'has_bounced': total_bounces > 0,
                'last_bounce': bounces[-1].get('last_bounce_date') if bounces else None
            }
            
        except Exception as e:
            logger.error(f"Failed to check bounce history: {e}")
            return {
                'total_bounces': 0,
                'hard_bounces': 0,
                'soft_bounces': 0,
                'risk_level': 'unknown',
                'safe_to_send': True,
                'warning': None,
                'has_bounced': False,
                'error': str(e)
            }
    
    def get_delivery_stats(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Get email delivery statistics from SendGrid.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dictionary with delivery statistics
        """
        try:
            # This would use SendGrid's Stats API
            # For now, return placeholder data
            return {
                'delivered': 0,
                'bounced': 0,
                'opened': 0,
                'clicked': 0,
                'unsubscribed': 0,
                'spam_reports': 0,
                'delivery_rate': 0.0,
                'open_rate': 0.0,
                'click_rate': 0.0
            }
            
        except Exception as e:
            logger.error(f"Failed to get delivery stats: {str(e)}")
            return {
                'error': str(e),
                'delivered': 0,
                'bounced': 0
            }
    
    def validate_api_key(self) -> Dict[str, Any]:
        """
        Validate SendGrid API key by making a test request.
        
        Returns:
            Dictionary with validation result
        """
        try:
            # Test API key by getting account info
            response = self.sg.client.user.get()
            
            if response.status_code == 200:
                user_data = json.loads(response.body)
                return {
                    'valid': True,
                    'username': user_data.get('username', 'Unknown'),
                    'email': user_data.get('email', 'Unknown'),
                    'status': 'API key is valid'
                }
            else:
                return {
                    'valid': False,
                    'error': f'API validation failed: {response.status_code}',
                    'status': 'Invalid API key'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'status': 'API key validation failed'
            }


# Convenience function
def get_email_sender() -> EmailSender:
    """
    Get configured EmailSender instance.
    
    Returns:
        EmailSender instance
    
    Example:
        >>> sender = get_email_sender()
        >>> result = sender.send_single_email("user@example.com", "Test", "Hello!")
    """
    return EmailSender()


# Email templates
EMAIL_TEMPLATES = {
    'welcome': {
        'subject': 'Welcome to Email Platform!',
        'content': '''
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #667eea;">Welcome!</h1>
            <p>Thank you for joining our email platform.</p>
            <p>You can now validate and send emails with ease.</p>
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>Getting Started:</h3>
                <ul>
                    <li>Validate your email lists</li>
                    <li>Compose and send campaigns</li>
                    <li>Track delivery results</li>
                </ul>
            </div>
            <p>Best regards,<br>The Email Platform Team</p>
        </body>
        </html>
        '''
    },
    
    'notification': {
        'subject': 'Email Campaign Results',
        'content': '''
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #667eea;">Campaign Results</h2>
            <p>Your email campaign has been completed.</p>
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px;">
                <p><strong>Emails Sent:</strong> {emails_sent}</p>
                <p><strong>Delivery Rate:</strong> {delivery_rate}%</p>
                <p><strong>Open Rate:</strong> {open_rate}%</p>
            </div>
            <p>View detailed analytics in your dashboard.</p>
        </body>
        </html>
        '''
    }
}


if __name__ == "__main__":
    # Test the email sender
    sender = EmailSender()
    
    # Validate API key
    validation = sender.validate_api_key()
    print(f"API Key Status: {validation}")
    
    if validation.get('valid'):
        print("✅ SendGrid integration ready!")
    else:
        print("❌ SendGrid API key not configured")
        print("Set SENDGRID_API_KEY environment variable")