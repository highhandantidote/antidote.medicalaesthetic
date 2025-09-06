#!/usr/bin/env python3
"""
Quick Database Restore Script

This script quickly adds essential data to the Antidote database
focusing only on the most important elements.
"""

import os
import logging
import psycopg2
import random
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def add_essential_body_parts():
    """Add essential body parts to get the app working."""
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        
        # List of essential body parts with descriptions
        essential_body_parts = [
            {"name": "Face", "description": "Procedures related to the face", "icon_url": "/static/images/body_parts/face.svg"},
            {"name": "Body", "description": "Procedures related to the body", "icon_url": "/static/images/body_parts/body.svg"},
            {"name": "Skin", "description": "Procedures related to the skin", "icon_url": "/static/images/body_parts/skin.svg"},
            {"name": "Hair", "description": "Procedures related to hair restoration", "icon_url": "/static/images/body_parts/hair.svg"},
            {"name": "Nose", "description": "Procedures related to the nose", "icon_url": "/static/images/body_parts/nose.svg"},
            {"name": "Breasts", "description": "Procedures related to the breasts", "icon_url": "/static/images/body_parts/breasts.svg"},
            {"name": "Eyes", "description": "Procedures related to the eyes", "icon_url": "/static/images/body_parts/eyes.svg"},
            {"name": "Lips", "description": "Procedures related to the lips", "icon_url": "/static/images/body_parts/lips.svg"},
        ]
        
        # Add body parts to database using direct SQL
        body_part_ids = {}
        with conn.cursor() as cur:
            for body_part in essential_body_parts:
                # Check if body part already exists
                cur.execute("SELECT id FROM body_parts WHERE name = %s", (body_part["name"],))
                result = cur.fetchone()
                
                if result:
                    # Body part already exists
                    body_part_ids[body_part["name"]] = result[0]
                    logger.info(f"Body part already exists: {body_part['name']} (ID: {result[0]})")
                else:
                    # Create new body part
                    cur.execute("""
                        INSERT INTO body_parts (name, description, icon_url, created_at)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (body_part["name"], body_part["description"], body_part["icon_url"], datetime.utcnow()))
                    
                    body_part_id = cur.fetchone()[0]
                    body_part_ids[body_part["name"]] = body_part_id
                    logger.info(f"Added body part: {body_part['name']} (ID: {body_part_id})")
        
        conn.commit()
        logger.info(f"Successfully added {len(body_part_ids)} body parts")
        return body_part_ids
    except Exception as e:
        logger.error(f"Error adding body parts: {str(e)}")
        if conn:
            conn.rollback()
        return {}
    finally:
        if conn:
            conn.close()

def add_essential_categories(body_part_ids):
    """Add essential categories to get the app working."""
    if not body_part_ids:
        logger.error("No body parts added")
        return {}
    
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        
        # List of essential categories
        essential_categories = [
            {"name": "Facial Rejuvenation", "body_part": "Face", "description": "Procedures to restore youthful appearance to the face"},
            {"name": "Facial Contouring", "body_part": "Face", "description": "Procedures to enhance facial shape and contours"},
            {"name": "Rhinoplasty", "body_part": "Nose", "description": "Nose surgery procedures"},
            {"name": "Skin Treatments", "body_part": "Skin", "description": "Non-invasive skin enhancement procedures"},
            {"name": "Anti-Aging", "body_part": "Skin", "description": "Procedures to combat signs of aging"},
            {"name": "Body Contouring", "body_part": "Body", "description": "Procedures to enhance body shape"},
            {"name": "Hair Restoration", "body_part": "Hair", "description": "Procedures to restore hair growth"},
            {"name": "Breast Surgery", "body_part": "Breasts", "description": "Surgical procedures for the breasts"},
            {"name": "Eye Surgery", "body_part": "Eyes", "description": "Procedures focused on the eye area"},
            {"name": "Lip Procedures", "body_part": "Lips", "description": "Treatments to enhance lips"}
        ]
        
        # Add categories to database using direct SQL
        category_ids = {}
        with conn.cursor() as cur:
            for category in essential_categories:
                # Skip if body part doesn't exist
                if category["body_part"] not in body_part_ids:
                    logger.warning(f"Body part not found for category: {category['body_part']} - {category['name']}")
                    continue
                
                body_part_id = body_part_ids[category["body_part"]]
                
                # Check if category already exists
                cur.execute(
                    "SELECT id FROM categories WHERE name = %s AND body_part_id = %s",
                    (category["name"], body_part_id)
                )
                result = cur.fetchone()
                
                if result:
                    # Category already exists
                    category_ids[(category["body_part"], category["name"])] = result[0]
                    logger.info(f"Category already exists: {category['name']} under {category['body_part']} (ID: {result[0]})")
                else:
                    # Create new category
                    cur.execute("""
                        INSERT INTO categories (name, description, body_part_id, popularity_score, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (category["name"], category["description"], body_part_id, 50, datetime.utcnow()))
                    
                    category_id = cur.fetchone()[0]
                    category_ids[(category["body_part"], category["name"])] = category_id
                    logger.info(f"Added category: {category['name']} under {category['body_part']} (ID: {category_id})")
        
        conn.commit()
        logger.info(f"Successfully added {len(category_ids)} categories")
        return category_ids
    except Exception as e:
        logger.error(f"Error adding categories: {str(e)}")
        if conn:
            conn.rollback()
        return {}
    finally:
        if conn:
            conn.close()

def add_essential_procedures(category_ids):
    """Add essential procedures to get the app working."""
    if not category_ids:
        logger.error("No categories added")
        return False
    
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # List of essential procedures with minimal data
        essential_procedures = [
            {
                "name": "Rhinoplasty", 
                "body_part": "Nose", 
                "category": "Rhinoplasty",
                "short_description": "Surgical reshaping of the nose to improve appearance or breathing",
                "min_cost": 80000,
                "max_cost": 200000
            },
            {
                "name": "Facelift", 
                "body_part": "Face", 
                "category": "Facial Rejuvenation",
                "short_description": "Surgical procedure to reduce sagging skin and wrinkles",
                "min_cost": 100000,
                "max_cost": 300000
            },
            {
                "name": "Botox Injections", 
                "body_part": "Face", 
                "category": "Anti-Aging",
                "short_description": "Injectable treatment to temporarily reduce facial wrinkles",
                "min_cost": 15000,
                "max_cost": 30000
            },
            {
                "name": "Dermal Fillers", 
                "body_part": "Face", 
                "category": "Facial Contouring",
                "short_description": "Injectable gel to restore volume and smooth wrinkles",
                "min_cost": 20000,
                "max_cost": 50000
            },
            {
                "name": "Liposuction", 
                "body_part": "Body", 
                "category": "Body Contouring",
                "short_description": "Surgical removal of excess fat to reshape specific areas",
                "min_cost": 70000,
                "max_cost": 200000
            },
            {
                "name": "Breast Augmentation", 
                "body_part": "Breasts", 
                "category": "Breast Surgery",
                "short_description": "Surgical enhancement of breast size and shape",
                "min_cost": 120000,
                "max_cost": 300000
            },
            {
                "name": "Hair Transplantation", 
                "body_part": "Hair", 
                "category": "Hair Restoration",
                "short_description": "Surgical redistribution of hair follicles to restore hair growth",
                "min_cost": 80000,
                "max_cost": 250000
            },
            {
                "name": "Blepharoplasty", 
                "body_part": "Eyes", 
                "category": "Eye Surgery",
                "short_description": "Surgical repair of droopy eyelids by removing excess skin",
                "min_cost": 60000,
                "max_cost": 150000
            },
            {
                "name": "Lip Augmentation", 
                "body_part": "Lips", 
                "category": "Lip Procedures",
                "short_description": "Procedure to enhance lip fullness and shape",
                "min_cost": 25000,
                "max_cost": 70000
            },
            {
                "name": "Chemical Peel", 
                "body_part": "Skin", 
                "category": "Skin Treatments",
                "short_description": "Application of chemical solution to improve skin appearance",
                "min_cost": 15000,
                "max_cost": 50000
            }
        ]
        
        # Add procedures to database using direct SQL
        procedures_added = 0
        with conn.cursor() as cur:
            for procedure in essential_procedures:
                # Create key for category lookup
                category_key = (procedure["body_part"], procedure["category"])
                
                # Skip if category doesn't exist
                if category_key not in category_ids:
                    logger.warning(f"Category not found for procedure: {category_key}")
                    continue
                
                category_id = category_ids[category_key]
                
                # Check if procedure already exists
                cur.execute("SELECT id FROM procedures WHERE procedure_name = %s", (procedure["name"],))
                result = cur.fetchone()
                
                if result:
                    # Procedure already exists
                    logger.info(f"Procedure already exists: {procedure['name']} (ID: {result[0]})")
                    continue
                
                # Create new procedure with minimal data
                cur.execute("""
                    INSERT INTO procedures (
                        procedure_name, short_description, 
                        min_cost, max_cost, category_id, 
                        popularity_score, avg_rating, review_count,
                        body_part, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    procedure["name"],
                    procedure["short_description"],
                    procedure["min_cost"],
                    procedure["max_cost"],
                    category_id,
                    50,  # popularity_score
                    4.5,  # avg_rating
                    random.randint(10, 50),  # review_count
                    procedure["body_part"],
                    datetime.utcnow()
                ))
                
                procedure_id = cur.fetchone()[0]
                logger.info(f"Added procedure: {procedure['name']} (ID: {procedure_id})")
                procedures_added += 1
        
        conn.commit()
        logger.info(f"Successfully added {procedures_added} procedures")
        return True
    except Exception as e:
        logger.error(f"Error adding procedures: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def add_essential_banners():
    """Add essential banners to get the app working."""
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
                title = f"Promotional Banner {position_index + 1}"
                content = "Special offers on cosmetic procedures. Contact us today!"
                
                cur.execute("""
                    INSERT INTO banner_slides (
                        banner_id, title, content, button_text, 
                        button_url, image_url, order_index, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    banner_id,
                    title,
                    content,
                    "Learn More",
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
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def add_more_doctors():
    """Add more essential doctors to get the app working."""
    doctors = [
        {"name": "Dr. Priya Sharma", "specialty": "Cosmetic Surgeon", "city": "Mumbai"},
        {"name": "Dr. Rajesh Patel", "specialty": "Plastic Surgeon", "city": "Delhi"},
        {"name": "Dr. Sunita Desai", "specialty": "Facial Plastic Surgeon", "city": "Bengaluru"},
        {"name": "Dr. Vikram Agarwal", "specialty": "Aesthetic Surgeon", "city": "Chennai"},
        {"name": "Dr. Meera Gupta", "specialty": "Plastic Surgeon", "city": "Hyderabad"},
        {"name": "Dr. Sanjay Mehta", "specialty": "Cosmetic Dermatologist", "city": "Pune"},
        {"name": "Dr. Kavita Singh", "specialty": "Plastic Surgeon", "city": "Kolkata"},
        {"name": "Dr. Arjun Khan", "specialty": "Aesthetic Surgeon", "city": "Ahmedabad"},
        {"name": "Dr. Nisha Ali", "specialty": "Plastic Surgeon", "city": "Jaipur"},
        {"name": "Dr. Deepak Naidu", "specialty": "Facial Plastic Surgeon", "city": "Lucknow"}
    ]
    
    try:
        # Get existing doctor names
        conn = get_db_connection()
        if not conn:
            return 0
            
        existing_doctors = []
        with conn.cursor() as cursor:
            cursor.execute("SELECT LOWER(name) FROM doctors")
            existing_doctors = [row[0] for row in cursor.fetchall() if row[0]]
        
        logger.info(f"Found {len(existing_doctors)} existing doctors")
        
        # Add doctors
        added_count = 0
        
        for doctor in doctors:
            # Skip if doctor already exists
            if doctor["name"].lower() in existing_doctors:
                logger.info(f"Doctor {doctor['name']} already exists. Skipping.")
                continue
                
            # Create user
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
                education = '[{"degree": "MBBS", "institution": "Medical College", "year": ""}]'
                certifications = '[]'
                
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
                
                added_count += 1
                existing_doctors.append(doctor["name"].lower())
                logger.info(f"Added doctor: {doctor['name']}")
        
        conn.commit()
        
        # Get final count
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM doctors")
            final_count = cursor.fetchone()[0]
            logger.info(f"Final doctor count: {final_count}")
        
        return added_count
    except Exception as e:
        logger.error(f"Error adding doctors: {str(e)}")
        if conn:
            conn.rollback()
        return 0
    finally:
        if conn:
            conn.close()

def add_essential_community_threads():
    """Add essential community threads to get the app working."""
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
                
                # Check if thread already exists
                cur.execute("SELECT id FROM community_threads WHERE title = %s", (thread["title"],))
                result = cur.fetchone()
                
                if result:
                    # Thread already exists
                    logger.info(f"Thread already exists: {thread['title']} (ID: {result[0]})")
                    continue
                
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
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function to restore essential data."""
    logger.info("Starting quick database restoration...")
    
    # Step 1: Add body parts
    logger.info("Step 1: Adding essential body parts...")
    body_part_ids = add_essential_body_parts()
    if not body_part_ids:
        logger.error("Failed to add body parts")
        return False
    
    # Step 2: Add categories
    logger.info("Step 2: Adding essential categories...")
    category_ids = add_essential_categories(body_part_ids)
    if not category_ids:
        logger.error("Failed to add categories")
        return False
    
    # Step 3: Add procedures
    logger.info("Step 3: Adding essential procedures...")
    if not add_essential_procedures(category_ids):
        logger.error("Failed to add procedures")
        return False
    
    # Step 4: Add banners
    logger.info("Step 4: Adding essential banners...")
    if not add_essential_banners():
        logger.warning("Failed to add banners")
        # Continue despite banner failures
    
    # Step 5: Add more doctors
    logger.info("Step 5: Adding essential doctors...")
    doctor_count = add_more_doctors()
    logger.info(f"Added {doctor_count} doctors")
    
    # Step 6: Add community threads
    logger.info("Step 6: Adding essential community threads...")
    if not add_essential_community_threads():
        logger.warning("Failed to add community threads")
        # Continue despite community thread failures
    
    logger.info("Quick database restoration completed successfully")
    return True

if __name__ == "__main__":
    main()