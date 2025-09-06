#!/usr/bin/env python3
"""
Verify database contents and print a summary.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a connection to the database."""
    import psycopg2
    
    # Get database connection info from environment variables
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        sys.exit(1)

def verify_db_contents():
    """Verify database contents and print summary."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get doctor count
        cursor.execute("SELECT COUNT(*) FROM doctors")
        doctor_count = cursor.fetchone()[0]
        
        # Get procedure count
        cursor.execute("SELECT COUNT(*) FROM procedures")
        procedure_count = cursor.fetchone()[0]
        
        # Get body part count
        cursor.execute("SELECT COUNT(*) FROM body_parts")
        body_part_count = cursor.fetchone()[0]
        
        # Get category count
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        
        # Get doctor-procedure link count
        cursor.execute("SELECT COUNT(*) FROM doctor_procedures")
        doctor_procedure_count = cursor.fetchone()[0]
        
        # Get doctor-category link count
        cursor.execute("SELECT COUNT(*) FROM doctor_categories")
        doctor_category_count = cursor.fetchone()[0]
        
        # Print summary
        print("=== Database Content Summary ===")
        print(f"Doctors: {doctor_count}")
        print(f"Procedures: {procedure_count}")
        print(f"Body Parts: {body_part_count}")
        print(f"Categories: {category_count}")
        print(f"Doctor-Procedure Links: {doctor_procedure_count}")
        print(f"Doctor-Category Links: {doctor_category_count}")
        
        # Sample doctor data
        cursor.execute("""
            SELECT d.id, u.email, d.name, d.city, d.rating
            FROM doctors d
            JOIN users u ON d.user_id = u.id
            ORDER BY d.id
            LIMIT 5
        """)
        print("\n=== Sample Doctor Data ===")
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, Email: {row[1]}, Name: {row[2]}, City: {row[3]}, Rating: {row[4]}")
        
        # Doctor city distribution
        cursor.execute("""
            SELECT city, COUNT(*) 
            FROM doctors 
            GROUP BY city 
            ORDER BY COUNT(*) DESC
        """)
        print("\n=== Doctor Distribution by City ===")
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} doctors")
            
    except Exception as e:
        logger.error(f"Error verifying database contents: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    verify_db_contents()