#!/usr/bin/env python3
"""
Supabase Storage Module for Email Validation Results
Handles all database operations for storing and retrieving validation data
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
TABLE_NAME = os.getenv('SUPABASE_TABLE_NAME', 'email_validations')


class SupabaseStorage:
    """
    Supabase storage handler for email validation results.
    
    Manages CRUD operations for email validation records including:
    - Email address
    - Validation status
    - Confidence score
    - Timestamp
    - Bounce history
    - Validation details
    """
    
    def __init__(self, url: str = None, key: str = None, table: str = None):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase project URL (defaults to env variable)
            key: Supabase API key (defaults to env variable)
            table: Table name (defaults to env variable or 'email_validations')
        
        Raises:
            ValueError: If URL or KEY is missing
        """
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_KEY
        self.table_name = table or TABLE_NAME
        
        if not self.url or not self.key:
            raise ValueError(
                "Supabase URL and KEY are required. "
                "Set SUPABASE_URL and SUPABASE_KEY environment variables."
            )
        
        try:
            self.client: Client = create_client(self.url, self.key)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {str(e)}")
    
    def create_record(self, validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new email validation record.
        
        Args:
            validation_data: Dictionary containing:
                - anon_user_id (required): Anonymous user ID
                - email (required): Email address
                - valid (required): Validation status (bool)
                - confidence_score (required): Score 0-100
                - checks (optional): Validation checks dict
                - smtp_details (optional): SMTP verification details
                - is_disposable (optional): Disposable email flag
                - is_role_based (optional): Role-based email flag
                - is_catch_all (optional): Catch-all domain flag
                - bounce_count (optional): Number of bounces
                - last_bounce_date (optional): Last bounce timestamp
                - notes (optional): Additional notes
        
        Returns:
            Dictionary with created record including 'id' and 'created_at'
        
        Raises:
            ValueError: If required fields are missing
            Exception: If database operation fails
        
        Example:
            >>> storage = SupabaseStorage()
            >>> data = {
            ...     'anon_user_id': 'abc-123-def-456',
            ...     'email': 'user@example.com',
            ...     'valid': True,
            ...     'confidence_score': 95
            ... }
            >>> result = storage.create_record(data)
            >>> print(result['id'])
        """
        # Validate required fields
        required_fields = ['anon_user_id', 'email', 'valid', 'confidence_score']
        for field in required_fields:
            if field not in validation_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Prepare record
        record = {
            'anon_user_id': validation_data['anon_user_id'],
            'email': validation_data['email'].lower().strip(),
            'valid': validation_data['valid'],
            'confidence_score': validation_data['confidence_score'],
            'checks': validation_data.get('checks', {}),
            'smtp_details': validation_data.get('smtp_details'),
            'is_disposable': validation_data.get('is_disposable', False),
            'is_role_based': validation_data.get('is_role_based', False),
            'is_catch_all': validation_data.get('is_catch_all', False),
            'bounce_count': validation_data.get('bounce_count', 0),
            'last_bounce_date': validation_data.get('last_bounce_date'),
            'notes': validation_data.get('notes', ''),
            'validated_at': datetime.utcnow().isoformat()
        }
        
        try:
            response = self.client.table(self.table_name).insert(record).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise Exception("No data returned from insert operation")
                
        except Exception as e:
            raise Exception(f"Failed to create record: {str(e)}")
    
    def get_record_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the most recent validation record for an email.
        
        Args:
            email: Email address to search for
        
        Returns:
            Dictionary with record data or None if not found
        
        Example:
            >>> storage = SupabaseStorage()
            >>> record = storage.get_record_by_email('user@example.com')
            >>> if record:
            ...     print(f"Confidence: {record['confidence_score']}")
        """
        try:
            response = self.client.table(self.table_name)\
                .select('*')\
                .eq('email', email.lower().strip())\
                .order('validated_at', desc=True)\
                .limit(1)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            raise Exception(f"Failed to fetch record: {str(e)}")
    
    def get_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific record by ID.
        
        Args:
            record_id: Record ID
        
        Returns:
            Dictionary with record data or None if not found
        """
        try:
            response = self.client.table(self.table_name)\
                .select('*')\
                .eq('id', record_id)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            raise Exception(f"Failed to fetch record by ID: {str(e)}")
    
    def get_all_records(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch all validation records with pagination.
        
        Args:
            limit: Maximum number of records to return (default: 100)
            offset: Number of records to skip (default: 0)
        
        Returns:
            List of record dictionaries
        
        Example:
            >>> storage = SupabaseStorage()
            >>> records = storage.get_all_records(limit=50)
            >>> print(f"Found {len(records)} records")
        """
        try:
            response = self.client.table(self.table_name)\
                .select('*')\
                .order('validated_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            raise Exception(f"Failed to fetch records: {str(e)}")
    
    def get_validation_history(self, email: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch validation history for a specific email.
        
        Args:
            email: Email address
            limit: Maximum number of records (default: 10)
        
        Returns:
            List of validation records ordered by date (newest first)
        
        Example:
            >>> storage = SupabaseStorage()
            >>> history = storage.get_validation_history('user@example.com')
            >>> for record in history:
            ...     print(f"{record['validated_at']}: {record['confidence_score']}")
        """
        try:
            response = self.client.table(self.table_name)\
                .select('*')\
                .eq('email', email.lower().strip())\
                .order('validated_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            raise Exception(f"Failed to fetch validation history: {str(e)}")
    
    def update_record(self, record_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing validation record.
        
        Args:
            record_id: Record ID to update
            updates: Dictionary with fields to update
        
        Returns:
            Updated record dictionary
        
        Raises:
            Exception: If record not found or update fails
        
        Example:
            >>> storage = SupabaseStorage()
            >>> updates = {
            ...     'confidence_score': 85,
            ...     'bounce_count': 1,
            ...     'notes': 'Updated after bounce'
            ... }
            >>> result = storage.update_record(123, updates)
        """
        try:
            # Add update timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            response = self.client.table(self.table_name)\
                .update(updates)\
                .eq('id', record_id)\
                .execute()
            
            if response.data:
                return response.data[0]
            else:
                raise Exception(f"Record with ID {record_id} not found")
                
        except Exception as e:
            raise Exception(f"Failed to update record: {str(e)}")
    
    def update_by_email(self, email: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the most recent record for an email.
        
        Args:
            email: Email address
            updates: Dictionary with fields to update
        
        Returns:
            Updated record dictionary
        """
        # Get most recent record
        record = self.get_record_by_email(email)
        if not record:
            raise Exception(f"No record found for email: {email}")
        
        return self.update_record(record['id'], updates)
    
    def increment_bounce_count(self, email: str) -> Dict[str, Any]:
        """
        Increment bounce count for an email.
        
        Args:
            email: Email address
        
        Returns:
            Updated record dictionary
        
        Example:
            >>> storage = SupabaseStorage()
            >>> result = storage.increment_bounce_count('user@example.com')
            >>> print(f"Bounce count: {result['bounce_count']}")
        """
        record = self.get_record_by_email(email)
        if not record:
            raise Exception(f"No record found for email: {email}")
        
        updates = {
            'bounce_count': record.get('bounce_count', 0) + 1,
            'last_bounce_date': datetime.utcnow().isoformat()
        }
        
        return self.update_record(record['id'], updates)
    
    def delete_record(self, record_id: int) -> bool:
        """
        Delete a validation record by ID.
        
        Args:
            record_id: Record ID to delete
        
        Returns:
            True if deleted successfully
        
        Raises:
            Exception: If deletion fails
        
        Example:
            >>> storage = SupabaseStorage()
            >>> success = storage.delete_record(123)
            >>> print(f"Deleted: {success}")
        """
        try:
            response = self.client.table(self.table_name)\
                .delete()\
                .eq('id', record_id)\
                .execute()
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to delete record: {str(e)}")
    
    def delete_by_email(self, email: str) -> int:
        """
        Delete all records for a specific email.
        
        Args:
            email: Email address
        
        Returns:
            Number of records deleted
        
        Example:
            >>> storage = SupabaseStorage()
            >>> count = storage.delete_by_email('user@example.com')
            >>> print(f"Deleted {count} records")
        """
        try:
            response = self.client.table(self.table_name)\
                .delete()\
                .eq('email', email.lower().strip())\
                .execute()
            
            return len(response.data) if response.data else 0
            
        except Exception as e:
            raise Exception(f"Failed to delete records: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics.
        
        Returns:
            Dictionary with statistics:
                - total_validations: Total number of records
                - valid_count: Number of valid emails
                - invalid_count: Number of invalid emails
                - avg_confidence: Average confidence score
                - disposable_count: Number of disposable emails
                - role_based_count: Number of role-based emails
        
        Example:
            >>> storage = SupabaseStorage()
            >>> stats = storage.get_statistics()
            >>> print(f"Total: {stats['total_validations']}")
            >>> print(f"Valid: {stats['valid_count']}")
        """
        try:
            # Get all records (consider pagination for large datasets)
            response = self.client.table(self.table_name)\
                .select('valid,confidence_score,is_disposable,is_role_based')\
                .execute()
            
            records = response.data or []
            
            if not records:
                return {
                    'total_validations': 0,
                    'valid_count': 0,
                    'invalid_count': 0,
                    'avg_confidence': 0,
                    'disposable_count': 0,
                    'role_based_count': 0
                }
            
            total = len(records)
            valid_count = sum(1 for r in records if r.get('valid'))
            invalid_count = total - valid_count
            avg_confidence = sum(r.get('confidence_score', 0) for r in records) / total
            disposable_count = sum(1 for r in records if r.get('is_disposable'))
            role_based_count = sum(1 for r in records if r.get('is_role_based'))
            
            return {
                'total_validations': total,
                'valid_count': valid_count,
                'invalid_count': invalid_count,
                'avg_confidence': round(avg_confidence, 2),
                'disposable_count': disposable_count,
                'role_based_count': role_based_count
            }
            
        except Exception as e:
            raise Exception(f"Failed to get statistics: {str(e)}")
    
    def search_records(
        self,
        valid: Optional[bool] = None,
        min_confidence: Optional[int] = None,
        max_confidence: Optional[int] = None,
        is_disposable: Optional[bool] = None,
        is_role_based: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search records with filters.
        
        Args:
            valid: Filter by validation status
            min_confidence: Minimum confidence score
            max_confidence: Maximum confidence score
            is_disposable: Filter by disposable status
            is_role_based: Filter by role-based status
            limit: Maximum number of records
        
        Returns:
            List of matching records
        
        Example:
            >>> storage = SupabaseStorage()
            >>> # Find all valid emails with high confidence
            >>> records = storage.search_records(
            ...     valid=True,
            ...     min_confidence=80
            ... )
        """
        try:
            query = self.client.table(self.table_name).select('*')
            
            if valid is not None:
                query = query.eq('valid', valid)
            
            if min_confidence is not None:
                query = query.gte('confidence_score', min_confidence)
            
            if max_confidence is not None:
                query = query.lte('confidence_score', max_confidence)
            
            if is_disposable is not None:
                query = query.eq('is_disposable', is_disposable)
            
            if is_role_based is not None:
                query = query.eq('is_role_based', is_role_based)
            
            response = query.order('validated_at', desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            raise Exception(f"Failed to search records: {str(e)}")
    
    # ========================================================================
    # ANONYMOUS USER ID METHODS
    # ========================================================================
    
    def get_user_history(
        self,
        anon_user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get validation history for a specific anonymous user.
        Returns ONLY records belonging to this user.
        
        Args:
            anon_user_id: Anonymous user ID
            limit: Maximum number of records (default: 100)
            offset: Pagination offset (default: 0)
        
        Returns:
            List of validation records for this user, sorted by newest first
        
        Example:
            >>> storage = SupabaseStorage()
            >>> history = storage.get_user_history('abc-123-def-456', limit=50)
            >>> print(f"User has {len(history)} validations")
        """
        try:
            response = self.client.table(self.table_name)\
                .select('*')\
                .eq('anon_user_id', anon_user_id)\
                .order('validated_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            raise Exception(f"Failed to fetch user history: {str(e)}")
    
    def get_user_analytics(self, anon_user_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific anonymous user.
        Returns statistics ONLY for this user's data.
        
        Args:
            anon_user_id: Anonymous user ID
        
        Returns:
            Dictionary with user-specific statistics:
                - total_validations: Total validations by this user
                - valid_count: Number of valid emails
                - invalid_count: Number of invalid emails
                - avg_confidence: Average confidence score
                - risk_distribution: Distribution of risk levels
                - domain_types: Distribution of domain types
                - top_domains: Most validated domains
        
        Example:
            >>> storage = SupabaseStorage()
            >>> analytics = storage.get_user_analytics('abc-123-def-456')
            >>> print(f"Total: {analytics['total_validations']}")
        """
        try:
            # Get all records for this user
            response = self.client.table(self.table_name)\
                .select('*')\
                .eq('anon_user_id', anon_user_id)\
                .execute()
            
            records = response.data or []
            
            if not records:
                return {
                    'total_validations': 0,
                    'valid_count': 0,
                    'invalid_count': 0,
                    'avg_confidence': 0,
                    'message': 'No data available for this user'
                }
            
            total = len(records)
            valid_count = sum(1 for r in records if r.get('valid'))
            invalid_count = total - valid_count
            avg_confidence = sum(r.get('confidence_score', 0) for r in records) / total
            
            # Risk distribution (if risk data exists)
            risk_distribution = {}
            domain_types = {}
            domain_counts = {}
            
            for record in records:
                # Count domain types
                email = record.get('email', '')
                if '@' in email:
                    domain = email.split('@')[1]
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
                
                # Extract domain type from checks
                checks = record.get('checks', {})
                if isinstance(checks, dict):
                    if checks.get('is_disposable'):
                        domain_types['Disposable'] = domain_types.get('Disposable', 0) + 1
                    elif checks.get('is_role_based'):
                        domain_types['Role-based'] = domain_types.get('Role-based', 0) + 1
                    else:
                        domain_types['Personal'] = domain_types.get('Personal', 0) + 1
            
            # Top domains
            top_domains = [
                {'domain': domain, 'count': count}
                for domain, count in sorted(
                    domain_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            ]
            
            return {
                'total_validations': total,
                'valid_count': valid_count,
                'invalid_count': invalid_count,
                'avg_confidence': round(avg_confidence, 2),
                'disposable_count': sum(1 for r in records if r.get('is_disposable')),
                'role_based_count': sum(1 for r in records if r.get('is_role_based')),
                'domain_types': domain_types,
                'top_domains': top_domains
            }
            
        except Exception as e:
            raise Exception(f"Failed to get user analytics: {str(e)}")
    
    def delete_user_history(self, anon_user_id: str) -> int:
        """
        Delete all validation records for a specific anonymous user.
        
        Args:
            anon_user_id: Anonymous user ID
        
        Returns:
            Number of records deleted
        
        Example:
            >>> storage = SupabaseStorage()
            >>> count = storage.delete_user_history('abc-123-def-456')
            >>> print(f"Deleted {count} records")
        """
        try:
            response = self.client.table(self.table_name)\
                .delete()\
                .eq('anon_user_id', anon_user_id)\
                .execute()
            
            return len(response.data) if response.data else 0
            
        except Exception as e:
            raise Exception(f"Failed to delete user history: {str(e)}")
    
    def get_user_record_count(self, anon_user_id: str) -> int:
        """
        Get total number of validation records for a user.
        
        Args:
            anon_user_id: Anonymous user ID
        
        Returns:
            Number of records
        
        Example:
            >>> storage = SupabaseStorage()
            >>> count = storage.get_user_record_count('abc-123-def-456')
            >>> print(f"User has {count} validations")
        """
        try:
            response = self.client.table(self.table_name)\
                .select('id', count='exact')\
                .eq('anon_user_id', anon_user_id)\
                .execute()
            
            return response.count if hasattr(response, 'count') else 0
            
        except Exception as e:
            raise Exception(f"Failed to count user records: {str(e)}")


# Convenience function for quick access
def get_storage() -> SupabaseStorage:
    """
    Get a configured SupabaseStorage instance.
    
    Returns:
        SupabaseStorage instance
    
    Example:
        >>> storage = get_storage()
        >>> record = storage.get_record_by_email('user@example.com')
    """
    return SupabaseStorage()
