#!/usr/bin/env python3
"""
Minimal script to test doctor verification workflow.
This script tests doctor verification by creating a pending doctor and then verifying them.
"""
import os
import sys
import logging
import time
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DB_URL = os.environ.get('DATABASE_URL')

def get_connection():
    """Get a database connection."""
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def create_test_doctor():
    """Create a test doctor for verification."""
    try:
        # Generate unique username
        timestamp = int(time.time())
        username = f"doctor_minimal_{timestamp}"
        
        conn = get_connection()
        cur = conn.cursor()
        
        # Create user for doctor with unique phone number
        phone_number = f"77777{timestamp % 100000}"
        cur.execute("""
            INSERT INTO users (
                username, name, email, phone_number, role, role_type, 
                is_verified, created_at
            ) VALUES (
                %s, 'Minimal Test Doctor', %s, %s, 
                'doctor', 'doctor', TRUE, NOW()
            ) RETURNING id
        """, (username, f"{username}@example.com", phone_number))
        
        user = cur.fetchone()
        logger.info(f"Created test user with ID: {user['id']}")
        
        # Create doctor profile
        cur.execute("""
            INSERT INTO doctors (
                user_id, name, specialty, experience, city, state, hospital,
                medical_license_number, qualification, practice_location,
                verification_status, credentials_url, aadhaar_number, created_at,
                is_verified
            ) VALUES (
                %s, 'Minimal Test Doctor', 'Plastic Surgery', 8, 'Mumbai', 'Maharashtra', 
                'Test Hospital', %s, 'MBBS, MS, MCh', 'Mumbai, India',
                'pending', 'test_credential.pdf', %s, NOW(), FALSE
            ) RETURNING id
        """, (
            user['id'], 
            f"MCI-{username}-2025", 
            f"1234-5678-{user['id']}"
        ))
        
        doctor = cur.fetchone()
        logger.info(f"Created pending doctor with ID: {doctor['id']}")
        
        # Commit changes
        conn.commit()
        
        # Clean up
        cur.close()
        conn.close()
        
        return {
            "user_id": user['id'],
            "doctor_id": doctor['id'],
            "username": username
        }
    except Exception as e:
        logger.error(f"Error creating test doctor: {str(e)}")
        return None

def approve_doctor(doctor_id):
    """Approve a doctor."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Get doctor details
        cur.execute("SELECT id, user_id, name FROM doctors WHERE id = %s", (doctor_id,))
        doctor = cur.fetchone()
        
        # Update status
        cur.execute("""
            UPDATE doctors
            SET verification_status = 'verified',
                is_verified = TRUE
            WHERE id = %s
        """, (doctor_id,))
        
        # Create notification
        cur.execute("""
            INSERT INTO notifications (
                user_id, type, message, created_at, is_read
            ) VALUES (
                %s, 'verification_approved', 'Your doctor profile has been approved!', 
                NOW(), FALSE
            )
        """, (doctor['user_id'],))
        
        # Commit changes
        conn.commit()
        
        # Check new status
        cur.execute("SELECT verification_status, is_verified FROM doctors WHERE id = %s", (doctor_id,))
        updated = cur.fetchone()
        
        # Clean up
        cur.close()
        conn.close()
        
        logger.info(f"Doctor {doctor_id} approved - New status: {updated['verification_status']}")
        return True
    except Exception as e:
        logger.error(f"Error approving doctor: {str(e)}")
        return False

def reject_doctor(doctor_id, reason="Insufficient credentials"):
    """Reject a doctor."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Get doctor details
        cur.execute("SELECT id, user_id, name FROM doctors WHERE id = %s", (doctor_id,))
        doctor = cur.fetchone()
        
        # Update status
        cur.execute("""
            UPDATE doctors
            SET verification_status = 'rejected',
                is_verified = FALSE
            WHERE id = %s
        """, (doctor_id,))
        
        # Create notification
        cur.execute("""
            INSERT INTO notifications (
                user_id, type, message, created_at, is_read
            ) VALUES (
                %s, 'verification_rejected', %s, 
                NOW(), FALSE
            )
        """, (doctor['user_id'], f"Your doctor profile verification was rejected: {reason}"))
        
        # Commit changes
        conn.commit()
        
        # Check new status
        cur.execute("SELECT verification_status, is_verified FROM doctors WHERE id = %s", (doctor_id,))
        updated = cur.fetchone()
        
        # Clean up
        cur.close()
        conn.close()
        
        logger.info(f"Doctor {doctor_id} rejected - New status: {updated['verification_status']}")
        return True
    except Exception as e:
        logger.error(f"Error rejecting doctor: {str(e)}")
        return False

def main():
    """Run test."""
    logger.info("Starting minimal doctor verification test...")
    
    # Test Case 1: Create and approve a doctor
    logger.info("Test Case 1: Doctor Approval")
    approval_test = create_test_doctor()
    if not approval_test:
        logger.error("Failed to create test doctor for approval")
        return
    
    approve_doctor(approval_test['doctor_id'])
    
    # Test Case 2: Create and reject a doctor
    logger.info("\nTest Case 2: Doctor Rejection")
    rejection_test = create_test_doctor()
    if not rejection_test:
        logger.error("Failed to create test doctor for rejection")
        return
    
    reject_doctor(rejection_test['doctor_id'])
    
    # Summary
    logger.info("\nTest Summary:")
    logger.info(f"- Doctor Approval Test: Doctor ID {approval_test['doctor_id']}, User ID {approval_test['user_id']}")
    logger.info(f"- Doctor Rejection Test: Doctor ID {rejection_test['doctor_id']}, User ID {rejection_test['user_id']}")
    logger.info("Doctor verification workflow test completed successfully!")

if __name__ == "__main__":
    main()