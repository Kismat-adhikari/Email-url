# Email Validator

A robust, production-ready Python backend script for validating email addresses using intermediate-level validation rules.

## Features

- **Intermediate-level validation** with comprehensive rules
- **Command-line interface** for easy batch processing
- **Comprehensive error handling** with clear, actionable messages
- **High performance** - processes thousands of emails per second
- **Clean architecture** - modular, maintainable, and testable
- **Production-ready** - thoroughly tested and documented

## Installation

No external dependencies required! Just Python 3.6+

```bash
git clone https://github.com/Kismat-adhikari/Email-url.git
cd Email-url
```

## Usage

```bash
python emailvali.py <filepath> [options]
```

### Options

- `--quiet` or `-q` - Only show summary statistics (suppress individual results)
- `--version` or `-v` - Show version number
- `--help` or `-h` - Show help message

### Examples

```bash
# Basic usage
python emailvali.py test_emails.txt

# Quiet mode (only summary)
python emailvali.py test_emails.txt --quiet

# Show version
python emailvali.py --version

# Show help
python emailvali.py --help
```

### Output

```
VALID: user@example.com
VALID: john.doe@company.co.uk
INVALID: user@example
INVALID: .user@example.com

==================================================
Total processed: 67
Total valid: 29
Total invalid: 38
==================================================
```

## Validation Rules

The validator implements intermediate-level email validation rules:

- ✅ Exactly one `@` symbol
- ✅ Non-empty local part and domain part
- ✅ No leading or trailing dots in local part
- ✅ No consecutive dots anywhere
- ✅ Domain must contain at least one dot
- ✅ Domain labels cannot start or end with hyphens
- ✅ Domain labels max 63 characters each
- ✅ TLD must be at least 2 characters
- ✅ Local part max 64 characters
- ✅ Total domain max 253 characters
- ✅ Total email max 254 
- ✅ No spaces anywhere
- ✅ Standard allowed characters only

### Allowed Characters

**Local part (before @):** `a-z A-Z 0-9 . _ + -`

**Domain part (after @):** `a-z A-Z 0-9 - .`

## Test Files

The repository includes comprehensive test suites:

- `test_emails.txt` - 67 basic test cases
- `stress_test_emails.txt` - 71 edge cases and boundary tests
- `bulk_test_emails.txt` - 571 realistic email addresses
- `test_cases_breakdown.txt` - Detailed explanation of each test
- `stress_test_breakdown.txt` - Edge case documentation

## Documentation

- `system_audit_report.txt` - Complete architecture and code quality audit
- `performance_analysis.txt` - Performance benchmarks and optimization analysis
- `validation_stress_review.txt` - Stress testing scenarios and behavior analysis
- `false_positives_negatives.txt` - Known limitations and trade-offs

## Performance

- **10,000 emails:** ~0.5 seconds
- **100,000 emails:** ~5 seconds
- **1,000,000 emails:** ~50 seconds

Time complexity: O(N) - Linear and optimal

## Architecture

Clean three-tier architecture:

1. **Input Handler** - File loading with comprehensive error handling
2. **Validator Logic** - Pure functions with modular validation rules
3. **Output Reporter** - Clean terminal output with summary statistics

## Error Handling

The validator provides clear, actionable error messages:

- Missing file
- Permission denied
- Invalid encoding
- Empty file
- Missing arguments

## Limitations

This is an **intermediate-level** validator that intentionally does not support:

- Unicode/international characters (ASCII-only)
- Quoted strings in local part
- IP addresses in domain part
- Comments in email addresses
- DNS/MX record validation
- Deliverability checking

These limitations are by design for simplicity, performance, and maintainability.

## Examples

### Valid Emails

```
user@example.com
john.doe@company.co.uk
alice_smith@test-domain.org
bob+filter@mail.example.com
admin@subdomain.example.com
test123@numbers456.com
a@bc.de
```

### Invalid Emails

```
user@example              # No TLD
.user@example.com         # Leading dot
user..name@example.com    # Consecutive dots
user name@example.com     # Space in email
user@-example.com         # Hyphen at start of label
user@@example.com         # Multiple @ symbols
```

## Contributing

Contributions are welcome! Please ensure:

- Code follows existing style and architecture
- All test cases pass
- New features include test cases
- Documentation is updated

## License

MIT License - feel free to use in your projects!

## Author

Kismat Adhikari

## Acknowledgments

Built with clean code principles and production-ready practices.
