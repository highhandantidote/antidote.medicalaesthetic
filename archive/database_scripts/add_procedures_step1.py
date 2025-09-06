#!/usr/bin/env python3
"""
Step 1: Reset database and add essential body parts and categories.

This is the first step in a multi-step import process.
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

def reset_database():
    """Reset the database by removing all existing entries."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if there are any dependencies on procedures
        cursor.execute("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE column_name = 'procedure_id'
            AND table_schema = 'public';
        """)
        dependencies = cursor.fetchall()
        
        # Delete from dependent tables first to avoid FK constraint errors
        for table, column in dependencies:
            logger.info(f"Clearing dependent table: {table}")
            cursor.execute(f"DELETE FROM {table}")
        
        # Delete all procedures
        logger.info("Deleting all procedures...")
        cursor.execute("DELETE FROM procedures")
        
        # Delete all categories
        logger.info("Deleting all categories...")
        cursor.execute("DELETE FROM categories")
        
        # Delete all body parts
        logger.info("Deleting all body parts...")
        cursor.execute("DELETE FROM body_parts")
        
        # Reset sequences
        cursor.execute("ALTER SEQUENCE procedures_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE categories_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE body_parts_id_seq RESTART WITH 1")
        
        conn.commit()
        logger.info("Database reset successful")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error resetting database: {e}")
    finally:
        cursor.close()
        conn.close()

def add_body_parts():
    """Add essential body parts to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    body_part_ids = {}
    
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
            body_part_ids[name] = body_part_id
            logger.info(f"Added body part: {name} (ID: {body_part_id})")
        
        conn.commit()
        logger.info(f"Added {len(body_part_ids)} body parts")
        return body_part_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding body parts: {e}")
    finally:
        cursor.close()
        conn.close()

def add_categories():
    """Add essential categories to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    category_ids = {}
    
    try:
        # Get body part IDs first
        cursor.execute("SELECT id, name FROM body_parts")
        body_part_ids = {row[1]: row[0] for row in cursor.fetchall()}
        
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
            category_ids[(body_part, name)] = category_id
            logger.info(f"Added category: {name} under {body_part} (ID: {category_id})")
        
        conn.commit()
        logger.info(f"Added {len(category_ids)} categories")
        
        # Save category IDs to file for next step
        with open('category_ids.txt', 'w') as f:
            for (body_part, name), cat_id in category_ids.items():
                f.write(f"{body_part}|{name}|{cat_id}\n")
        
        logger.info("Saved category IDs to file for next step")
        
        return category_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding categories: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to execute Step 1."""
    try:
        logger.info("Step 1: Reset database and add body parts and categories")
        
        # Reset database
        reset_database()
        
        # Add body parts
        add_body_parts()
        
        # Add categories
        add_categories()
        
        logger.info("Step 1 complete. Run Step 2 to add procedures.")
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()