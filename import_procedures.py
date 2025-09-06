#!/usr/bin/env python3
"""
Import procedures from CSV file.

This script imports procedures with all their details from the CSV file.
"""

import os
import csv
import logging
import random

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import required models and app
from app import create_app, db
from models import BodyPart, Category, Procedure

# Path to CSV file
PROCEDURES_CSV = "attached_assets/new_procedure_details - Sheet1.csv"

def clean_integer(value):
    """Clean cost values by removing commas and converting to integer."""
    if value is None or value == "":
        return 0
    
    # Remove commas, spaces, and non-numeric characters except for the first minus sign
    value = str(value)
    clean_value = ''.join(c for c in value if c.isdigit() or (c == '-' and value.index(c) == 0))
    
    try:
        return int(clean_value or 0)
    except ValueError:
        return 0

def import_procedures(batch_size=10):
    """Import procedures from CSV file in batches."""
    if not os.path.exists(PROCEDURES_CSV):
        logger.error(f"Procedures CSV file not found: {PROCEDURES_CSV}")
        return False
    
    try:
        # Create application context
        app = create_app()
        with app.app_context():
            # Get all categories for lookup
            categories = {}
            for cat in Category.query.all():
                body_part = BodyPart.query.get(cat.body_part_id)
                if body_part:
                    key = (body_part.name, cat.name)
                    categories[key] = cat.id
            
            if not categories:
                logger.warning("No categories found. Please run import_categories.py first.")
                return False
            
            # Import procedures in batches
            procedures_added = 0
            skipped = 0
            
            with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                current_batch = []
                
                for row in reader:
                    # Get essential fields
                    body_part_name = row.get('body_part_name', '').strip()
                    category_name = row.get('category_name', '').strip()
                    procedure_name = row.get('procedure_name', '').strip()
                    
                    # Skip if essential fields are missing
                    if not procedure_name or not body_part_name or not category_name:
                        skipped += 1
                        continue
                    
                    # Check if procedure already exists
                    existing = Procedure.query.filter_by(procedure_name=procedure_name).first()
                    if existing:
                        logger.info(f"Procedure already exists: {procedure_name}")
                        skipped += 1
                        continue
                    
                    # Get category ID
                    category_key = (body_part_name, category_name)
                    category_id = categories.get(category_key)
                    if not category_id:
                        logger.warning(f"Category not found for procedure: {category_name} under {body_part_name}")
                        skipped += 1
                        continue
                    
                    # Create new procedure
                    procedure = Procedure()
                    procedure.procedure_name = procedure_name
                    procedure.alternative_names = row.get('alternative_names', '')
                    procedure.short_description = row.get('short_description', '')
                    procedure.overview = row.get('overview', '')
                    procedure.procedure_details = row.get('procedure_details', '')
                    procedure.ideal_candidates = row.get('ideal_candidates', '')
                    procedure.recovery_process = row.get('recovery_process', '')
                    procedure.recovery_time = row.get('recovery_time', '')
                    procedure.procedure_duration = row.get('procedure_duration', '')
                    procedure.hospital_stay_required = row.get('hospital_stay_required', 'No')
                    procedure.results_duration = row.get('results_duration', '')
                    
                    # Clean cost values
                    min_cost = clean_integer(row.get('min_cost', '0'))
                    max_cost = clean_integer(row.get('max_cost', '0'))
                    procedure.min_cost = min_cost
                    procedure.max_cost = max_cost
                    
                    procedure.benefits = row.get('benefits', '')
                    procedure.benefits_detailed = row.get('benefits_detailed', '')
                    procedure.risks = row.get('risks', '')
                    procedure.procedure_types = row.get('procedure_types', '')
                    procedure.alternative_procedures = row.get('alternative_procedures', '')
                    procedure.category_id = category_id
                    
                    # Set initial ratings data
                    procedure.popularity_score = random.randint(50, 100)
                    procedure.avg_rating = 0
                    procedure.review_count = 0
                    
                    # Handle tags
                    tags = row.get('tags', '')
                    if tags:
                        procedure.tags = [tag.strip() for tag in tags.split(',')]
                    
                    # Set body part field
                    procedure.body_part = body_part_name
                    
                    # Add to batch
                    db.session.add(procedure)
                    procedures_added += 1
                    
                    # Commit batch when it reaches the batch size
                    if procedures_added % batch_size == 0:
                        db.session.commit()
                        logger.info(f"Imported {procedures_added} procedures so far (skipped {skipped})")
            
            # Commit any remaining procedures
            db.session.commit()
            logger.info(f"Successfully imported {procedures_added} procedures (skipped {skipped})")
            
            # Print sample procedures for verification
            sample_procedures = Procedure.query.limit(5).all()
            logger.info(f"Sample procedures in database:")
            for proc in sample_procedures:
                logger.info(f"Procedure: {proc.procedure_name} (ID: {proc.id})")
            
            return True
    except Exception as e:
        logger.error(f"Error importing procedures: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    import_procedures()