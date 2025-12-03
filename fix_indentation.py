#!/usr/bin/env python3
"""Fix indentation in emailvalidator_unified.py"""

with open('emailvalidator_unified.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    # Remove 4 leading spaces if present
    if line.startswith('    ') and len(line) > 4:
        fixed_lines.append(line[4:])
    else:
        fixed_lines.append(line)

with open('emailvalidator_unified.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("✅ Fixed indentation in emailvalidator_unified.py")
