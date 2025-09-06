#!/usr/bin/env python3
"""
Fix the admin login issue by creating a new admin user with proper password hash.
"""

import os
from werkzeug.security import generate_password_hash
import psycopg2
from urllib.parse import urlparse

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    return psycopg2.connect(database_url)

def fix_admin_user():
    """Fix the admin user by updating the password hash."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate a proper password hash for 'admin123'
        password_hash = generate_password_hash('admin123')
        print(f"Generated new password hash: {password_hash[:20]}...")
        
        # Update the existing admin user's password hash
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE email = 'admin@antidote.com'
        """, (password_hash,))
        
        conn.commit()
        print("Successfully updated admin user password")
        print("Email: admin@antidote.com")
        print("Password: admin123")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error fixing admin user: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if fix_admin_user():
        print("Admin user fixed successfully!")
    else:
        print("Failed to fix admin user")