#!/usr/bin/env python3
"""
Generate SQL statements from JSON backup files for Supabase import.

This script:
1. Reads the JSON backup files created by database_backup.py
2. Generates SQL statements to create tables and insert data
3. Outputs the SQL files in the correct order for import into Supabase
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("generate_sql.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
BACKUP_DIR = "database_backup/20250515_174306"  # Use the latest backup directory
SQL_OUTPUT_DIR = Path('sql_import') / datetime.now().strftime("%Y%m%d_%H%M%S")
README_FILE = SQL_OUTPUT_DIR / "README.md"

# Define the order of tables for import
TABLE_ORDER = [
    "users",
    "body_parts",
    "categories",
    "procedures",
    "doctors",
    "doctor_procedures",
    "doctor_categories",
    "banners",
    "banner_slides",
    "community",
    "community_replies",
    "community_tagging",
    "community_moderation",
    "face_scan_analyses",
    "face_scan_recommendations",
    "education_modules",
    "favorites",
    "appointments",
    "doctor_availability",
    "doctor_photos",
    "interactions"
]

def get_backup_files():
    """Get a list of all JSON backup files."""
    backup_path = Path(BACKUP_DIR)
    if not backup_path.exists():
        logger.error(f"Backup directory {BACKUP_DIR} does not exist")
        return []
        
    return sorted(list(backup_path.glob("*.json")))

def get_type_mapping(pg_type):
    """Map PostgreSQL types to Supabase compatible types."""
    type_map = {
        "character varying": "VARCHAR",
        "timestamp without time zone": "TIMESTAMP",
        "timestamp with time zone": "TIMESTAMPTZ",
        "double precision": "DOUBLE PRECISION",
        "boolean": "BOOLEAN",
        "integer": "INTEGER",
        "text": "TEXT",
        "json": "JSON",
        "jsonb": "JSONB",
        "date": "DATE",
        "time without time zone": "TIME",
        "time with time zone": "TIMETZ",
        "bytea": "BYTEA",
        "uuid": "UUID",
        "bigint": "BIGINT",
    }
    
    return type_map.get(pg_type, pg_type)

def generate_create_table_sql(table_name, schema):
    """Generate SQL to create a table."""
    try:
        column_defs = []
        
        for column in schema:
            col_name = column["name"]
            col_type = get_type_mapping(column["type"])
            nullable = "NULL" if column["nullable"] else "NOT NULL"
            
            # Special handling for serial types
            if col_name == "id" and col_type == "INTEGER":
                column_defs.append(f'    "{col_name}" SERIAL PRIMARY KEY')
            else:
                column_defs.append(f'    "{col_name}" {col_type} {nullable}')
        
        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n'
        create_sql += ",\n".join(column_defs)
        create_sql += "\n);\n\n"
        
        return create_sql
    except Exception as e:
        logger.error(f"Error generating CREATE TABLE SQL for {table_name}: {str(e)}")
        return ""

def format_value(value):
    """Format a value for SQL INSERT statement."""
    if value is None:
        return "NULL"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    else:
        # Escape quotes in strings
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"

def generate_insert_sql(table_name, data):
    """Generate SQL to insert data into a table."""
    try:
        if not data:
            logger.info(f"No data to insert for table {table_name}")
            return ""
            
        # Get column names from first row
        columns = data[0].keys()
        columns_sql = ", ".join([f'"{col}"' for col in columns])
        
        # Generate INSERT statements in batches of 100
        batch_size = 100
        sql_parts = []
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            
            insert_sql = f'INSERT INTO "{table_name}" ({columns_sql}) VALUES\n'
            
            value_rows = []
            for row in batch:
                values = [format_value(row[col]) for col in columns]
                value_rows.append(f"({', '.join(values)})")
            
            insert_sql += ",\n".join(value_rows)
            insert_sql += ";\n\n"
            
            sql_parts.append(insert_sql)
        
        return "".join(sql_parts)
    except Exception as e:
        logger.error(f"Error generating INSERT SQL for {table_name}: {str(e)}")
        return ""

def generate_sequence_update_sql(table_name, data):
    """Generate SQL to update sequences after data import."""
    try:
        if not data or "id" not in data[0]:
            return ""
            
        # Find maximum ID
        max_id = 0
        for row in data:
            if row["id"] is not None and isinstance(row["id"], int):
                max_id = max(max_id, row["id"])
        
        if max_id > 0:
            return f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), {max_id}, true);\n\n"
        
        return ""
    except Exception as e:
        logger.error(f"Error generating sequence update SQL for {table_name}: {str(e)}")
        return ""

def process_backup_file(file_path):
    """Process a single JSON backup file and generate SQL."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            backup = json.load(f)
            
        table_name = backup.get("table")
        schema = backup.get("schema")
        data = backup.get("data")
        
        if not table_name or not schema:
            logger.error(f"Invalid backup file: {file_path}")
            return None
            
        sql_file = SQL_OUTPUT_DIR / f"{table_name}.sql"
        
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(f"-- SQL for table: {table_name}\n")
            f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Row count: {len(data)}\n\n")
            
            # Create table
            f.write(generate_create_table_sql(table_name, schema))
            
            # Insert data
            f.write(generate_insert_sql(table_name, data))
            
            # Update sequence if needed
            f.write(generate_sequence_update_sql(table_name, data))
        
        logger.info(f"Generated SQL for table {table_name}")
        return table_name
    except Exception as e:
        logger.error(f"Error processing backup file {file_path}: {str(e)}")
        return None

def create_import_script():
    """Create a shell script to run the SQL files in the correct order."""
    try:
        script_file = SQL_OUTPUT_DIR / "import_to_supabase.sql"
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write("-- Supabase Import Script\n")
            f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Add comments about usage
            f.write("-- Run this script in the Supabase SQL Editor to import all tables\n")
            f.write("-- Note: This script includes all SQL in the proper order\n\n")
            
            # Include each table's SQL in the correct order
            for table_name in TABLE_ORDER:
                sql_file = SQL_OUTPUT_DIR / f"{table_name}.sql"
                if sql_file.exists():
                    f.write(f"\\echo 'Importing {table_name}...'\n")
                    with open(sql_file, 'r', encoding='utf-8') as table_sql:
                        f.write(table_sql.read())
                    f.write("\n")
            
            # Include any remaining tables not in the order list
            all_tables = [f.stem for f in SQL_OUTPUT_DIR.glob("*.sql") if f.stem != "import_to_supabase" and f.stem not in TABLE_ORDER]
            for table_name in all_tables:
                sql_file = SQL_OUTPUT_DIR / f"{table_name}.sql"
                f.write(f"\\echo 'Importing {table_name}...'\n")
                with open(sql_file, 'r', encoding='utf-8') as table_sql:
                    f.write(table_sql.read())
                f.write("\n")
        
        logger.info(f"Created import script at {script_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating import script: {str(e)}")
        return False

def create_readme():
    """Create a README.md file with import instructions."""
    try:
        with open(README_FILE, 'w', encoding='utf-8') as f:
            f.write("""# Supabase Import SQL Files

This directory contains SQL files for importing your database into Supabase.

## Files

- `*.sql` - Individual SQL files for each table
- `import_to_supabase.sql` - A single file containing all SQL in the correct order

## Import Instructions

### Option 1: Use the all-in-one script

1. Open the Supabase dashboard and navigate to the SQL Editor
2. Open the `import_to_supabase.sql` file
3. Copy and paste the contents into the SQL Editor
4. Run the script to import all tables and data

### Option 2: Import tables individually

If you prefer to import tables one at a time:

1. Start with the core tables in this order:
   - users.sql
   - body_parts.sql
   - categories.sql
   - procedures.sql
   - doctors.sql
   - doctor_procedures.sql
2. Then import the remaining tables

## After Import

Update your `.env` file with the Supabase connection string:

```
DATABASE_URL=postgresql://postgres:{YOUR-PASSWORD}@db.XXXXXXXXXXXXXXXX.supabase.co:5432/postgres
```

Replace `{YOUR-PASSWORD}` with your Supabase password and `XXXXXXXXXXXXXXXX` with your Supabase project ID.

## Troubleshooting

If you encounter errors during import:

1. Foreign key violations: Import tables in the correct order (dependencies first)
2. Data format issues: Check and modify the SQL as needed
3. Connection problems: Make sure your Supabase project is properly configured

## Support

For further assistance, refer to the Supabase documentation or contact their support team.
""")
            logger.info(f"Created README file at {README_FILE}")
            return True
    except Exception as e:
        logger.error(f"Error creating README file: {str(e)}")
        return False

def process_backup_files():
    """Process all backup files and generate SQL."""
    # Get all backup files
    backup_files = get_backup_files()
    
    if not backup_files:
        logger.error("No backup files found")
        return False
    
    # Create output directory
    SQL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process each backup file
    processed_tables = []
    for file_path in backup_files:
        # Skip metadata file
        if file_path.name == "metadata.json" or file_path.name == "README.md":
            continue
            
        table = process_backup_file(file_path)
        if table:
            processed_tables.append(table)
    
    # Create import script
    create_import_script()
    
    # Create README
    create_readme()
    
    logger.info(f"Generated SQL for {len(processed_tables)} tables")
    return True

def main():
    """Main function to run the SQL generation."""
    logger.info("=== Starting SQL generation from backup ===")
    
    success = process_backup_files()
    
    if success:
        logger.info("=== SQL generation completed successfully ===")
        logger.info(f"SQL files saved to: {SQL_OUTPUT_DIR}")
        logger.info("Follow the instructions in the README.md file to import into Supabase")
        return 0
    else:
        logger.error("=== SQL generation failed ===")
        logger.error("Please check the logs for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())