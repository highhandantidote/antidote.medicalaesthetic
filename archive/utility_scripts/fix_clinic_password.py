#!/usr/bin/env python3
"""
Fix the clinic user password to ensure proper authentication.
"""

import os
import psycopg2
from werkzeug.security import generate_password_hash
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def fix_clinic_password():
    """Reset clinic user password to a known value."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate new password hash for 'clinic123'
        new_password = 'clinic123'
        password_hash = generate_password_hash(new_password)
        
        # Update the clinic user's password
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE email = 'clinic.test@example.com'
        """, (password_hash,))
        
        # Check if update was successful
        if cursor.rowcount > 0:
            logger.info(f"✅ Updated password for clinic.test@example.com")
            conn.commit()
        else:
            logger.error("❌ No rows updated - user not found")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error updating clinic password: {e}")
        if conn:
            conn.close()

def verify_users():
    """Verify both admin and clinic users exist with correct roles."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT email, role, created_at 
            FROM users 
            WHERE email IN ('admin@antidote.com', 'clinic.test@example.com')
            ORDER BY email
        """)
        
        users = cursor.fetchall()
        logger.info("Current user status:")
        for user in users:
            logger.info(f"  Email: {user[0]}, Role: {user[1]}, Created: {user[2]}")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error verifying users: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Fixing clinic user authentication...")
    verify_users()
    fix_clinic_password()
    logger.info("Clinic password fix completed.")