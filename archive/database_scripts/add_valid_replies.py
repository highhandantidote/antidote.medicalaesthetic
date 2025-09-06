"""
Add replies to community threads using valid user IDs.

This script adds 2-3 replies to threads that currently have no replies,
using valid user IDs from the database.
"""
import os
import logging
import random
import psycopg2
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
BATCH_SIZE = 10  # Process threads in small batches
MIN_REPLIES = 2
MAX_REPLIES = 3  # 2-3 replies per thread

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
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Use transactions
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def get_threads_without_replies(conn, limit=BATCH_SIZE):
    """Get threads that have no replies."""
    try:
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
            """, (limit,))
            
            threads = [(row[0], row[1]) for row in cursor.fetchall()]
            logger.info(f"Found {len(threads)} threads with no replies")
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

def add_replies_to_threads(batch_size=BATCH_SIZE):
    """Add replies to threads that have none."""
    conn = None
    threads_processed = 0
    
    try:
        conn = get_db_connection()
        
        # Check current progress
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT thread_id, COUNT(*) 
                    FROM community_replies
                    GROUP BY thread_id
                    HAVING COUNT(*) BETWEEN 2 AND 4
                ) AS threads_with_replies
            """)
            threads_with_2_4_replies = cursor.fetchone()[0]
            
            threads_needed = max(0, 125 - threads_with_2_4_replies)
            logger.info(f"Currently have {threads_with_2_4_replies} threads with 2-4 replies")
            logger.info(f"Need {threads_needed} more threads to reach 125 requirement")
            
            if threads_needed <= 0:
                logger.info("✅ TASK COMPLETE: At least 125 threads have 2-4 replies")
                return 0
        
        # Get threads without replies
        threads = get_threads_without_replies(conn, min(batch_size, threads_needed))
        
        if not threads:
            logger.warning("No threads found without replies")
            return 0
        
        # Get current max reply ID
        last_reply_id = get_max_reply_id(conn)
        logger.info(f"Current max reply ID: {last_reply_id}")
        
        # Track new reply ID to avoid conflicts
        next_reply_id = last_reply_id + 1
        
        # Process each thread
        for thread_id, title in threads:
            try:
                # Decide number of replies (2-3)
                num_replies = random.randint(MIN_REPLIES, MAX_REPLIES)
                logger.info(f"Adding {num_replies} replies to thread {thread_id}: '{title}'")
                
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
                        reply_id = next_reply_id + i
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
                
                next_reply_id += num_replies
                threads_processed += 1
                conn.commit()
                logger.info(f"Successfully added {num_replies} replies to thread {thread_id}")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error adding replies to thread {thread_id}: {str(e)}")
        
        # Check final progress
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT thread_id, COUNT(*) 
                    FROM community_replies
                    GROUP BY thread_id
                    HAVING COUNT(*) BETWEEN 2 AND 4
                ) AS threads_with_replies
            """)
            new_threads_with_2_4_replies = cursor.fetchone()[0]
            
            new_threads_needed = max(0, 125 - new_threads_with_2_4_replies)
            logger.info(f"Updated: Now have {new_threads_with_2_4_replies} threads with 2-4 replies")
            logger.info(f"Need {new_threads_needed} more threads to reach 125 requirement")
        
        return threads_processed
    
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        return 0
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"Error closing connection: {str(close_error)}")

def process_all_batches(max_batches=10):
    """Process multiple batches of threads to reach the goal."""
    total_processed = 0
    for batch in range(1, max_batches + 1):
        logger.info(f"Processing batch {batch}/{max_batches}...")
        processed = add_replies_to_threads()
        
        if processed == 0:
            logger.info("No more threads to process or goal reached")
            break
            
        total_processed += processed
        
    logger.info(f"Total threads processed: {total_processed}")

if __name__ == "__main__":
    process_all_batches()