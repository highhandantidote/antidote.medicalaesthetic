"""
Backup database tables and data to JSON files.

This script:
1. Extracts all data from the existing database
2. Saves table structure and data to JSON files
3. Creates a backup directory with timestamped files
"""
import os
import sys
import json
import logging
import psycopg2
import psycopg2.extras
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define backup directory
BACKUP_DIR = Path('database_backup')

def get_db_connection():
    """Get a connection to the database."""
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return None
            
        logger.info(f"Connecting to database: {db_url[:20]}...")
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def get_all_tables(conn):
    """Get a list of all tables in the database."""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        return [table[0] for table in cursor.fetchall()]

def get_table_schema(conn, table_name):
    """Get the schema for a table including column names and types."""
    with conn.cursor() as cursor:
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = cursor.fetchall()
        schema = []
        for col in columns:
            column_name, data_type, is_nullable, column_default = col
            schema.append({
                'name': column_name,
                'type': data_type,
                'nullable': is_nullable == 'YES',
                'default': column_default
            })
        return schema

def extract_table_data(conn, table_name):
    """Extract all data from a table."""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(f'SELECT * FROM "{table_name}"')
            data = cursor.fetchall()
            
            # Convert data to list of dicts (JSON serializable)
            return [dict(row) for row in data]
    except Exception as e:
        logger.error(f"Error extracting data from {table_name}: {str(e)}")
        return []

def backup_table(conn, table_name, backup_dir):
    """Backup a single table schema and data to JSON files."""
    try:
        logger.info(f"Backing up table: {table_name}")
        
        # Get table schema
        schema = get_table_schema(conn, table_name)
        if not schema:
            logger.error(f"Failed to get schema for table {table_name}")
            return False
            
        # Get table data
        data = extract_table_data(conn, table_name)
        logger.info(f"Extracted {len(data)} rows from {table_name}")
        
        # Save schema to file
        schema_file = backup_dir / f"{table_name}_schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, default=str)
            
        # Save data to file
        data_file = backup_dir / f"{table_name}_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
            
        logger.info(f"Backed up table {table_name} to {data_file}")
        return True
    except Exception as e:
        logger.error(f"Error backing up table {table_name}: {str(e)}")
        return False

def backup_database():
    """Backup the entire database to JSON files."""
    # Create backup directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUP_DIR / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Backing up database to {backup_dir}")
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        # Get all tables
        tables = get_all_tables(conn)
        logger.info(f"Found {len(tables)} tables in database")
        
        # Save table list
        tables_file = backup_dir / "tables.json"
        with open(tables_file, 'w', encoding='utf-8') as f:
            json.dump(tables, f, indent=2)
        
        # Backup each table
        success_count = 0
        for table in tables:
            if backup_table(conn, table, backup_dir):
                success_count += 1
        
        logger.info(f"Backup completed successfully for {success_count}/{len(tables)} tables")
        return success_count == len(tables)
        
    except Exception as e:
        logger.error(f"Error during backup: {str(e)}")
        return False
    finally:
        conn.close()

def main():
    """Main function to run the backup."""
    logger.info("=== Starting database backup ===")
    
    success = backup_database()
    
    if success:
        logger.info("=== Database backup completed successfully ===")
        return 0
    else:
        logger.error("=== Database backup failed ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())