#!/usr/bin/env python3
"""
Fix the index route to resolve homepage loading issues.

This script modifies the index route in routes.py to simplify the queries
and reduce the data loaded on the homepage.
"""
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_index_route():
    """Update the index route to simplify doctor queries."""
    try:
        with open("routes.py", "r") as file:
            content = file.read()
            
        # Find and simplify the doctor query
        # 1. Change to simplified .limit(9) query
        # 2. Remove lazy-loaded relationships that might be causing issues
        pattern = r'top_doctors = Doctor\.query\.filter\(Doctor\.rating\.isnot\(None\)\)\.order_by\(Doctor\.rating\.desc\(\)\)\.limit\(18\)\.all\(\)'
        replacement = 'top_doctors = Doctor.query.order_by(Doctor.id).limit(9).all()'
        
        # Replace the pattern
        new_content = re.sub(pattern, replacement, content)
        
        # Also remove the fallback query that adds additional doctors
        pattern = r'if len\(top_doctors\) < 18:[\s\n]+additional_doctors = Doctor\.query\.filter\(Doctor\.rating\.is_\(None\)\)\.limit\(18 - len\(top_doctors\)\)\.all\(\)[\s\n]+top_doctors\.extend\(additional_doctors\)'
        replacement = '# Simplified query - no fallback needed'
        
        # Replace the fallback pattern
        new_content = re.sub(pattern, replacement, new_content)
        
        # Write the modified content back to the file
        with open("routes.py", "w") as file:
            file.write(new_content)
            
        logger.info("Successfully updated index route with simplified doctor query")
        return True
    except Exception as e:
        logger.error(f"Error updating index route: {str(e)}")
        return False

if __name__ == "__main__":
    update_index_route()