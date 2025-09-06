#!/usr/bin/env python3
"""
Create an admin user directly through database connection.

This script creates an admin user with the required fields in the database 
without loading the entire Flask application.
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

def create_admin_user():
    """Create an admin user in the database."""
    
    # Admin user details
    admin_details = {
        'name': 'Admin User',
        'email': 'admin@antidote.com',
        'username': 'admin',
        'phone_number': '9999999999',  # Placeholder phone number
        'role': 'admin',
        'role_type': 'admin',
        'is_verified': True,
        'password': generate_password_hash('Admin1234')
    }
    
    try:
        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if the user already exists
        cur.execute("SELECT id, role FROM users WHERE email = %s", (admin_details['email'],))
        existing_user = cur.fetchone()
        
        if existing_user:
            # Update the existing user
            user_id, role = existing_user
            logger.info(f"Admin user with email {admin_details['email']} already exists (ID: {user_id})")
            
            # Update role to admin if not already
            if role != 'admin':
                cur.execute(
                    "UPDATE users SET role = 'admin', role_type = 'admin', is_verified = TRUE WHERE id = %s",
                    (user_id,)
                )
                conn.commit()
                logger.info(f"Updated user ID {user_id} to admin role")
            else:
                logger.info(f"User ID {user_id} already has admin role")
                
            result = {"id": user_id, "email": admin_details['email'], "status": "updated"}
        else:
            # Insert a new admin user
            cur.execute(
                """
                INSERT INTO users (name, email, username, phone_number, role, role_type, is_verified, password_hash, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP) 
                RETURNING id
                """,
                (
                    admin_details['name'],
                    admin_details['email'],
                    admin_details['username'],
                    admin_details['phone_number'],
                    admin_details['role'],
                    admin_details['role_type'],
                    admin_details['is_verified'],
                    admin_details['password']
                )
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Created new admin user with email {admin_details['email']} (ID: {user_id})")
            
            result = {"id": user_id, "email": admin_details['email'], "status": "created"}
        
        # Close connection
        cur.close()
        conn.close()
        
        return result
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        return None

if __name__ == "__main__":
    result = create_admin_user()
    if result:
        logger.info("Admin user operation successful")
        logger.info(f"ID: {result['id']}, Email: {result['email']}, Status: {result['status']}")
        logger.info("Log in with email: admin@antidote.com and password: Admin1234")
    else:
        logger.error("Failed to create admin user")