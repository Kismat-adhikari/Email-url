#!/usr/bin/env python3
"""
Webhook and CRM/ESP Integration Module
Push email validation results to external systems
"""

import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import hmac
import hashlib


class WebhookManager:
    """
    Manage webhook deliveries to external systems.
    
    Supports:
    - Generic webhooks
    - CRM systems (Salesforce, HubSpot)
    - ESP systems (SendGrid, Mailchimp)
    """
    
    def __init__(self, webhook_url: str = None, secret: str = None):
        """
        Initialize webhook manager.
        
        Args:
            webhook_url: Target webhook URL
            secret: Secret key for HMAC signature (optional)
        """
        self.webhook_url = webhook_url
        self.secret = secret
    
    def send_webhook(
        self,
        data: Dict[str, Any],
        url: str = None,
        headers: Dict[str, str] = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Send data to webhook endpoint.
        
        Args:
            data: Data to send
            url: Webhook URL (overrides default)
            headers: Custom headers
            timeout: Request timeout in seconds
        
        Returns:
            Dictionary with:
                - success: bool
                - status_code: int
                - response: dict or str
                - error: str (if failed)
        
        Example:
            >>> manager = WebhookManager('https://example.com/webhook')
            >>> result = manager.send_webhook({
            ...     'email': 'user@example.com',
            ...     'valid': True,
            ...     'confidence_score': 95
            ... })
            >>> print(result['success'])
            True
        """
        target_url = url or self.webhook_url
        
        if not target_url:
            return {
                'success': False,
                'error': 'No webhook URL configured'
            }
        
        try:
            # Prepare payload
            payload = {
                'event': 'email.validated',
                'timestamp': datetime.utcnow().isoformat(),
                'data': data
            }
            
            # Prepare headers
            request_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'EmailValidator-Webhook/1.0'
            }
            
            # Add HMAC signature if secret is configured
            if self.secret:
                signature = self._generate_signature(payload)
                request_headers['X-Webhook-Signature'] = signature
            
            # Merge custom headers
            if headers:
                request_headers.update(headers)
            
            # Send request
            response = requests.post(
                target_url,
                json=payload,
                headers=request_headers,
                timeout=timeout
            )
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'response': response_data,
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout',
                'sent_at': datetime.utcnow().isoformat()
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error',
                'sent_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'sent_at': datetime.utcnow().isoformat()
            }
    
    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """
        Generate HMAC signature for webhook payload.
        
        Args:
            payload: Payload to sign
        
        Returns:
            HMAC signature (hex)
        """
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def send_batch_webhook(
        self,
        results: List[Dict[str, Any]],
        url: str = None
    ) -> Dict[str, Any]:
        """
        Send batch validation results to webhook.
        
        Args:
            results: List of validation results
            url: Webhook URL
        
        Returns:
            Webhook delivery result
        """
        payload = {
            'total': len(results),
            'valid_count': sum(1 for r in results if r.get('valid')),
            'invalid_count': sum(1 for r in results if not r.get('valid')),
            'results': results
        }
        
        return self.send_webhook(payload, url=url)


class CRMIntegration:
    """
    Integration with CRM systems.
    
    Supports:
    - Salesforce
    - HubSpot
    - Pipedrive
    - Generic CRM
    """
    
    def __init__(self, crm_type: str, api_key: str, api_url: str = None):
        """
        Initialize CRM integration.
        
        Args:
            crm_type: CRM type ('salesforce', 'hubspot', 'pipedrive', 'generic')
            api_key: API key or access token
            api_url: API base URL (optional)
        """
        self.crm_type = crm_type.lower()
        self.api_key = api_key
        self.api_url = api_url
    
    def update_contact(
        self,
        email: str,
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update contact in CRM with validation data.
        
        Args:
            email: Email address
            validation_data: Validation results
        
        Returns:
            Update result
        """
        if self.crm_type == 'salesforce':
            return self._update_salesforce(email, validation_data)
        elif self.crm_type == 'hubspot':
            return self._update_hubspot(email, validation_data)
        elif self.crm_type == 'pipedrive':
            return self._update_pipedrive(email, validation_data)
        else:
            return self._update_generic(email, validation_data)
    
    def _update_salesforce(
        self,
        email: str,
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update Salesforce contact."""
        # Salesforce API integration
        # In production, use salesforce-python library
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'Email': email,
            'Email_Valid__c': validation_data.get('valid'),
            'Email_Confidence__c': validation_data.get('confidence_score'),
            'Email_Validated_At__c': datetime.utcnow().isoformat()
        }
        
        try:
            # Placeholder for actual Salesforce API call
            return {
                'success': True,
                'crm': 'salesforce',
                'message': 'Contact updated (simulated)'
            }
        except Exception as e:
            return {
                'success': False,
                'crm': 'salesforce',
                'error': str(e)
            }
    
    def _update_hubspot(
        self,
        email: str,
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update HubSpot contact."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'properties': {
                'email': email,
                'email_valid': validation_data.get('valid'),
                'email_confidence_score': validation_data.get('confidence_score'),
                'email_validated_at': datetime.utcnow().isoformat()
            }
        }
        
        try:
            # Placeholder for actual HubSpot API call
            return {
                'success': True,
                'crm': 'hubspot',
                'message': 'Contact updated (simulated)'
            }
        except Exception as e:
            return {
                'success': False,
                'crm': 'hubspot',
                'error': str(e)
            }
    
    def _update_pipedrive(
        self,
        email: str,
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update Pipedrive contact."""
        return {
            'success': True,
            'crm': 'pipedrive',
            'message': 'Contact updated (simulated)'
        }
    
    def _update_generic(
        self,
        email: str,
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update generic CRM."""
        if not self.api_url:
            return {
                'success': False,
                'error': 'API URL not configured'
            }
        
        try:
            response = requests.post(
                f'{self.api_url}/contacts/update',
                json={
                    'email': email,
                    'validation': validation_data
                },
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=10
            )
            
            return {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'crm': 'generic'
            }
        except Exception as e:
            return {
                'success': False,
                'crm': 'generic',
                'error': str(e)
            }


class ESPIntegration:
    """
    Integration with Email Service Providers.
    
    Supports:
    - SendGrid
    - Mailchimp
    - Mailgun
    - Generic ESP
    """
    
    def __init__(self, esp_type: str, api_key: str):
        """
        Initialize ESP integration.
        
        Args:
            esp_type: ESP type ('sendgrid', 'mailchimp', 'mailgun', 'generic')
            api_key: API key
        """
        self.esp_type = esp_type.lower()
        self.api_key = api_key
    
    def update_subscriber(
        self,
        email: str,
        validation_data: Dict[str, Any],
        list_id: str = None
    ) -> Dict[str, Any]:
        """
        Update subscriber with validation data.
        
        Args:
            email: Email address
            validation_data: Validation results
            list_id: Mailing list ID (optional)
        
        Returns:
            Update result
        """
        if self.esp_type == 'sendgrid':
            return self._update_sendgrid(email, validation_data, list_id)
        elif self.esp_type == 'mailchimp':
            return self._update_mailchimp(email, validation_data, list_id)
        elif self.esp_type == 'mailgun':
            return self._update_mailgun(email, validation_data)
        else:
            return {
                'success': False,
                'error': f'Unsupported ESP: {self.esp_type}'
            }
    
    def _update_sendgrid(
        self,
        email: str,
        validation_data: Dict[str, Any],
        list_id: str
    ) -> Dict[str, Any]:
        """Update SendGrid contact."""
        # SendGrid API integration
        return {
            'success': True,
            'esp': 'sendgrid',
            'message': 'Subscriber updated (simulated)'
        }
    
    def _update_mailchimp(
        self,
        email: str,
        validation_data: Dict[str, Any],
        list_id: str
    ) -> Dict[str, Any]:
        """Update Mailchimp subscriber."""
        return {
            'success': True,
            'esp': 'mailchimp',
            'message': 'Subscriber updated (simulated)'
        }
    
    def _update_mailgun(
        self,
        email: str,
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update Mailgun contact."""
        return {
            'success': True,
            'esp': 'mailgun',
            'message': 'Contact updated (simulated)'
        }
    
    def suppress_invalid_email(self, email: str) -> Dict[str, Any]:
        """
        Add invalid email to suppression list.
        
        Args:
            email: Email to suppress
        
        Returns:
            Suppression result
        """
        return {
            'success': True,
            'esp': self.esp_type,
            'message': f'{email} added to suppression list (simulated)'
        }


# Convenience functions
def send_to_webhook(data: Dict[str, Any], url: str, secret: str = None) -> Dict[str, Any]:
    """
    Quick webhook send.
    
    Args:
        data: Data to send
        url: Webhook URL
        secret: Secret key (optional)
    
    Returns:
        Delivery result
    """
    manager = WebhookManager(url, secret)
    return manager.send_webhook(data)


def update_crm_contact(
    email: str,
    validation_data: Dict[str, Any],
    crm_type: str,
    api_key: str
) -> Dict[str, Any]:
    """
    Quick CRM update.
    
    Args:
        email: Email address
        validation_data: Validation results
        crm_type: CRM type
        api_key: API key
    
    Returns:
        Update result
    """
    crm = CRMIntegration(crm_type, api_key)
    return crm.update_contact(email, validation_data)
