#!/usr/bin/env python3
"""
Fix the admin user password using the User model's set_password method.
This ensures the password hash is in the correct format for check_password_hash.
"""
import os
import logging
import psycopg2
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(db_url)

def fix_admin_password():
    """Fix the admin user password hash."""
    
    # Generate proper password hash using werkzeug
    password = 'Admin1234'
    password_hash = generate_password_hash(password)
    
    try:
        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update both admin accounts to have the correct password hash
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE email IN ('admin@antidote.com', 'testadmin@example.com')",
            (password_hash,)
        )
        
        rows_updated = cur.rowcount
        conn.commit()
        
        logger.info(f"Updated password hash for {rows_updated} admin users")
        
        # Verify the update
        cur.execute("SELECT id, email, username FROM users WHERE email IN ('admin@antidote.com', 'testadmin@example.com')")
        admin_users = cur.fetchall()
        
        for user_id, email, username in admin_users:
            logger.info(f"Admin user: ID={user_id}, Email={email}, Username={username}")
            logger.info(f"Password for {email} is now: Admin1234")
        
        # Close connection
        cur.close()
        conn.close()
        
        return rows_updated
    except Exception as e:
        logger.error(f"Error fixing admin passwords: {str(e)}")
        return None

if __name__ == "__main__":
    result = fix_admin_password()
    if result:
        logger.info(f"Successfully updated {result} admin user passwords")
        logger.info("Use any of the admin emails with password: Admin1234")
    else:
        logger.error("Failed to update admin passwords")