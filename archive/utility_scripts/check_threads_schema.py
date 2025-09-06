"""
Check the schema of the threads table in the database.
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

def check_threads_schema():
    """Check the schema of the threads table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get all columns from the threads table
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'threads'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        if not columns:
            logger.error("No columns found in threads table or table does not exist.")
            return
        
        logger.info("Threads table schema:")
        for column in columns:
            col_name, data_type, max_length = column
            length_info = f", max length: {max_length}" if max_length else ""
            logger.info(f"Column: {col_name}, Type: {data_type}{length_info}")
        
        # Check if the flag-related columns exist
        flag_columns = ['is_flagged', 'flag_reason', 'flag_notes', 'fk_thread_flagged_by', 'flagged_at']
        for col in flag_columns:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'threads' AND column_name = %s;
            """, (col,))
            
            if cursor.fetchone():
                logger.info(f"✓ Column '{col}' exists in threads table.")
            else:
                logger.error(f"✗ Column '{col}' does NOT exist in threads table.")
        
        # Get table constraints (foreign keys, etc.)
        cursor.execute("""
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                LEFT JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
            WHERE
                tc.table_name = 'threads'
            ORDER BY
                tc.constraint_name;
        """)
        
        constraints = cursor.fetchall()
        
        if not constraints:
            logger.info("No constraints found for threads table.")
        else:
            logger.info("Threads table constraints:")
            for constraint in constraints:
                name, type_c, column, ft_name, ft_column = constraint
                fk_info = f" referencing {ft_name}.{ft_column}" if ft_name and ft_column else ""
                logger.info(f"Constraint: {name}, Type: {type_c}, Column: {column}{fk_info}")
                
    except Exception as e:
        logger.error(f"Error checking threads schema: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the schema check."""
    try:
        check_threads_schema()
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())