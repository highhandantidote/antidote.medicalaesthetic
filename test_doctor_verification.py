#!/usr/bin/env python3
"""
Test doctor verification workflow.

This script performs:
1. Manual testing of doctor approval
2. Manual testing of doctor rejection
3. Verification of notification creation
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

def get_pending_doctors():
    """Get a list of doctors with pending verification."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Query to get all doctors with pending verification
        cur.execute("""
            SELECT d.id, d.name, d.verification_status, d.is_verified, u.username, d.user_id
            FROM doctors d
            LEFT JOIN users u ON d.user_id = u.id
            WHERE d.verification_status = 'pending'
            ORDER BY d.id
        """)
        
        doctors = cur.fetchall()
        
        # Clean up
        cur.close()
        conn.close()
        
        return doctors
    except Exception as e:
        logger.error(f"Error getting pending doctors: {str(e)}")
        return []

def approve_doctor(doctor_id):
    """Approve a doctor's verification."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # First get the doctor's user_id for notification
        cur.execute("SELECT id, user_id, name FROM doctors WHERE id = %s", (doctor_id,))
        doctor = cur.fetchone()
        if not doctor:
            logger.error(f"Doctor with ID {doctor_id} not found")
            return False
        
        # Update doctor verification status
        cur.execute("""
            UPDATE doctors
            SET verification_status = 'verified',
                is_verified = TRUE
            WHERE id = %s
            RETURNING id, name, verification_status
        """, (doctor_id,))
        
        updated_doctor = cur.fetchone()
        
        # Create a notification for the doctor
        if doctor['user_id']:
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
        
        # Log success
        logger.info(f"Doctor {doctor_id} ({doctor['name']}) successfully approved")
        
        # Clean up
        cur.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error approving doctor: {str(e)}")
        return False

def reject_doctor(doctor_id, reason="Verification requirements not met"):
    """Reject a doctor's verification."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # First get the doctor's user_id for notification
        cur.execute("SELECT id, user_id, name FROM doctors WHERE id = %s", (doctor_id,))
        doctor = cur.fetchone()
        if not doctor:
            logger.error(f"Doctor with ID {doctor_id} not found")
            return False
        
        # Update doctor verification status
        cur.execute("""
            UPDATE doctors
            SET verification_status = 'rejected',
                is_verified = FALSE
            WHERE id = %s
            RETURNING id, name, verification_status
        """, (doctor_id,))
        
        updated_doctor = cur.fetchone()
        
        # Create a notification for the doctor
        if doctor['user_id']:
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
        
        # Log success
        logger.info(f"Doctor {doctor_id} ({doctor['name']}) successfully rejected with reason: {reason}")
        
        # Clean up
        cur.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error rejecting doctor: {str(e)}")
        return False

def check_doctor_status(doctor_id):
    """Check the verification status of a doctor."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Query to get doctor verification status
        cur.execute("""
            SELECT d.id, d.name, d.verification_status, d.is_verified, u.username
            FROM doctors d
            LEFT JOIN users u ON d.user_id = u.id
            WHERE d.id = %s
        """, (doctor_id,))
        
        doctor = cur.fetchone()
        
        # Clean up
        cur.close()
        conn.close()
        
        if doctor:
            logger.info(f"Doctor {doctor_id} status: {doctor['verification_status']}")
            return doctor
        else:
            logger.error(f"Doctor with ID {doctor_id} not found")
            return None
    except Exception as e:
        logger.error(f"Error checking doctor status: {str(e)}")
        return None

def check_notifications(user_id):
    """Check notifications for a user."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Query to get notifications for the user
        cur.execute("""
            SELECT id, type, message, created_at, is_read
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        
        notifications = cur.fetchall()
        
        # Clean up
        cur.close()
        conn.close()
        
        if notifications:
            logger.info(f"Found {len(notifications)} notifications for user {user_id}")
            for notification in notifications:
                logger.info(f"Notification: {notification['message']} ({notification['type']})")
            return notifications
        else:
            logger.warning(f"No notifications found for user {user_id}")
            return []
    except Exception as e:
        logger.error(f"Error checking notifications: {str(e)}")
        return []

def create_test_doctor():
    """Create a test doctor with pending verification status."""
    try:
        # Generate unique identifier
        timestamp = int(time.time())
        username = f"doctor_test_{timestamp}"
        
        conn = get_connection()
        cur = conn.cursor()
        
        # Create user for doctor
        cur.execute("""
            INSERT INTO users (
                username, name, email, phone_number, role, role_type, 
                is_verified, created_at
            ) VALUES (
                %s, 'Test Doctor', %s, '7777777777', 
                'doctor', 'doctor', TRUE, NOW()
            ) RETURNING id
        """, (username, f"{username}@example.com"))
        
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
                %s, 'Test Doctor', 'Plastic Surgery', 8, 'Mumbai', 'Maharashtra', 
                'Test Hospital', %s, 'MBBS, MS, MCh', 'Mumbai, India',
                'pending', 'test_credential.pdf', %s, NOW(), FALSE
            ) RETURNING id
        """, (
            user['id'], 
            f"MCI-{username}-2025", 
            f"1234-5678-{user['id']}"
        ))
        
        doctor = cur.fetchone()
        logger.info(f"Created test doctor with ID: {doctor['id']}")
        
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

def main():
    """Run the doctor verification workflow test cases."""
    logger.info("Starting doctor verification workflow testing...")
    
    # Check if we have pending doctors already
    pending_doctors = get_pending_doctors()
    if pending_doctors:
        logger.info(f"Found {len(pending_doctors)} pending doctors")
        test_doctor_id = pending_doctors[0]['id']
        test_user_id = pending_doctors[0]['user_id']
        test_username = pending_doctors[0]['username']
        logger.info(f"Using existing pending doctor: ID {test_doctor_id}, Username: {test_username}")
    else:
        # Create a test doctor
        logger.info("No pending doctors found, creating a test doctor...")
        test_data = create_test_doctor()
        if not test_data:
            logger.error("Failed to create test doctor. Exiting.")
            return
        test_doctor_id = test_data['doctor_id']
        test_user_id = test_data['user_id']
        test_username = test_data['username']
    
    # Check initial status
    logger.info("\n=== Initial Status ===")
    check_doctor_status(test_doctor_id)
    
    # Test Case 1: Approve a doctor
    logger.info("\n=== Test Case 1: Approve Doctor ===")
    logger.info(f"Approving doctor {test_doctor_id}...")
    
    if approve_doctor(test_doctor_id):
        # Verify status change
        doctor = check_doctor_status(test_doctor_id)
        if doctor and doctor['verification_status'] == 'verified' and doctor['is_verified']:
            logger.info("✓ Doctor approval successful")
        else:
            logger.error("✗ Doctor approval verification failed")
        
        # Check notifications
        logger.info(f"Checking notifications for user {test_user_id}...")
        notifications = check_notifications(test_user_id)
        if notifications and any(n['type'] == 'verification_approved' for n in notifications):
            logger.info("✓ Approval notification created successfully")
        else:
            logger.error("✗ Failed to create approval notification")
    else:
        logger.error("✗ Failed to approve doctor")
    
    # Create another test doctor for rejection
    logger.info("\n=== Creating a new test doctor for rejection ===")
    test_data2 = create_test_doctor()
    if not test_data2:
        logger.error("Failed to create second test doctor. Skipping rejection test.")
        return
    
    test_doctor_id2 = test_data2['doctor_id']
    test_user_id2 = test_data2['user_id']
    test_username2 = test_data2['username']
    
    # Test Case 2: Reject a doctor
    logger.info("\n=== Test Case 2: Reject Doctor ===")
    logger.info(f"Rejecting doctor {test_doctor_id2}...")
    
    if reject_doctor(test_doctor_id2, "Invalid or insufficient credentials"):
        # Verify status change
        doctor = check_doctor_status(test_doctor_id2)
        if doctor and doctor['verification_status'] == 'rejected' and not doctor['is_verified']:
            logger.info("✓ Doctor rejection successful")
        else:
            logger.error("✗ Doctor rejection verification failed")
        
        # Check notifications
        logger.info(f"Checking notifications for user {test_user_id2}...")
        notifications = check_notifications(test_user_id2)
        if notifications and any(n['type'] == 'verification_rejected' for n in notifications):
            logger.info("✓ Rejection notification created successfully")
        else:
            logger.error("✗ Failed to create rejection notification")
    else:
        logger.error("✗ Failed to reject doctor")
    
    logger.info("\n=== Doctor Verification Workflow Testing Completed ===")
    logger.info("Summary:")
    logger.info(f"  - Doctor 1 (ID: {test_doctor_id}, Username: {test_username}): Approval tested")
    logger.info(f"  - Doctor 2 (ID: {test_doctor_id2}, Username: {test_username2}): Rejection tested")

if __name__ == "__main__":
    main()