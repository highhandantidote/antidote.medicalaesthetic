#!/usr/bin/env python3
"""
Create associations between doctors and procedures in small batches.

This script associates doctors with procedures based on their specialties
and ensures comprehensive coverage of the doctor-procedure relationships.
It processes doctors in small batches to avoid timeouts.
"""

import os
import logging
import random
import json
import sys
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
BATCH_SIZE = 3  # Process 3 doctors at a time to avoid timeouts

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    import os
    import psycopg2
    
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def create_specialty_procedure_mapping():
    """Create a mapping between medical specialties and relevant procedures."""
    # This mapping connects specialty keywords to procedure types they likely perform
    specialty_mapping = {
        "plastic": ["all"],  # Plastic surgeons can do most procedures
        "cosmetic": ["all"],  # Cosmetic surgeons can do most procedures
        "aesthetic": ["all"],  # Aesthetic surgeons can do most procedures
        "reconstructive": ["all"],  # Reconstructive surgeons can do most procedures
        
        # Face-related specialists
        "facial": ["face", "nose", "eyes", "lips", "jawline", "neck"],
        "face": ["face", "nose", "eyes", "lips", "jawline", "neck"],
        "maxillofacial": ["jawline", "face"],
        "craniofacial": ["face", "jawline"],
        
        # Body area specialists
        "breast": ["breasts"],
        "body": ["body", "stomach", "butt", "arms", "legs", "hips"],
        "body contouring": ["body", "stomach", "butt", "arms", "legs", "liposuction"],
        
        # Specific area specialists
        "hair": ["hair"],
        "dermatol": ["skin"],
        "rhinoplasty": ["nose"],
        "ocular": ["eyes"],
        "eyelid": ["eyes"],
        "abdominoplasty": ["stomach"],
        "liposuction": ["body", "stomach", "butt", "arms", "legs"],
        "buttock": ["butt"],
        "hand": ["hands"],
    }
    
    return specialty_mapping

def associate_doctors_with_procedures_batch(start_index=0, batch_size=BATCH_SIZE):
    """Associate a batch of doctors with procedures based on their specialties."""
    try:
        conn = get_db_connection()
        if not conn:
            return False, 0, start_index
        
        # Get the specialty-procedure mapping
        specialty_mapping = create_specialty_procedure_mapping()
        
        # Get the batch of doctors
        doctors = []
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, specialty 
                FROM doctors 
                ORDER BY id
                LIMIT %s OFFSET %s
            """, (batch_size, start_index))
            doctors = cur.fetchall()
        
        if not doctors:
            logger.info(f"No more doctors found starting from index {start_index}")
            return True, 0, start_index  # No more doctors to process
        
        # Get all procedures and organize by body part
        procedures_by_body_part = defaultdict(list)
        all_procedures = []
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, p.procedure_name, p.body_part, c.name AS category_name
                FROM procedures p
                JOIN categories c ON p.category_id = c.id
                ORDER BY p.id
            """)
            
            for proc_id, proc_name, body_part, category_name in cur.fetchall():
                all_procedures.append((proc_id, proc_name, body_part, category_name))
                if body_part:
                    body_part_lower = body_part.lower()
                    procedures_by_body_part[body_part_lower].append((proc_id, proc_name, category_name))
                
                # Also add to specific categories for finer matching
                if category_name:
                    category_lower = category_name.lower()
                    procedures_by_body_part[category_lower].append((proc_id, proc_name, category_name))
        
        if not all_procedures:
            logger.warning("No procedures found in the database.")
            return False, 0, start_index
        
        # Keep track of associations
        created_associations = 0
        doctors_processed = 0
        
        # Process each doctor in the batch
        for doctor_id, doctor_name, specialty in doctors:
            logger.info(f"Processing doctor: {doctor_name} (ID: {doctor_id})")
            
            # First, remove existing associations to avoid duplicates
            with conn.cursor() as cur:
                cur.execute("DELETE FROM doctor_procedures WHERE doctor_id = %s", (doctor_id,))
            
            # Determine which procedures match this doctor's specialty
            matched_procedures = set()
            
            if specialty:
                specialty_lower = specialty.lower()
                
                # Check if the specialty contains any keywords from our mapping
                for keyword, body_parts in specialty_mapping.items():
                    if keyword in specialty_lower:
                        if "all" in body_parts:
                            # This specialist can do all procedures, just add them all
                            for proc_id, _, _, _ in all_procedures:
                                matched_procedures.add(proc_id)
                        else:
                            # Add procedures for each relevant body part
                            for body_part in body_parts:
                                for proc_id, _, _, _ in all_procedures:
                                    if proc_id not in matched_procedures:
                                        matched_procedures.add(proc_id)
            
            # If we didn't find specific matches or the doctor is a general plastic surgeon,
            # assign a random selection of procedures
            if len(matched_procedures) < 5 or "plastic" in specialty.lower():
                # Ensure at least 10 procedures for each doctor
                additional_count = max(0, 10 - len(matched_procedures))
                
                # Get procedures not already matched
                unmatched_procs = [(p_id, p_name) for p_id, p_name, _, _ in all_procedures 
                                  if p_id not in matched_procedures]
                
                # Add random selections if available
                if unmatched_procs and additional_count > 0:
                    sample_size = min(additional_count, len(unmatched_procs))
                    for proc_id, _ in random.sample(unmatched_procs, sample_size):
                        matched_procedures.add(proc_id)
            
            # Create associations
            for proc_id in matched_procedures:
                with conn.cursor() as cur:
                    # Check if association already exists (shouldn't, since we deleted them)
                    cur.execute("""
                        INSERT INTO doctor_procedures (doctor_id, procedure_id)
                        VALUES (%s, %s)
                    """, (doctor_id, proc_id))
                    
                    created_associations += 1
            
            # Log progress
            logger.info(f"Associated doctor ID {doctor_id} with {len(matched_procedures)} procedures")
            
            # Commit after each doctor to avoid losing progress
            conn.commit()
            doctors_processed += 1
        
        # Determine next index
        next_index = start_index + doctors_processed
        
        logger.info(f"Successfully processed {doctors_processed} doctors with {created_associations} procedure associations in this batch")
        return True, doctors_processed, next_index
    except Exception as e:
        logger.error(f"Error associating doctors with procedures: {str(e)}")
        if conn:
            conn.rollback()
        return False, 0, start_index
    finally:
        if conn:
            conn.close()

def process_all_doctors():
    """Process all doctors in batches."""
    start_index = 0
    total_processed = 0
    
    # Check if a starting point was provided as a command-line argument
    if len(sys.argv) > 1:
        try:
            start_index = int(sys.argv[1])
            logger.info(f"Starting from index {start_index}")
        except ValueError:
            logger.warning(f"Invalid start index: {sys.argv[1]}, starting from 0")
    
    while True:
        logger.info(f"Processing batch starting at index {start_index}")
        success, processed, next_index = associate_doctors_with_procedures_batch(start_index, BATCH_SIZE)
        
        if not success:
            logger.error(f"Failed to process batch starting at index {start_index}")
            print(f"ERROR: Failed to process batch starting at index {start_index}")
            print(f"To resume, run: python {sys.argv[0]} {start_index}")
            break
        
        total_processed += processed
        
        if processed == 0 or start_index == next_index:
            logger.info("No more doctors to process")
            break
            
        start_index = next_index
        logger.info(f"Next batch will start at index {next_index}")
        
        # Save progress after each batch
        with open("doctor_associations_progress.txt", "w") as f:
            f.write(str(start_index))
    
    logger.info(f"Finished processing {total_processed} doctors")
    print(f"Finished processing {total_processed} doctors")

if __name__ == "__main__":
    process_all_doctors()