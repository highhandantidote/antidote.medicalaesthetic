#!/usr/bin/env python3
"""
Connect directly to Supabase and migrate database.

This script:
1. Connects to your current database
2. Connects to Supabase
3. Creates the necessary tables in Supabase
4. Migrates all data
5. Updates application configuration
"""
import os
import sys
import json
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("supabase_migration.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
BACKUP_DIR = Path('database_backup') / datetime.now().strftime("%Y%m%d_%H%M%S")

# Supabase connection info
SUPABASE_HOST = "db.asgwdfirkanaaswobuj.supabase.co"
SUPABASE_PORT = "5432"
SUPABASE_USER = "postgres"
SUPABASE_DBNAME = "postgres"

def get_current_db_connection():
    """Get a connection to the current database."""
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("Current DATABASE_URL environment variable not set")
            return None
            
        logger.info(f"Connecting to current database: {db_url[:20]}...")
        conn = psycopg2.connect(db_url)
        logger.info("Connected to current database successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to current database: {str(e)}")
        return None

def get_supabase_connection():
    """Get a connection to the Supabase database."""
    try:
        # Get the Supabase URL from environment
        supabase_url = os.environ.get('SUPABASE_DATABASE_URL')
        
        if not supabase_url:
            logger.error("SUPABASE_DATABASE_URL environment variable not set")
            logger.error("Please provide the Supabase connection string")
            return None
        
        logger.info(f"Connecting to Supabase using provided URL...")
        conn = psycopg2.connect(supabase_url)
        logger.info("Connected to Supabase successfully")
        
        # Store the URL for later use
        os.environ['SUPABASE_URL'] = supabase_url
        
        return conn
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {str(e)}")
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
                logger.info(f"Table {table_name} already exists in Supabase")
                return True
                
            # Generate CREATE TABLE statement
            columns = []
            for col in schema:
                column_name, data_type, is_nullable, default = col
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                default_clause = f"DEFAULT {default}" if default else ""
                columns.append(f'"{column_name}" {data_type} {nullable} {default_clause}'.strip())
            
            create_stmt = f'CREATE TABLE "{table_name}" (\n  ' + ',\n  '.join(columns) + '\n);'
            logger.info(f"Creating table {table_name} in Supabase")
            logger.debug(create_stmt)
            
            cursor.execute(create_stmt)
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error creating table {table_name}: {str(e)}")
        conn.rollback()
        return False

def import_table_data(conn, table_name, data):
    """Import data into a table in the Supabase database."""
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

def backup_table_data(table_name, data):
    """Backup table data to a JSON file."""
    try:
        # Ensure backup directory exists
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save data to JSON file
        data_file = BACKUP_DIR / f"{table_name}_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump([dict(row) for row in data], f, indent=2, default=str)
            
        logger.info(f"Backed up {len(data)} rows from {table_name} to {data_file}")
        return True
    except Exception as e:
        logger.error(f"Error backing up data for {table_name}: {str(e)}")
        return False

def set_sequences(conn, table_name):
    """Set sequence values for tables with SERIAL columns."""
    try:
        with conn.cursor() as cursor:
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
            
            conn.commit()
            logger.info(f"Set sequence values for table {table_name}")
            return True
    except Exception as e:
        logger.error(f"Error setting sequence for {table_name}: {str(e)}")
        conn.rollback()
        return False

def update_env_file(supabase_url):
    """Update .env file with Supabase connection string."""
    try:
        env_file = Path('.env')
        
        # Check if .env file exists
        if env_file.exists():
            # Read current content
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Check if DATABASE_URL is already in the file
            database_url_exists = any(line.strip().startswith('DATABASE_URL=') for line in lines)
            
            if database_url_exists:
                # Update existing DATABASE_URL
                with open(env_file, 'w', encoding='utf-8') as f:
                    for line in lines:
                        if line.strip().startswith('DATABASE_URL='):
                            f.write(f'DATABASE_URL={supabase_url}\n')
                        else:
                            f.write(line)
            else:
                # Append DATABASE_URL to file
                with open(env_file, 'a', encoding='utf-8') as f:
                    f.write(f'\nDATABASE_URL={supabase_url}\n')
        else:
            # Create new .env file
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(f'DATABASE_URL={supabase_url}\n')
                
        logger.info("Updated .env file with Supabase connection string")
        return True
    except Exception as e:
        logger.error(f"Error updating .env file: {str(e)}")
        return False

def migrate_single_table(source_conn, target_conn, table_name):
    """Migrate a single table from source to target database."""
    logger.info(f"Migrating table: {table_name}")
    
    try:
        # Get table schema
        schema = get_table_schema(source_conn, table_name)
        if not schema:
            logger.error(f"Failed to get schema for table {table_name}")
            return False
            
        # Extract data from source
        data = extract_table_data(source_conn, table_name)
        logger.info(f"Extracted {len(data)} rows from {table_name}")
        
        # Backup data
        backup_table_data(table_name, data)
        
        # Create table in target database
        if not create_table_if_not_exists(target_conn, table_name, schema):
            logger.error(f"Failed to create table {table_name} in target database")
            return False
            
        # Import data to target
        if import_table_data(target_conn, table_name, data):
            # Set sequence values for auto-increment columns
            set_sequences(target_conn, table_name)
            return True
        else:
            logger.error(f"Failed to import data for table {table_name}")
            return False
    except Exception as e:
        logger.error(f"Error migrating table {table_name}: {str(e)}")
        return False

def migrate_database():
    """Migrate all data from current database to Supabase."""
    # Connect to source database
    source_conn = get_current_db_connection()
    if not source_conn:
        logger.error("Failed to connect to source database")
        return False
        
    # Connect to Supabase
    target_conn = get_supabase_connection()
    if not target_conn:
        logger.error("Failed to connect to Supabase")
        source_conn.close()
        return False
    
    try:
        # Get all tables from source database
        tables = get_all_tables(source_conn)
        logger.info(f"Found {len(tables)} tables in source database: {', '.join(tables)}")
        
        # Save list of tables
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        with open(BACKUP_DIR / "tables.json", 'w', encoding='utf-8') as f:
            json.dump(tables, f, indent=2)
        
        # Migrate each table
        success_count = 0
        for table in tables:
            if migrate_single_table(source_conn, target_conn, table):
                success_count += 1
        
        # Update .env file
        if 'SUPABASE_URL' in os.environ:
            update_env_file(os.environ['SUPABASE_URL'])
        
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
    logger.info("=== Starting direct migration to Supabase ===")
    
    success = migrate_database()
    
    if success:
        logger.info("=== Database migration to Supabase completed successfully ===")
        logger.info(f"Backup saved to: {BACKUP_DIR}")
        logger.info("Your application is now connected to Supabase!")
        return 0
    else:
        logger.error("=== Database migration to Supabase failed ===")
        logger.error("Please check the logs for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())