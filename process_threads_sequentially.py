"""
Process threads sequentially to add replies.
This script handles one thread at a time to avoid connection issues.
"""
import os
import logging
import psycopg2
import subprocess
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection string from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    """Get a connection to the database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def get_threads_without_replies(limit=66):
    """Get threads that have no replies."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.id
                FROM community c
                WHERE NOT EXISTS (
                    SELECT 1 FROM community_replies cr 
                    WHERE cr.thread_id = c.id
                )
                ORDER BY c.id DESC
                LIMIT %s
            """, (limit,))
            
            threads = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found {len(threads)} threads with no replies")
            return threads
    except Exception as e:
        logger.error(f"Error getting threads without replies: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

def check_progress():
    """Check progress toward meeting task requirements."""
    conn = None
    try:
        conn = get_db_connection()
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
    finally:
        if conn:
            conn.close()

def process_threads():
    """Process threads sequentially to add replies."""
    # Check how many more threads we need
    threads_needed = check_progress()
    if threads_needed <= 0:
        logger.info("✅ TASK COMPLETE: At least 125 threads have 2-4 replies")
        return
    
    # Get threads without replies
    threads = get_threads_without_replies(threads_needed)
    if not threads:
        logger.warning("No threads found without replies")
        return
    
    # Process each thread
    success_count = 0
    for i, thread_id in enumerate(threads):
        logger.info(f"Processing thread {i+1}/{len(threads)}: ID={thread_id}")
        
        # Run the add_thread_replies.py script for this thread
        cmd = ["python", "add_thread_replies.py", str(thread_id)]
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            success_count += 1
            logger.info(f"Success: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to process thread {thread_id}: {e.stderr}")
        
        # Add a small delay to avoid overwhelming the database
        time.sleep(1)
        
        # Check if we've reached our goal
        if i > 0 and i % 10 == 0:
            remaining = check_progress()
            if remaining <= 0:
                logger.info("✅ TASK COMPLETE: Reached 125 threads with 2-4 replies")
                break
    
    # Final progress check
    threads_needed = check_progress()
    logger.info(f"Successfully processed {success_count} threads")
    
    if threads_needed <= 0:
        logger.info("✅ TASK COMPLETE: At least 125 threads have 2-4 replies")
    else:
        logger.info(f"⚠️ TASK INCOMPLETE: Need {threads_needed} more threads with 2-4 replies")

if __name__ == "__main__":
    process_threads()