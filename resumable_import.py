#!/usr/bin/env python3
"""
Resumable Database Import Script

This script imports data from CSV files with checkpoint capability.
If interrupted, it can continue from the last successful position.
"""

import os
import csv
import json
import logging
import psycopg2
import random
import time
import pickle
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths to the latest CSV files
PROCEDURES_CSV = "attached_assets/new_procedure_details - Sheet1.csv"
DOCTORS_CSV = "attached_assets/new_doctors_profiles2 - Sheet1.csv"

# Checkpoint file to track progress
CHECKPOINT_FILE = "import_checkpoint.pkl.bak"

# Batch size for imports to avoid timeouts
BATCH_SIZE = 10
MAX_BATCHES_PER_RUN = 5  # Limit number of batches per run to avoid timeouts

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def save_checkpoint(checkpoint_data):
    """Save checkpoint data to file."""
    try:
        with open(CHECKPOINT_FILE, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        logger.info(f"Saved checkpoint: {checkpoint_data}")
        return True
    except Exception as e:
        logger.error(f"Error saving checkpoint: {str(e)}")
        return False

def load_checkpoint():
    """Load checkpoint data from file."""
    if not os.path.exists(CHECKPOINT_FILE):
        logger.info("No checkpoint file found, starting from beginning")
        return {
            'body_parts_done': False,
            'categories_done': False,
            'procedures_index': 0,
            'doctors_index': 0,
            'banners_done': False,
            'community_done': False,
            'body_part_ids': {},
            'category_ids': {}
        }
    
    try:
        with open(CHECKPOINT_FILE, 'rb') as f:
            checkpoint = pickle.load(f)
        logger.info(f"Loaded checkpoint: {checkpoint}")
        return checkpoint
    except Exception as e:
        logger.error(f"Error loading checkpoint: {str(e)}")
        return {
            'body_parts_done': False,
            'categories_done': False,
            'procedures_index': 0,
            'doctors_index': 0,
            'banners_done': False,
            'community_done': False,
            'body_part_ids': {},
            'category_ids': {}
        }

def add_body_parts_batch():
    """Add all body parts from the procedures CSV in batches."""
    if not os.path.exists(PROCEDURES_CSV):
        logger.error(f"Procedures CSV file not found: {PROCEDURES_CSV}")
        return {}
    
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        
        # Get unique body parts from CSV
        unique_body_parts = set()
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                body_part_name = row.get('body_part_name', '').strip()
                if body_part_name:
                    unique_body_parts.add(body_part_name)
        
        logger.info(f"Found {len(unique_body_parts)} unique body parts in CSV")
        
        # Add body parts to database using direct SQL
        body_part_ids = {}
        with conn.cursor() as cur:
            batch_count = 0
            for body_part_name in unique_body_parts:
                # Check if body part already exists
                cur.execute("SELECT id FROM body_parts WHERE name = %s", (body_part_name,))
                result = cur.fetchone()
                
                if result:
                    # Body part already exists
                    body_part_ids[body_part_name] = result[0]
                    logger.info(f"Body part already exists: {body_part_name} (ID: {result[0]})")
                else:
                    # Create new body part
                    description = f"Procedures related to the {body_part_name.lower()}"
                    icon_url = f"/static/images/body_parts/{body_part_name.lower().replace(' ', '_')}.svg"
                    
                    cur.execute("""
                        INSERT INTO body_parts (name, description, icon_url, created_at)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (body_part_name, description, icon_url, datetime.utcnow()))
                    
                    body_part_id = cur.fetchone()[0]
                    body_part_ids[body_part_name] = body_part_id
                    logger.info(f"Added body part: {body_part_name} (ID: {body_part_id})")
                
                batch_count += 1
                if batch_count % BATCH_SIZE == 0:
                    conn.commit()
                    logger.info(f"Committed batch of {BATCH_SIZE} body parts")
        
        conn.commit()
        logger.info(f"Successfully added {len(body_part_ids)} body parts")
        return body_part_ids
    except Exception as e:
        logger.error(f"Error adding body parts: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return {}
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def add_categories_batch(body_part_ids):
    """Add all categories from the procedures CSV in batches."""
    if not os.path.exists(PROCEDURES_CSV) or not body_part_ids:
        logger.error(f"Procedures CSV file not found or no body parts added")
        return {}
    
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        
        # Get unique categories per body part from CSV
        unique_categories = {}  # {(body_part_name, category_name): None}
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                body_part_name = row.get('body_part_name', '').strip()
                category_name = row.get('category_name', '').strip()
                
                if body_part_name and category_name:
                    unique_categories[(body_part_name, category_name)] = None
        
        logger.info(f"Found {len(unique_categories)} unique categories in CSV")
        
        # Add categories to database using direct SQL
        category_ids = {}
        with conn.cursor() as cur:
            batch_count = 0
            for (body_part_name, category_name) in unique_categories:
                # Skip if body part doesn't exist
                if body_part_name not in body_part_ids:
                    logger.warning(f"Body part not found for category: {body_part_name} - {category_name}")
                    continue
                
                body_part_id = body_part_ids[body_part_name]
                
                # Check if category already exists - first check by both name and body part
                cur.execute(
                    "SELECT id FROM categories WHERE name = %s AND body_part_id = %s",
                    (category_name, body_part_id)
                )
                result = cur.fetchone()
                
                if result:
                    # Category already exists with this name and body part
                    category_ids[(body_part_name, category_name)] = result[0]
                    logger.info(f"Category already exists: {category_name} under {body_part_name} (ID: {result[0]})")
                else:
                    # Check if the name exists globally (since there's a unique constraint)
                    cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
                    name_exists = cur.fetchone()
                    
                    if name_exists:
                        # Category name exists but under a different body part
                        # Create a slightly modified name to avoid duplicate
                        modified_name = f"{category_name} ({body_part_name})"
                        logger.info(f"Category name '{category_name}' already exists, using '{modified_name}' instead")
                        
                        # Check if modified name exists
                        cur.execute("SELECT id FROM categories WHERE name = %s", (modified_name,))
                        modified_exists = cur.fetchone()
                        
                        if modified_exists:
                            # Even the modified name exists, use it
                            category_ids[(body_part_name, category_name)] = modified_exists[0]
                            logger.info(f"Using existing modified category: {modified_name} (ID: {modified_exists[0]})")
                        else:
                            # Create with modified name
                            description = f"{category_name} procedures for {body_part_name}"
                            
                            cur.execute("""
                                INSERT INTO categories (name, description, body_part_id, popularity_score, created_at)
                                VALUES (%s, %s, %s, %s, %s)
                                RETURNING id
                            """, (modified_name, description, body_part_id, 50, datetime.utcnow()))
                            
                            category_id = cur.fetchone()[0]
                            category_ids[(body_part_name, category_name)] = category_id
                            logger.info(f"Added category with modified name: {modified_name} under {body_part_name} (ID: {category_id})")
                    else:
                        # Create new category with original name
                        description = f"{category_name} procedures for {body_part_name}"
                        
                        cur.execute("""
                            INSERT INTO categories (name, description, body_part_id, popularity_score, created_at)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id
                        """, (category_name, description, body_part_id, 50, datetime.utcnow()))
                        
                        category_id = cur.fetchone()[0]
                        category_ids[(body_part_name, category_name)] = category_id
                        logger.info(f"Added category: {category_name} under {body_part_name} (ID: {category_id})")
                
                batch_count += 1
                if batch_count % BATCH_SIZE == 0:
                    conn.commit()
                    logger.info(f"Committed batch of {BATCH_SIZE} categories")
        
        conn.commit()
        logger.info(f"Successfully added {len(category_ids)} categories")
        return category_ids
    except Exception as e:
        logger.error(f"Error adding categories: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return {}
    finally:
        if 'conn' in locals() and conn:
            conn.close()

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

def add_procedures_batch(category_ids, start_index=0, batch_size=BATCH_SIZE):
    """Add procedures from the CSV in batches."""
    if not os.path.exists(PROCEDURES_CSV) or not category_ids:
        logger.error(f"Procedures CSV file not found or no categories added")
        return 0, False, start_index
    
    try:
        conn = get_db_connection()
        if not conn:
            return 0, False, start_index
        
        # Load all procedures from CSV
        all_procedures = []
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                all_procedures.append(row)
        
        total_procedures = len(all_procedures)
        if start_index >= total_procedures:
            logger.info(f"No more procedures to process. Total procedures: {total_procedures}")
            return 0, True, total_procedures  # No more procedures to process
        
        # Process this batch
        end_index = min(start_index + batch_size, total_procedures)
        current_batch = all_procedures[start_index:end_index]
        
        logger.info(f"Processing procedures batch {start_index} to {end_index-1} of {total_procedures}")
        
        # Add procedures in this batch
        procedures_added = 0
        with conn.cursor() as cur:
            for row in current_batch:
                # Get essential fields
                body_part_name = row.get('body_part_name', '').strip()
                category_name = row.get('category_name', '').strip()
                procedure_name = row.get('procedure_name', '').strip()
                
                # Skip if essential fields are missing
                if not procedure_name or not body_part_name or not category_name:
                    logger.warning(f"Missing essential fields for procedure: {procedure_name}")
                    continue
                
                # Get category ID
                category_key = (body_part_name, category_name)
                if category_key not in category_ids:
                    logger.warning(f"Category not found for procedure: {category_name} under {body_part_name}")
                    continue
                
                category_id = category_ids[category_key]
                
                # Check if procedure already exists
                cur.execute("SELECT id FROM procedures WHERE procedure_name = %s", (procedure_name,))
                result = cur.fetchone()
                
                if result:
                    # Procedure already exists
                    logger.info(f"Procedure already exists: {procedure_name} (ID: {result[0]})")
                    continue
                
                # Clean cost values
                min_cost = clean_integer(row.get('min_cost', '0'))
                max_cost = clean_integer(row.get('max_cost', '0'))
                
                # Create new procedure
                cur.execute("""
                    INSERT INTO procedures (
                        procedure_name, alternative_names, short_description, overview,
                        procedure_details, ideal_candidates, recovery_process, recovery_time,
                        procedure_duration, hospital_stay_required, results_duration,
                        min_cost, max_cost, benefits, benefits_detailed, risks,
                        procedure_types, alternative_procedures, category_id, popularity_score,
                        avg_rating, review_count, body_part
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    procedure_name, 
                    row.get('alternative_names', ''),
                    row.get('short_description', ''), 
                    row.get('overview', ''),
                    row.get('procedure_details', ''), 
                    row.get('ideal_candidates', ''),
                    row.get('recovery_process', ''), 
                    row.get('recovery_time', ''),
                    row.get('procedure_duration', ''), 
                    row.get('hospital_stay_required', 'No'),
                    row.get('results_duration', ''),
                    min_cost, 
                    max_cost,
                    row.get('benefits', ''), 
                    row.get('benefits_detailed', ''),
                    row.get('risks', ''), 
                    row.get('procedure_types', ''),
                    row.get('alternative_procedures', ''), 
                    category_id,
                    50,  # popularity_score
                    round(random.uniform(4.0, 5.0), 1),  # avg_rating
                    random.randint(5, 50),  # review_count
                    body_part_name
                ))
                
                procedure_id = cur.fetchone()[0]
                logger.info(f"Added procedure: {procedure_name} (ID: {procedure_id})")
                procedures_added += 1
        
        conn.commit()
        logger.info(f"Successfully added {procedures_added} procedures in this batch")
        
        more_procedures = end_index < total_procedures
        return procedures_added, more_procedures, end_index
    except Exception as e:
        logger.error(f"Error adding procedures batch: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return 0, False, start_index
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def add_doctors_batch(start_index=0, batch_size=BATCH_SIZE):
    """Add doctors from the CSV in batches."""
    if not os.path.exists(DOCTORS_CSV):
        logger.error(f"Doctors CSV file not found: {DOCTORS_CSV}")
        return 0, False, start_index
    
    try:
        conn = get_db_connection()
        if not conn:
            return 0, False, start_index
        
        # Load all doctors from CSV
        all_doctors = []
        with open(DOCTORS_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                all_doctors.append(row)
        
        total_doctors = len(all_doctors)
        if start_index >= total_doctors:
            logger.info(f"No more doctors to process. Total doctors: {total_doctors}")
            return 0, True, total_doctors  # No more doctors to process
        
        # Get existing doctor names
        existing_doctors = set()
        with conn.cursor() as cursor:
            cursor.execute("SELECT LOWER(name) FROM doctors")
            for row in cursor.fetchall():
                if row[0]:
                    existing_doctors.add(row[0])
        
        logger.info(f"Found {len(existing_doctors)} existing doctors")
        
        # Process this batch
        end_index = min(start_index + batch_size, total_doctors)
        current_batch = all_doctors[start_index:end_index]
        
        logger.info(f"Processing doctors batch {start_index} to {end_index-1} of {total_doctors}")
        
        # Add doctors in this batch
        doctors_added = 0
        for row in current_batch:
            # Get essential fields
            doctor_name = row.get('name', '').strip()
            if not doctor_name:
                continue
                
            # Skip if doctor already exists
            if doctor_name.lower() in existing_doctors:
                logger.info(f"Doctor already exists: {doctor_name}")
                continue
            
            # Create new connection for each doctor to avoid transaction issues
            doctor_conn = get_db_connection()
            if not doctor_conn:
                continue
                
            try:
                with doctor_conn.cursor() as cursor:
                    # Create user first
                    username = doctor_name.lower().replace(' ', '_').replace('.', '')
                    email = f"{username}@example.com"
                    phone_number = row.get('phone', f"+91{random.randint(7000000000, 9999999999)}")
                    
                    cursor.execute("""
                        INSERT INTO users (
                            username, email, name, role, role_type, phone_number,
                            created_at, is_verified, password_hash
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """, (
                        username,
                        email,
                        doctor_name,
                        'doctor',
                        'doctor',
                        phone_number,
                        datetime.utcnow(),
                        True,
                        "pbkdf2:sha256:600000$default_password_hash"  # placeholder hash
                    ))
                    
                    user_id = cursor.fetchone()[0]
                    
                    # Get other doctor fields with defaults
                    specialty = row.get('specialty', 'Cosmetic Surgeon').strip()
                    experience = clean_integer(row.get('experience', random.randint(5, 20)))
                    city = row.get('city', 'Mumbai').strip()
                    consultation_fee = clean_integer(row.get('consultation_fee', 1500))
                    bio = row.get('bio', "Experienced healthcare professional specializing in cosmetic procedures.").strip()
                    
                    # Process education data
                    education_data = []
                    if row.get('education'):
                        try:
                            education_data = json.loads(row.get('education'))
                        except:
                            # Try to parse education from string
                            edu_str = row.get('education', '').strip()
                            if edu_str:
                                education_data = [{"degree": edu_str, "institution": "", "year": ""}]
                    
                    if not education_data:
                        education_data = [{"degree": "MBBS", "institution": "Medical College", "year": ""}]
                    
                    education_json = json.dumps(education_data)
                    
                    # Process certification data
                    certification_data = []
                    if row.get('certifications'):
                        try:
                            certification_data = json.loads(row.get('certifications'))
                        except:
                            cert_str = row.get('certifications', '').strip()
                            if cert_str:
                                certification_data = [{"name": cert_str, "year": ""}]
                    
                    certifications_json = json.dumps(certification_data)
                    
                    # Create doctor record
                    cursor.execute("""
                        INSERT INTO doctors (
                            user_id, name, specialty, experience, city,
                            consultation_fee, is_verified, rating, review_count, created_at,
                            bio, certifications, education, verification_status
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        user_id,
                        doctor_name,
                        specialty,
                        experience,
                        city,
                        consultation_fee,
                        True,  # is_verified
                        round(random.uniform(4.0, 5.0), 1),  # rating
                        random.randint(10, 50),  # review_count
                        datetime.utcnow(),
                        bio,
                        certifications_json,
                        education_json,
                        'approved'  # verification_status
                    ))
                    
                    doctor_conn.commit()
                    doctors_added += 1
                    existing_doctors.add(doctor_name.lower())
                    logger.info(f"Added doctor: {doctor_name}")
                    
            except Exception as e:
                logger.error(f"Error adding doctor {doctor_name}: {str(e)}")
                doctor_conn.rollback()
            finally:
                doctor_conn.close()
        
        logger.info(f"Successfully added {doctors_added} doctors in this batch")
        
        more_doctors = end_index < total_doctors
        return doctors_added, more_doctors, end_index
    except Exception as e:
        logger.error(f"Error adding doctors batch: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return 0, False, start_index
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def add_essential_banners():
    """Add essential banners."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # List of essential banner positions
        banner_positions = [
            "between_hero_stats",
            "between_treatment_categories",
            "between_popular_procedures",
            "between_top_specialists",
            "between_community_posts",
            "before_footer"
        ]
        
        # Add banners to database using direct SQL
        banners_added = 0
        with conn.cursor() as cur:
            for position_index, position in enumerate(banner_positions):
                # Check if banner already exists
                cur.execute("SELECT id FROM banners WHERE position = %s", (position,))
                result = cur.fetchone()
                
                if result:
                    # Banner already exists
                    logger.info(f"Banner already exists for position: {position} (ID: {result[0]})")
                    continue
                
                # Create new banner
                cur.execute("""
                    INSERT INTO banners (
                        position, is_active, created_at
                    ) VALUES (%s, %s, %s)
                    RETURNING id
                """, (
                    position,
                    True,
                    datetime.utcnow()
                ))
                
                banner_id = cur.fetchone()[0]
                
                # Create a slide for this banner
                title = f"Special Offers May 2025"
                content = "Limited time offers on premium cosmetic procedures. Book your consultation today!"
                
                cur.execute("""
                    INSERT INTO banner_slides (
                        banner_id, title, content, button_text, 
                        button_url, image_url, order_index, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    banner_id,
                    title,
                    content,
                    "Book Now",
                    "/promotions",
                    "/static/images/banners/default.jpg",
                    0,
                    datetime.utcnow()
                ))
                
                logger.info(f"Added banner for position: {position} (ID: {banner_id})")
                banners_added += 1
        
        conn.commit()
        logger.info(f"Successfully added {banners_added} banners")
        return True
    except Exception as e:
        logger.error(f"Error adding banners: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def add_essential_community_threads():
    """Add essential community threads."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # List of essential community threads
        essential_threads = [
            {
                "title": "Rhinoplasty Recovery Timeline",
                "content": "I'm considering getting a rhinoplasty but I'm worried about the recovery time. How long did it take others to feel comfortable going back to work or social events? Any tips for speeding up recovery?",
                "tags": "rhinoplasty,recovery,advice",
                "username": "beauty_seeker"
            },
            {
                "title": "Best age for facelift?",
                "content": "I've been noticing more sagging in my face and I'm wondering if I should consider a facelift now or wait a few more years. I'm 45 - is this too early? What are the pros and cons of getting it done sooner vs later?",
                "tags": "facelift,age,advice",
                "username": "ageless_wonder"
            },
            {
                "title": "Botox for the first time - what to expect?",
                "content": "I'm planning on getting Botox for the first time next month for my forehead lines. What should I expect during the procedure? How long will it last? Any side effects I should be prepared for?",
                "tags": "botox,first-time,expectations",
                "username": "eternal_youth"
            },
            {
                "title": "Liposuction vs non-surgical alternatives",
                "content": "I've been trying to lose stubborn fat in my abdomen area with diet and exercise, but it's not working well. I'm considering liposuction but I've also heard about non-surgical alternatives. Has anyone tried both? Which one gave better results?",
                "tags": "liposuction,non-surgical,comparison",
                "username": "fitness_journey"
            },
            {
                "title": "Hair transplant in India - doctor recommendations?",
                "content": "I'm looking to get a hair transplant done in India. Can anyone recommend good doctors in Delhi or Mumbai? What was your experience like and how much did it cost?",
                "tags": "hair-transplant,recommendations,india",
                "username": "new_hairline"
            }
        ]
        
        # Get a valid admin user or create one
        admin_user_id = None
        with conn.cursor() as cur:
            # Check if admin user exists
            cur.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
            result = cur.fetchone()
            
            if result:
                admin_user_id = result[0]
            else:
                # Create admin user
                cur.execute("""
                    INSERT INTO users (
                        username, email, name, role, role_type, 
                        created_at, is_verified, password_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    "admin_user",
                    "admin@example.com",
                    "Admin User",
                    'admin',
                    'admin',
                    datetime.utcnow(),
                    True,
                    "pbkdf2:sha256:600000$default_password_hash"  # placeholder hash
                ))
                admin_user_id = cur.fetchone()[0]
                logger.info(f"Created admin user (ID: {admin_user_id})")
        
        # Add community threads
        threads_added = 0
        with conn.cursor() as cur:
            for thread in essential_threads:
                # Check if thread already exists
                cur.execute("SELECT id FROM community_threads WHERE title = %s", (thread["title"],))
                result = cur.fetchone()
                
                if result:
                    # Thread already exists
                    logger.info(f"Thread already exists: {thread['title']} (ID: {result[0]})")
                    continue
                
                # Create user for this thread if needed
                cur.execute("SELECT id FROM users WHERE username = %s", (thread["username"],))
                result = cur.fetchone()
                
                user_id = None
                if result:
                    user_id = result[0]
                else:
                    # Create user
                    cur.execute("""
                        INSERT INTO users (
                            username, email, name, role, role_type, 
                            created_at, is_verified, password_hash
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        thread["username"],
                        f"{thread['username']}@example.com",
                        thread["username"].replace('_', ' ').title(),
                        'user',
                        'user',
                        datetime.utcnow(),
                        True,
                        "pbkdf2:sha256:600000$default_password_hash"  # placeholder hash
                    ))
                    user_id = cur.fetchone()[0]
                    logger.info(f"Created user {thread['username']} (ID: {user_id})")
                
                # Create new thread
                cur.execute("""
                    INSERT INTO community_threads (
                        title, content, tags, user_id, 
                        upvotes, is_approved, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    thread["title"],
                    thread["content"],
                    thread["tags"],
                    user_id,
                    random.randint(5, 50),  # upvotes
                    True,  # is_approved
                    datetime.utcnow()
                ))
                
                thread_id = cur.fetchone()[0]
                
                # Add a reply to the thread
                cur.execute("""
                    INSERT INTO community_replies (
                        thread_id, user_id, content, 
                        upvotes, is_approved, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    thread_id,
                    admin_user_id,
                    "Thank you for sharing your question with our community. This is a common concern many patients have. I recommend consulting with a board-certified specialist who can provide personalized advice for your situation.",
                    random.randint(2, 20),  # upvotes
                    True,  # is_approved
                    datetime.utcnow()
                ))
                
                logger.info(f"Added community thread: {thread['title']} (ID: {thread_id})")
                threads_added += 1
        
        conn.commit()
        logger.info(f"Successfully added {threads_added} community threads")
        return True
    except Exception as e:
        logger.error(f"Error adding community threads: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def main():
    """Main function to import data with checkpoint capability."""
    logger.info("Starting resumable database import...")
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    
    try:
        # Step 1: Add body parts if not done
        if not checkpoint['body_parts_done']:
            logger.info("Step 1: Adding body parts...")
            body_part_ids = add_body_parts_batch()
            if body_part_ids:
                checkpoint['body_parts_done'] = True
                checkpoint['body_part_ids'] = body_part_ids
                save_checkpoint(checkpoint)
            else:
                logger.error("Failed to add body parts")
                return False
        
        # Step 2: Add categories if not done
        if not checkpoint['categories_done']:
            logger.info("Step 2: Adding categories...")
            category_ids = add_categories_batch(checkpoint['body_part_ids'])
            if category_ids:
                checkpoint['categories_done'] = True
                checkpoint['category_ids'] = category_ids
                save_checkpoint(checkpoint)
            else:
                logger.error("Failed to add categories")
                return False
        
        # Step 3: Add procedures in batches
        logger.info(f"Step 3: Adding procedures starting from index {checkpoint['procedures_index']}...")
        
        procedures_batches_processed = 0
        while procedures_batches_processed < MAX_BATCHES_PER_RUN:
            added, done, new_index = add_procedures_batch(
                checkpoint['category_ids'], 
                checkpoint['procedures_index']
            )
            
            if added > 0:
                checkpoint['procedures_index'] = new_index
                save_checkpoint(checkpoint)
            
            procedures_batches_processed += 1
            
            if done:
                logger.info("All procedures have been imported")
                break
            
            # Add a small delay to avoid overloading the database
            time.sleep(0.5)
        
        # Step 4: Add doctors in batches
        logger.info(f"Step 4: Adding doctors starting from index {checkpoint['doctors_index']}...")
        
        doctors_batches_processed = 0
        while doctors_batches_processed < MAX_BATCHES_PER_RUN:
            added, done, new_index = add_doctors_batch(checkpoint['doctors_index'])
            
            if added > 0:
                checkpoint['doctors_index'] = new_index
                save_checkpoint(checkpoint)
            
            doctors_batches_processed += 1
            
            if done:
                logger.info("All doctors have been imported")
                break
            
            # Add a small delay to avoid overloading the database
            time.sleep(0.5)
        
        # Step 5: Add banners if not done
        if not checkpoint['banners_done']:
            logger.info("Step 5: Adding banners...")
            if add_essential_banners():
                checkpoint['banners_done'] = True
                save_checkpoint(checkpoint)
            else:
                logger.warning("Failed to add banners")
        
        # Step 6: Add community threads if not done
        if not checkpoint['community_done']:
            logger.info("Step 6: Adding community threads...")
            if add_essential_community_threads():
                checkpoint['community_done'] = True
                save_checkpoint(checkpoint)
            else:
                logger.warning("Failed to add community threads")
        
        # Check if everything is done
        all_done = (
            checkpoint['body_parts_done'] and
            checkpoint['categories_done'] and
            checkpoint['banners_done'] and
            checkpoint['community_done']
        )
        
        if all_done:
            logger.info("All data has been imported successfully")
        else:
            logger.info(f"Partial import completed. Current progress: {checkpoint}")
            logger.info("Run the script again to continue importing data")
        
        return True
    except Exception as e:
        logger.error(f"Error in main import process: {str(e)}")
        return False

if __name__ == "__main__":
    main()