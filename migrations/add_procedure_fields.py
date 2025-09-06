import sys
import os
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_procedure_fields():
    """
    Add procedure_duration, hospital_stay_required, and alternative_names columns to the procedures table.
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
        
        # First check if the procedures table exists
        logger.info("Checking if procedures table exists...")
        check_table_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'procedures'
        );
        """
        
        cursor.execute(check_table_query)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            logger.error("The procedures table does not exist yet. Please ensure the database is properly set up.")
            return False
        
        # Check if columns already exist
        logger.info("Checking if columns already exist...")
        inspect_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='procedures' 
        AND (column_name='procedure_duration' OR column_name='hospital_stay_required' OR column_name='alternative_names');
        """
        
        cursor.execute(inspect_query)
        result = cursor.fetchall()
        existing_columns = [row[0] for row in result]
        
        if 'procedure_duration' not in existing_columns:
            logger.info("Adding procedure_duration column to procedures table...")
            cursor.execute("""
            ALTER TABLE procedures
            ADD COLUMN procedure_duration TEXT
            """)
            logger.info("procedure_duration column added successfully.")
        else:
            logger.info("procedure_duration column already exists.")
            
        if 'hospital_stay_required' not in existing_columns:
            logger.info("Adding hospital_stay_required column to procedures table...")
            cursor.execute("""
            ALTER TABLE procedures
            ADD COLUMN hospital_stay_required TEXT
            """)
            logger.info("hospital_stay_required column added successfully.")
        else:
            logger.info("hospital_stay_required column already exists.")
            
        if 'alternative_names' not in existing_columns:
            logger.info("Adding alternative_names column to procedures table...")
            cursor.execute("""
            ALTER TABLE procedures
            ADD COLUMN alternative_names TEXT
            """)
            logger.info("alternative_names column added successfully.")
        else:
            logger.info("alternative_names column already exists.")
            
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
    logger.info("Starting migration to add new fields to procedures table...")
    success = add_procedure_fields()
    
    if success:
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration failed!")
        sys.exit(1)