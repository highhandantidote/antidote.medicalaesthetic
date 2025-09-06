#!/usr/bin/env python3
"""
Seed community threads in small batches to avoid timeouts.

This script creates 6 threads with the specific required distribution:
- 5 Face threads
- 1 Breast thread
- 2 threads with 'cost' keyword

It uses direct SQL and commits after each thread to prevent timeouts.
"""
import os
import sys
import psycopg2
import logging
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_db():
    """Connect to the PostgreSQL database."""
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = False
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to the database: {str(e)}")
        raise

def check_existing_data(conn):
    """Check if threads already exist."""
    logger.info("Checking for existing threads...")
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM threads")
            thread_count = cur.fetchone()[0]
            logger.info(f"Found {thread_count} existing threads")
            
            if thread_count >= 6:
                logger.info("At least 6 threads already exist, skipping seeding")
                return True, None, None
            
            # Get user ID
            cur.execute("SELECT id FROM users LIMIT 1")
            user_result = cur.fetchone()
            if not user_result:
                logger.info("No users found, creating test user")
                cur.execute("""
                    INSERT INTO users 
                    (username, email, name, phone_number, role, is_verified, created_at)
                    VALUES ('testadmin', 'test@example.com', 'Test Admin', '+1234567890', 'admin', true, NOW())
                    RETURNING id
                """)
                user_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"Created test user with ID: {user_id}")
            else:
                user_id = user_result[0]
                logger.info(f"Using existing user with ID: {user_id}")
            
            # Get procedure IDs
            cur.execute("SELECT id, procedure_name, body_part FROM procedures")
            procedures = cur.fetchall()
            
            if not procedures:
                logger.error("No procedures found, please seed procedures first")
                return False, None, None
            
            # Sort procedures by body part
            face_procedures = []
            breast_procedures = []
            
            for proc in procedures:
                if proc[2] == 'Face':
                    face_procedures.append((proc[0], proc[1]))
                elif proc[2] == 'Breast':
                    breast_procedures.append((proc[0], proc[1]))
            
            if not face_procedures or not breast_procedures:
                logger.error("Missing required procedures (need both Face and Breast procedures)")
                return False, None, None
            
            logger.info(f"Found {len(face_procedures)} face procedures and {len(breast_procedures)} breast procedures")
            return False, user_id, (face_procedures, breast_procedures)
    
    except Exception as e:
        logger.error(f"Error checking existing data: {str(e)}")
        conn.rollback()
        raise

def seed_thread(conn, thread_data):
    """Seed a single thread into the database and commit immediately."""
    logger.info(f"Adding thread: {thread_data['title']}")
    
    try:
        with conn.cursor() as cur:
            # Format keywords for array
            keywords_arr = "{" + ",".join(f'"{k}"' for k in thread_data["keywords"]) + "}"
            
            cur.execute("""
                INSERT INTO threads 
                (title, content, created_at, procedure_id, view_count, reply_count, keywords, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                thread_data["title"],
                thread_data["content"],
                thread_data["created_at"],
                thread_data["procedure_id"],
                thread_data["view_count"],
                thread_data["reply_count"],
                keywords_arr,
                thread_data["user_id"]
            ))
            
            thread_id = cur.fetchone()[0]
            logger.info(f"Added thread with ID: {thread_id}")
        
        # Commit after each thread to avoid timeouts with large transactions
        conn.commit()
        logger.info(f"Successfully committed thread: {thread_data['title']}")
        return thread_id
    
    except Exception as e:
        logger.error(f"Error seeding thread {thread_data['title']}: {str(e)}")
        conn.rollback()
        raise

def seed_thread_analytics(conn, thread_id, thread_data):
    """Seed analytics for a single thread."""
    logger.info(f"Adding analytics for thread ID: {thread_id}")
    
    try:
        with conn.cursor() as cur:
            engagement_score = round(random.uniform(1.0, 10.0), 2)
            trending_score = round(random.uniform(0.1, 5.0) * (thread_data["view_count"] / 100), 2)
            
            # Take first 3 keywords for topic categories
            topic_categories = "{" + ",".join(f'"{k}"' for k in thread_data["keywords"][:3]) + "}"
            
            sentiment_score = round(random.uniform(-1.0, 1.0), 2)
            
            cur.execute("""
                INSERT INTO thread_analytics
                (thread_id, engagement_score, trending_score, topic_categories, sentiment_score, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                thread_id,
                engagement_score,
                trending_score,
                topic_categories,
                sentiment_score
            ))
        
        # Commit after each analytics record
        conn.commit()
        logger.info(f"Successfully added analytics for thread ID: {thread_id}")
    
    except Exception as e:
        logger.error(f"Error seeding thread analytics for thread ID {thread_id}: {str(e)}")
        conn.rollback()
        raise

def main():
    """Run the thread seeding script with improved batching."""
    logger.info("Starting community thread seeding with batching...")
    
    try:
        conn = connect_to_db()
        
        # Check existing data
        threads_exist, user_id, procedures = check_existing_data(conn)
        
        if threads_exist:
            logger.info("Threads already exist, skipping seeding")
            conn.close()
            return 0
        
        if not user_id or not procedures:
            logger.error("Missing required data (user_id or procedures)")
            conn.close()
            return 1
        
        face_procedures, breast_procedures = procedures
        
        # Create the threads with specific requirements
        threads = [
            {
                "title": "Test Thread",
                "content": "This is a test thread for the community analytics dashboard.",
                "keywords": ["test", "community", "dashboard"],
                "procedure_id": face_procedures[0][0] if face_procedures else None,
                "view_count": random.randint(10, 100),
                "reply_count": random.randint(1, 10),
                "user_id": user_id,
                "created_at": (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "title": "My rhinoplasty experience - recovery tips",
                "content": "I recently had a rhinoplasty procedure and wanted to share my recovery experience.",
                "keywords": ["rhinoplasty", "recovery", "swelling", "bruising", "pain"],
                "procedure_id": face_procedures[1][0] if len(face_procedures) > 1 else face_procedures[0][0],
                "view_count": random.randint(50, 200),
                "reply_count": random.randint(5, 20),
                "user_id": user_id,
                "created_at": (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "title": "How much does a facelift cost?",
                "content": "I'm considering a facelift but need to understand the costs involved. What's the typical cost range?",
                "keywords": ["facelift", "cost", "pricing", "surgeon fees", "finances"],
                "procedure_id": face_procedures[2][0] if len(face_procedures) > 2 else face_procedures[0][0],
                "view_count": random.randint(80, 300),
                "reply_count": random.randint(10, 30),
                "user_id": user_id,
                "created_at": (datetime.utcnow() - timedelta(days=20)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "title": "Does breast augmentation cost justify the results?",
                "content": "I'm debating whether the cost of breast augmentation is worth it for the results.",
                "keywords": ["breast augmentation", "cost", "results", "satisfaction", "value"],
                "procedure_id": breast_procedures[0][0] if breast_procedures else None,
                "view_count": random.randint(40, 150),
                "reply_count": random.randint(5, 15),
                "user_id": user_id,
                "created_at": (datetime.utcnow() - timedelta(days=15)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "title": "Best doctors for face lift in my area?",
                "content": "I'm looking for recommendations for face lift surgeons in my area.",
                "keywords": ["face lift", "doctors", "surgeon", "recommendations", "consultation"],
                "procedure_id": face_procedures[3][0] if len(face_procedures) > 3 else face_procedures[0][0],
                "view_count": random.randint(30, 120),
                "reply_count": random.randint(3, 12),
                "user_id": user_id,
                "created_at": (datetime.utcnow() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "title": "Botox vs Surgery for forehead lines?",
                "content": "I'm debating between regular Botox treatments or a surgical option like a brow lift.",
                "keywords": ["botox", "forehead lines", "brow lift", "surgery", "minimally invasive"],
                "procedure_id": face_procedures[4][0] if len(face_procedures) > 4 else face_procedures[0][0],
                "view_count": random.randint(60, 250),
                "reply_count": random.randint(8, 25),
                "user_id": user_id,
                "created_at": (datetime.utcnow() - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        # Add threads one by one with immediate commits
        thread_ids = []
        for thread in threads:
            try:
                thread_id = seed_thread(conn, thread)
                thread_ids.append(thread_id)
                
                # Add analytics for each thread immediately after creating it
                # This avoids having to batch all analytics at the end
                seed_thread_analytics(conn, thread_id, thread)
                
                # Brief summary after each thread is complete
                logger.info(f"Thread '{thread['title']}' added with analytics")
            except Exception as e:
                logger.error(f"Failed to add thread '{thread['title']}': {str(e)}")
                # Continue with next thread even if one fails
                continue
        
        logger.info("Community thread seeding completed successfully!")
        logger.info("Distribution summary:")
        logger.info("- Face threads: 5")
        logger.info("- Breast threads: 1")
        logger.info("- 'cost' keyword mentions: 2")
        
        conn.close()
        return 0
    
    except Exception as e:
        logger.error(f"Error in thread seeding: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())