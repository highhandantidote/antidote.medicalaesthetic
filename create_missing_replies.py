"""
Create missing replies for community threads.
This script prioritizes creating 2-3 replies for threads that have no replies at all.
"""
import os
import logging
import random
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection string from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

# Batch size
BATCH_SIZE = 10
MIN_REPLIES = 2
MAX_REPLIES = 3  # 2-3 replies per thread for efficiency

# Sample patient and doctor user IDs
PATIENT_USER_IDS = [1, 2, 3, 147, 148, 149]  # Will be fetched from DB
DOCTOR_USER_IDS = [4, 5, 6, 150, 151, 152]   # Will be fetched from DB

# Sample content for replies (shortened to save time)
def generate_reply_content(thread_title, procedure_name=None):
    """Generate content for a reply based on the thread and procedure."""
    procedure = procedure_name if procedure_name else "Plastic Surgery"
    replies = [
        f"I had {procedure} recently and can share my experience. The recovery was manageable with proper post-op care. Follow your doctor's instructions carefully for best results.",
        f"From a medical perspective, {procedure} typically requires about 2-3 weeks of recovery. I recommend taking it easy and avoiding strenuous activities during this time.",
        f"The results of my {procedure} were excellent. I noticed final results after about 3 months when all swelling resolved. Definitely worth the recovery time.",
        f"Having performed many {procedure} procedures, I can tell you that patient satisfaction is high when expectations are realistic. Follow-up care is important.",
        f"I researched {procedure} extensively before getting it done. Finding a board-certified specialist made all the difference in my results.",
        f"Thanks for sharing your experience with {procedure}. I'm considering it too and appreciate hearing real patient stories.",
        f"The recovery from {procedure} was better than I expected. The first week was challenging but improved quickly after that.",
        f"As a doctor who specializes in this area, I recommend discussing all concerns with your surgeon before {procedure}. Communication is key to good outcomes."
    ]
    return random.choice(replies)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Use transactions
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def get_user_ids(conn):
    """Get actual user IDs from the database."""
    global PATIENT_USER_IDS, DOCTOR_USER_IDS
    
    try:
        with conn.cursor() as cursor:
            # Get patient user IDs (role='patient' or no role specified)
            cursor.execute("""
                SELECT id FROM users 
                WHERE role = 'patient' OR role IS NULL 
                ORDER BY id
                LIMIT 10
            """)
            patients = [row[0] for row in cursor.fetchall()]
            if patients:
                PATIENT_USER_IDS = patients
                logger.info(f"Found {len(patients)} patient users")
            
            # Get doctor user IDs
            cursor.execute("""
                SELECT id FROM users 
                WHERE role = 'doctor' 
                ORDER BY id
                LIMIT 5
            """)
            doctors = [row[0] for row in cursor.fetchall()]
            if doctors:
                DOCTOR_USER_IDS = doctors
                logger.info(f"Found {len(doctors)} doctor users")
            else:
                logger.warning("No doctor users found, using default IDs")
    except Exception as e:
        logger.error(f"Error getting user IDs: {str(e)}")

def get_threads_without_any_replies(conn, limit=BATCH_SIZE):
    """Get threads that have no replies at all."""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.procedure_id,
                       (SELECT procedure_name FROM procedures WHERE id = c.procedure_id) AS procedure_name
                FROM community c
                WHERE NOT EXISTS (
                    SELECT 1 FROM community_replies cr 
                    WHERE cr.thread_id = c.id
                )
                ORDER BY c.id DESC
                LIMIT %s
            """, (limit,))
            threads = cursor.fetchall()
            
            logger.info(f"Found {len(threads)} threads with no replies at all")
            return threads
    except Exception as e:
        logger.error(f"Error getting threads without replies: {str(e)}")
        return []

def get_max_reply_id(conn):
    """Get the maximum reply ID currently in the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) FROM community_replies")
            max_id = cursor.fetchone()[0]
            return max_id if max_id is not None else 0
    except Exception as e:
        logger.error(f"Error getting max reply ID: {str(e)}")
        return 0

def create_replies_for_thread(conn, thread, last_reply_id):
    """Create 2-3 replies for a thread that has no replies."""
    try:
        thread_id = thread['id']
        title = thread['title']
        procedure_name = thread['procedure_name']
        
        # Randomly decide between 2-3 replies
        num_replies = random.randint(MIN_REPLIES, MAX_REPLIES)
        
        logger.info(f"Creating {num_replies} replies for thread {thread_id}: '{title}'")
        
        # Create dates within last 2 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # 2 months ago
        
        # Generate reply dates
        date_range = (end_date - start_date).days
        reply_dates = [start_date + timedelta(days=random.randint(0, date_range)) for _ in range(num_replies)]
        reply_dates.sort()  # Sort chronologically
        
        # Track created replies
        created_replies = []
        
        with conn.cursor() as cursor:
            for i in range(num_replies):
                # Determine if this should be a doctor reply (make ~25% from doctors)
                is_doctor = random.random() < 0.25
                user_id = random.choice(DOCTOR_USER_IDS if is_doctor else PATIENT_USER_IDS)
                
                # Generate content
                content = generate_reply_content(title, procedure_name)
                
                # Determine if this should be an expert advice (doctors always give expert advice)
                is_expert_advice = is_doctor
                
                # Create reply
                reply_id = last_reply_id + i + 1
                cursor.execute("""
                    INSERT INTO community_replies 
                    (id, thread_id, content, user_id, created_at, is_expert_advice, is_doctor_response, upvotes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    reply_id, 
                    thread_id, 
                    content, 
                    user_id, 
                    reply_dates[i],
                    is_expert_advice,
                    is_doctor,
                    random.randint(0, 5)  # Random upvotes
                ))
                
                inserted_id = cursor.fetchone()[0]
                created_replies.append(inserted_id)
            
            # Update the reply_count in the community table
            cursor.execute("""
                UPDATE community 
                SET reply_count = %s 
                WHERE id = %s
            """, (num_replies, thread_id))
        
        conn.commit()
        logger.info(f"Successfully created {len(created_replies)} replies for thread {thread_id}")
        return max(created_replies) if created_replies else last_reply_id
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating replies for thread {thread['id']}: {str(e)}")
        return last_reply_id

def check_progress(conn):
    """Check progress toward meeting task requirements."""
    try:
        with conn.cursor() as cursor:
            # Count threads with 2-4 replies
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT thread_id, COUNT(*) as reply_count
                    FROM community_replies
                    GROUP BY thread_id
                    HAVING COUNT(*) BETWEEN 2 AND 4
                ) as threads_with_replies
            """)
            threads_with_2_4_replies = cursor.fetchone()[0]
            
            threads_needed = max(0, 125 - threads_with_2_4_replies)
            logger.info(f"Currently have {threads_with_2_4_replies} threads with 2-4 replies")
            logger.info(f"Need {threads_needed} more threads to reach 125 requirement")
            
            return threads_needed
    except Exception as e:
        logger.error(f"Error checking progress: {str(e)}")
        return -1

def process_batch():
    """Process a batch of threads, creating 2-3 replies each."""
    conn = None
    try:
        conn = get_db_connection()
        
        # Check current progress
        threads_needed = check_progress(conn)
        if threads_needed <= 0:
            logger.info("✅ TASK COMPLETE: At least 125 threads have 2-4 replies")
            return 0
        
        # Get actual user IDs
        get_user_ids(conn)
        
        # Get threads without any replies
        threads_without_replies = get_threads_without_any_replies(conn, min(BATCH_SIZE, threads_needed))
        
        if not threads_without_replies:
            logger.info("No more threads found with no replies")
            return 0
        
        # Get current max reply ID
        last_reply_id = get_max_reply_id(conn)
        logger.info(f"Current max reply ID: {last_reply_id}")
        
        # Create replies for each thread in batch
        threads_fixed = 0
        for thread in threads_without_replies:
            try:
                last_reply_id = create_replies_for_thread(conn, thread, last_reply_id)
                threads_fixed += 1
            except Exception as thread_error:
                logger.error(f"Error processing thread {thread['id']}: {str(thread_error)}")
                # Continue with next thread
        
        logger.info(f"Added replies to {threads_fixed} threads")
        
        # Check final progress
        threads_needed = check_progress(conn)
        
        return threads_fixed
    
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        return 0
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"Error closing connection: {str(close_error)}")

if __name__ == "__main__":
    batch_number = 1
    total_processed = 0
    
    while True:
        logger.info(f"Processing batch {batch_number}...")
        threads_processed = process_batch()
        
        if threads_processed == 0:
            break
            
        total_processed += threads_processed
        batch_number += 1
        
        # Safety limit - process up to 20 batches (200 threads)
        if batch_number > 20:
            logger.info("Reached maximum batch limit (20 batches)")
            break
    
    logger.info(f"Total threads processed: {total_processed}")
    logger.info("Processing complete")