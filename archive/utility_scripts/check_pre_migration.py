#!/usr/bin/env python3
"""
Check database status before migration to Supabase.

This script:
1. Counts records in key tables
2. Checks database connectivity 
3. Verifies table permissions and structure
4. Generates a pre-migration report

Run this before migrating to ensure everything is ready.
"""
import os
import sys
import json
import logging
import psycopg2
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pre_migration_check.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Define report file path
REPORT_FILE = "pre_migration_report.json"

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

def get_table_counts(conn):
    """Get record counts for all tables."""
    tables = {}
    
    try:
        with conn.cursor() as cursor:
            # Get all tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            all_tables = [row[0] for row in cursor.fetchall()]
            
            # Get count for each table
            for table in all_tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                    count = cursor.fetchone()[0]
                    tables[table] = count
                except Exception as e:
                    logger.error(f"Error getting count for table {table}: {str(e)}")
                    tables[table] = -1
            
            return tables
    except Exception as e:
        logger.error(f"Error getting table counts: {str(e)}")
        return {}

def check_key_relations(conn):
    """Check key relationship constraints in the database."""
    relations = []
    
    try:
        with conn.cursor() as cursor:
            # Get foreign key constraints
            cursor.execute("""
                SELECT
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu 
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
            """)
            
            for row in cursor.fetchall():
                table, column, ref_table, ref_column = row
                relations.append({
                    "table": table,
                    "column": column,
                    "references_table": ref_table,
                    "references_column": ref_column
                })
            
            return relations
    except Exception as e:
        logger.error(f"Error checking key relations: {str(e)}")
        return []

def check_sequence_values(conn):
    """Check sequence values compared to max IDs in tables."""
    sequences = []
    
    try:
        with conn.cursor() as cursor:
            # Get sequences
            cursor.execute("""
                SELECT sequence_name 
                FROM information_schema.sequences
                WHERE sequence_schema = 'public'
            """)
            
            for row in cursor.fetchall():
                sequence_name = row[0]
                
                # Try to find the table and column name based on sequence naming convention
                # Assuming format: tablename_columnname_seq
                parts = sequence_name.split('_')
                if len(parts) >= 3 and parts[-1] == 'seq':
                    table_name = '_'.join(parts[:-2])
                    column_name = parts[-2]
                    
                    # Get current sequence value
                    cursor.execute(f"SELECT last_value FROM {sequence_name}")
                    seq_value = cursor.fetchone()[0]
                    
                    # Get max ID from the table
                    try:
                        cursor.execute(f'SELECT MAX("{column_name}") FROM "{table_name}"')
                        max_id = cursor.fetchone()[0]
                        if max_id is None:
                            max_id = 0
                    except Exception:
                        max_id = -1
                    
                    sequences.append({
                        "sequence_name": sequence_name,
                        "table_name": table_name,
                        "column_name": column_name,
                        "sequence_value": seq_value,
                        "max_id": max_id
                    })
                else:
                    # For sequences that don't follow the convention
                    sequences.append({
                        "sequence_name": sequence_name,
                        "table_name": "unknown",
                        "column_name": "unknown",
                        "sequence_value": -1,
                        "max_id": -1
                    })
            
            return sequences
    except Exception as e:
        logger.error(f"Error checking sequence values: {str(e)}")
        return []

def check_db_permissions(conn):
    """Check if the database user has the necessary permissions."""
    permissions = {}
    
    try:
        with conn.cursor() as cursor:
            # Test SELECT permission
            try:
                cursor.execute("SELECT 1")
                permissions["select"] = True
            except Exception:
                permissions["select"] = False
            
            # Test INSERT permission
            try:
                # Create a temporary table to test insert
                cursor.execute("CREATE TEMPORARY TABLE permission_test (id int)")
                cursor.execute("INSERT INTO permission_test VALUES (1)")
                permissions["insert"] = True
            except Exception:
                permissions["insert"] = False
            
            # Test CREATE TABLE permission
            try:
                cursor.execute("CREATE TABLE IF NOT EXISTS permission_test_table (id int)")
                permissions["create_table"] = True
                # Clean up
                cursor.execute("DROP TABLE IF EXISTS permission_test_table")
            except Exception:
                permissions["create_table"] = False
            
            # Test CREATE INDEX permission
            try:
                cursor.execute("CREATE TABLE IF NOT EXISTS permission_test_table (id int)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_test ON permission_test_table (id)")
                permissions["create_index"] = True
                # Clean up
                cursor.execute("DROP TABLE IF EXISTS permission_test_table")
            except Exception:
                permissions["create_index"] = False
            
            # Test ALTER TABLE permission
            try:
                cursor.execute("CREATE TABLE IF NOT EXISTS permission_test_table (id int)")
                cursor.execute("ALTER TABLE permission_test_table ADD COLUMN test_col text")
                permissions["alter_table"] = True
                # Clean up
                cursor.execute("DROP TABLE IF EXISTS permission_test_table")
            except Exception:
                permissions["alter_table"] = False
            
            conn.rollback()  # Roll back any test operations
            
            return permissions
    except Exception as e:
        logger.error(f"Error checking database permissions: {str(e)}")
        return {}

def generate_report(table_counts, relations, sequences, permissions):
    """Generate a report of the database status."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "table_counts": table_counts,
        "total_tables": len(table_counts),
        "total_records": sum(count for count in table_counts.values() if count >= 0),
        "key_relations": relations,
        "sequences": sequences,
        "permissions": permissions,
        "migration_ready": all(permissions.values())
    }
    
    # Save report to file
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report

def main():
    """Run pre-migration check."""
    logger.info("=== Starting pre-migration database check ===")
    
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return 1
    
    try:
        # Get table counts
        logger.info("Getting table record counts...")
        table_counts = get_table_counts(conn)
        logger.info(f"Found {len(table_counts)} tables with {sum(count for count in table_counts.values() if count >= 0)} total records")
        
        # Check key relations
        logger.info("Checking key relationships...")
        relations = check_key_relations(conn)
        logger.info(f"Found {len(relations)} foreign key relationships")
        
        # Check sequence values
        logger.info("Checking sequence values...")
        sequences = check_sequence_values(conn)
        logger.info(f"Checked {len(sequences)} sequences")
        
        # Check database permissions
        logger.info("Checking database permissions...")
        permissions = check_db_permissions(conn)
        all_permissions = all(permissions.values())
        logger.info(f"Database permissions check: {'PASSED' if all_permissions else 'FAILED'}")
        
        # Generate report
        logger.info("Generating pre-migration report...")
        report = generate_report(table_counts, relations, sequences, permissions)
        
        # Print summary
        logger.info("=== Pre-Migration Check Summary ===")
        logger.info(f"Total tables: {report['total_tables']}")
        logger.info(f"Total records: {report['total_records']}")
        logger.info(f"Foreign key relationships: {len(report['key_relations'])}")
        logger.info(f"Sequences checked: {len(report['sequences'])}")
        logger.info(f"Migration ready: {report['migration_ready']}")
        logger.info(f"Report saved to: {REPORT_FILE}")
        
        if report['migration_ready']:
            logger.info("Database is READY for migration")
            return 0
        else:
            logger.warning("Database is NOT READY for migration - check permissions")
            return 1
    except Exception as e:
        logger.error(f"Error during pre-migration check: {str(e)}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())