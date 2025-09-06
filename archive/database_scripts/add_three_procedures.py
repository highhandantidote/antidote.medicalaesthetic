#!/usr/bin/env python3
"""
Add exactly three procedures to the database using the RealSelf hierarchy schema.
Designed to avoid timeouts by adding minimal data in each run.
"""
import logging
import sys
from datetime import datetime
from app import create_app, db

# Configure logging
LOG_FILE = f"add_three_procedures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Just three procedures to add in this batch
PROCEDURES_TO_ADD = [
    # New category for Face
    {
        "name": "Buccal Fat Removal",
        "body_part": "Face",
        "category": "Facial Contouring",
        "tags": ["Surgical", "Cosmetic"],
        "is_surgical": True,
        "min_cost": 3000,
        "max_cost": 7000
    },
    # New category for Breast
    {
        "name": "Breast Lift with Implants",
        "body_part": "Breast",
        "category": "Breast Lift",
        "tags": ["Surgical", "Cosmetic", "Combined"],
        "is_surgical": True,
        "min_cost": 9000,
        "max_cost": 15000
    },
    # New category for Skin
    {
        "name": "Fraxel Laser Treatment",
        "body_part": "Skin",
        "category": "Laser Treatments",
        "tags": ["Non-Surgical", "Rejuvenation"],
        "is_surgical": False,
        "min_cost": 1200,
        "max_cost": 3000
    }
]


def add_procedures():
    """
    Add exactly three procedures to the database.
    
    Returns:
        Number of procedures added
    """
    from models import Procedure, Category, BodyPart
    
    logger.info(f"Adding 3 procedures to the database...")
    
    # Get existing procedure names to avoid duplicates
    existing_names = [p.procedure_name for p in Procedure.query.all()]
    logger.info(f"Found {len(existing_names)} existing procedures")
    
    # Get body parts from database
    body_parts = {bp.name: bp.id for bp in BodyPart.query.all()}
    logger.info(f"Found {len(body_parts)} body parts in database")
    
    # Get categories from database
    categories = {cat.name: cat.id for cat in Category.query.all()}
    logger.info(f"Found {len(categories)} categories in database")
    
    # First ensure we have all necessary body parts
    needed_body_parts = set(proc["body_part"] for proc in PROCEDURES_TO_ADD)
    
    for body_part_name in needed_body_parts:
        if body_part_name not in body_parts:
            try:
                body_part = BodyPart(
                    name=body_part_name,
                    description=f"{body_part_name} procedures and treatments"
                )
                db.session.add(body_part)
                db.session.flush()  # Flush but don't commit yet
                body_parts[body_part_name] = body_part.id
                logger.info(f"Created '{body_part_name}' body part")
            except Exception as e:
                logger.error(f"Error creating body part {body_part_name}: {str(e)}")
                db.session.rollback()
    
    # Create all necessary categories with proper body_part_id
    category_to_body_part = {proc["category"]: proc["body_part"] for proc in PROCEDURES_TO_ADD}
    
    for category_name, body_part_name in category_to_body_part.items():
        if category_name not in categories:
            try:
                body_part_id = body_parts.get(body_part_name)
                if not body_part_id:
                    logger.error(f"Body part '{body_part_name}' not found for category '{category_name}'")
                    continue
                
                default_category = Category(
                    name=category_name, 
                    description=f"{category_name} procedures",
                    body_part_id=body_part_id
                )
                db.session.add(default_category)
                db.session.flush()  # Flush but don't commit yet
                categories[category_name] = default_category.id
                logger.info(f"Created '{category_name}' category under '{body_part_name}'")
            except Exception as e:
                logger.error(f"Error creating category {category_name}: {str(e)}")
                db.session.rollback()
    
    # Add procedures
    total_added = 0
    
    for proc_data in PROCEDURES_TO_ADD:
        try:
            name = proc_data["name"]
            
            # Skip if already exists
            if name in existing_names:
                logger.info(f"Procedure '{name}' already exists, skipping")
                continue
                
            body_part = proc_data["body_part"]
            category_name = proc_data["category"]
            tags = proc_data["tags"]
            is_surgical = proc_data["is_surgical"]
            min_cost = proc_data["min_cost"]
            max_cost = proc_data["max_cost"]
            
            # Create descriptions based on surgical/non-surgical
            if is_surgical:
                short_desc = f"A surgical procedure for the {body_part.lower()} area"
                benefits = "Long-lasting results, Significant improvement, Customized to your needs"
                risks = "Temporary swelling and bruising, Recovery time needed, Surgical risks apply"
                recovery_time = "10-14 days"
                results_duration = "Long-lasting"
            else:
                short_desc = f"A non-surgical procedure for the {body_part.lower()} area"
                benefits = "Minimal downtime, Quick results, Natural-looking improvement"
                risks = "Temporary redness, Results may not be permanent, Multiple sessions may be needed"
                recovery_time = "1-3 days"
                results_duration = "6-12 months"
            
            # Get category ID
            category_id = categories.get(category_name)
            if not category_id:
                logger.error(f"Category ID for '{category_name}' not found, skipping procedure")
                continue
            
            # Create the procedure
            procedure = Procedure(
                procedure_name=name,
                short_description=short_desc,
                overview=f"This {'surgical' if is_surgical else 'non-surgical'} procedure focuses on enhancing the {body_part.lower()} with {'significant' if is_surgical else 'minimal'} downtime.",
                procedure_details=f"The {name} procedure involves advanced techniques to address common concerns in the {body_part.lower()}.",
                ideal_candidates=f"Ideal candidates for {name} are individuals who wish to improve the appearance of their {body_part.lower()}.",
                recovery_process="Follow your doctor's post-procedure instructions carefully for optimal results." if is_surgical else "Minimal recovery time is needed for this procedure.",
                body_part=body_part,
                tags=tags,
                min_cost=min_cost,
                max_cost=max_cost,
                benefits=benefits,
                risks=risks,
                recovery_time=recovery_time,
                results_duration=results_duration,
                procedure_types=f"{name} Standard, {name} Advanced",
                category_id=category_id
            )
            
            # Add to session
            db.session.add(procedure)
            total_added += 1
            existing_names.append(name)  # Update to prevent duplicates
            
            # Log progress
            logger.info(f"Added procedure: {name}")
            
        except Exception as e:
            logger.error(f"Error adding procedure: {str(e)}")
            db.session.rollback()
    
    # Commit all changes
    try:
        db.session.commit()
        logger.info(f"Committed all changes: added {total_added} procedures")
    except Exception as e:
        logger.error(f"Error committing changes: {str(e)}")
        db.session.rollback()
    
    logger.info(f"Successfully added {total_added} new procedures to the database")
    return total_added

def main():
    """Run the procedure addition script."""
    logger.info("Starting procedure addition script...")
    
    # Create the application context
    app = create_app()
    
    with app.app_context():
        count = add_procedures()
        
    logger.info(f"Added {count} procedures to the database")
    logger.info(f"Log saved to: {LOG_FILE}")
    
    return 0 if count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())