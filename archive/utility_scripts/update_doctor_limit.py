#!/usr/bin/env python3
"""
Update the doctor display limit on the homepage.

This script modifies the number of doctors displayed on the homepage to show
all available doctors rather than the default limit of 3.
"""
import os
import logging
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a connection to the database."""
    # Get database connection info from environment variables
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def update_doctor_limit():
    """Update the number of doctors displayed on the homepage."""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Get the current doctor count
        cursor.execute("SELECT COUNT(*) FROM doctors")
        count = cursor.fetchone()[0]
        logger.info(f"Total doctors in database: {count}")
        
        # Find and update the doctor query in routes.py
        # Note: This is a simplified approach and may need adjustment for the actual file
        with open("routes.py", "r") as file:
            content = file.read()
        
        # Look for the pattern where doctors are limited
        if ".limit(18)" in content:
            updated_content = content.replace(".limit(18)", f".limit({count})")
            with open("routes.py", "w") as file:
                file.write(updated_content)
            logger.info(f"Updated doctor limit to {count}")
            return True
        else:
            logger.info("Could not find doctor limit pattern to update")
            return False
        
    except Exception as e:
        logger.error(f"Error updating doctor limit: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function."""
    if update_doctor_limit():
        logger.info("Doctor limit updated successfully")
    else:
        logger.error("Failed to update doctor limit")

if __name__ == "__main__":
    main()