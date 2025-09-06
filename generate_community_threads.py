#!/usr/bin/env python3
"""
Generate community threads for the Antidote platform.

This script:
1. Creates patient and doctor user accounts if they don't exist
2. Generates 125 community threads with realistic topics and content
3. Preserves all existing data

Usage:
    python generate_community_threads.py
"""
import os
import sys
import csv
import json
import random
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from pathlib import Path
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("generate_community_threads.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PATIENT_USERS = [
    {"username": "patientuser1", "email": "patient1@example.com", "role": "patient", "phone_number": "+919876543201", "name": "Patient User 1"},
    {"username": "patientuser2", "email": "patient2@example.com", "role": "patient", "phone_number": "+919876543202", "name": "Patient User 2"},
    {"username": "testuser", "email": "test@example.com", "role": "patient", "phone_number": "+919876543203", "name": "Test User"},
    {"username": "patient1", "email": "patient1@antidote.com", "role": "patient", "phone_number": "+919876543204", "name": "Patient One"},
    {"username": "patient2", "email": "patient2@antidote.com", "role": "patient", "phone_number": "+919876543205", "name": "Patient Two"},
    {"username": "patient3", "email": "patient3@antidote.com", "role": "patient", "phone_number": "+919876543206", "name": "Patient Three"},
]

# Thread topics by procedure
THREAD_TOPICS = {
    "Rhinoplasty": [
        "Recovery after Rhinoplasty - what to expect?",
        "Rhinoplasty swelling - how long does it last?",
        "Post-operative care for Rhinoplasty patients",
        "Pain management after Rhinoplasty",
        "When will I see final results after Rhinoplasty?"
    ],
    "Breast Augmentation": [
        "Breast Augmentation recovery - what to expect?",
        "Choosing the right implant size for Breast Augmentation",
        "Post-operative care after Breast Augmentation",
        "Massage techniques after Breast Augmentation",
        "Exercise restrictions after Breast Augmentation"
    ],
    "Liposuction": [
        "Liposuction recovery - what to expect?",
        "Compression garments after Liposuction - how long to wear?",
        "Dealing with swelling after Liposuction",
        "When can I exercise after Liposuction?",
        "Liposuction vs. non-surgical alternatives"
    ],
    "Tummy Tuck": [
        "Tummy Tuck recovery timeline",
        "Pain management after Tummy Tuck",
        "Sleeping positions after Tummy Tuck",
        "When can I exercise after Tummy Tuck?",
        "Tummy Tuck vs. Liposuction - which is right for me?"
    ],
    "Brazilian Butt Lift": [
        "Brazilian Butt Lift recovery - what to expect?",
        "Sitting restrictions after Brazilian Butt Lift",
        "How long do BBL results last?",
        "Fat survival rate after Brazilian Butt Lift",
        "BBL vs. butt implants - pros and cons"
    ],
    "General": [
        "How to choose the right plastic surgeon?",
        "Questions to ask during your consultation",
        "Preparing for plastic surgery",
        "Recovery essentials after plastic surgery",
        "Managing expectations in plastic surgery",
        "Plastic surgery abroad - pros and cons",
        "Financing options for plastic surgery",
        "How to tell if you're ready for plastic surgery",
        "Discussing plastic surgery with family and friends",
        "Non-surgical alternatives to plastic surgery"
    ]
}

# Thread content templates
THREAD_CONTENT_TEMPLATES = [
    "Hi everyone, I'm considering getting {procedure} and I'm a bit nervous about the recovery process. Can anyone share their experience? How long did it take you to feel normal again? What was the pain level like? Any tips for making recovery easier? Thanks in advance for any advice!",
    
    "I recently had {procedure} (2 weeks ago) and I'm experiencing quite a bit of swelling and bruising. My doctor says this is normal, but I wanted to check with others who've gone through this. How long did your swelling last? Did you do anything specific that helped reduce it faster? I'm using ice packs and keeping my head elevated as advised.",
    
    "I'm researching {procedure} and trying to understand the different techniques available. I've heard terms like 'open' and 'closed' techniques, but I'm not sure what's best for my situation. Could those who've had this procedure share what technique your surgeon used and why? What were the pros and cons in your experience?",
    
    "Cost question about {procedure} - I've been quoted a wide range of prices from different surgeons for the same procedure. The difference is substantial (almost $3000 between the lowest and highest). What factors should I consider besides cost? Is it always better to go with the more expensive surgeon? What was your experience with pricing?",
    
    "I'm 3 months post-op from my {procedure} and starting to worry about my results. My right side seems different from my left, and I'm not sure if this is just normal asymmetry or something I should be concerned about. How long should I wait before considering a revision? Did anyone else experience uneven results that improved over time?"
]

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return None
            
        logger.info(f"Connecting to database: {db_url[:20]}...")
        conn = psycopg2.connect(db_url)
        logger.info("Connected to database successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def get_or_create_users(conn, users, role):
    """Get or create user accounts."""
    user_ids = {}
    default_password_hash = generate_password_hash("Password123")
    
    try:
        with conn.cursor() as cursor:
            for user in users:
                # Check if user exists
                cursor.execute(
                    "SELECT id FROM users WHERE email = %s",
                    (user["email"],)
                )
                result = cursor.fetchone()
                
                if result:
                    user_id = result[0]
                    logger.info(f"User {user['username']} already exists with ID {user_id}")
                else:
                    # Create new user
                    cursor.execute(
                        """
                        INSERT INTO users (
                            username, email, role, password_hash, created_at, 
                            is_verified, points, phone_number, name
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            user["username"],
                            user["email"],
                            role,
                            default_password_hash,
                            datetime.now(),
                            True,
                            100,  # Default points
                            user["phone_number"],
                            user["name"]
                        )
                    )
                    user_id = cursor.fetchone()[0]
                    logger.info(f"Created new user {user['username']} with ID {user_id}")
                
                user_ids[user["email"]] = user_id
        
        conn.commit()
        logger.info(f"Successfully processed {len(user_ids)} {role} users")
        return user_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating {role} users: {str(e)}")
        return {}

def get_procedures(conn):
    """Get procedure IDs and names."""
    procedures = {}
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, procedure_name FROM procedures LIMIT 50")
            for procedure_id, procedure_name in cursor.fetchall():
                procedures[procedure_id] = procedure_name
        
        logger.info(f"Found {len(procedures)} procedures")
        return procedures
    except Exception as e:
        logger.error(f"Error getting procedures: {str(e)}")
        return {}

def generate_thread_content(procedure_name):
    """Generate realistic thread content for a procedure."""
    if procedure_name in THREAD_TOPICS:
        title = random.choice(THREAD_TOPICS[procedure_name])
    else:
        title = random.choice(THREAD_TOPICS["General"])
    
    content = random.choice(THREAD_CONTENT_TEMPLATES).format(procedure=procedure_name)
    
    return {
        "title": title,
        "content": content
    }

def random_date(start_date, end_date):
    """Generate a random date between start_date and end_date."""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_days)

def create_community_threads(conn, patient_user_ids, procedures, thread_count=125):
    """Create community threads."""
    threads = []
    
    # Get the current max ID
    current_max_id = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) FROM community")
            result = cursor.fetchone()
            if result and result[0]:
                current_max_id = result[0]
            logger.info(f"Current max thread ID: {current_max_id}")
    except Exception as e:
        logger.error(f"Error getting max ID: {str(e)}")
        return []
    
    start_id = current_max_id + 1  # Start from the next available ID
    
    # Date range from March 15, 2025 to May 15, 2025
    start_date = datetime(2025, 3, 15)
    end_date = datetime(2025, 5, 15)
    
    try:
        # Process threads in batches of 25
        batch_size = 25
        for batch in range(0, thread_count, batch_size):
            logger.info(f"Processing batch {batch//batch_size + 1}/{(thread_count+batch_size-1)//batch_size}")
            
            # Prepare batch data
            batch_values = []
            batch_threads = []
            
            for i in range(batch, min(batch + batch_size, thread_count)):
                # Select random user and procedure
                user_email = random.choice(list(patient_user_ids.keys()))
                user_id = patient_user_ids[user_email]
                procedure_id = random.choice(list(procedures.keys()))
                procedure_name = procedures[procedure_id]
                
                # Generate thread content
                thread_data = generate_thread_content(procedure_name)
                
                # Generate random date
                created_at = random_date(start_date, end_date)
                
                # Generate random view count (50-300)
                view_count = random.randint(50, 300)
                
                # Generate tags
                tags = [t.strip() for t in procedure_name.lower().split()]
                if len(tags) < 3:  # Add more tags if needed
                    additional_tags = ["recovery", "results", "pain", "swelling", "cost", 
                                     "surgeon", "clinic", "before and after", "consultation"]
                    tags.extend(random.sample(additional_tags, random.randint(1, 3)))
                
                # Add to batch values
                batch_values.append((
                    start_id + i,
                    user_id,
                    thread_data["title"],
                    thread_data["content"],
                    procedure_id,
                    created_at,
                    created_at,
                    view_count,
                    0,  # Will update this after adding replies
                    tags
                ))
                
                # Get username for CSV
                username = ""
                for user in PATIENT_USERS:
                    if user["email"] == user_email:
                        username = user["username"]
                        break
                
                # Add to threads list for CSV and replies
                batch_threads.append({
                    "id": start_id + i,
                    "title": thread_data["title"],
                    "content": thread_data["content"],
                    "username": username,
                    "email": user_email,
                    "user_role": "patient",
                    "procedure_name": procedure_name,
                    "view_count": view_count,
                    "reply_count": 0,  # Will update this
                    "keywords": ", ".join(tags),
                    "created_at": created_at.strftime("%Y-%m-%d"),
                    "user_id": user_id,
                    "procedure_id": procedure_id
                })
            
            # Insert batch
            with conn.cursor() as cursor:
                args_str = ','.join(cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", x).decode('utf-8') for x in batch_values)
                cursor.execute(f"""
                    INSERT INTO community (
                        id, user_id, title, content, procedure_id, created_at, 
                        updated_at, view_count, reply_count, tags
                    ) VALUES {args_str}
                """)
            
            conn.commit()
            threads.extend(batch_threads)
            logger.info(f"Created {len(batch_threads)} threads in batch {batch//batch_size + 1}")
        
        logger.info(f"Successfully created {len(threads)} community threads")
        return threads
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating community threads: {str(e)}")
        return []

def export_to_csv(threads):
    """Export threads to CSV file."""
    try:
        # Create directory for output files
        output_dir = Path("community_data")
        output_dir.mkdir(exist_ok=True)
        
        # Export threads
        thread_fields = [
            "title", "content", "username", "email", "user_role", 
            "procedure_name", "view_count", "reply_count", "keywords",
            "created_at"
        ]
        
        thread_csv_path = output_dir / "Community_Threads.csv"
        with open(thread_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=thread_fields)
            writer.writeheader()
            for thread in threads:
                writer.writerow({k: thread[k] for k in thread_fields})
        
        logger.info(f"Exported {len(threads)} threads to {thread_csv_path}")
        
        # Create empty replies file
        reply_fields = [
            "thread_id", "content", "username", "email", "user_role",
            "parent_reply_id", "created_at", "is_expert_advice", "reference"
        ]
        
        reply_csv_path = output_dir / "Community_Replies.csv"
        with open(reply_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=reply_fields)
            writer.writeheader()
        
        logger.info(f"Created empty replies file at {reply_csv_path}")
        
        # Save thread IDs for later reply generation
        with open(output_dir / "thread_ids.json", 'w', encoding='utf-8') as f:
            json.dump([t["id"] for t in threads], f)
        
        return True
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        return False

def main():
    """Main function to generate community threads."""
    logger.info("=== Starting community threads generation ===")
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return 1
    
    try:
        # Create or get patient users
        patient_user_ids = get_or_create_users(conn, PATIENT_USERS, "patient")
        
        if not patient_user_ids:
            logger.error("Failed to create or get patient users")
            return 1
        
        # Get procedures
        procedures = get_procedures(conn)
        if not procedures:
            logger.error("Failed to get procedures")
            return 1
        
        # Count existing data
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM community")
            thread_count_before = cursor.fetchone()[0]
            logger.info(f"Before: {thread_count_before} threads")
        
        # Create threads
        threads = create_community_threads(conn, patient_user_ids, procedures, thread_count=125)
        if not threads:
            logger.error("Failed to create community threads")
            return 1
        
        # Count final data
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM community")
            thread_count_after = cursor.fetchone()[0]
            logger.info(f"After: {thread_count_after} threads")
            logger.info(f"Added: {thread_count_after - thread_count_before} threads")
        
        # Export to CSV
        export_to_csv(threads)
        
        logger.info("=== Community threads generation completed successfully ===")
        return 0
    except Exception as e:
        logger.error(f"Error during community threads generation: {str(e)}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())