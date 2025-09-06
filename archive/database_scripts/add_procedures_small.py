#!/usr/bin/env python3
"""
Add procedures to the database using the new RealSelf hierarchy schema.
This script generates 84 additional procedures with realistic data 
to demonstrate the scalability of the recommendation system.
"""
import random
import string
import logging
import sys
import time
from datetime import datetime
from app import create_app, db

# Configure logging
LOG_FILE = f"add_procedures_small_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Lists for generating realistic procedure data
BODY_PARTS = [
    "Face", "Nose", "Eyes", "Lips", "Forehead", "Cheeks", "Chin", "Neck", 
    "Breast", "Body", "Abdomen", "Arms", "Hands", "Back", "Buttocks", 
    "Thighs", "Legs", "Skin"
]

# Treatment categories
CATEGORIES = [
    "Rhinoplasty",
    "Facelift",
    "Eyelid Surgery",
    "Injectables",
    "Breast Augmentation",
    "Breast Reduction",
    "Liposuction",
    "Tummy Tuck",
    "Body Contouring",
    "Skin Treatments",
    "Laser Treatments",
    "Hair Restoration"
]

# Tags for procedure types
TAGS = [
    "Surgical",
    "Non-Surgical",
    "Minimally Invasive",
    "Injectable",
    "Reconstructive",
    "Cosmetic"
]

# Procedure names for various categories
PROCEDURE_NAMES = {
    "Rhinoplasty": [
        "Open Rhinoplasty", "Closed Rhinoplasty", "Revision Rhinoplasty", 
        "Ethnic Rhinoplasty", "Septoplasty", "Tip Plasty", "Non-Surgical Rhinoplasty"
    ],
    "Facelift": [
        "Full Facelift", "Mini Facelift", "Deep Plane Facelift", "SMAS Facelift",
        "Thread Lift", "Liquid Facelift", "Neck Lift", "Mid-Face Lift"
    ],
    "Eyelid Surgery": [
        "Upper Eyelid Surgery", "Lower Eyelid Surgery", "Double Eyelid Surgery",
        "Asian Blepharoplasty", "Transconjunctival Blepharoplasty", "Canthopexy"
    ],
    "Injectables": [
        "Botox Injections", "Lip Filler Injections", "Cheek Fillers", "Jawline Fillers",
        "Under-Eye Fillers", "Marionette Line Fillers", "Hyaluronic Acid Fillers"
    ],
    "Breast Augmentation": [
        "Silicone Implants", "Saline Implants", "Fat Transfer Breast Augmentation",
        "Breast Lift with Implants", "Gummy Bear Implants", "Transaxillary Augmentation"
    ],
    "Breast Reduction": [
        "Vertical Breast Reduction", "Inverted-T Breast Reduction", "Liposuction Breast Reduction",
        "Male Breast Reduction", "Scarless Breast Reduction"
    ],
    "Liposuction": [
        "Tumescent Liposuction", "Ultrasound-Assisted Liposuction", "Laser Liposuction",
        "Power-Assisted Liposuction", "SmartLipo", "VASER Liposuction", "360 Liposuction"
    ],
    "Tummy Tuck": [
        "Full Abdominoplasty", "Mini Tummy Tuck", "Extended Tummy Tuck",
        "Circumferential Abdominoplasty", "Fleur-de-Lis Abdominoplasty"
    ],
    "Body Contouring": [
        "Arm Lift", "Thigh Lift", "Buttock Lift", "Mommy Makeover",
        "CoolSculpting", "Body Lift", "Post-Bariatric Body Contouring"
    ],
    "Skin Treatments": [
        "Chemical Peel", "Microdermabrasion", "HydraFacial", "Dermabrasion",
        "Microneedling", "PRP Facial", "LED Light Therapy"
    ],
    "Laser Treatments": [
        "Laser Hair Removal", "Laser Skin Resurfacing", "Fraxel Laser", "IPL Treatment",
        "CO2 Laser Resurfacing", "Laser Tattoo Removal", "Vascular Laser Treatment"
    ],
    "Hair Restoration": [
        "FUE Hair Transplant", "FUT Hair Transplant", "PRP Hair Treatment",
        "Scalp Micropigmentation", "Hair Mesotherapy", "Laser Hair Therapy"
    ]
}

# Relationships between body parts and categories
BODY_PART_CATEGORIES = {
    "Face": ["Facelift", "Injectables", "Skin Treatments"],
    "Nose": ["Rhinoplasty"],
    "Eyes": ["Eyelid Surgery"],
    "Lips": ["Injectables"],
    "Forehead": ["Facelift", "Injectables"],
    "Cheeks": ["Facelift", "Injectables"],
    "Chin": ["Injectables"],
    "Neck": ["Facelift"],
    "Breast": ["Breast Augmentation", "Breast Reduction"],
    "Body": ["Body Contouring", "Liposuction"],
    "Abdomen": ["Tummy Tuck", "Liposuction"],
    "Arms": ["Body Contouring", "Liposuction"],
    "Hands": ["Skin Treatments"],
    "Back": ["Liposuction"],
    "Buttocks": ["Body Contouring", "Liposuction"],
    "Thighs": ["Body Contouring", "Liposuction"],
    "Legs": ["Body Contouring", "Liposuction"],
    "Skin": ["Skin Treatments", "Laser Treatments"]
}

# Relationships between categories and tags
CATEGORY_TAGS = {
    "Rhinoplasty": ["Surgical", "Reconstructive", "Cosmetic"],
    "Facelift": ["Surgical", "Cosmetic", "Minimally Invasive"],
    "Eyelid Surgery": ["Surgical", "Cosmetic"],
    "Injectables": ["Non-Surgical", "Injectable", "Cosmetic"],
    "Breast Augmentation": ["Surgical", "Cosmetic"],
    "Breast Reduction": ["Surgical", "Reconstructive"],
    "Liposuction": ["Surgical", "Cosmetic"],
    "Tummy Tuck": ["Surgical", "Cosmetic"],
    "Body Contouring": ["Surgical", "Non-Surgical", "Cosmetic"],
    "Skin Treatments": ["Non-Surgical", "Cosmetic"],
    "Laser Treatments": ["Non-Surgical", "Minimally Invasive"],
    "Hair Restoration": ["Surgical", "Non-Surgical", "Minimally Invasive"]
}

def generate_cost_range(category):
    """Generate a realistic cost range based on procedure category."""
    # Cost ranges by category
    cost_ranges = {
        "Rhinoplasty": (5000, 15000),
        "Facelift": (7000, 20000),
        "Eyelid Surgery": (2000, 7000),
        "Injectables": (300, 2000),
        "Breast Augmentation": (5000, 12000),
        "Breast Reduction": (6000, 15000),
        "Liposuction": (2500, 10000),
        "Tummy Tuck": (6000, 15000),
        "Body Contouring": (3000, 20000),
        "Skin Treatments": (200, 1500),
        "Laser Treatments": (300, 3000),
        "Hair Restoration": (4000, 15000)
    }
    
    base_range = cost_ranges.get(category, (1000, 5000))
    min_cost = random.randint(base_range[0], base_range[0] + (base_range[1] - base_range[0])//2)
    max_cost = min_cost + random.randint(500, (base_range[1] - min_cost))
    
    return min_cost, max_cost

def add_procedures(count=84):
    """Add specified number of procedures to the database."""
    from models import Procedure, Category
    
    logger.info(f"Adding {count} new procedures to the database...")
    
    # Get existing procedure names to avoid duplicates
    existing_names = [p.procedure_name for p in Procedure.query.all()]
    logger.info(f"Found {len(existing_names)} existing procedures")
    
    # Get categories from database
    categories = {cat.name: cat.id for cat in Category.query.all()}
    logger.info(f"Found {len(categories)} categories in database")
    
    # If no categories exist, create a default one
    if not categories:
        default_category = Category(name="General", description="General procedures", body_part_id=1)
        db.session.add(default_category)
        db.session.commit()
        categories["General"] = default_category.id
        logger.info("Created default 'General' category")
    
    procedures_added = 0
    
    # First, migrate existing procedures to the new schema
    # For demonstration, we'll update at least 16 procedures to match the requested format
    existing_procedures = Procedure.query.all()
    updated_count = 0
    
    # Specific mappings for the first 5 standard procedures in the requirements
    standard_procedures = [
        {
            "name": "Open Rhinoplasty",
            "body_part": "Face",
            "category": "Rhinoplasty", 
            "tags": ["Surgical"]
        },
        {
            "name": "Full Facelift",
            "body_part": "Face",
            "category": "Facelift", 
            "tags": ["Surgical"]
        },
        {
            "name": "Upper Eyelid Surgery", 
            "body_part": "Eyes",
            "category": "Eyelid Surgery", 
            "tags": ["Surgical"]
        },
        {
            "name": "Botox Injections", 
            "body_part": "Face",
            "category": "Injectables", 
            "tags": ["Non-Surgical"]
        },
        {
            "name": "Lip Filler Injections", 
            "body_part": "Lips",
            "category": "Injectables", 
            "tags": ["Non-Surgical"]
        }
    ]
    
    for proc in existing_procedures:
        try:
            # Check if this is one of our standard procedures for migration
            matching_std = next((std for std in standard_procedures if std["name"] == proc.procedure_name), None)
            
            if matching_std:
                # Update with specific values for standard procedures
                proc.body_part = matching_std["body_part"]
                proc.tags = matching_std["tags"]
                # We're using the existing category relationship, just logging for reference
                logger.info(f"Standard procedure matched: {proc.procedure_name} → {matching_std['category']}")
            else:
                # For other procedures, migrate data using existing fields
                proc.body_part = proc.body_area if proc.body_area else random.choice(BODY_PARTS)
                proc.tags = [proc.category_type] if proc.category_type else [random.choice(TAGS)]
            
            db.session.add(proc)
            db.session.commit()
            updated_count += 1
            logger.info(f"Updated existing procedure {updated_count}: {proc.procedure_name}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating procedure {proc.procedure_name}: {str(e)}")
    
    logger.info(f"Updated {updated_count} existing procedures to new schema")
    
    # Add new procedures one at a time with commits to avoid transaction timeout
    for i in range(count):
        try:
            # Select a random body part
            body_part = random.choice(BODY_PARTS)
            
            # Select a category that goes with this body part
            possible_categories = BODY_PART_CATEGORIES.get(body_part, list(CATEGORIES))
            category_name = random.choice(possible_categories)
            
            # Select a procedure name for this category
            possible_names = PROCEDURE_NAMES.get(category_name, [f"New {category_name} Procedure"])
            # Filter out names that already exist
            available_names = [name for name in possible_names if name not in existing_names]
            
            if not available_names:
                # Create a unique name if all standard ones are taken
                unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                procedure_name = f"{category_name} Procedure {unique_id}"
            else:
                procedure_name = random.choice(available_names)
            
            # Add to existing names to avoid duplicates in this run
            existing_names.append(procedure_name)
            
            # Select tags for this category
            possible_tags = CATEGORY_TAGS.get(category_name, TAGS)
            # Get 1-2 random tags
            tags = random.sample(possible_tags, k=min(2, len(possible_tags)))
            
            # Generate cost range based on category
            min_cost, max_cost = generate_cost_range(category_name)
            
            # Create short description
            is_surgical = "Surgical" in tags
            procedure_type = "surgical" if is_surgical else "non-surgical"
            short_desc = f"A {procedure_type} procedure for the {body_part.lower()} area"
            
            # Generate sample benefits and risks
            if is_surgical:
                benefits = "Long-lasting results, Significant improvement, Customized to your needs"
                risks = "Temporary swelling and bruising, Recovery time needed, Surgical risks apply"
            else:
                benefits = "Minimal downtime, Quick results, Natural-looking improvement"
                risks = "Temporary redness, Results may not be permanent, Multiple sessions may be needed"
            
            # Get category ID
            category_id = categories.get(category_name, categories.get("General", 1))
            
            # Create the procedure
            procedure = Procedure(
                procedure_name=procedure_name,
                short_description=short_desc,
                overview=f"This {procedure_type} procedure for {body_part.lower()} focuses on enhancing appearance with {'' if is_surgical else 'minimal '}downtime and excellent results.",
                procedure_details=f"The {procedure_name} procedure involves advanced techniques to address common concerns in the {body_part.lower()}.",
                ideal_candidates=f"Ideal candidates for {procedure_name} are individuals who wish to improve the appearance of their {body_part.lower()}.",
                recovery_process="Follow your doctor's post-procedure instructions carefully for optimal results and recovery." if is_surgical else "Minimal recovery time is needed for this procedure.",
                body_part=body_part,
                tags=tags,
                min_cost=min_cost,
                max_cost=max_cost,
                benefits=benefits,
                risks=risks,
                recovery_time=f"{random.randint(1 if not is_surgical else 5, 30 if is_surgical else 7)} days",
                results_duration="Long-lasting" if is_surgical else f"{random.randint(3, 12)} months",
                procedure_types=f"{procedure_name} Standard, {procedure_name} Advanced",
                category_id=category_id
            )
            
            # Add and commit immediately
            db.session.add(procedure)
            db.session.commit()
            
            procedures_added += 1
            logger.info(f"Added new procedure {procedures_added}/{count}: {procedure_name}")
            
            # Sleep briefly to avoid overwhelming the database
            time.sleep(0.2)
            
        except Exception as e:
            logger.error(f"Error adding procedure: {str(e)}")
            db.session.rollback()
    
    logger.info(f"Successfully added {procedures_added} new procedures to the database")
    return procedures_added

def main():
    """Run the procedure addition script."""
    logger.info("Starting procedure addition script...")
    
    # Create the application context
    app = create_app()
    
    with app.app_context():
        # Add 84 new procedures to reach a total of 100 new (116 total with existing 16)
        count = add_procedures(84)
        
    logger.info(f"Added {count} procedures to the database")
    logger.info(f"Log saved to: {LOG_FILE}")
    
    return 0 if count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())