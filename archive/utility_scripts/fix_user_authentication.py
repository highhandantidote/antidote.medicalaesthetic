#!/usr/bin/env python3
"""
Fix user authentication by creating fresh admin and clinic users with known passwords.
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

def create_or_update_users():
    """Create or update admin and clinic users with known passwords."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Admin user credentials
        admin_email = 'admin@antidote.com'
        admin_password = 'admin123'
        admin_password_hash = generate_password_hash(admin_password)
        
        # Clinic user credentials  
        clinic_email = 'clinic.test@example.com'
        clinic_password = 'clinic123'
        clinic_password_hash = generate_password_hash(clinic_password)
        
        # Update or insert admin user
        cursor.execute("""
            INSERT INTO users (name, username, email, phone_number, password_hash, role, created_at, last_login_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (email) 
            DO UPDATE SET 
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                last_login_at = NOW()
        """, (
            'Admin User',
            'admin_user', 
            admin_email,
            '9999999999',
            admin_password_hash,
            'admin'
        ))
        
        # Update or insert clinic user
        cursor.execute("""
            INSERT INTO users (name, username, email, phone_number, password_hash, role, created_at, last_login_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (email) 
            DO UPDATE SET 
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                last_login_at = NOW()
        """, (
            'Test Clinic Owner',
            'clinic_owner',
            clinic_email,
            '8888888888', 
            clinic_password_hash,
            'clinic_owner'
        ))
        
        conn.commit()
        logger.info(f"✅ Successfully created/updated admin user: {admin_email}")
        logger.info(f"✅ Successfully created/updated clinic user: {clinic_email}")
        
        # Verify the users exist
        cursor.execute("""
            SELECT email, role, created_at 
            FROM users 
            WHERE email IN (%s, %s)
            ORDER BY email
        """, (admin_email, clinic_email))
        
        users = cursor.fetchall()
        logger.info("User verification:")
        for user in users:
            logger.info(f"  Email: {user[0]}, Role: {user[1]}, Created: {user[2]}")
            
        cursor.close()
        conn.close()
        
        logger.info("Authentication credentials:")
        logger.info(f"Admin - Email: {admin_email}, Password: {admin_password}")
        logger.info(f"Clinic - Email: {clinic_email}, Password: {clinic_password}")
        
    except Exception as e:
        logger.error(f"Error creating/updating users: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    logger.info("Fixing user authentication...")
    create_or_update_users()
    logger.info("User authentication fix completed.")