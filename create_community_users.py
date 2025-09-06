#!/usr/bin/env python3
"""
Create community user accounts and expert accounts for the Antidote platform.

This script creates patient accounts and in-house expert accounts that will be used
in community discussions and replies.
"""

import os
import sys
import logging
from datetime import datetime
import psycopg2
from werkzeug.security import generate_password_hash

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def create_patient_accounts():
    """Create patient user accounts."""
    patient_accounts = [
        {
            'username': 'NebulaNoodle',
            'email': 'nebulanoodle@antidote.com',
            'name': 'Nebula Noodle',
            'role': 'patient'
        },
        {
            'username': 'StardustMoss',
            'email': 'stardustmoss@antidote.com',
            'name': 'Stardust Moss',
            'role': 'patient'
        },
        {
            'username': 'ZodiacPeach',
            'email': 'zodiacpeach@antidote.com',
            'name': 'Zodiac Peach',
            'role': 'patient'
        },
        {
            'username': 'OrbitBunny',
            'email': 'orbitbunny@antidote.com',
            'name': 'Orbit Bunny',
            'role': 'patient'
        },
        {
            'username': 'GalaxiGlow',
            'email': 'galaxiglow@antidote.com',
            'name': 'Galaxi Glow',
            'role': 'patient'
        },
        {
            'username': 'MossyMoon',
            'email': 'mossymoon@antidote.com',
            'name': 'Mossy Moon',
            'role': 'patient'
        },
        {
            'username': 'FernFizz',
            'email': 'fernfizz@antidote.com',
            'name': 'Fern Fizz',
            'role': 'patient'
        },
        {
            'username': 'PetalDrift',
            'email': 'petaldrift@antidote.com',
            'name': 'Petal Drift',
            'role': 'patient'
        },
        {
            'username': 'CloudberryPop',
            'email': 'cloudberrypop@antidote.com',
            'name': 'Cloudberry Pop',
            'role': 'patient'
        },
        {
            'username': 'LeafLagoon',
            'email': 'leaflagoon@antidote.com',
            'name': 'Leaf Lagoon',
            'role': 'patient'
        }
    ]
    
    return patient_accounts

def create_expert_accounts():
    """Create expert user accounts."""
    expert_accounts = [
        {
            'username': 'expert_wyvern',
            'email': 'expert.wyvern@antidote.com',
            'name': 'Expert Wyvern',
            'role': 'expert'
        },
        {
            'username': 'expert_sequoia',
            'email': 'expert.sequoia@antidote.com',
            'name': 'Expert Sequoia',
            'role': 'expert'
        },
        {
            'username': 'expert_fenrir',
            'email': 'expert.fenrir@antidote.com',
            'name': 'Expert Fenrir',
            'role': 'expert'
        },
        {
            'username': 'expert_onyx',
            'email': 'expert.onyx@antidote.com',
            'name': 'Expert Onyx',
            'role': 'expert'
        }
    ]
    
    return expert_accounts

def insert_users(conn, users):
    """Insert users into the database."""
    try:
        with conn.cursor() as cursor:
            created_count = 0
            skipped_count = 0
            
            for user in users:
                # Check if user already exists
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s OR email = %s",
                    (user['username'], user['email'])
                )
                
                if cursor.fetchone():
                    logger.info(f"User {user['username']} already exists, skipping...")
                    skipped_count += 1
                    continue
                
                # Generate password hash
                password_hash = generate_password_hash("password123")  # Default password
                
                # Insert user
                cursor.execute("""
                    INSERT INTO users (
                        username, email, name, role, password_hash, 
                        is_verified, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    user['username'],
                    user['email'],
                    user['name'],
                    user['role'],
                    password_hash,
                    True,  # All accounts are verified
                    datetime.now()
                ))
                
                created_count += 1
                logger.info(f"Created {user['role']} account: {user['username']}")
            
            conn.commit()
            logger.info(f"Successfully created {created_count} users, skipped {skipped_count} existing users")
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting users: {str(e)}")
        raise

def main():
    """Main function to create community users."""
    logger.info("Starting community user creation...")
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return 1
    
    try:
        # Create patient accounts
        logger.info("Creating patient accounts...")
        patient_accounts = create_patient_accounts()
        insert_users(conn, patient_accounts)
        
        # Create expert accounts
        logger.info("Creating expert accounts...")
        expert_accounts = create_expert_accounts()
        insert_users(conn, expert_accounts)
        
        # Summary
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'patient'")
            result = cursor.fetchone()
            patient_count = result[0] if result else 0
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'expert'")
            result = cursor.fetchone()
            expert_count = result[0] if result else 0
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'doctor'")
            result = cursor.fetchone()
            doctor_count = result[0] if result else 0
        
        logger.info(f"=== USER ACCOUNT SUMMARY ===")
        logger.info(f"Total Patients: {patient_count}")
        logger.info(f"Total Experts: {expert_count}")
        logger.info(f"Total Doctors: {doctor_count}")
        logger.info(f"=== Community user creation completed successfully ===")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during community user creation: {str(e)}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())