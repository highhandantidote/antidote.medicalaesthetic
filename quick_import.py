#!/usr/bin/env python3
"""
Quick Database Import Script

This script quickly adds essential data to get the site working.
It focuses on adding the most important records without timing out.
"""

import os
import csv
import json
import logging
import psycopg2
import random
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths to the latest CSV files
PROCEDURES_CSV = "attached_assets/new_procedure_details - Sheet1.csv"
DOCTORS_CSV = "attached_assets/new_doctors_profiles2 - Sheet1.csv"

# Batch size for imports to avoid timeouts
BATCH_SIZE = 5

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def add_popular_body_parts():
    """Add just the most popular body parts."""
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        
        # List of most important body parts
        important_body_parts = [
            "Face", "Body", "Nose", "Breasts", "Skin", 
            "Hair", "Eyes", "Lips", "Jawline", "Chin"
        ]
        
        # Add body parts to database using direct SQL
        body_part_ids = {}
        with conn.cursor() as cur:
            for body_part_name in important_body_parts:
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
        
        conn.commit()
        logger.info(f"Added {len(body_part_ids)} essential body parts")
        return body_part_ids
    except Exception as e:
        logger.error(f"Error adding body parts: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return {}
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def add_popular_categories(body_part_ids):
    """Add just the most popular categories."""
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        
        # List of important categories with their body parts
        important_categories = [
            {"name": "Facial Rejuvenation", "body_part": "Face"},
            {"name": "Rhinoplasty", "body_part": "Nose"},
            {"name": "Breast Surgery", "body_part": "Breasts"},
            {"name": "Body Contouring", "body_part": "Body"},
            {"name": "Skin Treatments", "body_part": "Skin"},
            {"name": "Hair Restoration", "body_part": "Hair"},
            {"name": "Eyelid Surgery", "body_part": "Eyes"},
            {"name": "Lip Augmentation", "body_part": "Lips"},
            {"name": "Chin Augmentation", "body_part": "Chin"},
            {"name": "Jawline Contouring", "body_part": "Jawline"}
        ]
        
        # Add categories to database using direct SQL
        category_ids = {}
        with conn.cursor() as cur:
            for category in important_categories:
                body_part_name = category["body_part"]
                category_name = category["name"]
                
                # Skip if body part doesn't exist
                if body_part_name not in body_part_ids:
                    logger.warning(f"Body part not found for category: {body_part_name} - {category_name}")
                    continue
                
                body_part_id = body_part_ids[body_part_name]
                
                # Check if category already exists
                cur.execute(
                    "SELECT id FROM categories WHERE name = %s AND body_part_id = %s",
                    (category_name, body_part_id)
                )
                result = cur.fetchone()
                
                if result:
                    # Category already exists
                    category_ids[(body_part_name, category_name)] = result[0]
                    logger.info(f"Category already exists: {category_name} under {body_part_name} (ID: {result[0]})")
                else:
                    # Try alternative names if needed
                    alternative_name = f"{category_name} ({body_part_name})"
                    try:
                        # Create new category
                        description = f"{category_name} procedures for {body_part_name}"
                        
                        cur.execute("""
                            INSERT INTO categories (name, description, body_part_id, popularity_score, created_at)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id
                        """, (category_name, description, body_part_id, 80, datetime.utcnow()))
                        
                        category_id = cur.fetchone()[0]
                        category_ids[(body_part_name, category_name)] = category_id
                        logger.info(f"Added category: {category_name} under {body_part_name} (ID: {category_id})")
                    except Exception as e:
                        logger.warning(f"Could not add category {category_name}, trying alternative name: {str(e)}")
                        
                        # Try with alternative name
                        try:
                            cur.execute("""
                                INSERT INTO categories (name, description, body_part_id, popularity_score, created_at)
                                VALUES (%s, %s, %s, %s, %s)
                                RETURNING id
                            """, (alternative_name, description, body_part_id, 80, datetime.utcnow()))
                            
                            category_id = cur.fetchone()[0]
                            category_ids[(body_part_name, category_name)] = category_id
                            logger.info(f"Added category with alternative name: {alternative_name} under {body_part_name} (ID: {category_id})")
                        except Exception as e2:
                            logger.error(f"Could not add category with alternative name either: {str(e2)}")
        
        conn.commit()
        logger.info(f"Added {len(category_ids)} essential categories")
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

def add_essential_procedures(category_ids):
    """Add a fixed set of essential procedures."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # List of essential procedures
        essential_procedures = [
            {
                "name": "Rhinoplasty",
                "body_part": "Nose",
                "category": "Rhinoplasty",
                "description": "Surgical reshaping of the nose to improve appearance or breathing",
                "min_cost": 80000,
                "max_cost": 200000
            },
            {
                "name": "Facelift",
                "body_part": "Face",
                "category": "Facial Rejuvenation",
                "description": "Surgical procedure to reduce sagging skin and wrinkles",
                "min_cost": 100000,
                "max_cost": 300000
            },
            {
                "name": "Botox Injections",
                "body_part": "Face",
                "category": "Facial Rejuvenation",
                "description": "Injectable treatment to temporarily reduce facial wrinkles",
                "min_cost": 15000,
                "max_cost": 30000
            },
            {
                "name": "Breast Augmentation",
                "body_part": "Breasts",
                "category": "Breast Surgery",
                "description": "Surgical enhancement of breast size and shape",
                "min_cost": 120000,
                "max_cost": 300000
            },
            {
                "name": "Liposuction",
                "body_part": "Body",
                "category": "Body Contouring",
                "description": "Surgical removal of excess fat to reshape specific areas",
                "min_cost": 70000,
                "max_cost": 200000
            },
            {
                "name": "Hair Transplantation",
                "body_part": "Hair",
                "category": "Hair Restoration",
                "description": "Surgical redistribution of hair follicles to restore hair growth",
                "min_cost": 80000,
                "max_cost": 250000
            },
            {
                "name": "Blepharoplasty",
                "body_part": "Eyes",
                "category": "Eyelid Surgery",
                "description": "Surgical repair of droopy eyelids by removing excess skin",
                "min_cost": 60000,
                "max_cost": 150000
            },
            {
                "name": "Lip Fillers",
                "body_part": "Lips",
                "category": "Lip Augmentation",
                "description": "Injectable gel to enhance lip volume and shape",
                "min_cost": 20000,
                "max_cost": 50000
            },
            {
                "name": "Chemical Peel",
                "body_part": "Skin",
                "category": "Skin Treatments",
                "description": "Application of chemical solution to improve skin appearance",
                "min_cost": 15000,
                "max_cost": 50000
            },
            {
                "name": "Chin Implant",
                "body_part": "Chin",
                "category": "Chin Augmentation",
                "description": "Surgical placement of an implant to enhance chin projection",
                "min_cost": 60000,
                "max_cost": 150000
            }
        ]
        
        # Add procedures to database
        procedures_added = 0
        with conn.cursor() as cur:
            for proc in essential_procedures:
                body_part_name = proc["body_part"]
                category_name = proc["category"]
                
                # Skip if essential mappings are missing
                category_key = (body_part_name, category_name)
                if category_key not in category_ids:
                    logger.warning(f"Category mapping not found for {category_name} under {body_part_name}")
                    continue
                
                category_id = category_ids[category_key]
                
                # Check if procedure already exists
                cur.execute("SELECT id FROM procedures WHERE procedure_name = %s", (proc["name"],))
                result = cur.fetchone()
                
                if result:
                    # Procedure already exists
                    logger.info(f"Procedure already exists: {proc['name']} (ID: {result[0]})")
                    continue
                
                # Create procedure
                try:
                    cur.execute("""
                        INSERT INTO procedures (
                            procedure_name, short_description, min_cost, max_cost,
                            category_id, popularity_score, avg_rating, review_count,
                            body_part, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        proc["name"],
                        proc["description"],
                        proc["min_cost"],
                        proc["max_cost"],
                        category_id,
                        80,  # popularity_score
                        round(random.uniform(4.0, 5.0), 1),  # avg_rating
                        random.randint(10, 50),  # review_count
                        body_part_name,
                        datetime.utcnow()
                    ))
                    
                    procedure_id = cur.fetchone()[0]
                    logger.info(f"Added procedure: {proc['name']} (ID: {procedure_id})")
                    procedures_added += 1
                except Exception as e:
                    logger.error(f"Error adding procedure {proc['name']}: {str(e)}")
        
        conn.commit()
        logger.info(f"Added {procedures_added} essential procedures")
        return True
    except Exception as e:
        logger.error(f"Error adding procedures: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def add_essential_doctors():
    """Add a fixed set of essential doctors."""
    try:
        conn = get_db_connection()
        if not conn:
            return 0
        
        # List of essential doctors
        essential_doctors = [
            {"name": "Dr. Anand Sharma", "specialty": "Cosmetic Surgeon", "city": "Mumbai"},
            {"name": "Dr. Bhavna Patel", "specialty": "Plastic Surgeon", "city": "Delhi"},
            {"name": "Dr. Chetan Desai", "specialty": "Facial Plastic Surgeon", "city": "Bengaluru"},
            {"name": "Dr. Divya Agarwal", "specialty": "Aesthetic Surgeon", "city": "Chennai"},
            {"name": "Dr. Eshan Gupta", "specialty": "Plastic Surgeon", "city": "Hyderabad"}
        ]
        
        # Get existing doctor names
        existing_doctors = []
        with conn.cursor() as cursor:
            cursor.execute("SELECT LOWER(name) FROM doctors")
            existing_doctors = [row[0] for row in cursor.fetchall() if row[0]]
        
        logger.info(f"Found {len(existing_doctors)} existing doctors")
        
        # Add doctors
        doctors_added = 0
        for doctor in essential_doctors:
            # Skip if doctor already exists
            if doctor["name"].lower() in existing_doctors:
                logger.info(f"Doctor already exists: {doctor['name']}")
                continue
                
            # Create user first
            username = doctor["name"].lower().replace(' ', '_').replace('.', '')
            email = f"{username}@example.com"
            phone_number = f"+91{random.randint(7000000000, 9999999999)}"
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (
                        username, email, name, role, role_type, phone_number,
                        created_at, is_verified, password_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (
                    username,
                    email,
                    doctor["name"],
                    'doctor',
                    'doctor',
                    phone_number,
                    datetime.utcnow(),
                    True,
                    "pbkdf2:sha256:600000$default_password_hash"  # placeholder hash
                ))
                
                user_id = cursor.fetchone()[0]
                
                # Create doctor profile
                education = json.dumps([{"degree": "MBBS", "institution": "Medical College", "year": ""}])
                certifications = json.dumps([])
                
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
                    doctor["name"],
                    doctor["specialty"],
                    random.randint(5, 20),  # experience
                    doctor["city"],
                    1500,  # consultation_fee
                    True,  # is_verified
                    round(random.uniform(4.0, 5.0), 1),  # rating
                    random.randint(10, 50),  # review_count
                    datetime.utcnow(),
                    "Experienced healthcare professional specializing in cosmetic procedures.",  # bio
                    certifications,
                    education,
                    'approved'  # verification_status
                ))
                
                doctors_added += 1
                existing_doctors.append(doctor["name"].lower())
                logger.info(f"Added doctor: {doctor['name']}")
        
        conn.commit()
        logger.info(f"Added {doctors_added} essential doctors")
        return doctors_added
    except Exception as e:
        logger.error(f"Error adding doctors: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return 0
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def add_essential_banners():
    """Add essential banners for each position."""
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
        
        # Add banners
        banners_added = 0
        for position in banner_positions:
            # Check if banner already exists
            with conn.cursor() as cur:
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
        logger.info(f"Added {banners_added} essential banners")
        return True
    except Exception as e:
        logger.error(f"Error adding banners: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def add_community_thread():
    """Add one essential community thread."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # First, check if we already have threads
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM community_threads")
            count = cur.fetchone()[0]
            
            if count > 0:
                logger.info(f"Already have {count} community threads, skipping")
                return True
        
        # Create an admin user if needed
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
        
        # Create a community user
        user_id = None
        with conn.cursor() as cur:
            # Create user
            username = "beauty_seeker"
            cur.execute("""
                INSERT INTO users (
                    username, email, name, role, role_type, 
                    created_at, is_verified, password_hash
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                username,
                f"{username}@example.com",
                "Beauty Seeker",
                'user',
                'user',
                datetime.utcnow(),
                True,
                "pbkdf2:sha256:600000$default_password_hash"  # placeholder hash
            ))
            user_id = cur.fetchone()[0]
            logger.info(f"Created user {username} (ID: {user_id})")
        
        # Create thread
        with conn.cursor() as cur:
            # Create thread
            thread_title = "Rhinoplasty Recovery Timeline"
            thread_content = """I'm considering getting a rhinoplasty but I'm worried about the recovery time. 
            How long did it take others to feel comfortable going back to work or social events? 
            Any tips for speeding up recovery?"""
            
            cur.execute("""
                INSERT INTO community_threads (
                    title, content, tags, user_id, 
                    upvotes, is_approved, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                thread_title,
                thread_content,
                "rhinoplasty,recovery,advice",
                user_id,
                random.randint(5, 50),  # upvotes
                True,  # is_approved
                datetime.utcnow()
            ))
            
            thread_id = cur.fetchone()[0]
            
            # Add a reply
            cur.execute("""
                INSERT INTO community_replies (
                    thread_id, user_id, content, 
                    upvotes, is_approved, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                thread_id,
                admin_user_id,
                """Thank you for sharing your question with our community. 
                Most patients can return to work after 1-2 weeks, though you'll still have some swelling.
                Full recovery can take up to a year, but the most noticeable swelling subsides within the first month.
                I recommend consulting with a board-certified specialist who can provide personalized advice for your situation.""",
                random.randint(2, 20),  # upvotes
                True,  # is_approved
                datetime.utcnow()
            ))
            
            logger.info(f"Added community thread: {thread_title} (ID: {thread_id})")
        
        conn.commit()
        logger.info("Added essential community thread")
        return True
    except Exception as e:
        logger.error(f"Error adding community thread: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def main():
    """Main function to import essential data quickly."""
    logger.info("Starting quick data import...")
    
    # Check which stage we're at by checking counts in DB
    conn = get_db_connection()
    if not conn:
        logger.error("Could not connect to database")
        return False
    
    try:
        with conn.cursor() as cur:
            # Check procedure count
            cur.execute("SELECT COUNT(*) FROM procedures")
            procedure_count = cur.fetchone()[0]
            
            # Check doctor count
            cur.execute("SELECT COUNT(*) FROM doctors")
            doctor_count = cur.fetchone()[0]
            
            # Check banner count
            cur.execute("SELECT COUNT(*) FROM banners")
            banner_count = cur.fetchone()[0]
            
            # Check community thread count
            cur.execute("SELECT COUNT(*) FROM community_threads")
            thread_count = cur.fetchone()[0]
            
            logger.info(f"Current counts - Procedures: {procedure_count}, Doctors: {doctor_count}, Banners: {banner_count}, Threads: {thread_count}")
    except Exception as e:
        logger.error(f"Error checking database counts: {str(e)}")
        procedure_count = 0
        doctor_count = 0
        banner_count = 0
        thread_count = 0
    finally:
        if conn:
            conn.close()
    
    # Step 1: Add body parts
    logger.info("Step 1: Adding essential body parts...")
    body_part_ids = add_popular_body_parts()
    if not body_part_ids:
        logger.error("Failed to add body parts")
        return False
    
    # Step 2: Add categories
    logger.info("Step 2: Adding essential categories...")
    category_ids = add_popular_categories(body_part_ids)
    if not category_ids:
        logger.error("Failed to add categories")
        return False
    
    # Step 3: Add procedures if needed
    if procedure_count < 5:
        logger.info("Step 3: Adding essential procedures...")
        if not add_essential_procedures(category_ids):
            logger.error("Failed to add procedures")
            return False
    else:
        logger.info(f"Skipping procedures, already have {procedure_count}")
    
    # Step 4: Add doctors if needed
    if doctor_count < 3:
        logger.info("Step 4: Adding essential doctors...")
        new_doctor_count = add_essential_doctors()
        logger.info(f"Added {new_doctor_count} doctors")
    else:
        logger.info(f"Skipping doctors, already have {doctor_count}")
    
    # Step 5: Add banners if needed
    if banner_count < 3:
        logger.info("Step 5: Adding essential banners...")
        if not add_essential_banners():
            logger.warning("Failed to add banners")
    else:
        logger.info(f"Skipping banners, already have {banner_count}")
    
    # Step 6: Add community thread if needed
    if thread_count < 1:
        logger.info("Step 6: Adding essential community thread...")
        if not add_community_thread():
            logger.warning("Failed to add community thread")
    else:
        logger.info(f"Skipping community threads, already have {thread_count}")
    
    logger.info("Quick data import completed successfully!")
    return True

if __name__ == "__main__":
    main()