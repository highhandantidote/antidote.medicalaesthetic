#!/usr/bin/env python3
"""
Fix login passwords for admin and clinic owner accounts.
"""
import os
import psycopg2
from werkzeug.security import generate_password_hash

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def fix_passwords():
    """Fix passwords for admin and clinic owner accounts."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update admin password
        admin_password_hash = generate_password_hash('admin123')
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE email = 'admin@antidote.com'
        """, (admin_password_hash,))
        
        # Update clinic owner password
        clinic_password_hash = generate_password_hash('test123')
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE email = 'clinic.test@example.com'
        """, (clinic_password_hash,))
        
        conn.commit()
        print("✓ Admin password set to: admin123")
        print("✓ Clinic owner password set to: test123")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()

if __name__ == "__main__":
    fix_passwords()