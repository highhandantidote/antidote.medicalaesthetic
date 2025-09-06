#!/usr/bin/env python3
"""
Test connection to Supabase with URL-encoded password.

This script properly encodes special characters in the password
to ensure correct parsing of the connection string.
"""
import os
import sys
import logging
import psycopg2
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_connection():
    """Test connection to Supabase with URL-encoded password."""
    try:
        # Components from screenshot
        host = "db.asgwdfirkanaaswobuj.supabase.co"
        port = 5432
        database = "postgres"
        user = "postgres"
        password = "Ar8897365503@#"
        
        # URL-encode the password to handle special characters
        encoded_password = urllib.parse.quote_plus(password)
        
        # Build connection string
        conn_str = f"postgresql://{user}:{encoded_password}@{host}:{port}/{database}"
        
        logger.info(f"Connecting with encoded string: {conn_str[:25]}...")
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
    logger.info("=== Testing direct connection to Supabase with encoded password ===")
    
    success = test_connection()
    
    if success:
        logger.info("=== Connection test successful ===")
        return 0
    else:
        logger.error("=== Connection test failed ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())