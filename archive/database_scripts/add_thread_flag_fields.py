"""
Add flag-related fields to the threads table.

This script adds the flag-related fields to the threads table to enable community moderation.
"""
import os
import psycopg2
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def add_flag_fields():
    """Add flag-related fields to the threads table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if columns already exist
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'threads' AND column_name = 'is_flagged'")
        if cursor.fetchone():
            logger.info("Flag-related fields already exist in threads table.")
            return False
        
        # Add flag-related fields
        cursor.execute("""
            ALTER TABLE threads 
            ADD COLUMN is_flagged BOOLEAN DEFAULT FALSE,
            ADD COLUMN flag_reason TEXT,
            ADD COLUMN flag_notes TEXT,
            ADD COLUMN fk_thread_flagged_by INTEGER REFERENCES users(id),
            ADD COLUMN flagged_at TIMESTAMP WITHOUT TIME ZONE
        """)
        
        conn.commit()
        logger.info("Flag-related fields added to threads table successfully.")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding flag-related fields to threads table: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the migration."""
    logger.info("Starting migration to add flag-related fields to threads table...")
    try:
        result = add_flag_fields()
        if result:
            logger.info("Migration completed successfully.")
        else:
            logger.info("Migration skipped, fields already exist.")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())