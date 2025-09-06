#!/usr/bin/env python3
"""
Step 3: Add categories to the database.

This is the third step in a multi-step import process.
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

def add_categories():
    """Add essential categories to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    category_count = 0
    
    try:
        # Get body part IDs first
        cursor.execute("SELECT id, name FROM body_parts")
        body_part_ids = {row[1]: row[0] for row in cursor.fetchall()}
        
        if not body_part_ids:
            logger.error("No body parts found. Run Step 2 first.")
            return 0
        
        categories = [
            ("Face", "Face_And_Neck_Lifts", "Procedures to lift and rejuvenate the face and neck"),
            ("Face", "Fillers_And_Injectables", "Non-surgical enhancement using injectables"),
            ("Nose", "Rhinoplasty", "Procedures to reshape the nose"),
            ("Breasts", "Breast_Surgery", "Surgical procedures for breast enhancement"),
            ("Body", "Body_Contouring", "Procedures to reshape and contour the body"),
            ("Eyes", "Eyelid_Surgery", "Procedures to rejuvenate the eye area"),
            ("Lips", "Lip_Enhancement", "Procedures to enhance lip appearance"),
            ("Stomach", "Abdominoplasty", "Procedures to flatten and contour the abdomen"),
            ("Hair", "Hair_Restoration", "Procedures to restore hair growth"),
            ("Butt", "Butt_Enhancement", "Procedures to enhance the buttocks")
        ]
        
        for body_part, name, desc in categories:
            body_part_id = body_part_ids.get(body_part)
            if not body_part_id:
                logger.warning(f"Body part '{body_part}' not found")
                continue
            
            cursor.execute("""
                INSERT INTO categories (name, body_part_id, description, popularity_score, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id
            """, (name, body_part_id, desc, 5))
            
            category_id = cursor.fetchone()[0]
            category_count += 1
            logger.info(f"Added category: {name} under {body_part} (ID: {category_id})")
        
        conn.commit()
        logger.info(f"Added {category_count} categories")
        return category_count
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding categories: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to execute Step 3."""
    try:
        logger.info("Step 3: Add categories to the database")
        
        # Add categories
        count = add_categories()
        
        logger.info(f"Step 3 complete. Added {count} categories. Run Step 4 to add procedures.")
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()