#!/usr/bin/env python3
"""
Restore Antidote backup from JSON file to Supabase database.

This script reads the JSON backup file and restores all data to the connected database.
"""

import json
import os
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not found")
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

def load_backup_file(filename):
    """Load the JSON backup file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        logger.info(f"Loaded backup file: {filename}")
        logger.info(f"Backup date: {backup_data.get('backup_date', 'Unknown')}")
        return backup_data
    except Exception as e:
        logger.error(f"Failed to load backup file: {str(e)}")
        raise

def create_insert_query(table_name, columns, data_row):
    """Create an INSERT query for a single row."""
    # Filter out None values and prepare data
    filtered_data = {}
    filtered_columns = []
    
    for i, col in enumerate(columns):
        if col in data_row and data_row[col] is not None:
            filtered_data[col] = data_row[col]
            filtered_columns.append(col)
    
    if not filtered_columns:
        return None, None
    
    # Create the query
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT (id) DO NOTHING").format(
        sql.Identifier(table_name),
        sql.SQL(', ').join(map(sql.Identifier, filtered_columns)),
        sql.SQL(', ').join(sql.Placeholder() * len(filtered_columns))
    )
    
    values = [filtered_data[col] for col in filtered_columns]
    return query, values

def restore_table(conn, table_name, table_data):
    """Restore a single table from backup data."""
    logger.info(f"Starting restore for table: {table_name}")
    
    columns = table_data.get('columns', [])
    data = table_data.get('data', [])
    row_count = table_data.get('row_count', len(data))
    
    logger.info(f"Table {table_name}: {row_count} rows to restore")
    
    if not data:
        logger.info(f"No data to restore for table: {table_name}")
        return
    
    success_count = 0
    error_count = 0
    
    with conn.cursor() as cursor:
        for i, row in enumerate(data):
            try:
                query, values = create_insert_query(table_name, columns, row)
                
                if query and values:
                    cursor.execute(query, values)
                    success_count += 1
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"Processed {i + 1}/{len(data)} rows for {table_name}")
                        conn.commit()  # Commit every 100 rows
                
            except Exception as e:
                error_count += 1
                logger.warning(f"Failed to insert row {i+1} in {table_name}: {str(e)}")
                # Continue with next row
                continue
        
        # Final commit
        conn.commit()
    
    logger.info(f"Table {table_name} restore completed: {success_count} success, {error_count} errors")

def restore_backup(backup_filename):
    """Main function to restore the entire backup."""
    logger.info("Starting backup restoration process...")
    
    # Load backup data
    backup_data = load_backup_file(backup_filename)
    tables = backup_data.get('tables', {})
    
    if not tables:
        logger.error("No tables found in backup file")
        return
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        logger.info(f"Found {len(tables)} tables to restore")
        
        # Define table restoration order (to handle foreign key dependencies)
        table_order = [
            'users',
            'body_parts', 
            'categories',
            'procedures',
            'doctors',
            'community',
            'banners',
            'banner_slides',
            'education_modules',
            'education_quizzes',
            'education_questions',
            'recommendation_history',
            'leads',
            'user_sessions',
            'face_scan_recommendations',
            'cost_calculations'
        ]
        
        # Restore tables in order
        restored_tables = set()
        
        # First restore tables in the defined order
        for table_name in table_order:
            if table_name in tables:
                restore_table(conn, table_name, tables[table_name])
                restored_tables.add(table_name)
        
        # Then restore any remaining tables
        for table_name, table_data in tables.items():
            if table_name not in restored_tables:
                restore_table(conn, table_name, table_data)
        
        logger.info("Backup restoration completed successfully!")
        
        # Print summary
        with conn.cursor() as cursor:
            logger.info("\nRestoration Summary:")
            for table_name in tables.keys():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    logger.info(f"  {table_name}: {count} rows")
                except Exception as e:
                    logger.warning(f"  {table_name}: Could not count rows - {str(e)}")
    
    except Exception as e:
        logger.error(f"Error during restoration: {str(e)}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

def main():
    """Main function."""
    backup_filename = "attached_assets/antidote_backup_20250527_180345.json"
    
    if not os.path.exists(backup_filename):
        logger.error(f"Backup file not found: {backup_filename}")
        return
    
    try:
        restore_backup(backup_filename)
        logger.info("✅ Backup restoration completed successfully!")
    except Exception as e:
        logger.error(f"❌ Backup restoration failed: {str(e)}")

if __name__ == "__main__":
    main()