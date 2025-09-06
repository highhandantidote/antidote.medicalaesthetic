#!/usr/bin/env python3
"""
Export database to SQL files for Supabase import.

This script:
1. Exports the database schema (tables, sequences, indexes)
2. Exports all data as SQL INSERT statements
3. Creates a directory of SQL files that can be imported into Supabase
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
        logging.FileHandler("export_database.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
EXPORT_DIR = Path('database_export') / datetime.now().strftime("%Y%m%d_%H%M%S")
SCHEMA_FILE = EXPORT_DIR / "schema.sql"
DATA_DIR = EXPORT_DIR / "data"
TABLES_FILE = EXPORT_DIR / "tables.json"
README_FILE = EXPORT_DIR / "README.md"

def get_db_connection():
    """Get a connection to the current database."""
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
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        return [table[0] for table in cursor.fetchall()]

def export_table_schema(conn, table_name, schema_file):
    """Export the schema for a table."""
    try:
        with conn.cursor() as cursor:
            # Get table schema
            cursor.execute(f"""
                SELECT 
                    column_name, 
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM 
                    information_schema.columns
                WHERE 
                    table_schema = 'public' 
                    AND table_name = %s
                ORDER BY 
                    ordinal_position;
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            # Write CREATE TABLE statement
            with open(schema_file, 'a', encoding='utf-8') as f:
                f.write(f"\n-- Table: {table_name}\n")
                f.write(f"CREATE TABLE IF NOT EXISTS \"{table_name}\" (\n")
                
                column_defs = []
                for col in columns:
                    col_name, data_type, max_length, is_nullable, default = col
                    
                    # Format data type with length if applicable
                    if max_length is not None:
                        type_def = f"{data_type}({max_length})"
                    else:
                        type_def = data_type
                        
                    # Add NULL/NOT NULL constraint
                    nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                    
                    # Add default if present
                    default_clause = f" DEFAULT {default}" if default else ""
                    
                    column_defs.append(f"    \"{col_name}\" {type_def} {nullable}{default_clause}")
                
                # Add primary key constraint if exists
                cursor.execute(f"""
                    SELECT
                        kcu.column_name
                    FROM
                        information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                            ON tc.constraint_name = kcu.constraint_name
                    WHERE
                        tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_schema = 'public'
                        AND tc.table_name = %s
                    ORDER BY
                        kcu.ordinal_position;
                """, (table_name,))
                
                pk_columns = [row[0] for row in cursor.fetchall()]
                if pk_columns:
                    quoted_columns = [f'"{col}"' for col in pk_columns]
                    column_defs.append(f"    PRIMARY KEY ({', '.join(quoted_columns)})")
                
                f.write(",\n".join(column_defs))
                f.write("\n);\n\n")
                
                # Export indexes
                cursor.execute(f"""
                    SELECT
                        indexname,
                        indexdef
                    FROM
                        pg_indexes
                    WHERE
                        schemaname = 'public'
                        AND tablename = %s
                        AND indexname NOT LIKE '%pkey'
                    ORDER BY
                        indexname;
                """, (table_name,))
                
                indexes = cursor.fetchall()
                for index_name, index_def in indexes:
                    f.write(f"{index_def};\n")
                
                f.write("\n")
                
            return True
    except Exception as e:
        logger.error(f"Error exporting schema for table {table_name}: {str(e)}")
        return False

def export_table_data(conn, table_name, data_dir):
    """Export the data for a table as SQL INSERT statements."""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(f'SELECT * FROM "{table_name}"')
            rows = cursor.fetchall()
            
            if not rows:
                logger.info(f"No data to export for table {table_name}")
                return True
                
            data_file = data_dir / f"{table_name}.sql"
            with open(data_file, 'w', encoding='utf-8') as f:
                f.write(f"-- Data for table: {table_name}\n")
                f.write(f"-- Total rows: {len(rows)}\n\n")
                
                # Get column names
                columns = rows[0].keys()
                
                # Write INSERT statements in batches of 100
                batch_size = 100
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i+batch_size]
                    
                    f.write(f"INSERT INTO \"{table_name}\" (")
                    f.write(", ".join([f'"{col}"' for col in columns]))
                    f.write(") VALUES\n")
                    
                    values_list = []
                    for row in batch:
                        values = []
                        for col in columns:
                            if row[col] is None:
                                values.append("NULL")
                            elif isinstance(row[col], (int, float)):
                                values.append(str(row[col]))
                            elif isinstance(row[col], bool):
                                values.append("TRUE" if row[col] else "FALSE")
                            else:
                                # Escape special characters in strings
                                escaped = str(row[col]).replace("'", "''")
                                values.append(f"'{escaped}'")
                        
                        values_list.append(f"({', '.join(values)})")
                    
                    f.write(",\n".join(values_list))
                    f.write(";\n\n")
                
            logger.info(f"Exported {len(rows)} rows from table {table_name}")
            return True
    except Exception as e:
        logger.error(f"Error exporting data for table {table_name}: {str(e)}")
        return False

def export_sequences(conn, schema_file):
    """Export sequences current values."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    sequence_name
                FROM
                    information_schema.sequences
                WHERE
                    sequence_schema = 'public'
                ORDER BY
                    sequence_name;
            """)
            
            sequences = cursor.fetchall()
            
            with open(schema_file, 'a', encoding='utf-8') as f:
                f.write("\n-- Sequences\n")
                
                for seq_name in [seq[0] for seq in sequences]:
                    cursor.execute(f"SELECT last_value FROM {seq_name}")
                    last_value = cursor.fetchone()[0]
                    
                    f.write(f"SELECT setval('{seq_name}', {last_value}, true);\n")
                
                f.write("\n")
                
            logger.info(f"Exported {len(sequences)} sequences")
            return True
    except Exception as e:
        logger.error(f"Error exporting sequences: {str(e)}")
        return False

def create_readme():
    """Create a README.md file with import instructions."""
    try:
        with open(README_FILE, 'w', encoding='utf-8') as f:
            f.write("""# Database Export for Supabase

This directory contains SQL files to recreate your database in Supabase.

## Files

- `schema.sql` - SQL script to create all tables, indexes, and sequences
- `data/` - Directory containing SQL files with INSERT statements for each table
- `tables.json` - List of all tables in the database

## Import Instructions

1. **Create Database Schema**:
   - In the Supabase dashboard, go to the SQL Editor
   - Open and run the `schema.sql` file to create all tables and indexes

2. **Import Data**:
   - Run each SQL file in the `data/` directory to import the data
   - Start with tables that don't have foreign key dependencies

3. **Verify Import**:
   - After importing, verify row counts match the numbers in the data SQL files

## Notes

- If you encounter foreign key constraint errors, you may need to modify the import order
- If some inserts fail, you can edit the SQL files to skip problematic rows
- Large tables are split into batches of 100 rows per INSERT statement

## Support

If you encounter any issues with the import, review the error messages for specific guidance.

""")
            logger.info(f"Created README file at {README_FILE}")
            return True
    except Exception as e:
        logger.error(f"Error creating README file: {str(e)}")
        return False

def export_database():
    """Export the database schema and data."""
    # Connect to database
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        # Create export directory
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Get all tables
        tables = get_all_tables(conn)
        logger.info(f"Found {len(tables)} tables in database")
        
        # Save table list
        with open(TABLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(tables, f, indent=2)
        
        # Create schema file
        with open(SCHEMA_FILE, 'w', encoding='utf-8') as f:
            f.write("-- Database Schema Export\n")
            f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Export table schemas
        for table in tables:
            logger.info(f"Exporting schema for table: {table}")
            export_table_schema(conn, table, SCHEMA_FILE)
        
        # Export sequences
        export_sequences(conn, SCHEMA_FILE)
        
        # Export table data
        for table in tables:
            logger.info(f"Exporting data for table: {table}")
            export_table_data(conn, table, DATA_DIR)
        
        # Create README
        create_readme()
        
        logger.info(f"Database export completed successfully to {EXPORT_DIR}")
        return True
    except Exception as e:
        logger.error(f"Error during database export: {str(e)}")
        return False
    finally:
        conn.close()

def main():
    """Main function to run the export."""
    logger.info("=== Starting database export ===")
    
    success = export_database()
    
    if success:
        logger.info("=== Database export completed successfully ===")
        logger.info(f"Export saved to: {EXPORT_DIR}")
        logger.info("Follow the instructions in the README.md file to import into Supabase")
        return 0
    else:
        logger.error("=== Database export failed ===")
        logger.error("Please check the logs for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())