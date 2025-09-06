import sys
import os
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_verification_fields():
    """
    Add verification_date and verification_notes columns to the doctors table.
    """
    # Get database connection string from environment variable
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    if not DATABASE_URL:
        logger.error("DATABASE_URL not found in environment variables")
        return False
        
    try:
        # Connect to the database
        logger.info("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Check if columns already exist
        logger.info("Checking if columns already exist...")
        inspect_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='doctors' 
        AND (column_name='verification_date' OR column_name='verification_notes');
        """
        
        cursor.execute(inspect_query)
        result = cursor.fetchall()
        existing_columns = [row[0] for row in result]
        
        if 'verification_date' not in existing_columns:
            logger.info("Adding verification_date column to doctors table...")
            cursor.execute("""
            ALTER TABLE doctors
            ADD COLUMN verification_date TIMESTAMP
            """)
            logger.info("verification_date column added successfully.")
        else:
            logger.info("verification_date column already exists.")
            
        if 'verification_notes' not in existing_columns:
            logger.info("Adding verification_notes column to doctors table...")
            cursor.execute("""
            ALTER TABLE doctors
            ADD COLUMN verification_notes TEXT
            """)
            logger.info("verification_notes column added successfully.")
        else:
            logger.info("verification_notes column already exists.")
            
        # Commit the changes
        conn.commit()
        logger.info("Migration completed successfully.")
        
        # Close the connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    logger.info("Starting migration to add verification fields to doctors table...")
    success = add_verification_fields()
    
    if success:
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration failed!")
        sys.exit(1)