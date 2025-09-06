#!/usr/bin/env python3
"""
Seed a minimal test user for the Antidote platform.
This ensures we have at least one user for community threads.
"""
import os
import sys
import logging
import psycopg2
import hashlib
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_db():
    """Connect to the PostgreSQL database."""
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = False
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to the database: {str(e)}")
        raise

def seed_test_user(conn):
    """Seed a test user if one doesn't already exist."""
    logger.info("Checking for existing users...")
    
    try:
        with conn.cursor() as cur:
            # Check if users already exist
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            
            if user_count > 0:
                logger.info(f"Found {user_count} existing users. No need to create test user.")
                return True
            
            # Create a test admin user
            logger.info("Creating test admin user...")
            
            # Generate simple password hash since we're just creating a test user
            password_hash = hashlib.sha256("test_password".encode()).hexdigest()
            
            cur.execute("""
                INSERT INTO users
                (username, email, name, password_hash, phone_number, role, is_verified, created_at)
                VALUES
                ('testadmin', 'test@example.com', 'Test Admin', %s, '+1234567890', 'admin', true, %s)
                RETURNING id
            """, (password_hash, datetime.utcnow()))
            
            user_id = cur.fetchone()[0]
            logger.info(f"Created test admin user with ID: {user_id}")
            
            # Create user preferences
            cur.execute("""
                INSERT INTO user_preferences
                (user_id, email_notifications, sms_notifications, theme, created_at)
                VALUES
                (%s, true, false, 'dark', %s)
            """, (user_id, datetime.utcnow()))
            
            logger.info("Created user preferences")
            
            # Commit transaction
            conn.commit()
            logger.info("Test user seeding completed successfully")
            return True
    
    except Exception as e:
        logger.error(f"Error seeding test user: {str(e)}")
        conn.rollback()
        raise

def main():
    """Create a test user for the Antidote platform."""
    logger.info("Starting minimal user seeding...")
    
    try:
        conn = connect_to_db()
        success = seed_test_user(conn)
        conn.close()
        
        if success:
            logger.info("Test user seeding completed successfully")
            return 0
        else:
            logger.error("Failed to seed test user")
            return 1
    
    except Exception as e:
        logger.error(f"Error in minimal user seeding: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())