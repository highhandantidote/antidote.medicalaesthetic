"""
Fix community replies by adding missing replies to threads that have reply counts but no actual replies.
This batch version processes a limited number of threads to avoid timeouts.
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

# Batch processing parameters
BATCH_SIZE = 10  # Process 10 threads at a time

# Sample patient and doctor user IDs
PATIENT_USER_IDS = [1, 2, 3, 147, 148, 149]  # Sample IDs - will be fetched from DB
DOCTOR_USER_IDS = [4, 5, 6, 150, 151, 152]   # Sample IDs - will be fetched from DB

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
        logger.info("Database connection established successfully")
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

def get_threads_without_replies(conn, limit=BATCH_SIZE, offset=0):
    """Get threads that have reply_count > 0 but no actual replies."""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.reply_count, c.procedure_id,
                       (SELECT COUNT(*) FROM community_replies cr WHERE cr.thread_id = c.id) AS actual_replies,
                       (SELECT procedure_name FROM procedures WHERE id = c.procedure_id) AS procedure_name
                FROM community c
                WHERE c.reply_count > 0 AND
                      (SELECT COUNT(*) FROM community_replies cr WHERE cr.thread_id = c.id) = 0
                ORDER BY c.reply_count DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            threads = cursor.fetchall()
            
            logger.info(f"Found {len(threads)} threads with reply_count > 0 but no actual replies (batch {offset//limit + 1})")
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
    """Create replies for a thread that has reply_count > 0 but no actual replies."""
    try:
        # Get number of replies to create based on thread's reply_count
        num_replies = thread['reply_count']
        thread_id = thread['id']
        title = thread['title']
        procedure_name = thread['procedure_name']
        
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
                logger.debug(f"Created reply {inserted_id} for thread {thread_id}")
        
        conn.commit()
        logger.info(f"Successfully created {len(created_replies)} replies for thread {thread_id}")
        return max(created_replies) if created_replies else last_reply_id
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating replies for thread {thread['id']}: {str(e)}")
        return last_reply_id

def process_batch(batch_number=1, batch_size=BATCH_SIZE):
    """Process a batch of threads without replies."""
    conn = None
    try:
        conn = get_db_connection()
        offset = (batch_number - 1) * batch_size
        
        # Get actual user IDs
        get_user_ids(conn)
        
        # Get threads without replies
        threads_without_replies = get_threads_without_replies(conn, batch_size, offset)
        
        if not threads_without_replies:
            logger.info(f"No more threads found with reply_count > 0 but no actual replies (batch {batch_number})")
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
        
        # Get final count for this batch
        try:
            with conn.cursor() as cursor:
                # Count total replies
                cursor.execute("SELECT COUNT(*) FROM community_replies")
                final_count = cursor.fetchone()[0]
                
                # Count remaining threads to fix
                cursor.execute("""
                    SELECT COUNT(*) FROM community c
                    WHERE c.reply_count > 0 AND
                          (SELECT COUNT(*) FROM community_replies cr WHERE cr.thread_id = c.id) = 0
                """)
                remaining_unfixed = cursor.fetchone()[0]
            
            logger.info(f"Processed batch {batch_number}: Fixed {threads_fixed} threads")
            logger.info(f"Total replies in database: {final_count}")
            logger.info(f"Remaining threads with reply_count > 0 but no replies: {remaining_unfixed}")
        except Exception as count_error:
            logger.error(f"Error getting counts: {str(count_error)}")
        
        return threads_fixed
    
    except Exception as e:
        logger.error(f"Error processing batch {batch_number}: {str(e)}")
        return 0
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"Error closing connection: {str(close_error)}")

if __name__ == "__main__":
    batch_number = 1
    
    while True:
        logger.info(f"Processing batch {batch_number}...")
        threads_processed = process_batch(batch_number)
        
        if threads_processed == 0:
            logger.info("All threads processed successfully")
            break
            
        batch_number += 1
        
        # Safety limit - process up to 20 batches (200 threads)
        if batch_number > 20:
            logger.info("Reached maximum batch limit (20 batches)")
            break