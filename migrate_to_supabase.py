"""
Migrate database to Supabase.

This script:
1. Extracts all data from the existing database
2. Creates the necessary tables in Supabase (if they don't exist)
3. Imports the data to Supabase
"""
import os
import sys
import json
import logging
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_source_db_connection():
    """Get a connection to the source database."""
    try:
        db_url = os.environ.get('SOURCE_DATABASE_URL')
        if not db_url:
            logger.error("SOURCE_DATABASE_URL environment variable not set")
            return None
            
        logger.info(f"Connecting to source database: {db_url[:20]}...")
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to source database: {str(e)}")
        return None

def get_target_db_connection():
    """Get a connection to the target Supabase database."""
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return None
            
        logger.info(f"Connecting to target Supabase database: {db_url[:20]}...")
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to target Supabase database: {str(e)}")
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
        return cursor.fetchall()

def extract_table_data(conn, table_name):
    """Extract all data from a table."""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(f'SELECT * FROM "{table_name}"')
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error extracting data from {table_name}: {str(e)}")
        return []

def create_table_if_not_exists(conn, table_name, schema):
    """Create a table if it doesn't exist in the target database."""
    try:
        # Check if table exists
        with conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                logger.info(f"Table {table_name} already exists in target database")
                return True
                
            # Generate CREATE TABLE statement
            columns = []
            for col in schema:
                column_name, data_type, is_nullable, default = col
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                default_clause = f"DEFAULT {default}" if default else ""
                columns.append(f'"{column_name}" {data_type} {nullable} {default_clause}'.strip())
            
            create_stmt = f'CREATE TABLE "{table_name}" (\n  ' + ',\n  '.join(columns) + '\n);'
            logger.info(f"Creating table {table_name} in target database")
            logger.debug(create_stmt)
            
            cursor.execute(create_stmt)
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error creating table {table_name}: {str(e)}")
        conn.rollback()
        return False

def import_table_data(conn, table_name, data):
    """Import data into a table in the target database."""
    if not data:
        logger.info(f"No data to import for table {table_name}")
        return True
        
    try:
        with conn.cursor() as cursor:
            # Get column names from the first row of data
            columns = list(data[0].keys())
            
            # Generate INSERT statements for each row
            rows_imported = 0
            for row in data:
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join([f'"{col}"' for col in columns])
                
                insert_stmt = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
                values = [row[col] for col in columns]
                
                try:
                    cursor.execute(insert_stmt, values)
                    rows_imported += 1
                except Exception as e:
                    logger.error(f"Error importing row into {table_name}: {str(e)}")
                    logger.error(f"Row data: {json.dumps(row)}")
                    conn.rollback()
                    continue
            
            conn.commit()
            logger.info(f"Imported {rows_imported} rows into {table_name}")
            return True
    except Exception as e:
        logger.error(f"Error importing data into {table_name}: {str(e)}")
        conn.rollback()
        return False

def set_sequences(target_conn, table_name):
    """Set sequence values for tables with SERIAL columns."""
    try:
        with target_conn.cursor() as cursor:
            # Find sequences associated with this table
            cursor.execute("""
                SELECT column_name, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = %s
                AND column_default LIKE 'nextval%%'
            """, (table_name,))
            
            for col_name, default_value in cursor.fetchall():
                # Extract sequence name from default value (e.g., nextval('users_id_seq'::regclass))
                sequence_name = default_value.split("'")[1]
                
                # Set the sequence value to the max value of the column + 1
                cursor.execute(f"""
                    SELECT setval('{sequence_name}', COALESCE(
                        (SELECT MAX("{col_name}") FROM "{table_name}"), 0) + 1
                    );
                """)
            
            target_conn.commit()
            logger.info(f"Set sequence values for table {table_name}")
            return True
    except Exception as e:
        logger.error(f"Error setting sequence for {table_name}: {str(e)}")
        target_conn.rollback()
        return False

def migrate_database():
    """Migrate all data from source to target database."""
    # Connect to source database
    source_conn = get_source_db_connection()
    if not source_conn:
        logger.error("Failed to connect to source database")
        return False
        
    # Connect to target Supabase database
    target_conn = get_target_db_connection()
    if not target_conn:
        logger.error("Failed to connect to target Supabase database")
        return False
    
    try:
        # Get all tables from source database
        tables = get_all_tables(source_conn)
        logger.info(f"Found {len(tables)} tables in source database: {', '.join(tables)}")
        
        # Migrate each table
        success_count = 0
        for table in tables:
            logger.info(f"Migrating table: {table}")
            
            # Get table schema
            schema = get_table_schema(source_conn, table)
            if not schema:
                logger.error(f"Failed to get schema for table {table}")
                continue
                
            # Create table in target database
            if not create_table_if_not_exists(target_conn, table, schema):
                logger.error(f"Failed to create table {table} in target database")
                continue
                
            # Extract data from source
            data = extract_table_data(source_conn, table)
            logger.info(f"Extracted {len(data)} rows from {table}")
            
            # Import data to target
            if import_table_data(target_conn, table, data):
                # Set sequence values for auto-increment columns
                set_sequences(target_conn, table)
                success_count += 1
            else:
                logger.error(f"Failed to import data for table {table}")
        
        logger.info(f"Migration completed successfully for {success_count}/{len(tables)} tables")
        return success_count == len(tables)
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False
    finally:
        source_conn.close()
        target_conn.close()

def main():
    """Main function to run the migration."""
    logger.info("=== Starting database migration to Supabase ===")
    
    # Set SOURCE_DATABASE_URL to original DATABASE_URL if not already set
    if 'SOURCE_DATABASE_URL' not in os.environ:
        source_db_url = input("Enter the source database URL: ")
        if source_db_url:
            os.environ['SOURCE_DATABASE_URL'] = source_db_url
        else:
            logger.error("No source database URL provided")
            return 1
    
    # Run migration
    success = migrate_database()
    
    if success:
        logger.info("=== Database migration completed successfully ===")
        return 0
    else:
        logger.error("=== Database migration failed ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())