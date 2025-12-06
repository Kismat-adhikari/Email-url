#!/usr/bin/env python3
"""
CSV Export Module
Export validation results to CSV format
"""

import csv
import io
from typing import List, Dict, Any
from datetime import datetime


def export_to_csv(
    results: List[Dict[str, Any]],
    include_details: bool = True
) -> str:
    """
    Export validation results to CSV format.
    
    Args:
        results: List of validation result dictionaries
        include_details: Include detailed validation checks
    
    Returns:
        CSV string
    
    Example:
        >>> results = [
        ...     {'email': 'user@example.com', 'valid': True, 'confidence_score': 95},
        ...     {'email': 'invalid@', 'valid': False, 'confidence_score': 0}
        ... ]
        >>> csv_data = export_to_csv(results)
        >>> print(csv_data)
    """
    output = io.StringIO()
    
    if not results:
        return ''
    
    # Determine columns based on first result
    if include_details and 'checks' in results[0]:
        fieldnames = [
            'email',
            'valid',
            'confidence_score',
            'syntax',
            'dns_valid',
            'mx_records',
            'is_disposable',
            'is_role_based',
            'is_catch_all',
            'bounce_count',
            'risk_score',
            'risk_level',
            'validated_at',
            'reason'
        ]
    else:
        fieldnames = [
            'email',
            'valid',
            'confidence_score',
            'validated_at',
            'reason'
        ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    
    for result in results:
        row = {
            'email': result.get('email', ''),
            'valid': 'Yes' if result.get('valid') else 'No',
            'confidence_score': result.get('confidence_score', ''),
            'validated_at': result.get('validated_at', datetime.utcnow().isoformat()),
            'reason': result.get('reason', '')
        }
        
        # Add detailed checks if available
        if include_details and 'checks' in result:
            checks = result['checks']
            row.update({
                'syntax': 'Yes' if checks.get('syntax') else 'No',
                'dns_valid': 'Yes' if checks.get('dns_valid') else 'No',
                'mx_records': 'Yes' if checks.get('mx_records') else 'No',
                'is_disposable': 'Yes' if checks.get('is_disposable') else 'No',
                'is_role_based': 'Yes' if checks.get('is_role_based') else 'No',
                'is_catch_all': 'Yes' if checks.get('is_catch_all') else 'No'
            })
        
        # Add bounce and risk data if available
        if 'bounce_count' in result:
            row['bounce_count'] = result['bounce_count']
        
        if 'risk_score' in result:
            row['risk_score'] = result['risk_score']
            row['risk_level'] = result.get('risk_level', '')
        
        writer.writerow(row)
    
    return output.getvalue()


def export_risk_report_csv(assessments: List[Dict[str, Any]]) -> str:
    """
    Export risk assessments to CSV.
    
    Args:
        assessments: List of risk assessment dictionaries
    
    Returns:
        CSV string
    """
    output = io.StringIO()
    
    if not assessments:
        return ''
    
    fieldnames = [
        'email',
        'risk_score',
        'risk_level',
        'is_spam_trap',
        'is_blacklisted',
        'bounce_count',
        'confidence_score',
        'risk_factors',
        'recommendations',
        'assessed_at'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for assessment in assessments:
        if 'error' in assessment:
            continue
        
        row = {
            'email': assessment.get('email', ''),
            'risk_score': assessment.get('risk_score', ''),
            'risk_level': assessment.get('risk_level', ''),
            'is_spam_trap': 'Yes' if assessment.get('is_spam_trap') else 'No',
            'is_blacklisted': 'Yes' if assessment.get('is_blacklisted') else 'No',
            'bounce_count': assessment.get('bounce_count', 0),
            'confidence_score': assessment.get('confidence_score', ''),
            'risk_factors': '; '.join(assessment.get('risk_factors', [])),
            'recommendations': '; '.join(assessment.get('recommendations', [])),
            'assessed_at': assessment.get('assessed_at', '')
        }
        
        writer.writerow(row)
    
    return output.getvalue()


def export_statistics_csv(stats: Dict[str, Any]) -> str:
    """
    Export statistics to CSV.
    
    Args:
        stats: Statistics dictionary
    
    Returns:
        CSV string
    """
    output = io.StringIO()
    
    writer = csv.writer(output)
    writer.writerow(['Metric', 'Value'])
    
    for key, value in stats.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                writer.writerow([f'{key}.{sub_key}', sub_value])
        else:
            writer.writerow([key, value])
    
    return output.getvalue()
