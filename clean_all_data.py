"""
Clean all data from the website database.

This script removes all doctors, procedures, categories, body parts, and related data
from the database, essentially resetting it to a clean state.
"""

import os
import logging
import psycopg2
from psycopg2 import sql

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    logging.info("Connecting to database...")
    connection = psycopg2.connect(db_url)
    return connection

def clean_all_data():
    """Remove all data from the database."""
    connection = None
    
    # List of tables to clean in order (considering foreign key constraints)
    tables_to_clean = [
        'reviews',
        'doctor_procedures', 
        'favorites',
        'procedure_to_procedure',
        'face_scan_recommendations',
        'appointments',
        'patient_leads',
        'procedures',
        'categories',
        'body_parts',
        'doctors',
        'specialists',
        'community_threads',
        'community_replies',
        'community_thread_flags'
    ]
    
    try:
        # Get the list of tables that actually exist in the database
        connection = get_db_connection()
        connection.autocommit = True
        cursor = connection.cursor()
        
        logging.info("Checking existing tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        logging.info(f"Found existing tables: {existing_tables}")
        
        # For each table that exists, delete all rows
        for table in tables_to_clean:
            if table in existing_tables:
                try:
                    logging.info(f"Deleting all data from {table} table...")
                    cursor.execute(sql.SQL("DELETE FROM {}").format(sql.Identifier(table)))
                    logging.info(f"Successfully deleted all data from {table} table")
                except Exception as e:
                    logging.warning(f"Error deleting data from {table}: {e}")
            else:
                logging.info(f"Table {table} does not exist, skipping.")
                
        # Reset sequences for primary keys
        logging.info("Resetting sequences...")
        cursor.execute("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        sequences = [row[0] for row in cursor.fetchall()]
        
        for seq in sequences:
            try:
                logging.info(f"Resetting sequence {seq}...")
                cursor.execute(sql.SQL("ALTER SEQUENCE {} RESTART WITH 1").format(sql.Identifier(seq)))
            except Exception as e:
                logging.warning(f"Error resetting sequence {seq}: {e}")
                
        logging.info("Database cleaned successfully")
        
    except Exception as e:
        logging.error(f"Error cleaning database: {e}")
        raise
    finally:
        # Close connection
        if connection:
            if cursor:
                cursor.close()
            connection.close()

def main():
    """Run the database cleaning operation."""
    try:
        clean_all_data()
        logging.info("All data has been cleaned from the website.")
    except Exception as e:
        logging.error(f"Failed to clean data: {e}")

if __name__ == "__main__":
    main()