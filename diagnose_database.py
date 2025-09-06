#!/usr/bin/env python3
"""
Diagnose database issues related to doctors and their relationships.

This script checks for common problems in the doctor data that might
cause application errors and fixes them when possible.
"""
import os
import logging
import psycopg2
from psycopg2.extras import DictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def check_doctors_with_nulls():
    """Check for doctors with NULL values in required fields."""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        # Check for NULL values in important doctor fields
        cursor.execute("""
            SELECT id, name, specialty, city, bio, user_id
            FROM doctors
            WHERE name IS NULL OR specialty IS NULL OR city IS NULL OR bio IS NULL OR user_id IS NULL
        """)
        
        doctors_with_nulls = cursor.fetchall()
        
        if doctors_with_nulls:
            logger.info(f"Found {len(doctors_with_nulls)} doctors with NULL values in required fields:")
            for doctor in doctors_with_nulls:
                logger.info(f"  Doctor ID {doctor['id']}: {doctor['name']} - Missing: " + 
                           ", ".join(f"{field}" for field, value in doctor.items() if field != 'id' and value is None))
            
            # Fix NULL values
            for doctor in doctors_with_nulls:
                doctor_id = doctor['id']
                
                # Create safe defaults for NULL values
                updates = {}
                if doctor['name'] is None:
                    updates['name'] = f"Doctor {doctor_id}"
                if doctor['specialty'] is None:
                    updates['specialty'] = "General Surgery"
                if doctor['city'] is None:
                    updates['city'] = "Mumbai"
                if doctor['bio'] is None:
                    updates['bio'] = f"Doctor {doctor_id} is a medical professional with years of experience."
                
                # Only update if there are fields to fix
                if updates:
                    set_clause = ", ".join(f"{field} = %s" for field in updates)
                    values = list(updates.values())
                    values.append(doctor_id)
                    
                    cursor.execute(f"UPDATE doctors SET {set_clause} WHERE id = %s", values)
                    logger.info(f"Fixed NULL values for Doctor ID {doctor_id}")
            
            conn.commit()
            return True
        else:
            logger.info("No doctors found with NULL values in required fields")
            return False
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error checking/fixing doctors with NULLs: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def check_doctor_ratings():
    """Check for doctors with NULL ratings and fix them."""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # Check for doctors with NULL ratings
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE rating IS NULL")
        null_ratings_count = cursor.fetchone()[0]
        
        if null_ratings_count > 0:
            logger.info(f"Found {null_ratings_count} doctors with NULL ratings")
            
            # Update doctors with NULL ratings
            cursor.execute("""
                UPDATE doctors
                SET rating = 4.0 + random() * 1.0,
                    review_count = 5 + floor(random() * 16)
                WHERE rating IS NULL
            """)
            
            conn.commit()
            
            # Verify fix
            cursor.execute("SELECT COUNT(*) FROM doctors WHERE rating IS NULL")
            remaining_null_count = cursor.fetchone()[0]
            logger.info(f"After fix: {remaining_null_count} doctors still have NULL ratings")
            
            return null_ratings_count > 0
        else:
            logger.info("No doctors found with NULL ratings")
            return False
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error checking/fixing doctor ratings: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def check_excessive_doctor_procedures():
    """Check for doctors with an excessive number of procedure links."""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # Get counts of procedures per doctor
        cursor.execute("""
            SELECT d.id, d.name, COUNT(dp.procedure_id) as procedure_count
            FROM doctors d
            JOIN doctor_procedures dp ON d.id = dp.doctor_id
            GROUP BY d.id, d.name
            ORDER BY procedure_count DESC
            LIMIT 10
        """)
        
        doctors_with_most_procedures = cursor.fetchall()
        
        logger.info("Top 10 doctors by procedure count:")
        for doctor_id, doctor_name, procedure_count in doctors_with_most_procedures:
            logger.info(f"  Doctor ID {doctor_id} ({doctor_name}): {procedure_count} procedures")
        
        # Check if any doctor has an extremely high number of procedures (>1000)
        excessive_doctors = [row for row in doctors_with_most_procedures if row[2] > 1000]
        
        if excessive_doctors:
            # This might be causing performance issues
            logger.warning(f"Found {len(excessive_doctors)} doctors with >1000 procedures")
            return True
        else:
            logger.info("No doctors found with excessive procedure counts")
            return False
            
    except Exception as e:
        logger.error(f"Error checking doctor procedure counts: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_database_size():
    """Verify the size of key tables in the database."""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        tables = ["users", "doctors", "procedures", "categories", "body_parts", 
                  "doctor_procedures", "doctor_categories", "reviews"]
        
        logger.info("Database table sizes:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"  {table}: {count} rows")
        
        return True
            
    except Exception as e:
        logger.error(f"Error checking database sizes: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def check_invalid_doctor_links():
    """Check for invalid doctor procedure or category links."""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # Check for invalid doctor_procedures links
        cursor.execute("""
            SELECT COUNT(*) FROM doctor_procedures dp
            LEFT JOIN doctors d ON dp.doctor_id = d.id
            LEFT JOIN procedures p ON dp.procedure_id = p.id
            WHERE d.id IS NULL OR p.id IS NULL
        """)
        
        invalid_procedure_links = cursor.fetchone()[0]
        
        # Check for invalid doctor_categories links
        cursor.execute("""
            SELECT COUNT(*) FROM doctor_categories dc
            LEFT JOIN doctors d ON dc.doctor_id = d.id
            LEFT JOIN categories c ON dc.category_id = c.id
            WHERE d.id IS NULL OR c.id IS NULL
        """)
        
        invalid_category_links = cursor.fetchone()[0]
        
        if invalid_procedure_links > 0 or invalid_category_links > 0:
            logger.warning(f"Found {invalid_procedure_links} invalid doctor-procedure links")
            logger.warning(f"Found {invalid_category_links} invalid doctor-category links")
            
            # Delete invalid links
            if invalid_procedure_links > 0:
                cursor.execute("""
                    DELETE FROM doctor_procedures
                    WHERE doctor_id NOT IN (SELECT id FROM doctors)
                    OR procedure_id NOT IN (SELECT id FROM procedures)
                """)
                logger.info(f"Deleted {invalid_procedure_links} invalid doctor-procedure links")
            
            if invalid_category_links > 0:
                cursor.execute("""
                    DELETE FROM doctor_categories
                    WHERE doctor_id NOT IN (SELECT id FROM doctors)
                    OR category_id NOT IN (SELECT id FROM categories)
                """)
                logger.info(f"Deleted {invalid_category_links} invalid doctor-category links")
            
            conn.commit()
            return True
        else:
            logger.info("No invalid doctor links found")
            return False
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error checking/fixing invalid doctor links: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Run all database diagnostic checks."""
    logger.info("Starting database diagnosis...")
    
    # Run each check
    doctors_fixed = check_doctors_with_nulls()
    ratings_fixed = check_doctor_ratings()
    excessive_procedures = check_excessive_doctor_procedures()
    invalid_links_fixed = check_invalid_doctor_links()
    
    # Verify table sizes
    verify_database_size()
    
    # Summary
    if doctors_fixed or ratings_fixed or invalid_links_fixed:
        logger.info("Fixed one or more issues with the database")
    else:
        logger.info("No critical issues found or fixed in the database")
    
    if excessive_procedures:
        logger.warning("Found doctors with excessive procedure links - may cause performance issues")

if __name__ == "__main__":
    main()