#!/usr/bin/env python3
"""
Add 100 additional procedures to the database.

This script generates 100 additional procedures with realistic data 
to demonstrate the scalability of the recommendation system.
"""
import random
import logging
import sys
from datetime import datetime
from app import create_app, db

# Configure logging
LOG_FILE = f"add_procedures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
BODY_AREAS = [
    "Face", "Nose", "Eyes", "Lips", "Forehead", "Cheeks", "Chin", "Neck", 
    "Chest", "Breast", "Abdomen", "Arms", "Hands", "Back", "Buttocks", 
    "Thighs", "Legs", "Feet", "Skin", "Hair"
]

CATEGORIES = [
    "Surgical", "Non-surgical", "Minimally invasive", "Injectables", 
    "Laser", "Chemical", "Reconstructive", "Cosmetic", "Anti-aging"
]

PROCEDURE_NAMES = [
    # Face procedures
    "Blepharoplasty", "Brow Lift", "Cheek Augmentation", "Chin Augmentation",
    "Ear Surgery", "Ear Pinning", "Facial Fat Transfer", "Facial Implants",
    "Facial Rejuvenation", "Facial Contouring", "Jaw Reduction", "Neck Lift",
    "Rhinoplasty Revision", "Septoplasty", "Thread Lift", "V-Line Surgery",
    
    # Body procedures
    "Abdominoplasty", "Arm Lift", "Body Contouring", "Brazilian Butt Lift",
    "Breast Augmentation", "Breast Implant Removal", "Breast Lift", "Breast Reduction",
    "Fat Transfer", "Gynecomastia Surgery", "Labiaplasty", "Liposuction",
    "Lower Body Lift", "Mommy Makeover", "Thigh Lift", "Tummy Tuck Revision",
    
    # Non-surgical procedures
    "Chemical Peel", "CoolSculpting", "Dermal Fillers", "Dysport",
    "Facial Rejuvenation", "Hair Restoration", "Hydrafacial", "Intense Pulsed Light",
    "Kybella", "Laser Hair Removal", "Laser Resurfacing", "Laser Vein Treatment",
    "Microdermabrasion", "Microneedling", "Permanent Makeup", "PRP Therapy",
    "Radio Frequency Treatment", "Restylane", "Sclerotherapy", "Sculptra",
    "Skin Tightening", "Tattoo Removal", "Thread Lift", "Ultherapy",
    
    # Other specialized procedures
    "Acne Scar Treatment", "Age Spot Removal", "Body Contouring", "Cellulite Treatment",
    "Double Eyelid Surgery", "Ethnic Rhinoplasty", "Fat Freezing", "Hand Rejuvenation",
    "Hyperhidrosis Treatment", "Jawline Contouring", "Lip Enhancement", "Male Breast Reduction",
    "Neck Contouring", "Non-Surgical Nose Job", "Revision Rhinoplasty", "Scar Revision",
    "Skin Rejuvenation", "Stretch Mark Treatment", "Under Eye Treatment", "Vein Treatment"
]

def generate_procedure_name():
    """Generate a unique procedure name by combining existing names or adding modifiers."""
    if PROCEDURE_NAMES:
        base_name = random.choice(PROCEDURE_NAMES)
        PROCEDURE_NAMES.remove(base_name)  # Ensure uniqueness
        
        # Sometimes add a modifier
        modifiers = ["Advanced", "Premium", "Elite", "Modern", "Precision", "Ultra", "Mini"]
        if random.random() < 0.3:  # 30% chance to add a modifier
            return f"{random.choice(modifiers)} {base_name}"
        return base_name
    else:
        # If we run out of names, create a generic one
        return f"Procedure Type {random.randint(1000, 9999)}"

def generate_procedure_description(name, body_area, category):
    """Generate a realistic procedure description based on name, body area and category."""
    
    # Introduction templates
    intros = [
        f"{name} is a popular {category.lower()} procedure focused on the {body_area.lower()}.",
        f"This {category.lower()} procedure for the {body_area.lower()} offers significant results.",
        f"A specialized {category.lower()} procedure targeting the {body_area.lower()} area.",
        f"As one of our most requested {category.lower()} options for the {body_area.lower()}, {name} delivers exceptional results."
    ]
    
    # Benefit templates
    benefits = [
        "Patients typically experience reduced signs of aging and improved confidence.",
        "Results include enhanced contours and a more youthful appearance.",
        "This procedure can help restore a more natural, rejuvenated look.",
        "Many patients report increased satisfaction with their appearance following this treatment.",
        "The procedure is designed to create subtle yet noticeable improvements."
    ]
    
    # Process templates
    process = [
        "The procedure is performed using state-of-the-art techniques and equipment.",
        "Our board-certified specialists use the latest methods to ensure optimal results.",
        "Recovery time varies depending on individual factors and treatment extent.",
        "The process typically involves minimal discomfort and manageable recovery.",
        "We employ advanced techniques to minimize recovery time and maximize results."
    ]
    
    # Combine elements to create a comprehensive description
    description = f"{random.choice(intros)} {random.choice(benefits)} {random.choice(process)}"
    return description

def generate_cost_range(category):
    """Generate a realistic cost range based on procedure category."""
    if category == "Surgical":
        min_cost = random.randint(3000, 15000)
        max_cost = min_cost + random.randint(2000, 10000)
    elif category in ["Minimally invasive", "Reconstructive"]:
        min_cost = random.randint(1500, 8000)
        max_cost = min_cost + random.randint(1000, 7000)
    else:  # Non-surgical, injectables, etc.
        min_cost = random.randint(300, 3000)
        max_cost = min_cost + random.randint(300, 2000)
    
    return min_cost, max_cost

def generate_benefits_and_risks(name, category):
    """Generate realistic benefits and risks based on procedure type."""
    
    # Common benefits by category
    benefit_options = {
        "Surgical": [
            "Significant and long-lasting results",
            "Dramatic improvement in appearance",
            "Permanent correction of structural issues",
            "Comprehensive aesthetic enhancement",
            "Correction of multiple concerns in one procedure"
        ],
        "Non-surgical": [
            "Minimal to no downtime",
            "Natural-looking results",
            "Quick procedure with immediate results",
            "No anesthesia required",
            "Gradual improvement over time"
        ],
        "Minimally invasive": [
            "Less scarring than traditional surgery",
            "Shorter recovery period",
            "Lower risk of complications",
            "Local anesthesia options",
            "Outpatient procedure"
        ],
        "Injectables": [
            "Quick, in-office procedure",
            "Immediate visible results",
            "No downtime required",
            "Temporary and adjustable results",
            "Non-permanent option for those wanting flexibility"
        ],
        "Laser": [
            "Precise targeting of problem areas",
            "Progressive improvement over multiple sessions",
            "Stimulation of natural collagen production",
            "Minimal discomfort during treatment",
            "Effective for multiple skin concerns"
        ]
    }
    
    # Common risks by category
    risk_options = {
        "Surgical": [
            "Risks associated with anesthesia",
            "Potential for infection",
            "Scarring",
            "Extended recovery period",
            "Possibility of revision surgery"
        ],
        "Non-surgical": [
            "Temporary side effects like redness or swelling",
            "Multiple treatments may be required",
            "Results may be subtle compared to surgical options",
            "Potential skin sensitivity",
            "Temporary discomfort"
        ],
        "Minimally invasive": [
            "Bruising and swelling",
            "Potential for minor infection",
            "Small risk of nerve damage",
            "Temporary numbness",
            "Minimal scarring possible"
        ],
        "Injectables": [
            "Bruising at injection sites",
            "Temporary swelling or redness",
            "Risk of asymmetry",
            "Allergic reactions in rare cases",
            "Potential for migration of product"
        ],
        "Laser": [
            "Temporary skin redness",
            "Potential for hyperpigmentation",
            "Sensitivity to sunlight after treatment",
            "Multiple sessions typically required",
            "Risk of burns if not properly administered"
        ]
    }
    
    # Select category for benefits/risks - default to a random one if not found
    benefit_category = category if category in benefit_options else random.choice(list(benefit_options.keys()))
    risk_category = category if category in risk_options else random.choice(list(risk_options.keys()))
    
    # Select 3 random benefits and risks
    benefits = random.sample(benefit_options[benefit_category], 3)
    risks = random.sample(risk_options[risk_category], 3)
    
    return ", ".join(benefits), ", ".join(risks)

def add_procedures(count=100):
    """Add specified number of procedures to the database."""
    from models import Procedure
    
    logger.info(f"Adding {count} new procedures to the database...")
    
    # Get existing procedure names to avoid duplicates
    existing_names = [p.procedure_name for p in Procedure.query.all()]
    logger.info(f"Found {len(existing_names)} existing procedures")
    
    # Add to our exclusion list
    for name in existing_names:
        if name in PROCEDURE_NAMES:
            PROCEDURE_NAMES.remove(name)
    
    procedures_added = 0
    attempts = 0
    max_attempts = count * 2  # Allow for some failures
    
    # Add procedures in small batches
    batch_size = 5
    
    while procedures_added < count and attempts < max_attempts:
        attempts += 1
        
        try:
            # Generate procedure data
            name = generate_procedure_name()
            
            # Skip if name already exists
            if name in existing_names:
                continue
                
            body_area = random.choice(BODY_AREAS)
            category_type = random.choice(CATEGORIES)
            min_cost, max_cost = generate_cost_range(category_type)
            description = generate_procedure_description(name, body_area, category_type)
            benefits, risks = generate_benefits_and_risks(name, category_type)
            
            # Generate random results duration
            results_durations = ["Permanent", "3-6 months", "6-12 months", "1-2 years", "2-5 years", "5-10 years"]
            results_duration = random.choice(results_durations)
            
            # Generate short description
            short_desc = f"A {category_type.lower()} procedure for the {body_area.lower()} area that {description[:50].lower()}..."
            
            # Create the procedure
            procedure = Procedure(
                procedure_name=name,
                short_description=short_desc,
                overview=description[:200] + "...",
                procedure_details=description,
                ideal_candidates=f"Ideal candidates for {name} are individuals who wish to improve the appearance of their {body_area.lower()}.",
                recovery_process="Follow your doctor's post-procedure instructions carefully for optimal results.",
                body_area=body_area,
                category=category_type,
                min_cost=min_cost,
                max_cost=max_cost,
                benefits=benefits,
                risks=risks,
                recovery_time=f"{random.randint(1, 30)} days" if random.random() < 0.7 else f"{random.randint(1, 12)} weeks",
                results_duration=results_duration,
                procedure_types=", ".join([f"{name} Type {chr(65+i)}" for i in range(random.randint(1, 3))])
            )
            
            db.session.add(procedure)
            procedures_added += 1
            
            # Commit in small batches to avoid timeout issues
            if procedures_added % batch_size == 0:
                db.session.commit()
                logger.info(f"Added {procedures_added} procedures so far...")
                # Log the last procedure added
                logger.info(f"Last added: {name} ({body_area}, {category_type})")
            
            existing_names.append(name)
            
        except Exception as e:
            logger.error(f"Error adding procedure: {str(e)}")
            db.session.rollback()
    
    # Final commit
    db.session.commit()
    logger.info(f"Successfully added {procedures_added} new procedures to the database")
    return procedures_added

def main():
    """Run the procedure addition script."""
    logger.info("Starting procedure addition script...")
    
    # Create the application context
    app = create_app()
    
    with app.app_context():
        count = add_procedures(100)
        
    logger.info(f"Added {count} procedures to the database")
    logger.info(f"Log saved to: {LOG_FILE}")
    
    return 0 if count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())