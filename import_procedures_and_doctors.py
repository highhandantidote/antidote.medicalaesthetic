#!/usr/bin/env python3
"""
Import procedures and doctors data from CSV files.

This script imports procedure and doctor data from CSV files into the database,
maintaining proper relationships between entities.
"""

import os
import sys
import csv
import logging
from datetime import datetime
import json
import random

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set the DATABASE_URL environment variable if not already set
if 'DATABASE_URL' not in os.environ:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

# Import required models and app
try:
    from app import create_app, db
    from models import BodyPart, Category, Procedure, Doctor, User, DoctorProcedure
    
    # Create app and push an application context
    app = create_app()
    app_context = app.app_context()
    app_context.push()
    
except ImportError as e:
    logger.error(f"Failed to import required models: {str(e)}")
    sys.exit(1)

# Paths to CSV files
PROCEDURES_CSV = "attached_assets/new_procedure_details - Sheet1.csv"
DOCTORS_CSV = "attached_assets/new_doctors_profiles - Sheet1.csv"

def clean_integer(value):
    """Clean cost values by removing commas and converting to integer."""
    if value is None or value == "":
        return 0
    
    # Remove commas, spaces, and non-numeric characters except for the first minus sign
    clean_value = ''.join(c for c in value if c.isdigit() or (c == '-' and value.index(c) == 0))
    
    try:
        return int(clean_value or 0)
    except ValueError:
        return 0

def import_procedures():
    """Import procedures from CSV file."""
    if not os.path.exists(PROCEDURES_CSV):
        logger.error(f"Procedures CSV file not found: {PROCEDURES_CSV}")
        return False
    
    try:
        # Track counts for summary
        body_parts_added = 0
        categories_added = 0
        procedures_added = 0
        
        # First pass: Collect all unique body parts and categories
        body_parts_map = {}  # Maps body part names to their IDs
        categories_map = {}  # Maps category names to their IDs
        
        logger.info("First pass: Collecting all unique body parts and categories...")
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                body_part_name = row.get('body_part_name', '').strip()
                category_name = row.get('category_name', '').strip()
                
                if body_part_name and body_part_name not in body_parts_map:
                    body_parts_map[body_part_name] = None
                
                if category_name and body_part_name and (body_part_name, category_name) not in categories_map:
                    categories_map[(body_part_name, category_name)] = None
        
        # Create body parts first
        for body_part_name in body_parts_map:
            existing_body_part = BodyPart.query.filter_by(name=body_part_name).first()
            if existing_body_part:
                body_parts_map[body_part_name] = existing_body_part.id
                logger.info(f"Body part already exists: {body_part_name} (ID: {existing_body_part.id})")
            else:
                body_part = BodyPart()
                body_part.name = body_part_name
                body_part.description = f"{body_part_name} procedures and treatments"
                body_part.icon_url = f"/static/images/{body_part_name.lower().replace(' ', '_')}.svg"
                db.session.add(body_part)
                db.session.flush()  # Get ID
                body_parts_map[body_part_name] = body_part.id
                body_parts_added += 1
                logger.info(f"Added body part: {body_part_name} (ID: {body_part.id})")
        
        # Create categories next
        for (body_part_name, category_name) in categories_map:
            existing_category = Category.query.filter_by(name=category_name).first()
            if existing_category:
                categories_map[(body_part_name, category_name)] = existing_category.id
                logger.info(f"Category already exists: {category_name} (ID: {existing_category.id})")
            else:
                body_part_id = body_parts_map.get(body_part_name)
                if not body_part_id:
                    logger.warning(f"Cannot add category {category_name}, body part {body_part_name} not found")
                    continue
                    
                category = Category()
                category.name = category_name
                category.description = f"{category_name} procedures"
                category.body_part_id = body_part_id
                category.popularity_score = 0  # Default score, will be updated based on procedures
                db.session.add(category)
                db.session.flush()  # Get ID
                categories_map[(body_part_name, category_name)] = category.id
                categories_added += 1
                logger.info(f"Added category: {category_name} under {body_part_name} (ID: {category.id})")
        
        # Commit these changes to ensure references exist
        db.session.commit()
        logger.info(f"Added {body_parts_added} body parts and {categories_added} categories")
        
        # Second pass: Add procedures using the established body parts and categories
        logger.info("Second pass: Adding procedures...")
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                body_part_name = row.get('body_part_name', '').strip()
                category_name = row.get('category_name', '').strip()
                procedure_name = row.get('procedure_name', '').strip()
                
                if not procedure_name:
                    logger.warning("Skipping row with empty procedure name")
                    continue
                    
                if not body_part_name or not category_name:
                    logger.warning(f"Skipping procedure {procedure_name} with missing body part or category")
                    continue
                
                # Check if procedure already exists
                existing_procedure = Procedure.query.filter_by(procedure_name=procedure_name).first()
                if existing_procedure:
                    logger.info(f"Procedure already exists: {procedure_name} (ID: {existing_procedure.id})")
                    continue
                
                # Get category ID
                category_id = categories_map.get((body_part_name, category_name))
                if not category_id:
                    logger.warning(f"Cannot add procedure {procedure_name}, category {category_name} not found under {body_part_name}")
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
                
                # Clean cost values (remove commas and convert to integers)
                min_cost_str = row.get('min_cost', '0')
                max_cost_str = row.get('max_cost', '0')
                
                procedure.min_cost = clean_integer(min_cost_str)
                procedure.max_cost = clean_integer(max_cost_str)
                
                procedure.benefits = row.get('benefits', '')
                procedure.benefits_detailed = row.get('benefits_detailed', '')
                procedure.risks = row.get('risks', '')
                procedure.procedure_types = row.get('procedure_types', '')
                procedure.alternative_procedures = row.get('alternative_procedures', '')
                procedure.category_id = category_id
                
                # Real rating data should come from reviews, but set defaults for display
                procedure.popularity_score = 0
                procedure.avg_rating = 0
                procedure.review_count = 0
                
                # Handle tags
                tags = row.get('tags', '')
                if tags:
                    procedure.tags = [tag.strip() for tag in tags.split(',')]
                
                # Set body part for new structure
                procedure.body_part = body_part_name
                
                db.session.add(procedure)
                procedures_added += 1
                
                # Commit every 10 procedures to avoid timeout
                if procedures_added % 10 == 0:
                    db.session.commit()
                    logger.info(f"Committed batch of procedures. Total so far: {procedures_added}")
            
            # Final commit
            db.session.commit()
            
            logger.info(f"Successfully imported procedures from CSV: {procedures_added} procedures")
            return True
            
    except Exception as e:
        logger.error(f"Error importing procedures: {str(e)}")
        db.session.rollback()
        return False

def import_doctors():
    """Import doctors from CSV file."""
    if not os.path.exists(DOCTORS_CSV):
        logger.error(f"Doctors CSV file not found: {DOCTORS_CSV}")
        return False
    
    try:
        # Track counts for summary
        users_added = 0
        doctors_added = 0
        
        # Read CSV file
        with open(DOCTORS_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # Get doctor name
                doctor_name = row.get('Doctor Name', '').strip()
                if not doctor_name:
                    logger.warning("Skipping row with empty doctor name")
                    continue
                
                # Check if doctor already exists
                existing_doctor = Doctor.query.filter_by(name=doctor_name).first()
                if existing_doctor:
                    logger.info(f"Doctor already exists: {doctor_name}")
                    continue
                
                # Extract phone number from Address field if available (since we don't have a direct phone field)
                # If not available, we'll use a placeholder
                address = row.get('Address', '').strip()
                phone_number = '9999999999'  # Default placeholder
                
                # Create a user for this doctor
                username = doctor_name.lower().replace(' ', '_').replace('.', '').replace(',', '')
                email = f"{username}@example.com"
                
                # Check if user with this email already exists
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    # Use an alternative email
                    email = f"{username}_{random.randint(100, 999)}@example.com"
                
                user = User()
                user.name = doctor_name
                user.email = email
                user.username = username
                user.role = 'doctor'
                user.role_type = 'doctor'
                user.phone_number = phone_number
                user.is_verified = True
                user.set_password('password123')  # Default password for demonstration
                
                db.session.add(user)
                db.session.flush()  # Flush to get the ID
                users_added += 1
                
                # Create doctor profile
                doctor = Doctor()
                doctor.user_id = user.id
                doctor.name = doctor_name
                doctor.specialty = row.get('specialty', 'Plastic Surgeon')
                
                # Extract years from experience text
                experience_text = row.get('Experience', '')
                experience_years = 0
                if experience_text:
                    # Try to extract the years
                    try:
                        experience_years = int(''.join(filter(str.isdigit, experience_text.split(' ')[0])))
                    except (ValueError, IndexError):
                        experience_years = 10  # Default to 10 years if parsing fails
                else:
                    experience_years = 10  # Default to 10 years if not specified
                
                doctor.experience = experience_years
                doctor.city = row.get('city', '')
                doctor.state = row.get('state', '')
                doctor.hospital = address
                doctor.consultation_fee = 1000  # Standard consultation fee
                doctor.is_verified = True
                doctor.rating = 4.0  # Default rating
                doctor.review_count = 0  # No reviews initially
                doctor.bio = f"Dr. {doctor_name.split()[-1]} is a {row.get('specialty', 'Plastic Surgeon')} with {experience_years} years of experience."
                
                # Store education as JSON
                education = row.get('education', '')
                if education:
                    doctor.education = json.dumps([{"degree": degree.strip()} for degree in education.split(',')])
                
                # Add verification details
                doctor.verification_status = 'approved'
                doctor.verification_date = datetime.utcnow()
                
                db.session.add(doctor)
                doctors_added += 1
                
                # Commit every 10 doctors to avoid timeout
                if doctors_added % 10 == 0:
                    db.session.commit()
                    logger.info(f"Committed batch of doctors. Total so far: {doctors_added}")
            
            # Final commit
            db.session.commit()
            
            logger.info(f"Successfully imported doctors from CSV: {doctors_added} doctors, {users_added} users")
            return True
            
    except Exception as e:
        logger.error(f"Error importing doctors: {str(e)}")
        db.session.rollback()
        return False

def associate_doctors_with_procedures():
    """Associate doctors with procedures to create relationships based on specialty."""
    try:
        # Get all doctors and procedures
        doctors = Doctor.query.all()
        procedures = Procedure.query.all()
        
        if not doctors:
            logger.warning("No doctors found to associate with procedures")
            return False
            
        if not procedures:
            logger.warning("No procedures found to associate with doctors")
            return False
        
        # Track counts
        associations_added = 0
        
        # Get all categories for mapping
        categories = Category.query.all()
        category_map = {c.name.lower(): c for c in categories}
        
        # For each doctor, assign procedures based on specialty
        for doctor in doctors:
            matched_procedures = []
            specialty = doctor.specialty.lower() if doctor.specialty else "plastic surgeon"
            
            # For plastic surgeons, we'll assign a broader range of procedures
            if "plastic" in specialty or "cosmetic" in specialty or "aesthetic" in specialty:
                # Pick a range of procedures across different categories
                categories_to_use = categories
                
                # Get a subset of categories (between 3-5 categories)
                num_categories = min(len(categories), random.randint(3, 5))
                selected_categories = random.sample(categories, num_categories)
                
                # Get procedures from these categories
                for category in selected_categories:
                    category_procedures = [p for p in procedures if p.category_id == category.id]
                    # Take a subset of procedures from each category (up to 5)
                    if category_procedures:
                        num_to_take = min(len(category_procedures), random.randint(2, 5))
                        matched_procedures.extend(random.sample(category_procedures, num_to_take))
                        
            # For specific specialists, try to match to their specialty
            else:
                # Try to match specialty keywords to categories
                matched_categories = []
                specialty_keywords = specialty.split()
                
                # Look for category matches
                for keyword in specialty_keywords:
                    if len(keyword) > 3:  # Ignore short words
                        for category in categories:
                            if keyword.lower() in category.name.lower():
                                matched_categories.append(category)
                
                # If no matches, assign some general procedures
                if not matched_categories:
                    # Assign a small random selection
                    num_procedures = min(len(procedures), random.randint(3, 8))
                    matched_procedures = random.sample(procedures, num_procedures)
                else:
                    # Get procedures from matched categories
                    for category in matched_categories:
                        category_procedures = [p for p in procedures if p.category_id == category.id]
                        if category_procedures:
                            matched_procedures.extend(category_procedures)
            
            # If we still have no matches, take a small random sample
            if not matched_procedures:
                num_procedures = min(len(procedures), random.randint(3, 8))
                matched_procedures = random.sample(procedures, num_procedures)
            
            # Remove duplicates while preserving order
            seen = set()
            matched_procedures = [p for p in matched_procedures if not (p.id in seen or seen.add(p.id))]
            
            # Create the associations
            for procedure in matched_procedures:
                # Check if association already exists
                existing = DoctorProcedure.query.filter_by(
                    doctor_id=doctor.id, 
                    procedure_id=procedure.id
                ).first()
                
                if not existing:
                    doctor_procedure = DoctorProcedure()
                    doctor_procedure.doctor_id = doctor.id
                    doctor_procedure.procedure_id = procedure.id
                    db.session.add(doctor_procedure)
                    associations_added += 1
            
            # Commit per doctor to avoid timeout
            db.session.commit()
            logger.info(f"Associated doctor {doctor.name} with {len(matched_procedures)} procedures")
        
        logger.info(f"Successfully associated doctors with procedures: {associations_added} associations created")
        return True
        
    except Exception as e:
        logger.error(f"Error associating doctors with procedures: {str(e)}")
        db.session.rollback()
        return False

def main():
    """Main function to import all data."""
    try:
        logger.info("Starting data import process...")
        
        # Import procedures
        logger.info("Importing procedures...")
        procedures_result = import_procedures()
        
        # Import doctors
        logger.info("Importing doctors...")
        doctors_result = import_doctors()
        
        # Associate doctors with procedures
        if procedures_result and doctors_result:
            logger.info("Associating doctors with procedures...")
            association_result = associate_doctors_with_procedures()
        else:
            association_result = False
            logger.warning("Skipping doctor-procedure associations due to import failures")
        
        # Final status
        if procedures_result and doctors_result and association_result:
            logger.info("Data import completed successfully!")
            return True
        else:
            logger.warning("Data import completed with some issues.")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error during import: {str(e)}")
        return False

if __name__ == "__main__":
    main()