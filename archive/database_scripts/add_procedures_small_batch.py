#!/usr/bin/env python3
"""
Add procedures to the database using the RealSelf hierarchy schema.
This version uses very small batches (5 procedures) to avoid timeouts on Replit.
"""
import logging
import sys
from datetime import datetime
from app import create_app, db
from add_ten_procedures import BASE_PROCEDURES, ADDITIONAL_PROCEDURES

# Configure logging
LOG_FILE = f"add_procedures_small_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Use a very small batch size for Replit
BATCH_SIZE = 5
MAX_PROCEDURES_PER_RUN = 15  # Add up to 15 procedures per execution

def add_procedures(batch_size=BATCH_SIZE, max_procedures=MAX_PROCEDURES_PER_RUN, start_index=0):
    """
    Add procedures to the database in very small batches to avoid timeouts.
    
    Args:
        batch_size: Number of procedures to add in a single batch
        max_procedures: Maximum number of procedures to add in this run
        start_index: Index to start from in the combined procedures list
        
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
    logger.info(f"Starting from index {start_index} (up to index {min(start_index + max_procedures, len(all_procedures))})")
    
    # Create all necessary categories
    all_categories = set(proc["category"] for proc in all_procedures)
    logger.info(f"Need to ensure {len(all_categories)} categories exist")
    
    for category_name in all_categories:
        if category_name not in categories:
            try:
                default_category = Category(name=category_name, description=f"{category_name} procedures")
                db.session.add(default_category)
                db.session.commit()
                categories[category_name] = default_category.id
                logger.info(f"Created '{category_name}' category")
            except Exception as e:
                logger.error(f"Error creating category {category_name}: {str(e)}")
                db.session.rollback()
    
    # Limit the procedures to process in this run
    procedures_to_process = all_procedures[start_index:start_index + max_procedures]
    logger.info(f"Processing {len(procedures_to_process)} procedures in this run")
    
    # Process procedures in batches
    total_added = 0
    batch_num = 1
    
    for i in range(0, len(procedures_to_process), batch_size):
        batch = procedures_to_process[i:i+batch_size]
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
                logger.info(f"Added procedure {total_added}/{len(procedures_to_process)}: {name}")
                
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
    
    logger.info(f"Successfully added {total_added} new procedures to the database")
    
    # Return the next start index
    next_start_index = start_index + max_procedures
    if next_start_index >= len(all_procedures):
        next_start_index = -1  # Indicate completion
    
    return total_added, next_start_index

def main():
    """Run the procedure addition script with parameters."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add procedures to the database in small batches')
    parser.add_argument('--start-index', type=int, default=0, help='Starting index in the procedure list')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Number of procedures to add in each batch')
    parser.add_argument('--max-procedures', type=int, default=MAX_PROCEDURES_PER_RUN, help='Maximum procedures to add in this run')
    
    args = parser.parse_args()
    
    logger.info("Starting procedure addition script...")
    logger.info(f"Parameters: start_index={args.start_index}, batch_size={args.batch_size}, max_procedures={args.max_procedures}")
    
    # Create the application context
    app = create_app()
    
    with app.app_context():
        count, next_index = add_procedures(
            batch_size=args.batch_size,
            max_procedures=args.max_procedures,
            start_index=args.start_index
        )
        
    logger.info(f"Added {count} procedures to the database")
    logger.info(f"Next start index: {next_index}")
    logger.info(f"Log saved to: {LOG_FILE}")
    
    # Print for script chaining
    print(f"NEXT_INDEX={next_index}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())