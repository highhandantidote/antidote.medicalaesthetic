#!/usr/bin/env python3
"""
Fix test user and doctor passwords using proper password hashing.
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

def fix_test_account_passwords():
    """Fix the test user and doctor passwords."""
    
    # Generate proper password hash using werkzeug
    password = 'Password123'
    password_hash = generate_password_hash(password)
    
    try:
        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update test user accounts to have the correct password hash
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE email IN ('testuser@example.com', 'testdoctor@example.com')",
            (password_hash,)
        )
        
        rows_updated = cur.rowcount
        conn.commit()
        
        logger.info(f"Updated password hash for {rows_updated} test users")
        
        # Verify the update
        cur.execute("SELECT id, email, username, role FROM users WHERE email IN ('testuser@example.com', 'testdoctor@example.com')")
        test_users = cur.fetchall()
        
        for user_id, email, username, role in test_users:
            logger.info(f"{role.title()} account: ID={user_id}, Email={email}, Username={username}")
            logger.info(f"Password for {email} is now: Password123")
        
        # Close connection
        cur.close()
        conn.close()
        
        return rows_updated
    except Exception as e:
        logger.error(f"Error fixing test account passwords: {str(e)}")
        return None

if __name__ == "__main__":
    result = fix_test_account_passwords()
    if result:
        logger.info(f"Successfully updated {result} test account passwords")
        logger.info("Test accounts can now be accessed with password: Password123")
    else:
        logger.error("Failed to update test account passwords")