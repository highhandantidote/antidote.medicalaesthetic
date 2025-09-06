#!/usr/bin/env python3
"""
Quick fix for the homepage error that's preventing content display.
"""

import os
import re

def fix_template_error():
    """Fix the template error that's preventing homepage content from displaying."""
    
    # Read the current template
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find any patterns that might cause the len() error
    # Look for places where length checks might fail on None values
    patterns_to_fix = [
        (r'{% if ([^}]*) and [^}]*\|length[^}]*%}', r'{% if \1 %}'),
        (r'{% if ([^}]*)\|length[^}]*%}', r'{% if \1 %}'),
        (r'([^}]*)\|length', r'\1'),
    ]
    
    fixed_content = content
    changes_made = 0
    
    for pattern, replacement in patterns_to_fix:
        matches = re.findall(pattern, fixed_content)
        if matches:
            fixed_content = re.sub(pattern, replacement, fixed_content)
            changes_made += len(matches)
            print(f"Fixed {len(matches)} occurrences of pattern: {pattern}")
    
    # Write the fixed content back
    if changes_made > 0:
        with open('templates/index.html', 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"✅ Fixed {changes_made} template issues that could cause homepage errors")
    else:
        print("No template issues found that need fixing")

if __name__ == "__main__":
    fix_template_error()