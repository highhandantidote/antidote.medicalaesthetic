#!/usr/bin/env python3
"""
Add ratings to doctors in the database.
"""
import os
import sys
import logging
import random
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a connection to the database."""
    import psycopg2
    
    # Get database connection info from environment variables
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        sys.exit(1)

def add_doctor_ratings():
    """Add ratings to doctors in the database."""
    conn = get_db_connection()
    conn.autocommit = False
    cursor = conn.cursor()
    
    try:
        # Get all doctors without ratings
        cursor.execute("SELECT id, name FROM doctors WHERE rating IS NULL")
        doctors = cursor.fetchall()
        
        if not doctors:
            logger.warning("No doctors found without ratings")
            return
        
        print(f"Found {len(doctors)} doctors without ratings")
        
        # Add ratings to each doctor
        for doctor_id, name in doctors:
            # Generate a random rating between 3.5 and 5.0
            rating = round(random.uniform(3.5, 5.0), 1)
            
            # Update the doctor's rating
            cursor.execute(
                "UPDATE doctors SET rating = %s WHERE id = %s",
                (rating, doctor_id)
            )
            
            print(f"Added rating {rating} to {name} (ID: {doctor_id})")
        
        # Commit changes
        conn.commit()
        print(f"Successfully added ratings to {len(doctors)} doctors")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding doctor ratings: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_doctor_ratings()