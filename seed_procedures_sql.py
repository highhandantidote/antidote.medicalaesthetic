"""
Add procedures to the database using direct SQL statements for better performance.
"""
import os
import sys
import psycopg2
import logging
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

def get_existing_data(conn):
    """Get existing data from the database to avoid duplicates."""
    logger.info("Retrieving existing data...")
    existing_body_parts = {}
    existing_categories = {}
    existing_procedures = set()
    
    try:
        with conn.cursor() as cur:
            # Get body parts
            cur.execute("SELECT id, name FROM body_parts")
            for row in cur.fetchall():
                existing_body_parts[row[1]] = row[0]
            logger.info(f"Found {len(existing_body_parts)} existing body parts")
            
            # Get categories
            cur.execute("SELECT id, name, body_part_id FROM categories")
            for row in cur.fetchall():
                existing_categories[row[1]] = {"id": row[0], "body_part_id": row[2]}
            logger.info(f"Found {len(existing_categories)} existing categories")
            
            # Get procedure names
            cur.execute("SELECT procedure_name FROM procedures")
            existing_procedures = {row[0] for row in cur.fetchall()}
            logger.info(f"Found {len(existing_procedures)} existing procedures")
            
        return existing_body_parts, existing_categories, existing_procedures
    except Exception as e:
        logger.error(f"Error retrieving existing data: {str(e)}")
        conn.rollback()
        raise

def ensure_body_parts_exist(conn, needed_body_parts, existing_body_parts):
    """Ensure all needed body parts exist in the database."""
    logger.info("Ensuring required body parts exist...")
    body_parts = existing_body_parts.copy()
    
    try:
        with conn.cursor() as cur:
            for name in needed_body_parts:
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

def ensure_categories_exist(conn, procedures, existing_body_parts, existing_categories):
    """Ensure all needed categories exist in the database."""
    logger.info("Ensuring required categories exist...")
    categories = existing_categories.copy()
    
    # Mapping of body parts to categories
    body_part_categories = {
        "Face": "Facial Procedures",
        "Breast": "Breast Augmentation",
        "Body": "Body Contouring"
    }
    
    try:
        with conn.cursor() as cur:
            for body_part, category_name in body_part_categories.items():
                if category_name not in categories and body_part in existing_body_parts:
                    logger.info(f"Adding category: {category_name} for body part: {body_part}")
                    body_part_id = existing_body_parts[body_part]
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

def add_procedures(conn, procedures_data, existing_procedures, existing_categories):
    """Add procedures to the database using SQL."""
    logger.info(f"Adding {len(procedures_data)} procedures...")
    added_procedures = []
    
    try:
        with conn.cursor() as cur:
            for proc in procedures_data:
                if proc["name"] not in existing_procedures:
                    logger.info(f"Adding procedure: {proc['name']}")
                    
                    # Get category ID
                    category_name = "Facial Procedures" if proc["body_part"] == "Face" else \
                                   "Breast Augmentation" if proc["body_part"] == "Breast" else \
                                   "Body Contouring"
                    
                    if category_name in existing_categories:
                        category_id = existing_categories[category_name]["id"]
                        
                        # Insert procedure
                        cur.execute("""
                            INSERT INTO procedures 
                            (procedure_name, short_description, overview, procedure_details, ideal_candidates, 
                            recovery_time, min_cost, max_cost, risks, procedure_types, category_id, body_part, created_at,
                            tags)
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
                            [proc["body_part"]]  # Simple tag array
                        ))
                        
                        proc_id = cur.fetchone()[0]
                        added_procedures.append(proc_id)
                        logger.info(f"Added procedure {proc['name']} with id {proc_id}")
                    else:
                        logger.warning(f"Skipping procedure {proc['name']}: category {category_name} not found")
                else:
                    logger.info(f"Procedure {proc['name']} already exists, skipping")
            
            conn.commit()
        return added_procedures
    except Exception as e:
        logger.error(f"Error adding procedures: {str(e)}")
        conn.rollback()
        raise

def main():
    """Run the procedure addition script."""
    logger.info("Starting minimal procedure seeding using SQL...")
    
    try:
        conn = connect_to_db()
        
        # Get existing data
        existing_body_parts, existing_categories, existing_procedures = get_existing_data(conn)
        
        # Ensure body parts exist
        needed_body_parts = ["Face", "Breast", "Body"]
        body_parts = ensure_body_parts_exist(conn, needed_body_parts, existing_body_parts)
        
        # Ensure categories exist
        categories = ensure_categories_exist(conn, None, body_parts, existing_categories)
        
        # Define minimal procedures (just what we need for the dashboard)
        procedures_to_add = [
            {
                "name": "Rhinoplasty",
                "body_part": "Face",
                "min_cost": 5000,
                "max_cost": 10000
            },
            {
                "name": "Facelift",
                "body_part": "Face",
                "min_cost": 7000,
                "max_cost": 12000
            },
            {
                "name": "Botox",
                "body_part": "Face",
                "min_cost": 300,
                "max_cost": 1000
            },
            {
                "name": "Eyelid Surgery",
                "body_part": "Face",
                "min_cost": 4000,
                "max_cost": 8000
            },
            {
                "name": "Breast Augmentation",
                "body_part": "Breast",
                "min_cost": 6000,
                "max_cost": 12000
            }
        ]
        
        # Add procedures
        added_procedures = add_procedures(conn, procedures_to_add, existing_procedures, categories)
        
        logger.info(f"Successfully added {len(added_procedures)} procedures")
        conn.close()
        return 0
    
    except Exception as e:
        logger.error(f"Error in procedure seeding: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())