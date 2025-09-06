"""
Import procedures from the provided CSV file.

This script reads the procedure data from the CSV file and imports it into the database.
It handles the new fields: procedure_duration, hospital_stay_required, and alternative_names.
"""
import os
import csv
import logging
from datetime import datetime
from app import db, create_app
from models import Procedure, Category, BodyPart

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_or_get_body_part(name):
    """Create or get a body part by name."""
    body_part = BodyPart.query.filter_by(name=name).first()
    if not body_part:
        logger.info(f"Creating new body part: {name}")
        body_part = BodyPart(name=name, description=f"Body part: {name}")
        db.session.add(body_part)
        db.session.flush()  # Flush to get the ID without committing
    return body_part

def create_or_get_category(name, body_part_id):
    """Create or get a category by name and body part ID."""
    category = Category.query.filter_by(name=name).first()
    if not category:
        logger.info(f"Creating new category: {name} for body part ID: {body_part_id}")
        category = Category(name=name, body_part_id=body_part_id, description=f"Category: {name}")
        db.session.add(category)
        db.session.flush()  # Flush to get the ID without committing
    return category

def import_procedures_from_csv(csv_path):
    """Import procedures from the CSV file."""
    with open(csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        row_count = 0
        success_count = 0
        error_count = 0
        
        for row in csv_reader:
            row_count += 1
            try:
                # Get or create body part and category
                body_part = create_or_get_body_part(row['body_part_name'])
                category = create_or_get_category(row['category_name'], body_part.id)
                
                # Check if procedure already exists
                existing_procedure = Procedure.query.filter_by(procedure_name=row['procedure_name']).first()
                if existing_procedure:
                    logger.info(f"Procedure already exists: {row['procedure_name']} - Updating...")
                    procedure = existing_procedure
                else:
                    logger.info(f"Creating new procedure: {row['procedure_name']}")
                    procedure = Procedure()
                
                # Set procedure fields
                procedure.procedure_name = row['procedure_name']
                procedure.alternative_names = row['alternative_names']
                procedure.short_description = row['short_description']
                procedure.overview = row['overview']
                procedure.procedure_details = row['procedure_details']
                procedure.ideal_candidates = row['ideal_candidates']
                procedure.recovery_process = row.get('recovery_process', '')
                procedure.recovery_time = row['recovery_time']
                procedure.procedure_duration = row['procedure_duration']
                procedure.hospital_stay_required = row['hospital_stay_required']
                procedure.results_duration = row.get('results_duration', '')
                
                # Handle cost as integers
                try:
                    procedure.min_cost = int(row['min_cost'].replace(',', '')) if row['min_cost'] else 0
                    procedure.max_cost = int(row['max_cost'].replace(',', '')) if row['max_cost'] else 0
                except (ValueError, KeyError):
                    logger.warning(f"Error parsing cost for procedure: {row['procedure_name']}")
                    procedure.min_cost = 0
                    procedure.max_cost = 0
                
                procedure.benefits = row.get('benefits', '')
                procedure.benefits_detailed = row.get('benefits_detailed', '')
                procedure.risks = row['risks']
                procedure.procedure_types = row['procedure_types']
                procedure.alternative_procedures = row.get('alternative_procedures', '')
                procedure.category_id = category.id
                procedure.body_part = row['body_part_name']  # Also store the body part name
                
                # Handle tags
                if 'tags' in row and row['tags']:
                    tags = [tag.strip() for tag in row['tags'].split(',')]
                    procedure.tags = tags
                
                # Save the procedure
                if not existing_procedure:
                    db.session.add(procedure)
                
                # Commit every 10 procedures to avoid long transactions
                if row_count % 10 == 0:
                    db.session.commit()
                    logger.info(f"Committed batch of procedures. Total processed: {row_count}")
                
                success_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"Error importing procedure {row.get('procedure_name', 'unknown')}: {str(e)}")
        
        # Final commit
        db.session.commit()
        logger.info(f"Import complete. Processed {row_count} rows with {success_count} successes and {error_count} errors.")
        return success_count, error_count

def main():
    """Main function to run the import."""
    csv_path = 'attached_assets/procedure_details - Sheet1.csv'
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    app = create_app()
    with app.app_context():
        logger.info(f"Starting import from {csv_path}")
        success_count, error_count = import_procedures_from_csv(csv_path)
        logger.info(f"Import completed: {success_count} procedures imported successfully, {error_count} errors.")

if __name__ == "__main__":
    main()