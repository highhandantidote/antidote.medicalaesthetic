"""
Check the queries used in the index route to diagnose issues.
"""
import os
import psycopg2
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
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

def check_index_queries():
    """Check the queries used in the index route."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if threads table has any data
        cursor.execute("SELECT COUNT(*) FROM threads")
        thread_count = cursor.fetchone()[0]
        logger.info(f"Threads table has {thread_count} rows")
        
        # Check if procedures table has any data
        cursor.execute("SELECT COUNT(*) FROM procedures")
        procedure_count = cursor.fetchone()[0]
        logger.info(f"Procedures table has {procedure_count} rows")
        
        # Check if doctors table has any data
        cursor.execute("SELECT COUNT(*) FROM doctors")
        doctor_count = cursor.fetchone()[0]
        logger.info(f"Doctors table has {doctor_count} rows")
        
        # Check if categories table has any data
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        logger.info(f"Categories table has {category_count} rows")
        
        # Check if banner_slides table has any data
        cursor.execute("SELECT COUNT(*) FROM banner_slides")
        banner_count = cursor.fetchone()[0]
        logger.info(f"Banner_slides table has {banner_count} rows")
        
        # Check if the index page can fetch popular threads with flag-related columns
        try:
            cursor.execute("""
                SELECT id, title, content, created_at, procedure_id, view_count, 
                       reply_count, keywords, user_id, is_flagged, flag_reason, 
                       flag_notes, fk_thread_flagged_by, flagged_at
                FROM threads
                ORDER BY created_at DESC
                LIMIT 3
            """)
            threads = cursor.fetchall()
            logger.info(f"Successfully fetched {len(threads)} threads for display on index")
        except Exception as e:
            logger.error(f"Error fetching threads for index display: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error checking index queries: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the index route checks."""
    try:
        check_index_queries()
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())