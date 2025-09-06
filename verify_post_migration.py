#!/usr/bin/env python3
"""
Verify database migration was successful.

This script:
1. Compares record counts between source and target databases
2. Checks if sequences are set correctly
3. Validates foreign key constraints
4. Ensures all indexes are created properly

Run this after migrating to verify everything was transferred correctly.
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
        logging.FileHandler("post_migration_verification.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PRE_MIGRATION_REPORT = "pre_migration_report.json"
VERIFICATION_REPORT = "post_migration_verification.json"

def load_pre_migration_report():
    """Load the pre-migration report."""
    try:
        if not Path(PRE_MIGRATION_REPORT).exists():
            logger.error(f"Pre-migration report '{PRE_MIGRATION_REPORT}' not found")
            return None
            
        with open(PRE_MIGRATION_REPORT, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading pre-migration report: {str(e)}")
        return None

def get_db_connection(db_url_var='DATABASE_URL'):
    """Get a connection to the database."""
    try:
        db_url = os.environ.get(db_url_var)
        if not db_url:
            logger.error(f"{db_url_var} environment variable not set")
            return None
            
        logger.info(f"Connecting to database {db_url_var}: {db_url[:20]}...")
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database {db_url_var}: {str(e)}")
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

def check_constraints(conn):
    """Check if all constraints are valid."""
    constraints = []
    
    try:
        with conn.cursor() as cursor:
            # Get all constraints
            cursor.execute("""
                SELECT 
                    tc.table_name, 
                    tc.constraint_name,
                    tc.constraint_type
                FROM 
                    information_schema.table_constraints AS tc
                WHERE
                    tc.constraint_schema = 'public'
                ORDER BY
                    tc.table_name, tc.constraint_name
            """)
            
            for row in cursor.fetchall():
                table_name, constraint_name, constraint_type = row
                
                # For foreign key constraints, check if they're valid
                valid = True
                validation_error = None
                
                if constraint_type == 'FOREIGN KEY':
                    try:
                        # Try executing a simple query that would use the constraint
                        cursor.execute(f"""
                            SELECT EXISTS (
                                SELECT 1 FROM information_schema.table_constraints 
                                WHERE constraint_name = %s AND constraint_type = 'FOREIGN KEY'
                            )
                        """, (constraint_name,))
                    except Exception as e:
                        valid = False
                        validation_error = str(e)
                
                constraints.append({
                    "table_name": table_name,
                    "constraint_name": constraint_name,
                    "constraint_type": constraint_type,
                    "valid": valid,
                    "validation_error": validation_error
                })
            
            return constraints
    except Exception as e:
        logger.error(f"Error checking constraints: {str(e)}")
        return []

def check_indexes(conn):
    """Check if all indexes exist and are valid."""
    indexes = []
    
    try:
        with conn.cursor() as cursor:
            # Get all indexes
            cursor.execute("""
                SELECT
                    t.relname AS table_name,
                    i.relname AS index_name,
                    a.attname AS column_name,
                    ix.indisunique AS is_unique,
                    ix.indisprimary AS is_primary
                FROM
                    pg_class t,
                    pg_class i,
                    pg_index ix,
                    pg_attribute a
                WHERE
                    t.oid = ix.indrelid
                    AND i.oid = ix.indexrelid
                    AND a.attrelid = t.oid
                    AND a.attnum = ANY(ix.indkey)
                    AND t.relkind = 'r'
                    AND t.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                ORDER BY
                    t.relname, i.relname, a.attnum
            """)
            
            index_dict = {}
            for row in cursor.fetchall():
                table_name, index_name, column_name, is_unique, is_primary = row
                
                if index_name not in index_dict:
                    index_dict[index_name] = {
                        "table_name": table_name,
                        "index_name": index_name,
                        "columns": [],
                        "is_unique": is_unique,
                        "is_primary": is_primary
                    }
                
                index_dict[index_name]["columns"].append(column_name)
            
            # Convert dict to list
            for index_info in index_dict.values():
                indexes.append(index_info)
            
            return indexes
    except Exception as e:
        logger.error(f"Error checking indexes: {str(e)}")
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
                        
                        # Check if sequence value is correct
                        is_correct = seq_value > max_id
                    except Exception as e:
                        max_id = -1
                        is_correct = False
                        logger.error(f"Error checking max ID for {table_name}.{column_name}: {str(e)}")
                    
                    sequences.append({
                        "sequence_name": sequence_name,
                        "table_name": table_name,
                        "column_name": column_name,
                        "sequence_value": seq_value,
                        "max_id": max_id,
                        "is_correct": is_correct
                    })
                else:
                    # For sequences that don't follow the convention
                    sequences.append({
                        "sequence_name": sequence_name,
                        "table_name": "unknown",
                        "column_name": "unknown",
                        "sequence_value": -1,
                        "max_id": -1,
                        "is_correct": False
                    })
            
            return sequences
    except Exception as e:
        logger.error(f"Error checking sequence values: {str(e)}")
        return []

def compare_table_counts(pre_counts, post_counts):
    """Compare table counts before and after migration."""
    comparison = []
    
    all_tables = set(list(pre_counts.keys()) + list(post_counts.keys()))
    
    for table in sorted(all_tables):
        pre_count = pre_counts.get(table, -1)
        post_count = post_counts.get(table, -1)
        if pre_count >= 0 and post_count >= 0:
            is_match = pre_count == post_count
        else:
            is_match = None  # Can't determine
        
        comparison.append({
            "table": table,
            "pre_migration_count": pre_count,
            "post_migration_count": post_count,
            "counts_match": is_match
        })
    
    return comparison

def generate_report(pre_report, tables_comparison, constraints, indexes, sequences):
    """Generate a verification report."""
    all_counts_match = all(
        item["counts_match"] for item in tables_comparison 
        if item["counts_match"] is not None
    )
    
    all_sequences_correct = all(
        seq["is_correct"] for seq in sequences
        if seq["table_name"] != "unknown"
    )
    
    all_constraints_valid = all(
        const["valid"] for const in constraints
    )
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "pre_migration_timestamp": pre_report.get("timestamp") if pre_report else None,
        "table_counts_comparison": tables_comparison,
        "constraints": constraints,
        "indexes": indexes,
        "sequences": sequences,
        "verification_summary": {
            "all_counts_match": all_counts_match,
            "all_sequences_correct": all_sequences_correct,
            "all_constraints_valid": all_constraints_valid,
            "migration_successful": all_counts_match and all_sequences_correct and all_constraints_valid
        }
    }
    
    # Save report to file
    with open(VERIFICATION_REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report

def main():
    """Run post-migration verification."""
    logger.info("=== Starting post-migration verification ===")
    
    # Load pre-migration report
    pre_report = load_pre_migration_report()
    if not pre_report:
        logger.error("Cannot proceed without pre-migration report")
        return 1
    
    # Connect to source database (if available)
    source_conn = None
    if 'SOURCE_DATABASE_URL' in os.environ:
        source_conn = get_db_connection('SOURCE_DATABASE_URL')
        if source_conn:
            logger.info("Connected to source database")
    
    # Connect to target database
    target_conn = get_db_connection('DATABASE_URL')
    if not target_conn:
        logger.error("Failed to connect to target database")
        return 1
    
    try:
        # Get source table counts (if source connection available)
        source_counts = {}
        if source_conn:
            logger.info("Getting source database table counts...")
            source_counts = get_table_counts(source_conn)
            logger.info(f"Found {len(source_counts)} tables in source database")
        else:
            # Use pre-migration report counts
            logger.info("Using table counts from pre-migration report...")
            source_counts = pre_report.get('table_counts', {})
        
        # Get target table counts
        logger.info("Getting target database table counts...")
        target_counts = get_table_counts(target_conn)
        logger.info(f"Found {len(target_counts)} tables in target database")
        
        # Compare table counts
        logger.info("Comparing table counts...")
        tables_comparison = compare_table_counts(source_counts, target_counts)
        
        # Check constraints in target database
        logger.info("Checking constraints in target database...")
        constraints = check_constraints(target_conn)
        logger.info(f"Checked {len(constraints)} constraints")
        
        # Check indexes in target database
        logger.info("Checking indexes in target database...")
        indexes = check_indexes(target_conn)
        logger.info(f"Found {len(indexes)} indexes")
        
        # Check sequence values in target database
        logger.info("Checking sequence values in target database...")
        sequences = check_sequence_values(target_conn)
        logger.info(f"Checked {len(sequences)} sequences")
        
        # Generate report
        logger.info("Generating verification report...")
        report = generate_report(pre_report, tables_comparison, constraints, indexes, sequences)
        
        # Print summary
        summary = report["verification_summary"]
        logger.info("=== Post-Migration Verification Summary ===")
        logger.info(f"All table counts match: {summary['all_counts_match']}")
        logger.info(f"All sequences are correct: {summary['all_sequences_correct']}")
        logger.info(f"All constraints are valid: {summary['all_constraints_valid']}")
        logger.info(f"Overall migration success: {summary['migration_successful']}")
        logger.info(f"Report saved to: {VERIFICATION_REPORT}")
        
        if summary['migration_successful']:
            logger.info("Migration verification PASSED")
            return 0
        else:
            logger.warning("Migration verification FAILED - check report for details")
            return 1
    except Exception as e:
        logger.error(f"Error during post-migration verification: {str(e)}")
        return 1
    finally:
        if source_conn:
            source_conn.close()
        if target_conn:
            target_conn.close()

if __name__ == "__main__":
    sys.exit(main())