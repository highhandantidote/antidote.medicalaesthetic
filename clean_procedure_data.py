"""
Clean existing procedure data from the database.

This script removes all existing procedures, categories, and body parts to ensure a clean slate
before importing the full set of procedures from the CSV file.
"""
import os
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_database():
    """Remove all procedures, categories, and body parts from the database."""
    # Get database connection string from environment variable
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    if not DATABASE_URL:
        logger.error("DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Connect to the database
        logger.info("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # First, check foreign key constraints to ensure we handle dependencies correctly
        logger.info("Checking for dependencies before deletion...")
        
        # Check for procedures referenced in other tables
        tables_with_procedure_fk = [
            "doctor_procedures", "reviews", "community", "community_tagging", 
            "face_scan_recommendations", "recommendation_history"
        ]
        
        for table in tables_with_procedure_fk:
            # Check if table exists first
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table,))
            
            table_exists = cursor.fetchone()[0]
            if not table_exists:
                logger.info(f"Table {table} does not exist, skipping")
                continue
                
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                logger.info(f"Found {count} records in {table} referencing procedures")
                logger.info(f"Deleting records from {table}...")
                cursor.execute(f"DELETE FROM {table}")
        
        # Delete procedures
        logger.info("Deleting all procedures...")
        cursor.execute("DELETE FROM procedures")
        logger.info("All procedures deleted.")
        
        # Delete categories (only if they're not referenced elsewhere)
        logger.info("Deleting all categories...")
        cursor.execute("DELETE FROM categories")
        logger.info("All categories deleted.")
        
        # Delete body parts (only if they're not referenced elsewhere)
        logger.info("Deleting all body parts...")
        cursor.execute("DELETE FROM body_parts")
        logger.info("All body parts deleted.")
        
        # Commit the changes
        conn.commit()
        logger.info("Database cleaned successfully.")
        
        # Close the connection
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning database: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting database cleaning process...")
    success = clean_database()
    
    if success:
        logger.info("Database cleaned successfully!")
    else:
        logger.error("Failed to clean database.")