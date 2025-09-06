"""
List all tables in the database.
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
        # Print the database URL (masked) for debugging
        db_url = os.environ.get('DATABASE_URL', '')
        if db_url:
            logger.info(f"Using DATABASE_URL (first 20 chars): {db_url[:20]}...")
        else:
            logger.error("DATABASE_URL environment variable is not set")
            
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def list_tables():
    """List all tables in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get all tables in the current schema
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            logger.error("No tables found in the database.")
            return
        
        logger.info("Tables in the database:")
        for table in tables:
            logger.info(f" - {table[0]}")
            
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the table listing."""
    try:
        list_tables()
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())