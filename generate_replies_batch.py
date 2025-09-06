#!/usr/bin/env python3
"""
Generate community thread replies in small batches.

This script:
1. Processes a small batch of threads (25 at a time)
2. Adds 2-4 replies to each thread
3. Preserves all existing data

Usage:
    python generate_replies_batch.py [batch_number]

Example:
    python generate_replies_batch.py 1  # Process first batch of 25 threads
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
        logging.FileHandler(f"generate_replies_batch.log"),
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

DOCTOR_USERS = [
    {"username": "doctor_kumar", "email": "drkumar@example.com", "role": "doctor", "phone_number": "+919876543207", "name": "Dr. Kumar"},
    {"username": "dr.sharma", "email": "dr.sharma@antidote.com", "role": "doctor", "phone_number": "+919876543208", "name": "Dr. Sharma"},
    {"username": "dr.patel", "email": "dr.patel@antidote.com", "role": "doctor", "phone_number": "+919876543209", "name": "Dr. Patel"},
]

# Reply templates
REPLY_TEMPLATES = {
    "patient": [
        "I had {procedure} about 6 months ago, and my experience was similar to what you're describing. The swelling took about 3-4 weeks to go down significantly, but I noticed subtle changes for up to 3 months. Arnica gel helped a lot with the bruising. Don't worry, it gets better!",
        
        "My recovery from {procedure} was pretty smooth. The first week was the hardest, but after that, things improved quickly. I followed all my doctor's instructions carefully, which I think made a big difference. Make sure you have someone to help you for at least the first 3-4 days.",
        
        "I went to Dr. {doctor} for my {procedure} and had a great experience. The results exceeded my expectations, and the staff was incredibly supportive throughout the process. The cost was on the higher end, but worth every rupee in my opinion.",
        
        "I had some asymmetry issues after my {procedure} too. I panicked at first, but my surgeon assured me that some asymmetry is normal and that final results take time. Sure enough, by month 4, things had evened out considerably. Try to be patient!",
        
        "I researched {procedure} for almost a year before taking the plunge. The most important factors for me were the surgeon's experience with this specific procedure and before/after photos of their work. Don't just go with the cheapest option - this is your body we're talking about!"
    ],
    "doctor": [
        "As a plastic surgeon who specializes in {procedure}, I can tell you that what you're experiencing is completely normal. Swelling typically peaks at 48-72 hours post-operation and gradually subsides over 2-3 weeks. Some residual swelling can persist for up to 6 months, especially in the morning. Continue following your surgeon's post-operative care instructions.",
        
        "Regarding your question about technique options for {procedure}, both open and closed approaches have their advantages. The open technique allows for more precise work and is generally preferred for complex cases, while the closed technique results in less visible scarring. Your surgeon should recommend the appropriate technique based on your specific anatomy and aesthetic goals.",
        
        "The price variation you're seeing for {procedure} likely reflects differences in surgeon experience, facility fees, anesthesia type, and geographic location. While cost is a factor, the surgeon's expertise with this specific procedure should be your primary consideration. Ask to see before and after photos of patients with similar concerns to yours.",
        
        "Post-operative asymmetry after {procedure} is not uncommon and often resolves as swelling subsides. However, if significant asymmetry persists beyond 6 months, a follow-up with your surgeon is appropriate. Minor revisions are sometimes necessary, but I recommend waiting at least 6-12 months before considering revision surgery.",
        
        "Exercise restrictions after {procedure} are not arbitrary - they're designed to protect your results and prevent complications. Resuming strenuous activity too soon can lead to increased swelling, bleeding, or compromised results. Even if you feel good, internal healing takes time. Consider gentle walking as an alternative until you reach the 6-week mark."
    ]
}

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
    """Get user accounts."""
    user_ids = {}
    
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
                    user_ids[user["email"]] = user_id
                else:
                    logger.warning(f"User {user['username']} not found")
        
        logger.info(f"Found {len(user_ids)} {role} users")
        return user_ids
    except Exception as e:
        logger.error(f"Error getting {role} users: {str(e)}")
        return {}

def get_threads_to_reply(conn, batch_number=1, batch_size=25):
    """Get a batch of threads to add replies to."""
    threads = []
    
    try:
        # Calculate offset
        offset = (batch_number - 1) * batch_size
        
        # Get the newest threads that don't have replies yet
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.content, c.created_at, c.procedure_id, c.reply_count,
                       p.procedure_name, u.username, u.email
                FROM community c
                JOIN users u ON c.user_id = u.id
                JOIN procedures p ON c.procedure_id = p.id
                WHERE c.reply_count = 0
                ORDER BY c.id DESC
                LIMIT %s OFFSET %s
            """, (batch_size, offset))
            
            threads = [dict(row) for row in cursor.fetchall()]
        
        logger.info(f"Found {len(threads)} threads to add replies to in batch {batch_number}")
        return threads
    except Exception as e:
        logger.error(f"Error getting threads to reply: {str(e)}")
        return []

def create_thread_replies(conn, threads, patient_user_ids, doctor_user_ids):
    """Create replies for each thread."""
    replies = []
    
    # Get the current max ID
    current_max_id = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) FROM community_replies")
            result = cursor.fetchone()
            if result and result[0]:
                current_max_id = result[0]
            logger.info(f"Current max reply ID: {current_max_id}")
    except Exception as e:
        logger.error(f"Error getting max ID: {str(e)}")
        return []
    
    start_id = current_max_id + 1  # Start from the next available ID
    reply_count = 0
    
    try:
        batch_replies = []
        batch_values = []
        thread_reply_counts = {}
        
        for thread in threads:
            thread_id = thread["id"]
            procedure_name = thread["procedure_name"]
            thread_date = thread["created_at"]
            if isinstance(thread_date, str):
                thread_date = datetime.strptime(thread_date, "%Y-%m-%d")
            
            # Generate 2-4 replies per thread
            num_replies = random.randint(2, 4)
            thread_replies = []
            parent_ids = {}  # To track references for CSV
            
            for j in range(num_replies):
                # Determine if this is a doctor reply (25% chance)
                is_doctor = random.random() < 0.25
                
                if is_doctor:
                    # Doctor reply
                    user_email = random.choice(list(doctor_user_ids.keys()))
                    user_id = doctor_user_ids[user_email]
                    is_expert_advice = True
                    is_doctor_response = True
                    content = random.choice(REPLY_TEMPLATES["doctor"]).format(
                        procedure=procedure_name,
                        doctor=random.choice(["Sharma", "Patel", "Kumar", "Gupta", "Reddy"])
                    )
                    
                    # Get username
                    username = ""
                    for user in DOCTOR_USERS:
                        if user["email"] == user_email:
                            username = user["username"]
                            break
                else:
                    # Patient reply
                    user_email = random.choice(list(patient_user_ids.keys()))
                    user_id = patient_user_ids[user_email]
                    is_expert_advice = False
                    is_doctor_response = False
                    content = random.choice(REPLY_TEMPLATES["patient"]).format(
                        procedure=procedure_name,
                        doctor=random.choice(["Sharma", "Patel", "Kumar", "Gupta", "Reddy"])
                    )
                    
                    # Get username
                    username = ""
                    for user in PATIENT_USERS:
                        if user["email"] == user_email:
                            username = user["username"]
                            break
                
                # Generate reply date (1-10 days after thread or previous reply)
                if j == 0:
                    # First reply is 1-5 days after thread creation
                    days_after = random.randint(1, 5)
                    reply_date = thread_date + timedelta(days=days_after)
                else:
                    # Subsequent replies are 1-3 days after previous reply
                    prev_reply_date = thread_replies[-1]["created_at"]
                    if isinstance(prev_reply_date, str):
                        prev_reply_date = datetime.strptime(prev_reply_date, "%Y-%m-%d")
                    days_after = random.randint(1, 3)
                    reply_date = prev_reply_date + timedelta(days=days_after)
                
                # Ensure reply date is not after May 15, 2025
                if reply_date > datetime(2025, 5, 15):
                    reply_date = datetime(2025, 5, 15)
                
                # Determine parent reply (20% chance for nested reply after first reply)
                parent_reply_id = None
                parent_reference = None
                if j > 0 and random.random() < 0.2:
                    prev_reply_id = start_id + reply_count - 1  # ID of the previous reply
                    parent_reply_id = prev_reply_id
                    parent_reference = f"r{j}"  # Reference to previous reply
                
                # Create reply data
                reply_id = start_id + reply_count
                reply_data = {
                    "id": reply_id,
                    "thread_id": thread_id,
                    "content": content,
                    "username": username,
                    "email": user_email,
                    "user_role": "doctor" if is_doctor else "patient",
                    "parent_reply_id": parent_reply_id,
                    "created_at": reply_date,
                    "is_expert_advice": "true" if is_expert_advice else "false",
                    "reference": f"r{j+1}"  # r1, r2, etc.
                }
                
                # Add to batch values for SQL insertion
                batch_values.append((
                    reply_id,
                    thread_id,
                    user_id,
                    parent_reply_id,
                    is_expert_advice,
                    False,  # is_ai_response
                    False,  # is_anonymous
                    is_doctor_response,
                    reply_date,
                    random.randint(0, 15),  # upvotes
                    content
                ))
                
                parent_ids[f"r{j+1}"] = reply_id  # Store for CSV parent references
                thread_replies.append(reply_data)
                batch_replies.append(reply_data)
                reply_count += 1
            
            # Update references with actual IDs
            for reply in thread_replies:
                if reply["parent_reply_id"] is not None and reply.get("parent_reference"):
                    parent_ref = reply["parent_reference"]
                    if parent_ref in parent_ids:
                        reply["parent_reply_id"] = parent_ids[parent_ref]
            
            # Track reply count for thread
            thread_reply_counts[thread_id] = num_replies
        
        # Insert batch of replies
        with conn.cursor() as cursor:
            args_str = ','.join(cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", x).decode('utf-8') 
                              for x in batch_values)
            if args_str:  # Only execute if we have replies to add
                cursor.execute(f"""
                    INSERT INTO community_replies (
                        id, thread_id, user_id, parent_reply_id, is_expert_advice,
                        is_ai_response, is_anonymous, is_doctor_response, created_at,
                        upvotes, content
                    ) VALUES {args_str}
                """)
            
            # Update thread reply counts
            for thread_id, count in thread_reply_counts.items():
                cursor.execute(
                    "UPDATE community SET reply_count = %s WHERE id = %s",
                    (count, thread_id)
                )
        
        conn.commit()
        replies.extend(batch_replies)
        logger.info(f"Created {len(batch_replies)} replies for {len(threads)} threads")
        
        return replies
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating thread replies: {str(e)}")
        return []

def export_to_csv(replies):
    """Export replies to CSV file."""
    try:
        # Create directory for output files
        output_dir = Path("community_data")
        output_dir.mkdir(exist_ok=True)
        
        # Export replies
        reply_fields = [
            "thread_id", "content", "username", "email", "user_role",
            "parent_reply_id", "created_at", "is_expert_advice", "reference"
        ]
        
        # Check if we need to merge with existing file
        reply_csv_path = output_dir / "Community_Replies.csv"
        existing_replies = []
        if reply_csv_path.exists():
            try:
                with open(reply_csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    existing_replies = list(reader)
                logger.info(f"Found {len(existing_replies)} existing replies in CSV")
            except Exception as e:
                logger.warning(f"Error reading existing CSV: {str(e)}")
        
        # Write all replies
        with open(reply_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=reply_fields)
            writer.writeheader()
            
            # Write existing replies
            for reply in existing_replies:
                writer.writerow(reply)
                
            # Write new replies
            for reply in replies:
                # Convert datetime to string if needed
                if isinstance(reply["created_at"], datetime):
                    reply["created_at"] = reply["created_at"].strftime("%Y-%m-%d")
                    
                writer.writerow({k: reply[k] for k in reply_fields if k in reply})
        
        logger.info(f"Exported {len(replies)} replies to {reply_csv_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        return False

def main():
    """Main function to generate community replies for a batch of threads."""
    # Get batch number from command line
    batch_number = 1
    if len(sys.argv) > 1:
        try:
            batch_number = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid batch number. Using default (1).")
    
    logger.info(f"=== Starting community replies generation for batch {batch_number} ===")
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return 1
    
    try:
        # Get user IDs
        patient_user_ids = get_or_create_users(conn, PATIENT_USERS, "patient")
        doctor_user_ids = get_or_create_users(conn, DOCTOR_USERS, "doctor")
        
        if not patient_user_ids or not doctor_user_ids:
            logger.error("Failed to get user IDs")
            return 1
        
        # Get threads to reply to for this batch
        threads = get_threads_to_reply(conn, batch_number=batch_number)
        if not threads:
            logger.error(f"No threads found for batch {batch_number}")
            return 1
        
        # Count existing data
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM community_replies")
            reply_count_before = cursor.fetchone()[0]
            logger.info(f"Before: {reply_count_before} replies")
        
        # Create replies
        replies = create_thread_replies(conn, threads, patient_user_ids, doctor_user_ids)
        if not replies:
            logger.error("Failed to create thread replies")
            return 1
        
        # Count final data
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM community_replies")
            reply_count_after = cursor.fetchone()[0]
            logger.info(f"After: {reply_count_after} replies")
            logger.info(f"Added: {reply_count_after - reply_count_before} replies")
        
        # Export to CSV
        export_to_csv(replies)
        
        logger.info(f"=== Community replies generation for batch {batch_number} completed successfully ===")
        return 0
    except Exception as e:
        logger.error(f"Error during community replies generation: {str(e)}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())