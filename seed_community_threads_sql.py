"""
Seed community threads using direct SQL for better performance.
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

def seed_threads(conn, user_id, procedures):
    """Seed threads into the database."""
    logger.info("Seeding threads...")
    face_procedures, breast_procedures = procedures
    thread_ids = []
    
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
    
    try:
        with conn.cursor() as cur:
            # Insert threads
            for thread in threads:
                logger.info(f"Adding thread: {thread['title']}")
                
                # Format keywords for array
                keywords_arr = "{" + ",".join(f'"{k}"' for k in thread["keywords"]) + "}"
                
                cur.execute("""
                    INSERT INTO threads 
                    (title, content, created_at, procedure_id, view_count, reply_count, keywords, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    thread["title"],
                    thread["content"],
                    thread["created_at"],
                    thread["procedure_id"],
                    thread["view_count"],
                    thread["reply_count"],
                    keywords_arr,
                    thread["user_id"]
                ))
                
                thread_id = cur.fetchone()[0]
                thread_ids.append(thread_id)
                logger.info(f"Added thread with ID: {thread_id}")
        
        conn.commit()
        logger.info(f"Successfully added {len(thread_ids)} threads")
        return thread_ids
    
    except Exception as e:
        logger.error(f"Error seeding threads: {str(e)}")
        conn.rollback()
        raise

def seed_thread_analytics(conn, thread_ids, threads):
    """Seed analytics for the threads."""
    logger.info("Seeding thread analytics...")
    
    try:
        with conn.cursor() as cur:
            for i, thread_id in enumerate(thread_ids):
                if i < len(threads):  # Safety check
                    thread = threads[i]
                    engagement_score = round(random.uniform(1.0, 10.0), 2)
                    trending_score = round(random.uniform(0.1, 5.0) * (thread["view_count"] / 100), 2)
                    
                    # Take first 3 keywords for topic categories
                    topic_categories = "{" + ",".join(f'"{k}"' for k in thread["keywords"][:3]) + "}"
                    
                    sentiment_score = round(random.uniform(-1.0, 1.0), 2)
                    
                    logger.info(f"Adding analytics for thread ID: {thread_id}")
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
        
        conn.commit()
        logger.info("Successfully added thread analytics")
    
    except Exception as e:
        logger.error(f"Error seeding thread analytics: {str(e)}")
        conn.rollback()
        raise

def main():
    """Run the thread seeding script."""
    logger.info("Starting community thread seeding using SQL...")
    
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
        
        # Create threads with specific distribution
        thread_ids = seed_threads(conn, user_id, procedures)
        
        # Create thread analytics
        if thread_ids:
            threads = [
                {
                    "title": "Test Thread",
                    "content": "This is a test thread for the community analytics dashboard.",
                    "keywords": ["test", "community", "dashboard"],
                    "view_count": 50
                },
                {
                    "title": "My rhinoplasty experience - recovery tips",
                    "content": "I recently had a rhinoplasty procedure and wanted to share my recovery experience.",
                    "keywords": ["rhinoplasty", "recovery", "swelling", "bruising", "pain"],
                    "view_count": 100
                },
                {
                    "title": "How much does a facelift cost?",
                    "content": "I'm considering a facelift but need to understand the costs involved.",
                    "keywords": ["facelift", "cost", "pricing", "surgeon fees", "finances"],
                    "view_count": 150
                },
                {
                    "title": "Does breast augmentation cost justify the results?",
                    "content": "I'm debating whether the cost of breast augmentation is worth it for the results.",
                    "keywords": ["breast augmentation", "cost", "results", "satisfaction", "value"],
                    "view_count": 80
                },
                {
                    "title": "Best doctors for face lift in my area?",
                    "content": "I'm looking for recommendations for face lift surgeons in my area.",
                    "keywords": ["face lift", "doctors", "surgeon", "recommendations", "consultation"],
                    "view_count": 60
                },
                {
                    "title": "Botox vs Surgery for forehead lines?",
                    "content": "I'm debating between regular Botox treatments or a surgical option like a brow lift.",
                    "keywords": ["botox", "forehead lines", "brow lift", "surgery", "minimally invasive"],
                    "view_count": 120
                }
            ]
            seed_thread_analytics(conn, thread_ids, threads)
        
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