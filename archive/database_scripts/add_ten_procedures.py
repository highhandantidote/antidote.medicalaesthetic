#!/usr/bin/env python3
"""
Add procedures to the database using the RealSelf hierarchy schema.
Adds procedures in small batches to avoid timeouts, with a target of 100+ total procedures.
"""
import logging
import sys
from datetime import datetime
from app import create_app, db
from add_procedures_small import BODY_PARTS, PROCEDURE_NAMES, TAGS, generate_cost_range

# Configure logging
LOG_FILE = f"add_ten_procedures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Base procedures matching RealSelf hierarchy (required for initial setup)
BASE_PROCEDURES = [
    # Surgical procedures for Face
    {
        "name": "Open Rhinoplasty",
        "body_part": "Face",
        "category": "Rhinoplasty",
        "tags": ["Surgical", "Cosmetic"],
        "is_surgical": True,
        "min_cost": 7000,
        "max_cost": 12000
    },
    {
        "name": "Full Facelift",
        "body_part": "Face",
        "category": "Facelift",
        "tags": ["Surgical", "Cosmetic"],
        "is_surgical": True,
        "min_cost": 10000,
        "max_cost": 15000
    },
    {
        "name": "Upper Eyelid Surgery",
        "body_part": "Face",
        "category": "Eyelid Surgery",
        "tags": ["Surgical", "Cosmetic"],
        "is_surgical": True,
        "min_cost": 3000,
        "max_cost": 5000
    },
    # Non-surgical procedures for Face
    {
        "name": "Botox Injections",
        "body_part": "Face",
        "category": "Injectables",
        "tags": ["Non-Surgical", "Injectable"],
        "is_surgical": False,
        "min_cost": 300,
        "max_cost": 800
    },
    {
        "name": "Lip Filler Injections",
        "body_part": "Face",
        "category": "Injectables",
        "tags": ["Non-Surgical", "Injectable"],
        "is_surgical": False,
        "min_cost": 500,
        "max_cost": 1200
    },
    {
        "name": "Chemical Peel",
        "body_part": "Face",
        "category": "Skin Treatments",
        "tags": ["Non-Surgical", "Cosmetic"],
        "is_surgical": False,
        "min_cost": 200,
        "max_cost": 800
    }
]

# Additional procedures by body part 
ADDITIONAL_PROCEDURES = {
    "Face": [
        # More facial procedures
        {
            "name": "Non-Surgical Nose Job",
            "category": "Rhinoplasty",
            "tags": ["Non-Surgical", "Injectable"],
            "is_surgical": False,
            "min_cost": 800,
            "max_cost": 1500
        },
        {
            "name": "Mini Facelift",
            "category": "Facelift",
            "tags": ["Surgical", "Minimally Invasive"],
            "is_surgical": True,
            "min_cost": 5000,
            "max_cost": 9000
        },
        {
            "name": "Lower Eyelid Surgery",
            "category": "Eyelid Surgery",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 3500,
            "max_cost": 6000
        },
        {
            "name": "Cheek Fillers",
            "category": "Injectables",
            "tags": ["Non-Surgical", "Injectable"],
            "is_surgical": False,
            "min_cost": 700,
            "max_cost": 1500
        },
        {
            "name": "Chin Augmentation",
            "category": "Facial Implants",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 3000,
            "max_cost": 7000
        },
        {
            "name": "Laser Skin Resurfacing",
            "category": "Skin Treatments",
            "tags": ["Non-Surgical", "Laser"],
            "is_surgical": False,
            "min_cost": 1000,
            "max_cost": 3000
        }
    ],
    "Breast": [
        # Breast procedures
        {
            "name": "Breast Augmentation with Silicone Implants",
            "category": "Breast Augmentation",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 6000,
            "max_cost": 10000
        },
        {
            "name": "Breast Augmentation with Saline Implants",
            "category": "Breast Augmentation",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 5500,
            "max_cost": 9000
        },
        {
            "name": "Breast Lift",
            "category": "Breast Lift",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 7000,
            "max_cost": 11000
        },
        {
            "name": "Breast Reduction",
            "category": "Breast Reduction",
            "tags": ["Surgical", "Cosmetic", "Medical"],
            "is_surgical": True,
            "min_cost": 8000,
            "max_cost": 12000
        },
        {
            "name": "Breast Reconstruction",
            "category": "Breast Reconstruction",
            "tags": ["Surgical", "Medical"],
            "is_surgical": True,
            "min_cost": 15000,
            "max_cost": 25000
        }
    ],
    "Body": [
        # Body procedures
        {
            "name": "Tummy Tuck",
            "category": "Tummy Tuck",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 8000,
            "max_cost": 12000
        },
        {
            "name": "Liposuction",
            "category": "Liposuction",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 3500,
            "max_cost": 8000
        },
        {
            "name": "Body Lift",
            "category": "Body Lift",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 12000,
            "max_cost": 18000
        },
        {
            "name": "Arm Lift",
            "category": "Arm Lift",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 4000,
            "max_cost": 8000
        },
        {
            "name": "Thigh Lift",
            "category": "Thigh Lift",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 5000,
            "max_cost": 9000
        },
        {
            "name": "Brazilian Butt Lift",
            "category": "Buttock Enhancement",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 9000,
            "max_cost": 15000
        },
        {
            "name": "Mommy Makeover",
            "category": "Mommy Makeover",
            "tags": ["Surgical", "Cosmetic", "Combined Procedures"],
            "is_surgical": True,
            "min_cost": 15000,
            "max_cost": 25000
        },
        {
            "name": "CoolSculpting",
            "category": "Fat Reduction",
            "tags": ["Non-Surgical", "Cosmetic"],
            "is_surgical": False,
            "min_cost": 1500,
            "max_cost": 4000
        }
    ],
    "Skin": [
        # Skin procedures
        {
            "name": "Microdermabrasion",
            "category": "Skin Treatments",
            "tags": ["Non-Surgical", "Cosmetic"],
            "is_surgical": False,
            "min_cost": 150,
            "max_cost": 400
        },
        {
            "name": "Laser Hair Removal",
            "category": "Laser Treatments",
            "tags": ["Non-Surgical", "Cosmetic"],
            "is_surgical": False,
            "min_cost": 300,
            "max_cost": 1500
        },
        {
            "name": "PRP Hair Treatment",
            "category": "Hair Restoration",
            "tags": ["Non-Surgical", "Minimally Invasive"],
            "is_surgical": False,
            "min_cost": 800,
            "max_cost": 2000
        },
        {
            "name": "Dermabrasion",
            "category": "Skin Treatments",
            "tags": ["Non-Surgical", "Cosmetic"],
            "is_surgical": False,
            "min_cost": 400,
            "max_cost": 1200
        },
        {
            "name": "Microneedling",
            "category": "Skin Treatments",
            "tags": ["Non-Surgical", "Cosmetic"],
            "is_surgical": False,
            "min_cost": 300,
            "max_cost": 700
        },
        {
            "name": "Hair Transplant",
            "category": "Hair Restoration",
            "tags": ["Surgical", "Cosmetic"],
            "is_surgical": True,
            "min_cost": 5000,
            "max_cost": 15000
        }
    ]
}

# Batch size for adding procedures to avoid timeouts
BATCH_SIZE = 3  # Reduced to 3 to prevent timeouts

def add_procedures(batch_size=BATCH_SIZE, max_procedures=97):
    """
    Add procedures to the database in smaller batches to avoid timeouts.
    
    Args:
        batch_size: Number of procedures to add in a single batch (default: 3)
        max_procedures: Maximum number of procedures to add in total (default: 97, to reach 117 total procedures)
    
    Returns:
        Number of procedures added
    """
    from models import Procedure, Category
    
    logger.info(f"Adding procedures to the database in batches of {batch_size}...")
    
    # Get existing procedure names to avoid duplicates
    existing_names = [p.procedure_name for p in Procedure.query.all()]
    logger.info(f"Found {len(existing_names)} existing procedures")
    
    # Get categories from database
    categories = {cat.name: cat.id for cat in Category.query.all()}
    logger.info(f"Found {len(categories)} categories in database")
    
    # Combine all procedures for easy processing
    all_procedures = []
    
    # First add base procedures (required for initial setup)
    all_procedures.extend(BASE_PROCEDURES)
    
    # Then add all additional procedures by body part
    for body_part, procedures in ADDITIONAL_PROCEDURES.items():
        for proc in procedures:
            # Add the body part to each procedure data
            proc["body_part"] = body_part
            all_procedures.append(proc)
    
    logger.info(f"Total procedure data available: {len(all_procedures)}")
    
    # First ensure we have all necessary body parts
    from models import BodyPart
    body_parts = {bp.name: bp.id for bp in BodyPart.query.all()}
    needed_body_parts = set(proc["body_part"] for proc in all_procedures)
    
    for body_part_name in needed_body_parts:
        if body_part_name not in body_parts:
            try:
                body_part = BodyPart(
                    name=body_part_name,
                    description=f"{body_part_name} procedures and treatments"
                )
                db.session.add(body_part)
                db.session.commit()
                body_parts[body_part_name] = body_part.id
                logger.info(f"Created '{body_part_name}' body part")
            except Exception as e:
                logger.error(f"Error creating body part {body_part_name}: {str(e)}")
                db.session.rollback()
    
    # Create all necessary categories with proper body_part_id
    all_categories = set(proc["category"] for proc in all_procedures)
    logger.info(f"Need to ensure {len(all_categories)} categories exist")
    
    # Group procedures by category to determine which body part each category belongs to
    category_to_body_part = {}
    for proc in all_procedures:
        category_name = proc["category"]
        body_part_name = proc["body_part"]
        category_to_body_part[category_name] = body_part_name
    
    for category_name in all_categories:
        if category_name not in categories:
            try:
                body_part_name = category_to_body_part.get(category_name)
                if body_part_name not in body_parts:
                    logger.error(f"Body part '{body_part_name}' not found for category '{category_name}'")
                    continue
                
                body_part_id = body_parts[body_part_name]
                default_category = Category(
                    name=category_name, 
                    description=f"{category_name} procedures",
                    body_part_id=body_part_id
                )
                db.session.add(default_category)
                db.session.commit()
                categories[category_name] = default_category.id
                logger.info(f"Created '{category_name}' category under '{body_part_name}'")
            except Exception as e:
                logger.error(f"Error creating category {category_name}: {str(e)}")
                db.session.rollback()
    
    # Process procedures in batches
    total_added = 0
    batch_num = 1
    
    for i in range(0, len(all_procedures), batch_size):
        batch = all_procedures[i:i+batch_size]
        logger.info(f"Processing batch {batch_num} with {len(batch)} procedures...")
        
        batch_added = 0
        
        for proc_data in batch:
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
                category_id = categories.get(category_name, categories.get("General", 1))
                
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
                batch_added += 1
                total_added += 1
                existing_names.append(name)  # Update to prevent duplicates
                
                # Log progress
                logger.info(f"Added procedure {total_added}/{len(all_procedures)}: {name}")
                
                # Stop if we've hit the maximum
                if total_added >= max_procedures:
                    logger.info(f"Reached maximum procedure count ({max_procedures})")
                    break
                
            except Exception as e:
                logger.error(f"Error adding procedure: {str(e)}")
                db.session.rollback()
        
        # Commit the batch
        try:
            db.session.commit()
            logger.info(f"Committed batch {batch_num}: added {batch_added} procedures")
        except Exception as e:
            logger.error(f"Error committing batch {batch_num}: {str(e)}")
            db.session.rollback()
        
        batch_num += 1
        
        # Stop if we've hit the maximum
        if total_added >= max_procedures:
            break
    
    logger.info(f"Successfully added {total_added} new procedures to the database")
    return total_added

def main():
    """Run the procedure addition script."""
    logger.info("Starting procedure addition script...")
    
    # Create the application context
    app = create_app()
    
    # Using a very small batch size to avoid timeouts
    batch_size = 2
    # Start with just 10 procedures at a time to avoid timeouts
    # We can run this script multiple times to add more
    target_procedures = 10
    
    with app.app_context():
        try:
            # Check current procedure count
            from models import Procedure
            current_count = Procedure.query.count()
            logger.info(f"Current procedure count: {current_count}")
            
            # Calculate how many more procedures are needed to reach 117
            remaining = max(0, 117 - current_count)
            target_procedures = min(target_procedures, remaining)
            
            if target_procedures <= 0:
                logger.info(f"Already have {current_count} procedures. No need to add more.")
                return 0
                
            logger.info(f"Will add {target_procedures} more procedures to reach total of {current_count + target_procedures}")
            count = add_procedures(batch_size=batch_size, max_procedures=target_procedures)
            
            # Check final count
            final_count = Procedure.query.count()
            logger.info(f"Final procedure count: {final_count}")
            
        except Exception as e:
            logger.error(f"Error in main procedure: {str(e)}")
            return 1
    
    logger.info(f"Added {count} procedures to the database")
    logger.info(f"Log saved to: {LOG_FILE}")
    
    return 0 if count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())