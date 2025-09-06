"""
Seed a small batch of procedures for testing.
"""
import sys
import logging
from datetime import datetime
from app import db
from models import Procedure, Category, BodyPart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_test_procedures():
    """Add a small batch of procedures for testing."""
    # Get existing categories
    face_category = Category.query.filter_by(name='Facial Procedures').first()
    breast_category = Category.query.filter_by(name='Breast Augmentation').first()
    
    if not face_category or not breast_category:
        logger.error("Required categories not found")
        return 0
    
    logger.info(f"Found face category ID: {face_category.id}")
    logger.info(f"Found breast category ID: {breast_category.id}")
    
    # Define test procedures
    procedures = [
        {
            "name": "Rhinoplasty Standard",
            "body_part": "Face",
            "category_id": face_category.id,
            "is_surgical": True,
            "min_cost": 5000,
            "max_cost": 12000,
            "tags": ["Surgical"]
        },
        {
            "name": "Facelift Advanced",
            "body_part": "Face",
            "category_id": face_category.id,
            "is_surgical": True,
            "min_cost": 7000,
            "max_cost": 15000,
            "tags": ["Surgical"]
        },
        {
            "name": "Botox Treatment",
            "body_part": "Face",
            "category_id": face_category.id,
            "is_surgical": False,
            "min_cost": 300,
            "max_cost": 800,
            "tags": ["Non-Surgical"]
        },
        {
            "name": "Lip Fillers",
            "body_part": "Face",
            "category_id": face_category.id,
            "is_surgical": False,
            "min_cost": 500,
            "max_cost": 1200,
            "tags": ["Non-Surgical"]
        },
        {
            "name": "Forehead Lift",
            "body_part": "Face",
            "category_id": face_category.id,
            "is_surgical": True,
            "min_cost": 4000,
            "max_cost": 9000,
            "tags": ["Surgical"]
        },
        {
            "name": "Breast Implants",
            "body_part": "Breast",
            "category_id": breast_category.id,
            "is_surgical": True,
            "min_cost": 6000,
            "max_cost": 12000,
            "tags": ["Surgical"]
        }
    ]
    
    # Add procedures
    added = 0
    for proc in procedures:
        try:
            # Skip if already exists
            existing = Procedure.query.filter_by(procedure_name=proc["name"]).first()
            if existing:
                logger.info(f"Procedure '{proc['name']}' already exists, skipping")
                continue
                
            # Create the procedure with all required fields
            procedure = Procedure(
                procedure_name=proc["name"],
                short_description=f"A {'surgical' if proc['is_surgical'] else 'non-surgical'} procedure for {proc['body_part'].lower()}",
                overview=f"This {'surgical' if proc['is_surgical'] else 'non-surgical'} procedure focuses on enhancing the {proc['body_part'].lower()} with {'significant' if proc['is_surgical'] else 'minimal'} downtime.",
                procedure_details=f"The {proc['name']} procedure involves advanced techniques to address common concerns in the {proc['body_part'].lower()}.",
                ideal_candidates=f"Ideal candidates for {proc['name']} are individuals who wish to improve the appearance of their {proc['body_part'].lower()}.",
                recovery_process=f"Recovery involves {'several weeks' if proc['is_surgical'] else 'minimal downtime'} with follow-up appointments to monitor progress.",
                recovery_time=f"{'7-14 days' if proc['is_surgical'] else '1-3 days'}",
                results_duration=f"{'Long-lasting' if proc['is_surgical'] else '6-12 months'}",
                min_cost=proc["min_cost"],
                max_cost=proc["max_cost"],
                benefits=f"Enhanced appearance, {'Long-lasting results' if proc['is_surgical'] else 'Quick recovery'}, Improved self-confidence",
                risks=f"{'Infection, scarring, anesthesia risks' if proc['is_surgical'] else 'Temporary redness, swelling, bruising'}, Unsatisfactory results",
                procedure_types=f"{proc['name']} Standard, {proc['name']} Advanced",
                category_id=proc["category_id"],
                body_part=proc["body_part"],
                tags=proc["tags"],
                created_at=datetime.utcnow()
            )
            
            # Add to database
            db.session.add(procedure)
            db.session.commit()
            
            added += 1
            logger.info(f"Added procedure: {proc['name']}")
            
        except Exception as e:
            logger.error(f"Error adding procedure '{proc['name']}': {str(e)}")
            db.session.rollback()
    
    logger.info(f"Successfully added {added} procedures")
    return added

if __name__ == "__main__":
    try:
        from main import app
        with app.app_context():
            seed_test_procedures()
    except Exception as e:
        logger.error(f"Error in seed script: {str(e)}")
        sys.exit(1)