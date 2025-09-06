"""
Seed procedures to the database, ensuring all required fields are present.
This script adds 117 procedures in total to meet the requirements.
"""
import random
import string
import logging
import sys
import time
from datetime import datetime
from app import db
from models import Procedure, Category, BodyPart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Categories mapped to body parts (based on existing data in the database)
BODY_PART_CATEGORIES = {
    "Face": ["Facial Procedures"],
    "Breast": ["Breast Augmentation"],
    "Body": ["Body Contouring"]
}

def add_procedures_batch(start_index, batch_size, total_count):
    """Add a batch of procedures to the database."""
    from models import Procedure, Category, BodyPart
    
    # Get existing procedure names to avoid duplicates
    existing_names = [p.procedure_name for p in Procedure.query.all()]
    logger.info(f"Found {len(existing_names)} existing procedures")
    
    # Get body parts and categories from database
    body_parts = {bp.name: bp.id for bp in BodyPart.query.all()}
    logger.info(f"Found body parts: {list(body_parts.keys())}")
    
    categories = {cat.name: cat.id for cat in Category.query.all()}
    logger.info(f"Found categories: {list(categories.keys())}")
    
    # Procedure types for each body part
    procedure_types = {
        "Face": [
            "Rhinoplasty", "Facelift", "Botox", "Fillers", "Eyelid Surgery", 
            "Chin Augmentation", "Lip Enhancement", "Cheek Augmentation",
            "Brow Lift", "Facial Implants", "Facial Contouring"
        ],
        "Breast": [
            "Breast Augmentation", "Breast Lift", "Breast Reduction", 
            "Breast Reconstruction", "Breast Implant Revision"
        ],
        "Body": [
            "Liposuction", "Tummy Tuck", "Body Lift", "Arm Lift", "Thigh Lift",
            "Buttock Augmentation", "Body Contouring", "Mommy Makeover"
        ]
    }
    
    # Count procedures to add
    remaining = total_count - len(existing_names)
    to_add = min(batch_size, remaining)
    
    if remaining <= 0:
        logger.info(f"Already have {len(existing_names)} procedures, which meets the target of {total_count}")
        return 0
    
    logger.info(f"Adding batch of {to_add} procedures (starting at index {start_index})")
    
    procedures_added = 0
    
    for i in range(start_index, start_index + to_add):
        try:
            # Select a body part - distribute evenly with more face procedures
            if i % 4 == 0 or i % 4 == 1 or i % 4 == 2:
                body_part = "Face"  # 75% face procedures
            elif i % 4 == 3:
                body_part = random.choice(["Breast", "Body"])  # 25% other procedures
            
            # Get categories for this body part
            category_name = BODY_PART_CATEGORIES[body_part][0]
            category_id = categories[category_name]
            
            # Create a unique procedure name
            base_name = random.choice(procedure_types[body_part])
            procedure_name = f"{base_name} {i+1}"
            
            # Ensure procedure name is unique
            while procedure_name in existing_names:
                suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
                procedure_name = f"{base_name} {suffix}"
            
            # Add to existing names to avoid duplicates in this run
            existing_names.append(procedure_name)
            
            # Determine if surgical
            is_surgical = random.choice([True, False])
            tags = ["Surgical"] if is_surgical else ["Non-Surgical"]
            
            # Generate cost range
            min_cost = random.randint(500, 5000) if not is_surgical else random.randint(3000, 8000)
            max_cost = min_cost + random.randint(500, 5000)
            
            # Create procedure with all required fields
            procedure = Procedure(
                procedure_name=procedure_name,
                short_description=f"A {'surgical' if is_surgical else 'non-surgical'} procedure for {body_part.lower()}",
                overview=f"This {'surgical' if is_surgical else 'non-surgical'} procedure focuses on enhancing the {body_part.lower()} with {'significant' if is_surgical else 'minimal'} downtime.",
                procedure_details=f"The {procedure_name} procedure involves advanced techniques to address common concerns in the {body_part.lower()}.",
                ideal_candidates=f"Ideal candidates for {procedure_name} are individuals who wish to improve the appearance of their {body_part.lower()}.",
                recovery_process=f"Recovery involves {'several weeks' if is_surgical else 'minimal downtime'} with follow-up appointments to monitor progress.",
                recovery_time=f"{random.randint(1, 4) if not is_surgical else random.randint(7, 28)} days",
                results_duration=f"{'Permanent' if is_surgical else f'{random.randint(6, 18)} months'}",
                min_cost=min_cost,
                max_cost=max_cost,
                benefits=f"Enhanced appearance, {'Long-lasting results' if is_surgical else 'Quick recovery'}, Improved self-confidence",
                risks=f"{'Infection, scarring, anesthesia risks' if is_surgical else 'Temporary redness, swelling, bruising'}, Unsatisfactory results",
                procedure_types=f"{procedure_name} Standard, {procedure_name} Advanced",
                category_id=category_id,
                body_part=body_part,
                tags=tags,
                created_at=datetime.utcnow()
            )
            
            # Add to database
            db.session.add(procedure)
            
            # Commit after each procedure to avoid timeout
            db.session.commit()
            
            procedures_added += 1
            logger.info(f"Added procedure {procedures_added}/{to_add}: {procedure_name}")
            
            # Brief pause to avoid overloading the database
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error adding procedure: {str(e)}")
            db.session.rollback()
    
    logger.info(f"Successfully added {procedures_added} procedures to the database")
    return procedures_added

def main():
    """Run the procedure seeding script."""
    logger.info("Starting procedure seeding script...")
    
    total_count = 117  # Total procedures needed
    batch_size = 25   # Process in manageable batches
    
    # Create the application context
    from main import app
    
    total_added = 0
    
    with app.app_context():
        # Get current count
        current_count = Procedure.query.count()
        logger.info(f"Current procedure count: {current_count}")
        
        # Calculate remaining procedures to reach target
        remaining = max(0, total_count - current_count)
        
        if remaining == 0:
            logger.info(f"Already have {current_count} procedures, which meets or exceeds the target of {total_count}")
            return 0
        
        # Process in batches
        for i in range(0, remaining, batch_size):
            count = add_procedures_batch(i, min(batch_size, remaining - i), total_count)
            total_added += count
            
            # Check if we've reached the target
            if Procedure.query.count() >= total_count:
                break
    
    logger.info(f"Added a total of {total_added} procedures to the database")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())