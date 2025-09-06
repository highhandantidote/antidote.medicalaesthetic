"""
Check procedures in the database.

This script queries the procedures table and prints out all procedures found.
"""

import os
import sys
import logging
from dotenv import load_dotenv
import psycopg2

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a direct connection to the database."""
    try:
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            logger.error("DATABASE_URL environment variable not set")
            sys.exit(1)
        
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("Database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)

def check_procedures():
    """Check all procedures in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get procedure count
        cursor.execute("SELECT COUNT(*) FROM procedures")
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} procedures in the database")
        
        # Get all procedures
        cursor.execute("""
            SELECT 
                id, 
                procedure_name, 
                category_id, 
                min_cost, 
                max_cost, 
                popularity_score, 
                avg_rating,
                COALESCE(
                    (SELECT COUNT(*) FROM reviews WHERE procedure_id = p.id), 
                    0
                ) as review_count
            FROM 
                procedures p
            ORDER BY 
                id
        """)
        
        procedures = cursor.fetchall()
        
        # Print all procedures
        logger.info("=== PROCEDURES IN DATABASE ===")
        for proc in procedures:
            logger.info(f"ID: {proc[0]}, Name: {proc[1]}, Category: {proc[2]}, Price: ${proc[3]}-${proc[4]}, Rating: {proc[6]}, Reviews: {proc[7]}")
        
        # Also check if procedures have categories
        cursor.execute("""
            SELECT 
                p.id, 
                p.procedure_name, 
                c.id, 
                c.name
            FROM 
                procedures p
            LEFT JOIN 
                categories c ON p.category_id = c.id
            ORDER BY 
                p.id
        """)
        
        proc_categories = cursor.fetchall()
        
        logger.info("=== PROCEDURE CATEGORIES ===")
        for pc in proc_categories:
            logger.info(f"Procedure ID: {pc[0]}, Name: {pc[1]}, Category ID: {pc[2]}, Category Name: {pc[3]}")
        
        return procedures
    except Exception as e:
        logger.error(f"Error checking procedures: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_procedures()