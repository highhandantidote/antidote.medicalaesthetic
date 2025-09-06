"""
Process exactly 10 threads at a time to add replies.
This script handles a limited batch to avoid connection timeouts.
"""
import os
import logging
import psycopg2
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection string from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

# Constants
BATCH_SIZE = 10
MIN_REPLIES = 2
MAX_REPLIES = 3

# Valid user IDs from the database
PATIENT_USER_IDS = [147, 148, 149, 150, 151, 152]  # patientuser1, patientuser2, testuser, etc.
DOCTOR_USER_IDS = [14, 15, 17, 21, 22, 23]  # Various doctor IDs

# Sample reply templates
REPLY_TEMPLATES = [
    "I had this procedure done recently and can share my experience. The recovery was manageable with proper post-op care. Follow your doctor's instructions carefully for best results.",
    "From a medical perspective, this procedure typically requires about 2-3 weeks of recovery. I recommend taking it easy and avoiding strenuous activities during this time.",
    "The results were excellent. I noticed final results after about 3 months when all swelling resolved. Definitely worth the recovery time.",
    "Having performed many similar procedures, I can tell you that patient satisfaction is high when expectations are realistic. Follow-up care is important.",
    "I researched extensively before getting it done. Finding a board-certified specialist made all the difference in my results.",
    "Thanks for sharing your experience. I'm considering this too and appreciate hearing real patient stories.",
    "The recovery was better than I expected. The first week was challenging but improved quickly after that.",
    "As a doctor who specializes in this area, I recommend discussing all concerns with your surgeon before the procedure. Communication is key to good outcomes."
]

def get_db_connection():
    """Get a connection to the database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Use transactions for safety
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def get_threads_without_replies():
    """Get exactly 10 threads with no replies."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.title
                FROM community c
                WHERE NOT EXISTS (
                    SELECT 1 FROM community_replies cr 
                    WHERE cr.thread_id = c.id
                )
                ORDER BY c.id DESC
                LIMIT %s
            """, (BATCH_SIZE,))
            
            threads = [(row[0], row[1]) for row in cursor.fetchall()]
            logger.info(f"Found {len(threads)} threads with no replies")
            
        conn.close()
        return threads
    except Exception as e:
        logger.error(f"Error getting threads without replies: {str(e)}")
        if conn:
            conn.close()
        return []

def get_max_reply_id():
    """Get the maximum reply ID currently in the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) FROM community_replies")
            result = cursor.fetchone()
            max_id = result[0] if result and result[0] is not None else 0
            
        conn.close()
        return max_id
    except Exception as e:
        logger.error(f"Error getting max reply ID: {str(e)}")
        if conn:
            conn.close()
        return 0

def add_replies_to_thread(thread_id, thread_title, last_reply_id):
    """Add 2-3 replies to a specific thread."""
    conn = None
    try:
        conn = get_db_connection()
        
        # Decide number of replies (2-3)
        num_replies = random.randint(MIN_REPLIES, MAX_REPLIES)
        logger.info(f"Adding {num_replies} replies to thread {thread_id}: '{thread_title}'")
        
        # Create dates within last 2 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        date_range = (end_date - start_date).days
        reply_dates = [start_date + timedelta(days=random.randint(0, date_range)) for _ in range(num_replies)]
        reply_dates.sort()  # Sort chronologically
        
        # Add replies
        with conn.cursor() as cursor:
            for i in range(num_replies):
                # Determine if this should be a doctor reply
                is_doctor = random.random() < 0.25
                user_id = random.choice(DOCTOR_USER_IDS if is_doctor else PATIENT_USER_IDS)
                
                # Create reply
                reply_id = last_reply_id + i + 1
                cursor.execute("""
                    INSERT INTO community_replies 
                    (id, thread_id, content, user_id, created_at, is_expert_advice, is_doctor_response, upvotes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    reply_id, 
                    thread_id, 
                    random.choice(REPLY_TEMPLATES), 
                    user_id, 
                    reply_dates[i],
                    is_doctor,
                    is_doctor,
                    random.randint(0, 5)
                ))
            
            # Update the reply_count in the community table
            cursor.execute("""
                UPDATE community 
                SET reply_count = %s 
                WHERE id = %s
            """, (num_replies, thread_id))
            
        conn.commit()
        conn.close()
        logger.info(f"Successfully added {num_replies} replies to thread {thread_id}")
        return num_replies
        
    except Exception as e:
        logger.error(f"Error adding replies to thread {thread_id}: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return 0

def check_progress():
    """Check progress toward the target of 125 threads with 2-4 replies."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT thread_id, COUNT(*) as reply_count 
                    FROM community_replies 
                    GROUP BY thread_id 
                    HAVING COUNT(*) BETWEEN 2 AND 4
                ) AS threads_with_replies
            """)
            
            threads_with_2_4_replies = cursor.fetchone()[0]
            threads_needed = max(0, 125 - threads_with_2_4_replies)
            
            logger.info(f"Progress: {threads_with_2_4_replies}/125 threads with 2-4 replies")
            logger.info(f"Need {threads_needed} more threads to reach target")
            
            conn.close()
            return threads_needed
    except Exception as e:
        logger.error(f"Error checking progress: {str(e)}")
        if conn:
            conn.close()
        return -1

def process_batch():
    """Process exactly 10 threads to add replies to each."""
    # Get the current max reply ID
    last_reply_id = get_max_reply_id()
    logger.info(f"Current max reply ID: {last_reply_id}")
    
    # Get threads without replies
    threads = get_threads_without_replies()
    if not threads:
        logger.warning("No threads found without replies")
        return 0
    
    # Process each thread
    threads_processed = 0
    replies_added = 0
    
    for thread_id, title in threads:
        next_reply_id = last_reply_id + replies_added
        num_added = add_replies_to_thread(thread_id, title, next_reply_id)
        
        if num_added > 0:
            threads_processed += 1
            replies_added += num_added
    
    # Check our progress
    remaining = check_progress()
    
    logger.info(f"Batch complete: added replies to {threads_processed} threads")
    logger.info(f"Added {replies_added} total replies")
    
    if remaining <= 0:
        logger.info("✅ TASK COMPLETE: At least 125 threads have 2-4 replies!")
    
    return threads_processed

if __name__ == "__main__":
    process_batch()