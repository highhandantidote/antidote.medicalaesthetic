#!/usr/bin/env python3
"""
Standalone script to verify doctor workflow functionality.

This script uses direct database operations to test and demonstrate the
doctor verification workflow without relying on the Flask application.
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

# Database connection parameters from environment variables
DB_URL = os.environ.get('DATABASE_URL')

def get_connection():
    """Get a connection to the database."""
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def get_doctor_status(doctor_id):
    """
    Get a doctor's verification status.
    
    Args:
        doctor_id: ID of the doctor
        
    Returns:
        str: Verification status or None if doctor not found
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Query to get doctor verification status
        cur.execute("""
            SELECT id, user_id, name, verification_status, is_verified 
            FROM doctors 
            WHERE id = %s
        """, (doctor_id,))
        
        doctor = cur.fetchone()
        if not doctor:
            logger.error(f"Doctor with ID {doctor_id} not found")
            return None
        
        logger.info(f"Doctor {doctor_id} status: {doctor['verification_status']}")
        
        # Clean up
        cur.close()
        conn.close()
        
        return doctor['verification_status']
    except Exception as e:
        logger.error(f"Error getting doctor status: {str(e)}")
        return None

def approve_doctor(doctor_id):
    """
    Approve a doctor's verification.
    
    Args:
        doctor_id: ID of the doctor to approve
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # First check if the doctor exists
        cur.execute("SELECT id, user_id FROM doctors WHERE id = %s", (doctor_id,))
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
        logger.info(f"Doctor {doctor_id} successfully approved")
        if updated_doctor:
            logger.info(f"Updated doctor details: {updated_doctor}")
        
        # Clean up
        cur.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error approving doctor: {str(e)}")
        return False

def reject_doctor(doctor_id, reason="Verification requirements not met"):
    """
    Reject a doctor's verification.
    
    Args:
        doctor_id: ID of the doctor to reject
        reason: Reason for rejection
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # First check if the doctor exists
        cur.execute("SELECT id, user_id FROM doctors WHERE id = %s", (doctor_id,))
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
        logger.info(f"Doctor {doctor_id} successfully rejected")
        if updated_doctor:
            logger.info(f"Updated doctor details: {updated_doctor}")
        
        # Clean up
        cur.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error rejecting doctor: {str(e)}")
        return False

def get_all_doctors():
    """Get a list of all doctors with their verification status."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Query to get all doctors and their verification status
        cur.execute("""
            SELECT d.id, d.name, d.verification_status, d.is_verified, u.username
            FROM doctors d
            LEFT JOIN users u ON d.user_id = u.id
            ORDER BY d.id
        """)
        
        doctors = cur.fetchall()
        
        # Clean up
        cur.close()
        conn.close()
        
        return doctors
    except Exception as e:
        logger.error(f"Error getting all doctors: {str(e)}")
        return []

def create_test_doctor(username_base, name, verification_status="pending"):
    """Create a test doctor account for verification testing."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Generate a unique username
        timestamp = int(time.time())
        username = f"{username_base}_{timestamp}"
        
        # First check if the user already exists
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        
        if not user:
            # Create a new user
            cur.execute("""
                INSERT INTO users (
                    username, name, email, phone_number, role, role_type, 
                    is_verified, created_at
                ) VALUES (
                    %s, %s, %s, %s, 'doctor', 'doctor', TRUE, NOW()
                ) RETURNING id
            """, (username, name, f"{username}_{int(time.time())}@example.com", f"98765{int(time.time())%100000}"))
            
            user = cur.fetchone()
            logger.info(f"Created test user: {username} with ID {user['id']}")
        
        # Check if doctor profile exists
        cur.execute("SELECT id FROM doctors WHERE user_id = %s", (user['id'],))
        doctor = cur.fetchone()
        
        if not doctor:
            # Create doctor profile
            cur.execute("""
                INSERT INTO doctors (
                    user_id, name, specialty, experience, city, state, hospital,
                    medical_license_number, qualification, practice_location,
                    verification_status, credentials_url, aadhaar_number, created_at
                ) VALUES (
                    %s, %s, 'Plastic Surgery', 8, 'Mumbai', 'Maharashtra', 'Test Hospital',
                    %s, 'MBBS, MS, MCh Plastic Surgery', 'Mumbai, India',
                    %s, 'test_credential.pdf', %s, NOW()
                ) RETURNING id
            """, (
                user['id'], 
                name, 
                f"MCI-{username}-2025", 
                verification_status,
                f"1234-5678-{user['id']}"
            ))
            
            doctor = cur.fetchone()
            logger.info(f"Created doctor profile with ID {doctor['id']} for {username} with {verification_status} status")
        
        # Commit changes
        conn.commit()
        
        # Clean up
        cur.close()
        conn.close()
        
        return doctor['id'] if doctor else None
    except Exception as e:
        logger.error(f"Error creating test doctor: {str(e)}")
        return None

def main():
    """Test the doctor verification workflow."""
    logger.info("Starting doctor verification workflow test...")
    
    # Test Case 1: Approve a doctor
    logger.info("\n=== Test Case 1: Approve Doctor ===")
    
    # Check if doctor ID was provided as command line argument
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        doctor_id = int(sys.argv[1])
        logger.info(f"Using provided doctor ID: {doctor_id}")
    else:
        # Use a default ID or create a new test doctor
        try:
            doctor_id = create_test_doctor("doctor_test1", "Test Doctor 1")
            if not doctor_id:
                logger.error("Failed to create test doctor. Exiting.")
                return
            logger.info(f"Created new test doctor with ID: {doctor_id}")
        except Exception as e:
            logger.error(f"Error creating test doctor: {str(e)}")
            logger.info("Using default doctor ID 101")
            doctor_id = 101
    
    # Check initial status
    initial_status = get_doctor_status(doctor_id)
    logger.info(f"Initial status: {initial_status}")
    
    if initial_status != "verified":
        # Approve the doctor
        logger.info(f"Approving doctor {doctor_id}...")
        approve_result = approve_doctor(doctor_id)
        
        if approve_result:
            logger.info(f"Successfully approved doctor {doctor_id}")
            
            # Verify status change
            new_status = get_doctor_status(doctor_id)
            if new_status == "verified":
                logger.info(f"Verification successful: status updated to {new_status}")
            else:
                logger.error(f"Verification failed: status is {new_status}, expected 'verified'")
        else:
            logger.error(f"Failed to approve doctor {doctor_id}")
    else:
        logger.info(f"Doctor {doctor_id} is already verified, resetting to pending for demonstration...")
        
        # Reset to pending using direct SQL to demonstrate the workflow
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE doctors 
            SET verification_status = 'pending', is_verified = FALSE 
            WHERE id = %s
        """, (doctor_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Reset doctor {doctor_id} to pending status")
        
        # Now approve the doctor
        logger.info(f"Now approving doctor {doctor_id}...")
        approve_result = approve_doctor(doctor_id)
        
        if approve_result:
            logger.info(f"Successfully approved doctor {doctor_id}")
            
            # Verify status change
            new_status = get_doctor_status(doctor_id)
            if new_status == "verified":
                logger.info(f"Verification successful: status updated to {new_status}")
            else:
                logger.error(f"Verification failed: status is {new_status}, expected 'verified'")
        else:
            logger.error(f"Failed to approve doctor {doctor_id}")
    
    # Test Case 2: Reject a doctor
    logger.info("\n=== Test Case 2: Reject Doctor ===")
    
    # Create a new test doctor
    new_doctor_id = create_test_doctor("doctor_test2", "Test Doctor 2")
    if not new_doctor_id:
        logger.error("Failed to create second test doctor. Skipping rejection test.")
    else:
        logger.info(f"Created test doctor with ID: {new_doctor_id}")
        
        # Check initial status
        initial_status = get_doctor_status(new_doctor_id)
        logger.info(f"Initial status of doctor {new_doctor_id}: {initial_status}")
        
        # Reject the doctor
        logger.info(f"Rejecting doctor {new_doctor_id}...")
        reject_result = reject_doctor(new_doctor_id, "Insufficient credentials")
        
        if reject_result:
            logger.info(f"Successfully rejected doctor {new_doctor_id}")
            
            # Verify status change
            new_status = get_doctor_status(new_doctor_id)
            if new_status == "rejected":
                logger.info(f"Verification successful: status updated to {new_status}")
            else:
                logger.error(f"Verification failed: status is {new_status}, expected 'rejected'")
        else:
            logger.error(f"Failed to reject doctor {new_doctor_id}")
    
    # Show final status of all doctors
    logger.info("\n=== Final Doctor Verification Status ===")
    doctors = get_all_doctors()
    if doctors:
        for doctor in doctors:
            logger.info(f"ID: {doctor['id']}, Name: {doctor['name']}, " + 
                       f"Username: {doctor['username']}, Status: {doctor['verification_status']}")
    else:
        logger.warning("No doctors found in the database")
    
    logger.info("\nDoctor verification workflow test completed!")

if __name__ == "__main__":
    main()