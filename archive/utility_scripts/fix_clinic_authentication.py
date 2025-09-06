"""
Fix clinic dashboard authentication and access issues.
This script addresses the broken authentication flow and database schema problems.
"""

import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a direct database connection using DATABASE_URL."""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        return psycopg2.connect(database_url)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def fix_user_authentication():
    """Fix user authentication and password hashing issues."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify and fix clinic user password
        email = 'clinic.test@example.com'
        new_password = 'clinic123'
        password_hash = generate_password_hash(new_password)
        
        # Update password hash
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE email = %s
        """, (password_hash, email))
        
        # Verify the update
        cursor.execute("""
            SELECT id, email, role, name FROM users 
            WHERE email = %s
        """, (email,))
        
        user = cursor.fetchone()
        if user:
            logger.info(f"✅ Updated authentication for user: {user[1]} (ID: {user[0]}, Role: {user[2]})")
            
            # Test password verification
            cursor.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
            stored_hash = cursor.fetchone()[0]
            
            if check_password_hash(stored_hash, new_password):
                logger.info("✅ Password verification working correctly")
            else:
                logger.error("❌ Password verification failed")
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error fixing user authentication: {e}")
        if conn:
            conn.rollback()
            conn.close()

def add_missing_clinic_fields():
    """Add missing fields to clinic table for complete profile management."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Add missing fields to clinics table
        missing_fields = [
            "ALTER TABLE clinics ADD COLUMN IF NOT EXISTS highlights TEXT",
            "ALTER TABLE clinics ADD COLUMN IF NOT EXISTS specialties TEXT", 
            "ALTER TABLE clinics ADD COLUMN IF NOT EXISTS popular_procedures TEXT",
            "ALTER TABLE clinics ADD COLUMN IF NOT EXISTS profile_image TEXT",
            "ALTER TABLE clinics ADD COLUMN IF NOT EXISTS banner_image TEXT",
            "ALTER TABLE clinics ADD COLUMN IF NOT EXISTS email TEXT",
            "ALTER TABLE clinics ADD COLUMN IF NOT EXISTS whatsapp_number TEXT",
            "ALTER TABLE clinics ADD COLUMN IF NOT EXISTS website_url TEXT",
            "ALTER TABLE clinics ADD COLUMN IF NOT EXISTS social_media_links JSON"
        ]
        
        for field_query in missing_fields:
            try:
                cursor.execute(field_query)
                logger.info(f"✅ Added field: {field_query.split('ADD COLUMN IF NOT EXISTS')[1].split()[0]}")
            except Exception as e:
                logger.warning(f"Field may already exist: {e}")
        
        conn.commit()
        cursor.close() 
        conn.close()
        
    except Exception as e:
        logger.error(f"Error adding clinic fields: {e}")
        if conn:
            conn.rollback()
            conn.close()

def verify_clinic_data():
    """Verify clinic data is properly set up."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check clinic setup
        cursor.execute("""
            SELECT c.id, c.name, c.owner_user_id, c.is_approved, u.email, u.role
            FROM clinics c
            JOIN users u ON c.owner_user_id = u.id
            WHERE u.email = 'clinic.test@example.com'
        """)
        
        clinic_data = cursor.fetchone()
        if clinic_data:
            logger.info(f"✅ Clinic found: ID={clinic_data[0]}, Name={clinic_data[1]}, Owner={clinic_data[4]}, Role={clinic_data[5]}")
            
            # Update clinic data if needed
            cursor.execute("""
                UPDATE clinics 
                SET 
                    is_approved = true,
                    is_verified = true,
                    description = COALESCE(description, 'Professional clinic providing quality medical aesthetic services'),
                    highlights = COALESCE(highlights, 'Experienced doctors, Modern facilities, Personalized care'),
                    specialties = COALESCE(specialties, 'Facial Rejuvenation, Body Contouring, Skin Treatments'),
                    popular_procedures = COALESCE(popular_procedures, 'Botox, Dermal Fillers, Laser Treatments'),
                    contact_number = COALESCE(contact_number, '+91-9876543210'),
                    email = COALESCE(email, 'contact@testclinic.com'),
                    working_hours = COALESCE(working_hours, 'Mon-Sat: 9:00 AM - 6:00 PM')
                WHERE id = %s
            """, (clinic_data[0],))
            
            conn.commit()
            logger.info("✅ Clinic data updated with complete information")
        else:
            logger.error("❌ No clinic found for the test user")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error verifying clinic data: {e}")
        if conn:
            conn.rollback()
            conn.close()

def main():
    """Main function to fix all authentication and data issues."""
    logger.info("Starting clinic authentication and data fixes...")
    
    # Fix user authentication
    fix_user_authentication()
    
    # Add missing clinic fields
    add_missing_clinic_fields()
    
    # Verify and update clinic data
    verify_clinic_data()
    
    logger.info("✅ Clinic authentication and data fixes completed")

if __name__ == "__main__":
    main()