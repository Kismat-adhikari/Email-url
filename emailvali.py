#!/usr/bin/env python3
"""
Email Validator - Backend Script
Validates emails from a text file using intermediate-level rules.
Usage: python emailvali.py <filepath>
"""

import sys
import re


# ============================================================================
# INPUT HANDLER
# ============================================================================

def load_emails_from_file(filepath):
    """
    Load emails from file, one per line.
    
    Args:
        filepath (str): Path to the file containing emails
    
    Returns:
        list: List of email strings
    
    Exits:
        - If file does not exist
        - If file cannot be read
        - If file contains zero emails
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            emails = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"ERROR: File '{filepath}' does not exist.")
        print("Please provide a valid file path.")
        sys.exit(1)
    except PermissionError:
        print(f"ERROR: Permission denied reading file '{filepath}'.")
        print("Please check file permissions.")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"ERROR: File '{filepath}' contains invalid characters.")
        print("Please ensure the file is a valid text file with UTF-8 encoding.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read file '{filepath}'.")
        print(f"Reason: {e}")
        sys.exit(1)
    
    # Check if file contains zero emails
    if len(emails) == 0:
        print(f"ERROR: File '{filepath}' contains zero emails.")
        print("Please provide a file with at least one email address.")
        sys.exit(1)
    
    return emails


# ============================================================================
# VALIDATOR LOGIC
# ============================================================================

# Compile regex patterns once for efficiency
LOCAL_PART_PATTERN = re.compile(r'^[a-zA-Z0-9._+\-]+$')
DOMAIN_LABEL_PATTERN = re.compile(r'^[a-zA-Z0-9\-]+$')

# Constants for validation limits
MAX_EMAIL_LENGTH = 254
MAX_LOCAL_LENGTH = 64
MIN_TLD_LENGTH = 2


def validate_email(email):
    """
    Pure function: Validate email using intermediate-level rules.
    
    Args:
        email (str): Raw email string to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    email = email.strip()
    
    if not _is_valid_format(email):
        return False
    
    local, domain = email.split('@')
    
    return _is_valid_local_part(local) and _is_valid_domain_part(domain)


def _is_valid_format(email):
    """Check basic email format requirements."""
    return (
        email
        and ' ' not in email
        and len(email) <= MAX_EMAIL_LENGTH
        and email.count('@') == 1
    )


def _is_valid_local_part(local):
    """Validate the local part (before @) of the email."""
    return (
        local
        and len(local) <= MAX_LOCAL_LENGTH
        and not local.startswith('.')
        and not local.endswith('.')
        and '..' not in local
        and LOCAL_PART_PATTERN.match(local)
    )


def _is_valid_domain_part(domain):
    """Validate the domain part (after @) of the email."""
    if not domain or '.' not in domain or '..' in domain:
        return False
    
    labels = domain.split('.')
    
    return all(_is_valid_domain_label(label) for label in labels) and len(labels[-1]) >= MIN_TLD_LENGTH


def _is_valid_domain_label(label):
    """Validate a single domain label."""
    return (
        label
        and not label.startswith('-')
        and not label.endswith('-')
        and DOMAIN_LABEL_PATTERN.match(label)
    )


# ============================================================================
# OUTPUT REPORTER
# ============================================================================

def report_results(results):
    """
    Print validation results and summary to terminal.
    
    Args:
        results (list): List of tuples (email, is_valid)
    """
    valid_count = sum(1 for _, is_valid in results if is_valid)
    invalid_count = len(results) - valid_count
    
    _print_validation_results(results)
    _print_summary(len(results), valid_count, invalid_count)


def _print_validation_results(results):
    """Print each validation result line by line."""
    for email, is_valid in results:
        status = "VALID" if is_valid else "INVALID"
        print(f"{status}: {email}")


def _print_summary(total, valid, invalid):
    """Print summary statistics."""
    print()
    print("=" * 50)
    print(f"Total processed: {total}")
    print(f"Total valid: {valid}")
    print(f"Total invalid: {invalid}")
    print("=" * 50)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point with comprehensive error handling."""
    filepath = _parse_command_line_args()
    emails = load_emails_from_file(filepath)
    results = _validate_all_emails(emails)
    report_results(results)


def _parse_command_line_args():
    """Parse and validate command line arguments."""
    if len(sys.argv) != 2:
        print("ERROR: Missing input argument.")
        print()
        print("Usage: python emailvali.py <filepath>")
        print()
        print("Example: python emailvali.py emails.txt")
        sys.exit(1)
    return sys.argv[1]


def _validate_all_emails(emails):
    """Validate a list of emails efficiently."""
    return [(email, validate_email(email)) for email in emails]


if __name__ == "__main__":
    main()
