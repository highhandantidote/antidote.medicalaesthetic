"""
Add new procedure fields to the database.

This script adds the following fields to the procedures table:
- procedure_duration: How much time the procedure will take to complete
- hospital_stay_required: Whether a hospital stay is required (yes/no)
- alternative_names: Alternative names for the procedure
"""
import os
import logging
import psycopg2
from psycopg2 import sql

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        logger.info("Database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def add_new_procedure_fields():
    """Add new fields to the procedures table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if alternative_names column exists
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'procedures' AND column_name = 'alternative_names'")
        if cursor.fetchone() is None:
            logger.info("Adding alternative_names column to procedures table")
            cursor.execute(
                sql.SQL("ALTER TABLE procedures ADD COLUMN alternative_names TEXT")
            )
        else:
            logger.info("alternative_names column already exists")
        
        # Check if procedure_duration column exists
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'procedures' AND column_name = 'procedure_duration'")
        if cursor.fetchone() is None:
            logger.info("Adding procedure_duration column to procedures table")
            cursor.execute(
                sql.SQL("ALTER TABLE procedures ADD COLUMN procedure_duration TEXT")
            )
        else:
            logger.info("procedure_duration column already exists")
        
        # Check if hospital_stay_required column exists
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'procedures' AND column_name = 'hospital_stay_required'")
        if cursor.fetchone() is None:
            logger.info("Adding hospital_stay_required column to procedures table")
            cursor.execute(
                sql.SQL("ALTER TABLE procedures ADD COLUMN hospital_stay_required TEXT")
            )
        else:
            logger.info("hospital_stay_required column already exists")
        
        conn.commit()
        logger.info("Successfully added new procedure fields to the database")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding new procedure fields: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the migration."""
    try:
        add_new_procedure_fields()
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")

if __name__ == "__main__":
    main()