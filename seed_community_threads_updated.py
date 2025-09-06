"""
Seed community threads for the analytics dashboard.
Creates 6 threads with appropriate keyword distribution, including exactly 2 mentions of "cost"
and a body part distribution of 5 Face, 1 Breast.
"""
import sys
import logging
from app import db
from sqlalchemy import text
from models import Thread, ThreadAnalytics, Procedure, User
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_community_threads_updated():
    """Seed exactly 6 community threads with specific distribution requirements."""
    logger.info("Seeding Thread and ThreadAnalytics tables with specific distribution...")
    
    # Check if we already have data
    conn = db.engine.connect()
    
    # Check if threads already exist
    thread_count = conn.execute(text("SELECT COUNT(*) FROM threads")).scalar()
    if thread_count > 0:
        logger.info(f"Thread data already exists ({thread_count} threads). Skipping seed.")
        conn.close()
        return
    
    # Get procedure IDs for specific body parts
    face_procedures = []
    breast_procedures = []
    
    # Get face procedures
    result = conn.execute(text("SELECT id, procedure_name FROM procedures WHERE body_part = 'Face' LIMIT 10"))
    for row in result:
        face_procedures.append((row[0], row[1]))
    
    # Get breast procedures
    result = conn.execute(text("SELECT id, procedure_name FROM procedures WHERE body_part = 'Breast' LIMIT 5"))
    for row in result:
        breast_procedures.append((row[0], row[1]))
    
    if not face_procedures or not breast_procedures:
        logger.error("Not enough procedures found. Please seed procedures first.")
        conn.close()
        return
    
    # Get user IDs
    users = []
    result = conn.execute(text("SELECT id FROM users LIMIT 5"))
    for row in result:
        users.append(row[0])
    
    if not users:
        logger.error("No users found. Please seed users first.")
        conn.close()
        return
    
    user_id = users[0]
    
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
    
    thread_ids = []
    
    # Insert threads
    for thread in threads:
        keywords = "{" + ",".join(f'"{k}"' for k in thread["keywords"]) + "}"
        sql = text("""
            INSERT INTO threads 
            (title, content, created_at, procedure_id, view_count, reply_count, keywords, user_id)
            VALUES (:title, :content, :created_at, :procedure_id, :view_count, :reply_count, :keywords, :user_id)
            RETURNING id
        """)
        
        result = conn.execute(sql, {
            "title": thread["title"],
            "content": thread["content"],
            "created_at": thread["created_at"],
            "procedure_id": thread["procedure_id"],
            "view_count": thread["view_count"],
            "reply_count": thread["reply_count"],
            "keywords": keywords,
            "user_id": thread["user_id"]
        })
        
        thread_id = result.scalar()
        thread_ids.append(thread_id)
    
    conn.commit()
    logger.info(f"Added {len(threads)} sample threads with specific distribution.")
    
    # Insert thread analytics
    for i, thread_id in enumerate(thread_ids):
        thread = threads[i]
        engagement_score = round(random.uniform(1.0, 10.0), 2)
        trending_score = round(random.uniform(0.1, 5.0) * (thread["view_count"] / 100), 2)
        topic_categories = "{" + ",".join(f'"{k}"' for k in thread["keywords"][:3]) + "}"
        sentiment_score = round(random.uniform(-1.0, 1.0), 2)
        
        sql = text("""
            INSERT INTO thread_analytics
            (thread_id, engagement_score, trending_score, topic_categories, sentiment_score, created_at)
            VALUES (:thread_id, :engagement_score, :trending_score, :topic_categories, :sentiment_score, NOW())
        """)
        
        conn.execute(sql, {
            "thread_id": thread_id,
            "engagement_score": engagement_score,
            "trending_score": trending_score,
            "topic_categories": topic_categories,
            "sentiment_score": sentiment_score
        })
    
    conn.commit()
    conn.close()
    logger.info("Added thread analytics for all sample threads.")
    logger.info("Community threads seeding completed successfully with required distribution!")
    
    # Summarize the distribution
    logger.info("Distribution summary:")
    logger.info("- Face threads: 5")
    logger.info("- Breast threads: 1")
    logger.info("- 'cost' keyword mentions: 2")

def main():
    """Run the thread seeding script."""
    try:
        seed_community_threads_updated()
        return 0
    except Exception as e:
        logger.error(f"Error seeding community threads: {str(e)}")
        return 1

if __name__ == "__main__":
    try:
        # Import the Flask app 
        from main import app
        with app.app_context():
            sys.exit(main())
    except Exception as e:
        logger.error(f"Error in script: {str(e)}")
        sys.exit(1)