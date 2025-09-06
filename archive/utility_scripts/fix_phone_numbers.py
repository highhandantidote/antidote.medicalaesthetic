#!/usr/bin/env python3
"""
Fix the issue with doctors having duplicate empty phone numbers.
This script adds unique phone numbers to doctors that don't have one.
"""
import os
import logging
import psycopg2
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def generate_unique_phone(conn):
    """Generate a unique 10-digit phone number not in the database."""
    while True:
        # Generate a random 10-digit phone number
        phone = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        
        # Check if it exists
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE phone_number = %s",
                (phone,)
            )
            if cursor.fetchone()[0] == 0:
                return phone

def fix_empty_phone_numbers(conn):
    """Fix users with empty phone numbers."""
    try:
        with conn.cursor() as cursor:
            # Find users with empty phone numbers
            cursor.execute(
                """
                SELECT id, name 
                FROM users 
                WHERE phone_number = '' OR phone_number IS NULL
                """
            )
            users = cursor.fetchall()
            
            if not users:
                logger.info("No users with empty phone numbers found")
                return 0
                
            logger.info(f"Found {len(users)} users with empty phone numbers")
            
            # Update each user with a unique phone number
            updated = 0
            for user_id, name in users:
                phone = generate_unique_phone(conn)
                cursor.execute(
                    "UPDATE users SET phone_number = %s WHERE id = %s",
                    (phone, user_id)
                )
                logger.info(f"Updated user {name} (ID: {user_id}) with phone: {phone}")
                updated += 1
                
            return updated
    except Exception as e:
        logger.error(f"Error fixing phone numbers: {e}")
        return 0

def set_default_empty_phone(conn):
    """Update the constraints to allow NULL phone numbers."""
    try:
        with conn.cursor() as cursor:
            # Drop the unique constraint
            cursor.execute(
                """
                ALTER TABLE users 
                DROP CONSTRAINT IF EXISTS users_phone_number_key
                """
            )
            
            # Add it back allowing NULL values
            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS users_phone_number_unique_idx 
                ON users (phone_number) 
                WHERE phone_number IS NOT NULL AND phone_number != ''
                """
            )
            
            logger.info("Updated constraints on phone_number to allow NULL values")
            return True
    except Exception as e:
        logger.error(f"Error updating phone number constraints: {e}")
        return False

def main():
    """Fix the phone number issues in the database."""
    logger.info("Starting phone number fix process...")
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return
    
    try:
        # Update constraints to allow NULL phone numbers
        if set_default_empty_phone(conn):
            logger.info("Successfully updated phone number constraints")
        
        # Fix existing empty phone numbers
        updated = fix_empty_phone_numbers(conn)
        logger.info(f"Updated {updated} users with unique phone numbers")
    except Exception as e:
        logger.error(f"Error during phone number fix: {e}")
    finally:
        conn.close()
    
    logger.info("Phone number fix process completed.")

if __name__ == "__main__":
    main()