#!/usr/bin/env python3
"""
Test direct connection to Supabase.

This script attempts to connect directly to Supabase using
the connection string format seen in the screenshot.
"""
import os
import sys
import logging
import psycopg2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Connection string exactly as shown in screenshot
CONNECTION_STRING = "postgresql://postgres:[YOUR-PASSWORD]@db.asgwdfirkanaaswobuj.supabase.co:5432/postgres"

def test_connection():
    """Test connection to Supabase."""
    try:
        # Replace placeholder with actual password
        conn_str = CONNECTION_STRING.replace("[YOUR-PASSWORD]", "Ar8897365503@#")
        
        logger.info(f"Connecting with string: {conn_str[:25]}...")
        conn = psycopg2.connect(conn_str)
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"Successfully connected to Supabase!")
            logger.info(f"PostgreSQL version: {version[0]}")
            
            # List all tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            if tables:
                logger.info(f"Found {len(tables)} tables in Supabase:")
                for table in tables:
                    logger.info(f"  - {table[0]}")
            else:
                logger.info("No tables found in Supabase database.")
                
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {str(e)}")
        return False

def main():
    """Main function."""
    logger.info("=== Testing direct connection to Supabase ===")
    
    success = test_connection()
    
    if success:
        logger.info("=== Connection test successful ===")
        return 0
    else:
        logger.error("=== Connection test failed ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())