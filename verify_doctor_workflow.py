#!/usr/bin/env python3
"""
Doctor verification workflow utility.

This module provides standalone functions for the doctor verification workflow,
allowing administrators to approve or reject doctor verification requests
and handle the associated notifications.

Usage:
    - Import and use these functions directly in Flask routes or API endpoints 
    - Run this script directly to test the doctor verification workflow
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
    """Get a database connection."""
    try:
        return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

def get_pending_doctors(limit=100, offset=0):
    """
    Get a list of pending doctor verification requests.
    
    Args:
        limit: Maximum number of records to return (default: 100)
        offset: Number of records to skip (default: 0)
        
    Returns:
        List of doctor records with pending verification
    """
    try:
        conn = get_connection()
        if not conn:
            return []
            
        cur = conn.cursor()
        
        # Query to get all doctors with pending verification
        cur.execute("""
            SELECT d.id, d.user_id, d.name, d.specialty, d.experience, 
                   d.city, d.state, d.hospital, d.medical_license_number,
                   d.qualification, d.practice_location, d.verification_status,
                   d.credentials_url, d.aadhaar_number, d.is_verified, d.created_at,
                   u.username, u.email, u.phone_number
            FROM doctors d
            LEFT JOIN users u ON d.user_id = u.id
            WHERE d.verification_status = 'pending'
            ORDER BY d.created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        doctors = cur.fetchall()
        
        # Clean up
        cur.close()
        conn.close()
        
        return doctors
    except Exception as e:
        logger.error(f"Error getting pending doctors: {str(e)}")
        return []

def get_doctor_details(doctor_id):
    """
    Get detailed information about a specific doctor.
    
    Args:
        doctor_id: ID of the doctor to retrieve
        
    Returns:
        Dictionary containing doctor details or None if not found
    """
    try:
        conn = get_connection()
        if not conn:
            return None
            
        cur = conn.cursor()
        
        # Query to get doctor details
        cur.execute("""
            SELECT d.id, d.user_id, d.name, d.specialty, d.experience, 
                   d.city, d.state, d.hospital, d.medical_license_number,
                   d.qualification, d.practice_location, d.verification_status,
                   d.credentials_url, d.aadhaar_number, d.is_verified, d.created_at,
                   u.username, u.email, u.phone_number
            FROM doctors d
            LEFT JOIN users u ON d.user_id = u.id
            WHERE d.id = %s
        """, (doctor_id,))
        
        doctor = cur.fetchone()
        
        # Clean up
        cur.close()
        conn.close()
        
        return doctor
    except Exception as e:
        logger.error(f"Error getting doctor details: {str(e)}")
        return None

def approve_doctor(doctor_id, admin_id=None):
    """
    Approve a doctor's verification request.
    
    Args:
        doctor_id: ID of the doctor to approve
        admin_id: ID of the admin user performing the approval (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = get_connection()
        if not conn:
            return False
            
        cur = conn.cursor()
        
        # First get the doctor's user_id for notification
        cur.execute("SELECT id, user_id, name FROM doctors WHERE id = %s", (doctor_id,))
        doctor = cur.fetchone()
        
        if not doctor:
            logger.error(f"Doctor with ID {doctor_id} not found")
            cur.close()
            conn.close()
            return False
        
        # Update doctor verification status
        cur.execute("""
            UPDATE doctors
            SET verification_status = 'verified',
                is_verified = TRUE
            WHERE id = %s
            RETURNING id, name
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
                ) RETURNING id
            """, (doctor['user_id'],))
            
            notification = cur.fetchone()
            notification_id = notification['id'] if notification else None
            
            # Log the approval
            if admin_id:
                cur.execute("""
                    INSERT INTO admin_logs (
                        admin_id, action, entity_type, entity_id, details, created_at
                    ) VALUES (
                        %s, 'approve', 'doctor', %s, %s, NOW()
                    )
                """, (
                    admin_id, 
                    doctor_id, 
                    f"Approved doctor {doctor['name']} (ID: {doctor_id})"
                ))
        
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

def reject_doctor(doctor_id, reason="Verification requirements not met", admin_id=None):
    """
    Reject a doctor's verification request.
    
    Args:
        doctor_id: ID of the doctor to reject
        reason: Reason for rejection (default: "Verification requirements not met")
        admin_id: ID of the admin user performing the rejection (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = get_connection()
        if not conn:
            return False
            
        cur = conn.cursor()
        
        # First get the doctor's user_id for notification
        cur.execute("SELECT id, user_id, name FROM doctors WHERE id = %s", (doctor_id,))
        doctor = cur.fetchone()
        
        if not doctor:
            logger.error(f"Doctor with ID {doctor_id} not found")
            cur.close()
            conn.close()
            return False
        
        # Update doctor verification status
        cur.execute("""
            UPDATE doctors
            SET verification_status = 'rejected',
                is_verified = FALSE
            WHERE id = %s
            RETURNING id, name
        """, (doctor_id,))
        
        updated_doctor = cur.fetchone()
        
        # Create a notification for the doctor
        if doctor['user_id']:
            notification_message = f"Your doctor profile verification was rejected: {reason}"
            
            cur.execute("""
                INSERT INTO notifications (
                    user_id, type, message, created_at, is_read
                ) VALUES (
                    %s, 'verification_rejected', %s, 
                    NOW(), FALSE
                ) RETURNING id
            """, (doctor['user_id'], notification_message))
            
            notification = cur.fetchone()
            notification_id = notification['id'] if notification else None
            
            # Log the rejection
            if admin_id:
                cur.execute("""
                    INSERT INTO admin_logs (
                        admin_id, action, entity_type, entity_id, details, created_at
                    ) VALUES (
                        %s, 'reject', 'doctor', %s, %s, NOW()
                    )
                """, (
                    admin_id, 
                    doctor_id, 
                    f"Rejected doctor {doctor['name']} (ID: {doctor_id}) - Reason: {reason}"
                ))
        
        # Commit changes
        conn.commit()
        
        # Log success
        logger.info(f"Doctor {doctor_id} ({doctor['name']}) successfully rejected")
        logger.info(f"Rejection reason: {reason}")
        
        # Clean up
        cur.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error rejecting doctor: {str(e)}")
        return False

def get_verification_stats():
    """
    Get statistics on doctor verification.
    
    Returns:
        Dictionary containing verification statistics
    """
    try:
        conn = get_connection()
        if not conn:
            return {}
            
        cur = conn.cursor()
        
        # Query to get verification statistics
        cur.execute("""
            SELECT 
                verification_status,
                COUNT(*) as count
            FROM doctors
            GROUP BY verification_status
            ORDER BY verification_status
        """)
        
        status_counts = cur.fetchall()
        
        # Clean up
        cur.close()
        conn.close()
        
        # Format the results
        stats = {
            'total': sum(row['count'] for row in status_counts),
            'statuses': {row['verification_status']: row['count'] for row in status_counts}
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting verification stats: {str(e)}")
        return {}

def find_doctors_by_criteria(search_text=None, status=None, limit=50, offset=0):
    """
    Search for doctors by various criteria.
    
    Args:
        search_text: Text to search in name, username, email, or license number
        status: Verification status filter ('pending', 'verified', 'rejected')
        limit: Maximum number of records to return
        offset: Number of records to skip for pagination
        
    Returns:
        List of doctors matching the criteria
    """
    try:
        conn = get_connection()
        if not conn:
            return []
            
        cur = conn.cursor()
        
        # Build the query
        query = """
            SELECT d.id, d.user_id, d.name, d.specialty, d.verification_status,
                   d.is_verified, d.created_at, u.username, u.email
            FROM doctors d
            LEFT JOIN users u ON d.user_id = u.id
            WHERE 1=1
        """
        
        # Prepare parameters list
        params = []
        
        # Add search condition if provided
        if search_text:
            query += """
                AND (
                    d.name ILIKE %s OR
                    u.username ILIKE %s OR
                    u.email ILIKE %s OR
                    d.medical_license_number ILIKE %s
                )
            """
            search_pattern = f"%{search_text}%"
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
        
        # Add status filter if provided
        if status:
            query += " AND d.verification_status = %s"
            params.append(status)
        
        # Add order, limit and offset
        query += """
            ORDER BY d.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        # Execute the query
        cur.execute(query, params)
        doctors = cur.fetchall()
        
        # Clean up
        cur.close()
        conn.close()
        
        return doctors
    except Exception as e:
        logger.error(f"Error searching doctors: {str(e)}")
        return []

def test_workflow():
    """Run a test of the doctor verification workflow."""
    logger.info("Testing doctor verification workflow...")
    
    # 1. Get verification statistics
    stats = get_verification_stats()
    logger.info(f"Current verification statistics: {stats}")
    
    # 2. Get pending doctors
    pending_doctors = get_pending_doctors(limit=5)
    if pending_doctors:
        logger.info(f"Found {len(pending_doctors)} pending verification requests")
        
        # Display the first pending doctor
        doctor = pending_doctors[0]
        logger.info(f"Sample pending doctor: {doctor['name']} (ID: {doctor['id']})")
        
        # 3. Test approval workflow
        logger.info(f"Testing approval for doctor ID {doctor['id']}...")
        if approve_doctor(doctor['id']):
            logger.info("✓ Doctor approval successful")
        else:
            logger.error("✗ Doctor approval failed")
            
        # 4. Create a test doctor for rejection
        # This would normally be done via the UI registration process
        
        # 5. Get another pending doctor (if any) for rejection test
        remaining_pending = get_pending_doctors(limit=1)
        if remaining_pending:
            reject_doctor_id = remaining_pending[0]['id']
            logger.info(f"Testing rejection for doctor ID {reject_doctor_id}...")
            if reject_doctor(reject_doctor_id, "Documentation incomplete or invalid"):
                logger.info("✓ Doctor rejection successful")
            else:
                logger.error("✗ Doctor rejection failed")
        else:
            logger.info("No more pending doctors available for rejection test")
    else:
        logger.warning("No pending doctors found for testing")
    
    # 6. Get updated statistics
    updated_stats = get_verification_stats()
    logger.info(f"Updated verification statistics: {updated_stats}")
    
    logger.info("Doctor verification workflow test completed")

if __name__ == "__main__":
    # If run directly, perform a test of the workflow
    test_workflow()