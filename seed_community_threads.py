import os
import sys
from app import db
from models import Thread, ThreadAnalytics, Procedure, User
from sqlalchemy import text
from datetime import datetime, timedelta
import random

# Direct SQL approach for faster execution
def seed_community_threads_sql():
    """Seed the community threads using direct SQL for better performance."""
    print("Seeding Thread and ThreadAnalytics tables with SQL...")
    
    # Check if we already have data
    conn = db.engine.connect()
    
    # Check if threads already exist
    thread_count = conn.execute(text("SELECT COUNT(*) FROM threads")).scalar()
    if thread_count > 0:
        print(f"Thread data already exists ({thread_count} threads). Skipping seed.")
        conn.close()
        return
    
    # Get procedure IDs
    procedures = []
    result = conn.execute(text("SELECT id, procedure_name FROM procedures LIMIT 15"))
    for row in result:
        procedures.append((row[0], row[1]))
    
    if not procedures:
        print("No procedures found. Please seed procedures first.")
        conn.close()
        return
    
    # Get user IDs
    users = []
    result = conn.execute(text("SELECT id FROM users LIMIT 5"))
    for row in result:
        users.append(row[0])
    
    if not users:
        print("No users found. Please seed users first.")
        conn.close()
        return
    
    # Now create the threads
    threads = [
        {
            "title": "My rhinoplasty experience - recovery tips",
            "content": "I recently had a rhinoplasty procedure and wanted to share my recovery experience.",
            "keywords": ["rhinoplasty", "recovery", "swelling", "bruising", "pain"],
            "procedure_id": next((p[0] for p in procedures if "Rhinoplasty" in p[1]), procedures[0][0]),
            "view_count": random.randint(50, 200),
            "reply_count": random.randint(5, 20),
            "user_id": users[0] if users else None,
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "title": "Is breast augmentation worth the cost?",
            "content": "I'm considering breast augmentation but hesitant about the cost.",
            "keywords": ["breast augmentation", "cost", "financing", "worth it", "expenses"],
            "procedure_id": next((p[0] for p in procedures if "Breast Augmentation" in p[1]), procedures[0][0]),
            "view_count": random.randint(80, 300),
            "reply_count": random.randint(10, 30),
            "user_id": users[1] if len(users) > 1 else users[0],
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 20))).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "title": "Comparing different types of fillers for lip enhancement",
            "content": "I'm researching different types of fillers for lip enhancement.",
            "keywords": ["fillers", "lip enhancement", "Juvederm", "Restylane", "results"],
            "procedure_id": next((p[0] for p in procedures if "Filler" in p[1]), procedures[0][0]),
            "view_count": random.randint(40, 150),
            "reply_count": random.randint(5, 15),
            "user_id": users[2] if len(users) > 2 else users[0],
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 15))).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "title": "Best doctors for face lift in Delhi?",
            "content": "I'm looking for recommendations for face lift surgeons in Delhi, India.",
            "keywords": ["face lift", "Delhi", "surgeon", "India", "cost"],
            "procedure_id": next((p[0] for p in procedures if "Face" in p[1]), procedures[0][0]),
            "view_count": random.randint(30, 120),
            "reply_count": random.randint(3, 12),
            "user_id": users[3] if len(users) > 3 else users[0],
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 10))).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "title": "Botox vs Surgery for forehead lines - which is better?",
            "content": "I'm debating between regular Botox treatments or a surgical option like a brow lift.",
            "keywords": ["botox", "forehead lines", "brow lift", "surgery", "minimally invasive"],
            "procedure_id": next((p[0] for p in procedures if "Botox" in p[1]), procedures[0][0]),
            "view_count": random.randint(60, 250),
            "reply_count": random.randint(8, 25),
            "user_id": users[4] if len(users) > 4 else users[0],
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d %H:%M:%S')
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
    print(f"Added {len(threads)} sample threads.")
    
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
    print("Added thread analytics for all sample threads.")
    print("Community threads seeding completed successfully!")

if __name__ == "__main__":
    try:
        # Import the Flask app 
        from main import app
        with app.app_context():
            seed_community_threads_sql()
    except Exception as e:
        print(f"Error seeding community threads: {str(e)}")
        sys.exit(1)