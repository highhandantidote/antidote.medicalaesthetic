#!/usr/bin/env python3
"""
Add image field to categories table for admin image uploads.
"""
import os
import psycopg2
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL environment variable not set")
    
    # Parse the database URL
    parsed_url = urlparse(database_url)
    
    conn = psycopg2.connect(
        host=parsed_url.hostname,
        port=parsed_url.port,
        database=parsed_url.path[1:],  # Remove leading slash
        user=parsed_url.username,
        password=parsed_url.password
    )
    
    return conn

def add_image_field():
    """Add image field to categories table."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check if image column already exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'categories' AND column_name = 'image_url'
            """)
            
            if cursor.fetchone():
                logger.info("Image field already exists in categories table")
                return
            
            # Add the image_url column
            cursor.execute("""
                ALTER TABLE categories 
                ADD COLUMN image_url TEXT
            """)
            
            conn.commit()
            logger.info("Successfully added image_url field to categories table")
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding image field: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_image_field()