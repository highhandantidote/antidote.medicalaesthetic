#!/usr/bin/env python3
"""
Verify connection to Supabase and check that data was migrated correctly.

This script:
1. Attempts to connect to the database using DATABASE_URL from .env
2. Performs basic queries to verify table existence and row counts
3. Reports on the migration status
"""
import os
import sys
import logging
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("verify_connection.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
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

def get_table_count(conn, table_name):
    """Get the number of rows in a table."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            count = cursor.fetchone()[0]
            return count
    except Exception as e:
        logger.error(f"Error getting count for table {table_name}: {str(e)}")
        return -1

def verify_key_tables(conn):
    """Verify existence and count of key tables."""
    key_tables = [
        "body_parts",
        "categories",
        "procedures",
        "doctors",
        "community",
        "banners",
        "banner_slides"
    ]
    
    results = {}
    for table in key_tables:
        count = get_table_count(conn, table)
        results[table] = count
        
    return results

def run_sample_queries(conn):
    """Run sample queries to verify data integrity."""
    queries = [
        {
            "name": "Doctor count",
            "sql": "SELECT COUNT(*) FROM doctors",
            "description": "Total number of doctors"
        },
        {
            "name": "Body parts",
            "sql": "SELECT name FROM body_parts LIMIT 5",
            "description": "Sample body parts"
        },
        {
            "name": "Active banners",
            "sql": "SELECT name, position FROM banners WHERE is_active = TRUE",
            "description": "Active banner positions"
        },
        {
            "name": "Category distribution",
            "sql": """
                SELECT b.name AS body_part, COUNT(c.id) AS category_count
                FROM categories c
                JOIN body_parts b ON c.body_part_id = b.id
                GROUP BY b.name
                ORDER BY category_count DESC
                LIMIT 5
            """,
            "description": "Categories per body part"
        }
    ]
    
    results = []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            for query in queries:
                try:
                    cursor.execute(query["sql"])
                    rows = cursor.fetchall()
                    results.append({
                        "name": query["name"],
                        "description": query["description"],
                        "success": True,
                        "rows": len(rows),
                        "data": rows if len(rows) <= 5 else rows[:5]
                    })
                except Exception as e:
                    results.append({
                        "name": query["name"],
                        "description": query["description"],
                        "success": False,
                        "error": str(e)
                    })
        return results
    except Exception as e:
        logger.error(f"Error running sample queries: {str(e)}")
        return []

def print_results(table_counts, query_results):
    """Print verification results in an easy-to-read format."""
    print("\n===== DATABASE VERIFICATION RESULTS =====\n")
    
    print("TABLE COUNTS:")
    print("-------------")
    for table, count in table_counts.items():
        status = "✅" if count >= 0 else "❌"
        print(f"{status} {table}: {count if count >= 0 else 'ERROR'}")
    
    print("\nSAMPLE QUERIES:")
    print("--------------")
    for result in query_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['name']} - {result['description']}")
        if result["success"]:
            if isinstance(result["data"], list) and len(result["data"]) > 0:
                if isinstance(result["data"][0], dict):
                    # Format dictionary results
                    keys = result["data"][0].keys()
                    for row in result["data"]:
                        values = [str(row.get(k, '')) for k in keys]
                        print(f"    {', '.join(values)}")
                else:
                    # Format simple results
                    for row in result["data"]:
                        print(f"    {row}")
        else:
            print(f"    Error: {result.get('error', 'Unknown error')}")
    
    print("\nSUMMARY:")
    print("--------")
    tables_ok = sum(1 for count in table_counts.values() if count >= 0)
    queries_ok = sum(1 for result in query_results if result["success"])
    
    print(f"Tables verified: {tables_ok}/{len(table_counts)}")
    print(f"Queries succeeded: {queries_ok}/{len(query_results)}")
    
    if tables_ok == len(table_counts) and queries_ok == len(query_results):
        print("\n✅ DATABASE MIGRATION SUCCESSFUL! The application is ready to use with Supabase.")
    else:
        print("\n⚠️ DATABASE VERIFICATION INCOMPLETE. Some checks failed, please review the logs.")

def main():
    """Main function to verify database connection and data."""
    logger.info("=== Starting Supabase connection verification ===")
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return 1
    
    try:
        # Get all tables
        tables = get_all_tables(conn)
        if not tables:
            logger.error("No tables found in database")
            return 1
            
        logger.info(f"Found {len(tables)} tables in database")
        
        # Verify key tables
        table_counts = verify_key_tables(conn)
        logger.info(f"Verified {len(table_counts)} key tables")
        
        # Run sample queries
        query_results = run_sample_queries(conn)
        logger.info(f"Ran {len(query_results)} sample queries")
        
        # Print results
        print_results(table_counts, query_results)
        
        logger.info("=== Database verification completed ===")
        return 0
    except Exception as e:
        logger.error(f"Error during database verification: {str(e)}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())