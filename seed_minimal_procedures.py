#!/usr/bin/env python3
"""
Seed just the minimum required 5 procedures for the community analytics dashboard.
This script adds exactly 5 procedures with the specific distribution needed:
- 4 Face procedures (Rhinoplasty, Facelift, Botox, Eyelid Surgery)
- 1 Breast procedure (Breast Augmentation)
"""
import os
import sys
import logging
import psycopg2
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_db():
    """Connect to the PostgreSQL database."""
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = False
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to the database: {str(e)}")
        raise

def ensure_body_parts_exist(conn):
    """Ensure the required body parts exist in the database."""
    logger.info("Ensuring required body parts exist...")
    
    body_parts = {}
    
    try:
        with conn.cursor() as cur:
            # Check existing body parts
            cur.execute("SELECT id, name FROM body_parts")
            for row in cur.fetchall():
                body_parts[row[1]] = row[0]
            
            # Add missing body parts
            for name in ["Face", "Breast"]:
                if name not in body_parts:
                    logger.info(f"Adding body part: {name}")
                    cur.execute(
                        "INSERT INTO body_parts (name, description, created_at) VALUES (%s, %s, %s) RETURNING id",
                        (name, f"The {name.lower()} area", datetime.utcnow())
                    )
                    body_part_id = cur.fetchone()[0]
                    body_parts[name] = body_part_id
                    logger.info(f"Added body part {name} with id {body_part_id}")
        
        conn.commit()
        return body_parts
    except Exception as e:
        logger.error(f"Error ensuring body parts: {str(e)}")
        conn.rollback()
        raise

def ensure_categories_exist(conn, body_parts):
    """Ensure the required categories exist in the database."""
    logger.info("Ensuring required categories exist...")
    
    categories = {}
    
    try:
        with conn.cursor() as cur:
            # Check existing categories
            cur.execute("SELECT id, name, body_part_id FROM categories")
            for row in cur.fetchall():
                categories[row[1]] = {"id": row[0], "body_part_id": row[2]}
            
            # Define needed categories
            needed_categories = {
                "Face": "Facial Procedures",
                "Breast": "Breast Augmentation"
            }
            
            # Add missing categories
            for body_part, category_name in needed_categories.items():
                if category_name not in categories and body_part in body_parts:
                    logger.info(f"Adding category: {category_name} for body part: {body_part}")
                    body_part_id = body_parts[body_part]
                    cur.execute(
                        "INSERT INTO categories (name, body_part_id, description, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
                        (category_name, body_part_id, f"{category_name} for {body_part}", datetime.utcnow())
                    )
                    category_id = cur.fetchone()[0]
                    categories[category_name] = {"id": category_id, "body_part_id": body_part_id}
                    logger.info(f"Added category {category_name} with id {category_id}")
        
        conn.commit()
        return categories
    except Exception as e:
        logger.error(f"Error ensuring categories: {str(e)}")
        conn.rollback()
        raise

def seed_procedures(conn, body_parts, categories):
    """Seed the minimum required procedures for the analytics dashboard."""
    logger.info("Seeding minimal procedures for the community analytics dashboard...")
    
    try:
        # Define the required procedures
        required_procedures = [
            {
                "name": "Rhinoplasty",
                "body_part": "Face",
                "category": "Facial Procedures",
                "min_cost": 5000,
                "max_cost": 10000
            },
            {
                "name": "Facelift",
                "body_part": "Face",
                "category": "Facial Procedures",
                "min_cost": 7000,
                "max_cost": 12000
            },
            {
                "name": "Botox",
                "body_part": "Face",
                "category": "Facial Procedures",
                "min_cost": 300,
                "max_cost": 1000
            },
            {
                "name": "Eyelid Surgery",
                "body_part": "Face", 
                "category": "Facial Procedures",
                "min_cost": 4000,
                "max_cost": 8000
            },
            {
                "name": "Breast Augmentation",
                "body_part": "Breast",
                "category": "Breast Augmentation",
                "min_cost": 6000,
                "max_cost": 12000
            }
        ]
        
        added_count = 0
        existing_procedures = []
        
        with conn.cursor() as cur:
            # Get existing procedures
            cur.execute("SELECT id, procedure_name FROM procedures")
            existing_procedures = [row[1] for row in cur.fetchall()]
            logger.info(f"Found {len(existing_procedures)} existing procedures")
            
            # Add each procedure individually
            for proc in required_procedures:
                if proc["name"] not in existing_procedures:
                    if proc["category"] in categories:
                        category_id = categories[proc["category"]]["id"]
                        
                        # Create simple tags array
                        tags_arr = "{" + f'"{proc["body_part"]}"' + "}"
                        
                        logger.info(f"Adding procedure: {proc['name']}")
                        cur.execute("""
                            INSERT INTO procedures 
                            (procedure_name, short_description, overview, procedure_details, 
                            ideal_candidates, recovery_time, min_cost, max_cost, 
                            risks, procedure_types, category_id, body_part, created_at, tags)
                            VALUES 
                            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            proc["name"],
                            f"A procedure for {proc['body_part'].lower()}",
                            f"This procedure focuses on enhancing the {proc['body_part'].lower()}.",
                            f"The {proc['name']} procedure involves advanced techniques.",
                            f"Ideal candidates for {proc['name']} are individuals who wish to improve their appearance.",
                            "7 days",
                            proc["min_cost"],
                            proc["max_cost"],
                            "Infection, scarring, anesthesia risks",
                            f"{proc['name']} Standard",
                            category_id,
                            proc["body_part"],
                            datetime.utcnow(),
                            tags_arr
                        ))
                        
                        proc_id = cur.fetchone()[0]
                        logger.info(f"Added procedure {proc['name']} with id {proc_id}")
                        
                        # Commit after each procedure to avoid transaction timeouts
                        conn.commit()
                        added_count += 1
                    else:
                        logger.warning(f"Skipping procedure {proc['name']}: category {proc['category']} not found")
                else:
                    logger.info(f"Procedure {proc['name']} already exists, skipping")
        
        logger.info(f"Successfully added {added_count} new procedures")
        
        # Check if we have the minimum 5 procedures
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM procedures")
            total_count = cur.fetchone()[0]
            logger.info(f"Total procedures in database: {total_count}")
            
            if total_count >= 5:
                logger.info("Successfully seeded the minimum required procedures")
            else:
                logger.warning(f"Only have {total_count}/5 required procedures")
        
        return added_count
        
    except Exception as e:
        logger.error(f"Error seeding procedures: {str(e)}")
        conn.rollback()
        raise

def main():
    """Run the minimal procedure seeding script."""
    logger.info("Starting minimal procedure seeding...")
    
    try:
        conn = connect_to_db()
        
        # Ensure required body parts and categories exist
        body_parts = ensure_body_parts_exist(conn)
        categories = ensure_categories_exist(conn, body_parts)
        
        # Seed the procedures
        added_count = seed_procedures(conn, body_parts, categories)
        
        conn.close()
        logger.info(f"Minimal procedure seeding completed successfully, added {added_count} procedures")
        return 0
    
    except Exception as e:
        logger.error(f"Error in minimal procedure seeding: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())