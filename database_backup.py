#!/usr/bin/env python3
"""
Simple database backup script that exports each table to a JSON file.

This approach is more reliable and can handle any table structure without
needing to parse schema details. The JSON format can later be used to
recreate SQL statements for import into Supabase.
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
        logging.FileHandler("database_backup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
BACKUP_DIR = Path('database_backup') / datetime.now().strftime("%Y%m%d_%H%M%S")

def get_db_connection():
    """Get a connection to the database."""
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return None
            
        logger.info(f"Connecting to database: {db_url[:20]}...")
        conn = psycopg2.connect(db_url)
        logger.info("Connected to database successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def get_all_tables(conn):
    """Get a list of all tables in the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = [table[0] for table in cursor.fetchall()]
            return tables
    except Exception as e:
        logger.error(f"Error getting tables: {str(e)}")
        return []

def get_table_schema(conn, table_name):
    """Get the schema for a table including column names and types."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    column_name, 
                    data_type,
                    is_nullable
                FROM 
                    information_schema.columns
                WHERE 
                    table_schema = 'public' 
                    AND table_name = %s
                ORDER BY 
                    ordinal_position;
            """, (table_name,))
            
            columns = cursor.fetchall()
            return [
                {
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2] == "YES"
                }
                for col in columns
            ]
    except Exception as e:
        logger.error(f"Error getting schema for table {table_name}: {str(e)}")
        return []

def backup_table(conn, table_name):
    """Backup a table to a JSON file."""
    try:
        # Get table schema
        schema = get_table_schema(conn, table_name)
        
        # Get table data
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(f'SELECT * FROM "{table_name}"')
            rows = cursor.fetchall()
            
            # Convert rows to list of dicts
            data = [dict(row) for row in rows]
            
            # Create backup file
            table_file = BACKUP_DIR / f"{table_name}.json"
            with open(table_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "table": table_name,
                    "schema": schema,
                    "data": data,
                    "count": len(data)
                }, f, indent=2, default=str)
            
            logger.info(f"Backed up table {table_name} with {len(data)} rows")
            return True
    except Exception as e:
        logger.error(f"Error backing up table {table_name}: {str(e)}")
        return False

def create_migration_readme():
    """Create a README.md file with migration instructions."""
    try:
        readme_file = BACKUP_DIR / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write("""# Database Backup for Supabase Migration

## Overview

This directory contains JSON backups of all tables in the database. These files can be used to recreate the database in Supabase.

## Files

Each table has a corresponding JSON file with the following structure:

```json
{
  "table": "table_name",
  "schema": [
    {
      "name": "column_name",
      "type": "data_type",
      "nullable": true|false
    },
    ...
  ],
  "data": [
    {
      "column1": "value1",
      "column2": "value2",
      ...
    },
    ...
  ],
  "count": number_of_rows
}
```

## Migration Steps

1. Create a new Supabase project
2. Use the SQL Editor in Supabase to create tables based on the schema information
3. Write SQL statements to insert the data from these JSON files
4. Execute the SQL statements in the correct order to populate the database

## Recommended Migration Order

To avoid foreign key constraint violations, import tables in this order:

1. users
2. body_parts
3. categories
4. procedures
5. Other dependent tables

## Connection String

After migration, update your `.env` file with the Supabase connection string:

```
DATABASE_URL=postgresql://postgres:{YOUR-PASSWORD}@db.XXXXXXXXXXXXXXXX.supabase.co:5432/postgres
```

Replace `{YOUR-PASSWORD}` with your Supabase password and `XXXXXXXXXXXXXXXX` with your Supabase project ID.

## Support

For further assistance, refer to the Supabase documentation or contact their support team.
""")
            logger.info(f"Created migration README at {readme_file}")
            return True
    except Exception as e:
        logger.error(f"Error creating migration README: {str(e)}")
        return False

def create_metadata_file(tables):
    """Create a metadata.json file with table information."""
    try:
        metadata_file = BACKUP_DIR / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                "backup_date": datetime.now().isoformat(),
                "tables": tables,
                "table_count": len(tables)
            }, f, indent=2)
            
        logger.info(f"Created metadata file at {metadata_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating metadata file: {str(e)}")
        return False

def backup_database():
    """Backup the entire database."""
    # Connect to database
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        # Create backup directory
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Get all tables
        tables = get_all_tables(conn)
        if not tables:
            logger.error("No tables found in database")
            return False
            
        logger.info(f"Found {len(tables)} tables to backup")
        
        # Create metadata file
        create_metadata_file(tables)
        
        # Backup each table
        successful_backups = 0
        for table in tables:
            if backup_table(conn, table):
                successful_backups += 1
        
        # Create migration README
        create_migration_readme()
        
        logger.info(f"Successfully backed up {successful_backups} of {len(tables)} tables")
        return successful_backups == len(tables)
    except Exception as e:
        logger.error(f"Error during database backup: {str(e)}")
        return False
    finally:
        conn.close()

def main():
    """Main function to run the backup."""
    logger.info("=== Starting database backup ===")
    
    success = backup_database()
    
    if success:
        logger.info("=== Database backup completed successfully ===")
        logger.info(f"Backup saved to: {BACKUP_DIR}")
        return 0
    else:
        logger.error("=== Database backup failed ===")
        logger.error("Please check the logs for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())