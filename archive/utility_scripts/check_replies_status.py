"""
Check the status of community replies.
This script reports how many threads have replies and how many still need them.
"""
import os
import logging
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection string from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def check_status():
    """Check the status of community replies."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Count total threads
            cursor.execute("SELECT COUNT(*) FROM community")
            total_threads = cursor.fetchone()[0]
            
            # Count threads with 0 replies
            cursor.execute("""
                SELECT COUNT(*) FROM community c
                WHERE NOT EXISTS (
                    SELECT 1 FROM community_replies cr 
                    WHERE cr.thread_id = c.id
                )
            """)
            threads_with_no_replies = cursor.fetchone()[0]
            
            # Count threads with 1 reply
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT thread_id, COUNT(*) as reply_count
                    FROM community_replies
                    GROUP BY thread_id
                    HAVING COUNT(*) = 1
                ) as threads_with_1_reply
            """)
            threads_with_1_reply = cursor.fetchone()[0]
            
            # Count threads with 2-4 replies (our target)
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT thread_id, COUNT(*) as reply_count
                    FROM community_replies
                    GROUP BY thread_id
                    HAVING COUNT(*) BETWEEN 2 AND 4
                ) as threads_with_2_4_replies
            """)
            threads_with_2_4_replies = cursor.fetchone()[0]
            
            # Count threads with more than 4 replies
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT thread_id, COUNT(*) as reply_count
                    FROM community_replies
                    GROUP BY thread_id
                    HAVING COUNT(*) > 4
                ) as threads_with_many_replies
            """)
            threads_with_more_than_4 = cursor.fetchone()[0]
            
            # Calculate progress
            target = 125
            progress = min(100, round((threads_with_2_4_replies / target) * 100))
            
            # Display results
            logger.info(f"📊 COMMUNITY REPLIES STATUS:")
            logger.info(f"----------------------------")
            logger.info(f"Total threads: {total_threads}")
            logger.info(f"Threads with NO replies: {threads_with_no_replies}")
            logger.info(f"Threads with 1 reply: {threads_with_1_reply}")
            logger.info(f"Threads with 2-4 replies: {threads_with_2_4_replies} (TARGET: 125)")
            logger.info(f"Threads with >4 replies: {threads_with_more_than_4}")
            logger.info(f"----------------------------")
            logger.info(f"Progress: {progress}% ({threads_with_2_4_replies}/{target})")
            
            # Check if we're done
            if threads_with_2_4_replies >= target:
                logger.info("✅ TASK COMPLETE: At least 125 threads have 2-4 replies!")
            else:
                needed = target - threads_with_2_4_replies
                logger.info(f"⏳ TASK IN PROGRESS: Need {needed} more threads with 2-4 replies")
                
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_status()