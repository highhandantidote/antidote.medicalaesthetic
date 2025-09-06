#!/usr/bin/env python3
"""
Step 2: Add body parts to the database.

This is the second step in a multi-step import process.
"""

import os
import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False
    return conn

def add_body_parts():
    """Add essential body parts to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    body_part_count = 0
    
    try:
        body_parts = [
            ("Face", "Face and facial features"),
            ("Nose", "Nasal structure and appearance"),
            ("Breasts", "Breast size, shape, and appearance"),
            ("Body", "Overall body contouring and shaping"),
            ("Butt", "Buttocks enhancement and shaping"),
            ("Eyes", "Eye and eyelid appearance"),
            ("Lips", "Lip enhancement and shaping"),
            ("Hair", "Hair restoration and removal"),
            ("Skin", "Skin rejuvenation and treatment"),
            ("Stomach", "Abdominal contouring and flattening")
        ]
        
        for name, desc in body_parts:
            cursor.execute("""
                INSERT INTO body_parts (name, description, created_at)
                VALUES (%s, %s, NOW())
                RETURNING id
            """, (name, desc))
            
            body_part_id = cursor.fetchone()[0]
            body_part_count += 1
            logger.info(f"Added body part: {name} (ID: {body_part_id})")
        
        conn.commit()
        logger.info(f"Added {body_part_count} body parts")
        return body_part_count
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding body parts: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to execute Step 2."""
    try:
        logger.info("Step 2: Add body parts to the database")
        
        # Add body parts
        count = add_body_parts()
        
        logger.info(f"Step 2 complete. Added {count} body parts. Run Step 3 to add categories.")
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()