#!/usr/bin/env python3
"""
Test the doctor verification workflow for the Antidote platform.

This script tests both doctor approval and rejection workflows using direct database operations.
It logs the time taken for each operation and verifies the status changes.
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

def create_test_doctor(username, name, verification_status="pending"):
    """Create a test doctor account for verification testing."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Generate a unique username with timestamp to avoid conflicts
        timestamp = int(time.time())
        unique_username = f"{username}_{timestamp}"
        
        # Create a new user
        cur.execute("""
            INSERT INTO users (
                username, name, email, phone_number, role, role_type, 
                is_verified, created_at
            ) VALUES (
                %s, %s, %s, %s, 'doctor', 'doctor', TRUE, NOW()
            ) RETURNING id
        """, (unique_username, name, f"{unique_username}@example.com", f"98765{timestamp%100000}"))
        
        user = cur.fetchone()
        logger.info(f"Created test user: {unique_username} with ID {user['id']}")
        
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
            f"MCI-{unique_username}-2025", 
            verification_status,
            f"1234-5678-{user['id']}"
        ))
        
        doctor = cur.fetchone()
        logger.info(f"Created doctor profile with ID {doctor['id']} for {unique_username} with {verification_status} status")
        
        # Commit changes
        conn.commit()
        
        # Clean up
        cur.close()
        conn.close()
        
        return doctor['id']
    except Exception as e:
        logger.error(f"Error creating test doctor: {str(e)}")
        return None

def approve_doctor(doctor_id):
    """Approve a doctor's verification through direct database update."""
    try:
        start_time = time.time()
        
        conn = get_connection()
        cur = conn.cursor()
        
        # Get doctor info to notify the user
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
        
        # Calculate time taken
        elapsed_time = time.time() - start_time
        
        # Log success
        logger.info(f"Doctor {doctor_id} successfully approved in {elapsed_time:.2f} seconds")
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
    """Reject a doctor's verification through direct database update."""
    try:
        start_time = time.time()
        
        conn = get_connection()
        cur = conn.cursor()
        
        # Get doctor info to notify the user
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
        
        # Calculate time taken
        elapsed_time = time.time() - start_time
        
        # Log success
        logger.info(f"Doctor {doctor_id} successfully rejected in {elapsed_time:.2f} seconds")
        if updated_doctor:
            logger.info(f"Updated doctor details: {updated_doctor}")
        
        # Clean up
        cur.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error rejecting doctor: {str(e)}")
        return False

def verify_status_change(doctor_id, expected_status):
    """Verify that the doctor's verification status was updated correctly."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Query to get doctor verification status
        cur.execute("""
            SELECT id, name, verification_status, is_verified 
            FROM doctors 
            WHERE id = %s
        """, (doctor_id,))
        
        doctor = cur.fetchone()
        if not doctor:
            logger.error(f"Doctor with ID {doctor_id} not found")
            return False
        
        actual_status = doctor['verification_status']
        result = actual_status == expected_status
        
        if result:
            logger.info(f"Status verification successful: Doctor {doctor_id} has status '{actual_status}'")
        else:
            logger.error(f"Status verification failed: Doctor {doctor_id} has status '{actual_status}', expected '{expected_status}'")
        
        # Clean up
        cur.close()
        conn.close()
        
        return result
    except Exception as e:
        logger.error(f"Error verifying doctor status: {str(e)}")
        return False

def get_all_doctors_status():
    """Get status of all doctors for verification."""
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

def main():
    """Run the doctor verification workflow tests."""
    logger.info("Starting doctor verification workflow tests...")
    
    # Test Case 1: Create, Approve, and Verify a Doctor
    logger.info("\n=== Test Case 1: Create and Approve Doctor ===")
    
    doctor1_id = create_test_doctor("doctor_approval_test", "Test Doctor Approval")
    if doctor1_id:
        # Approve the doctor
        logger.info(f"Approving doctor {doctor1_id}...")
        if approve_doctor(doctor1_id):
            # Verify the status change
            verify_status_change(doctor1_id, "verified")
        else:
            logger.error(f"Failed to approve doctor {doctor1_id}")
    else:
        logger.error("Failed to create test doctor for approval test")
    
    # Test Case 2: Create, Reject, and Verify a Doctor
    logger.info("\n=== Test Case 2: Create and Reject Doctor ===")
    
    doctor2_id = create_test_doctor("doctor_rejection_test", "Test Doctor Rejection")
    if doctor2_id:
        # Reject the doctor
        logger.info(f"Rejecting doctor {doctor2_id}...")
        if reject_doctor(doctor2_id, "Missing or incomplete credentials"):
            # Verify the status change
            verify_status_change(doctor2_id, "rejected")
        else:
            logger.error(f"Failed to reject doctor {doctor2_id}")
    else:
        logger.error("Failed to create test doctor for rejection test")
    
    # Show final status of all doctors
    logger.info("\n=== Final Doctor Verification Status ===")
    doctors = get_all_doctors_status()
    if doctors:
        for doctor in doctors:
            logger.info(f"ID: {doctor['id']}, Name: {doctor['name']}, " + 
                      f"Username: {doctor['username']}, Status: {doctor['verification_status']}")
    else:
        logger.warning("No doctors found in the database")
    
    logger.info("Doctor verification workflow tests completed!")

if __name__ == "__main__":
    main()