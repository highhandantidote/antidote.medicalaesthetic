#!/usr/bin/env python3
"""
Super minimal script to create test users for doctor verification
"""
import os
import sys
import logging
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DB_URL = os.environ.get('DATABASE_URL')

def get_connection():
    """Get a connection to the database."""
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def main():
    """Create bare minimum test data for doctor verification"""
    try:
        # Connect to database
        conn = get_connection()
        cur = conn.cursor()
        
        # Create admin user if it doesn't exist
        admin_username = "admin_test"
        cur.execute("SELECT id FROM users WHERE username = %s", (admin_username,))
        admin_user = cur.fetchone()
        
        if not admin_user:
            # Create admin user
            cur.execute("""
                INSERT INTO users (
                    username, name, email, phone_number, role, role_type, 
                    is_verified, created_at
                ) VALUES (
                    %s, 'Admin User', 'admin@example.com', '9999999999', 
                    'admin', 'admin', TRUE, NOW()
                ) RETURNING id
            """, (admin_username,))
            
            admin_user = cur.fetchone()
            logger.info(f"Created admin user with ID: {admin_user['id']}")
        else:
            logger.info(f"Admin user already exists with ID: {admin_user['id']}")
        
        # Create a pending doctor for verification
        timestamp = int(time.time())
        doctor_username = f"doctor_pending_{timestamp}"
        
        # Create user for doctor
        cur.execute("""
            INSERT INTO users (
                username, name, email, phone_number, role, role_type, 
                is_verified, created_at
            ) VALUES (
                %s, 'Test Pending Doctor', %s, '8888888888', 
                'doctor', 'doctor', TRUE, NOW()
            ) RETURNING id
        """, (doctor_username, f"{doctor_username}@example.com"))
        
        doctor_user = cur.fetchone()
        logger.info(f"Created doctor user with ID: {doctor_user['id']}")
        
        # Create doctor profile with pending status
        cur.execute("""
            INSERT INTO doctors (
                user_id, name, specialty, experience, city, state, hospital,
                medical_license_number, qualification, practice_location,
                verification_status, credentials_url, aadhaar_number, created_at, 
                is_verified
            ) VALUES (
                %s, 'Test Pending Doctor', 'Plastic Surgery', 8, 'Mumbai', 'Maharashtra', 
                'Test Hospital', %s, 'MBBS, MS, MCh', 'Mumbai, India',
                'pending', 'test_credential.pdf', %s, NOW(), FALSE
            ) RETURNING id
        """, (
            doctor_user['id'], 
            f"MCI-{doctor_username}-2025", 
            f"1234-5678-{doctor_user['id']}"
        ))
        
        doctor = cur.fetchone()
        logger.info(f"Created pending doctor with ID: {doctor['id']}")
        
        # Commit changes
        conn.commit()
        
        # Output verification instructions
        print("\n============ Verification Test Instructions ============")
        print(f"1. Admin User ID: {admin_user['id']}")
        print(f"   Username: {admin_username}")
        print(f"2. Doctor User ID: {doctor_user['id']}")
        print(f"   Username: {doctor_username}")
        print(f"3. Doctor Profile ID: {doctor['id']}")
        print(f"   Status: pending")
        print("\nTo approve the doctor, use:")
        print(f"   UPDATE doctors SET verification_status = 'verified', is_verified = TRUE WHERE id = {doctor['id']};")
        print("\nTo reject the doctor, use:")
        print(f"   UPDATE doctors SET verification_status = 'rejected', is_verified = FALSE WHERE id = {doctor['id']};")
        print("=====================================================\n")
        
        # Clean up
        cur.close()
        conn.close()
        
        return {
            "admin_id": admin_user['id'],
            "doctor_user_id": doctor_user['id'],
            "doctor_id": doctor['id']
        }
    except Exception as e:
        logger.error(f"Error creating test data: {str(e)}")
        return None

if __name__ == "__main__":
    main()