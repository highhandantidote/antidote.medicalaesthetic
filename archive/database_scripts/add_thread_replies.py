"""
Add replies to a specific thread ID.
This simple script adds 2-3 replies to a single thread to avoid connection issues.
"""
import os
import sys
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
MIN_REPLIES = 2
MAX_REPLIES = 3

# Sample user IDs
PATIENT_USER_IDS = [1, 2, 3, 147, 148, 149]
DOCTOR_USER_IDS = [4, 5, 6, 150, 151, 152]

def generate_reply_content():
    """Generate content for a reply."""
    replies = [
        "I had this procedure done recently and can share my experience. The recovery was manageable with proper post-op care. Follow your doctor's instructions carefully for best results.",
        "From a medical perspective, this procedure typically requires about 2-3 weeks of recovery. I recommend taking it easy and avoiding strenuous activities during this time.",
        "The results were excellent. I noticed final results after about 3 months when all swelling resolved. Definitely worth the recovery time.",
        "Having performed many similar procedures, I can tell you that patient satisfaction is high when expectations are realistic. Follow-up care is important.",
        "I researched extensively before getting it done. Finding a board-certified specialist made all the difference in my results.",
        "Thanks for sharing your experience. I'm considering this too and appreciate hearing real patient stories.",
        "The recovery was better than I expected. The first week was challenging but improved quickly after that.",
        "As a doctor who specializes in this area, I recommend discussing all concerns with your surgeon before the procedure. Communication is key to good outcomes."
    ]
    return random.choice(replies)

def add_replies_to_thread(thread_id):
    """Add 2-3 replies to a specific thread."""
    conn = None
    try:
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Use transactions
        
        # Check if thread exists
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title FROM community WHERE id = %s", (thread_id,))
            thread = cursor.fetchone()
            
            if not thread:
                logger.error(f"Thread ID {thread_id} not found")
                return False
            
            # Check if thread already has replies
            cursor.execute("SELECT COUNT(*) FROM community_replies WHERE thread_id = %s", (thread_id,))
            reply_count = cursor.fetchone()[0]
            
            if reply_count > 0:
                logger.warning(f"Thread ID {thread_id} already has {reply_count} replies")
                return False
            
            # Get max reply ID
            cursor.execute("SELECT MAX(id) FROM community_replies")
            max_id = cursor.fetchone()[0]
            last_reply_id = max_id if max_id is not None else 0
            
            # Decide number of replies (2-3)
            num_replies = random.randint(MIN_REPLIES, MAX_REPLIES)
            logger.info(f"Adding {num_replies} replies to thread {thread_id}: '{thread[1]}'")
            
            # Create dates within last 2 months
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            date_range = (end_date - start_date).days
            reply_dates = [start_date + timedelta(days=random.randint(0, date_range)) for _ in range(num_replies)]
            reply_dates.sort()
            
            # Add replies
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
                    generate_reply_content(), 
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
            logger.info(f"Successfully added {num_replies} replies to thread {thread_id}")
            return True
            
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error adding replies to thread {thread_id}: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_thread_replies.py <thread_id>")
        sys.exit(1)
    
    try:
        thread_id = int(sys.argv[1])
        success = add_replies_to_thread(thread_id)
        sys.exit(0 if success else 1)
    except ValueError:
        print("Thread ID must be an integer")
        sys.exit(1)