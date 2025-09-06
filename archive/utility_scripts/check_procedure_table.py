#!/usr/bin/env python3
"""
Simple debug script to check procedure table structure and attributes.
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def check_procedure_table():
    """Check the procedure table structure in the database directly."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL not found in environment")
        sys.exit(1)
    
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        logger.info("Database connection established successfully")
        cursor = conn.cursor()
        
        logger.info("Checking procedure table structure...")
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'procedure'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            logger.info("Table 'procedure' exists in database")
            
            # Get table columns
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'procedure';
            """)
            
            columns = cursor.fetchall()
            logger.info(f"Found {len(columns)} columns in table 'procedure':")
            for col_name, data_type in columns:
                logger.info(f"  - {col_name} ({data_type})")
                
            # Get procedure records
            cursor.execute("SELECT * FROM procedure LIMIT 5;")
            records = cursor.fetchall()
            
            logger.info(f"Found {len(records)} records in table 'procedure'")
            
            # Pretty print column names and first 2 records with values
            if records:
                col_names = [desc[0] for desc in cursor.description]
                logger.info("Column names: " + ", ".join(col_names))
                
                for i, record in enumerate(records[:2]):
                    logger.info(f"Record {i+1}:")
                    for j, value in enumerate(record):
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        logger.info(f"  - {col_names[j]}: {value}")
                        
                # Check category_id values
                cursor.execute("SELECT id, procedure_name, category_id FROM procedure;")
                cat_records = cursor.fetchall()
                
                logger.info("Checking category_id values:")
                for record in cat_records:
                    proc_id, proc_name, cat_id = record
                    logger.info(f"  - Procedure {proc_id} ({proc_name}): category_id = {cat_id}")
                    
                    # Check if category exists
                    if cat_id is not None:
                        cursor.execute(f"SELECT name FROM category WHERE id = {cat_id};")
                        cat_result = cursor.fetchone()
                        if cat_result:
                            logger.info(f"    - Category exists: {cat_result[0]}")
                        else:
                            logger.warning(f"    - Category {cat_id} does not exist!")
                    else:
                        logger.warning(f"    - No category_id for procedure {proc_id}")
        else:
            logger.warning("Table 'procedure' does NOT exist in database")
            
            # Check if there's a procedures table (plural)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'procedures'
                );
            """)
            exists_plural = cursor.fetchone()[0]
            
            if exists_plural:
                logger.info("Table 'procedures' exists in database (note the plural name)")
                
                # Similar checks for the procedures table
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'procedures';
                """)
                
                columns = cursor.fetchall()
                logger.info(f"Found {len(columns)} columns in table 'procedures':")
                for col_name, data_type in columns:
                    logger.info(f"  - {col_name} ({data_type})")
                    
                # Get procedure records
                cursor.execute("SELECT * FROM procedures LIMIT 5;")
                records = cursor.fetchall()
                
                logger.info(f"Found {len(records)} records in table 'procedures'")
                
                # Pretty print column names and first 2 records with values
                if records:
                    col_names = [desc[0] for desc in cursor.description]
                    logger.info("Column names: " + ", ".join(col_names))
                    
                    for i, record in enumerate(records[:2]):
                        logger.info(f"Record {i+1}:")
                        for j, value in enumerate(record):
                            if isinstance(value, datetime):
                                value = value.isoformat()
                            logger.info(f"  - {col_names[j]}: {value}")
            else:
                logger.warning("Neither 'procedure' nor 'procedures' table found")
            
            # List all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            logger.info(f"Found {len(tables)} tables in database:")
            for table in tables:
                logger.info(f"  - {table[0]}")
                
    except Exception as e:
        logger.error(f"Error checking procedure table: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_procedure_table()