"""
Delete all procedures, categories, and body parts from the database.

This script will completely clear the procedure-related data to prepare
for importing a new dataset with more detailed categorization.
"""
import os
import logging
import psycopg2
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'delete_procedure_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def count_records(conn, table_name):
    """Count records in a table."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except Exception as e:
        logger.error(f"Error counting records in {table_name}: {str(e)}")
        return -1

def delete_all_procedure_data():
    """Delete all procedure-related data."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check initial record counts
        procedures_count = count_records(conn, "procedures")
        categories_count = count_records(conn, "categories")
        body_parts_count = count_records(conn, "body_parts")
        
        logger.info(f"Initial record counts:")
        logger.info(f"- Procedures: {procedures_count}")
        logger.info(f"- Categories: {categories_count}")
        logger.info(f"- Body Parts: {body_parts_count}")
        
        # Create a backup of the data (just in case)
        try:
            logger.info("Creating backup of procedure data...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS procedures_backup AS 
                SELECT * FROM procedures
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories_backup AS 
                SELECT * FROM categories
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS body_parts_backup AS 
                SELECT * FROM body_parts
            """)
            conn.commit()
            logger.info("Backup created successfully.")
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            conn.rollback()
        
        # Delete procedures first (to maintain referential integrity)
        logger.info("Deleting procedures...")
        cursor.execute("DELETE FROM procedures")
        
        # Reset the sequences
        cursor.execute("ALTER SEQUENCE procedures_id_seq RESTART WITH 1")
        
        # Delete categories
        logger.info("Deleting categories...")
        cursor.execute("DELETE FROM categories")
        cursor.execute("ALTER SEQUENCE categories_id_seq RESTART WITH 1")
        
        # Delete body parts
        logger.info("Deleting body parts...")
        cursor.execute("DELETE FROM body_parts")
        cursor.execute("ALTER SEQUENCE body_parts_id_seq RESTART WITH 1")
        
        # Commit the transaction
        conn.commit()
        
        # Verify deletion
        procedures_after = count_records(conn, "procedures")
        categories_after = count_records(conn, "categories")
        body_parts_after = count_records(conn, "body_parts")
        
        logger.info(f"After deletion:")
        logger.info(f"- Procedures: {procedures_after}")
        logger.info(f"- Categories: {categories_after}")
        logger.info(f"- Body Parts: {body_parts_after}")
        
        # Close the connection
        cursor.close()
        conn.close()
        
        return {
            "procedures_deleted": procedures_count,
            "categories_deleted": categories_count,
            "body_parts_deleted": body_parts_count,
            "success": (procedures_after == 0 and categories_after == 0 and body_parts_after == 0)
        }
        
    except Exception as e:
        logger.error(f"Error deleting procedure data: {str(e)}")
        if 'conn' in locals() and conn is not None:
            conn.rollback()
            conn.close()
        raise

def main():
    """Run the deletion process."""
    logger.info("Starting procedure data deletion process...")
    try:
        result = delete_all_procedure_data()
        if result["success"]:
            logger.info("Successfully deleted all procedure data:")
            logger.info(f"- {result['procedures_deleted']} procedures deleted")
            logger.info(f"- {result['categories_deleted']} categories deleted")
            logger.info(f"- {result['body_parts_deleted']} body parts deleted")
            logger.info("The database is now ready for importing new data.")
        else:
            logger.error("Failed to delete all records.")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()