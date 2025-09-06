"""
Minimal seeding script that focuses on creating just the data needed for the analytics dashboard.
This is optimized for speed and will add just a few records directly to the database.
"""
import sys
import logging
from datetime import datetime, timedelta
from app import db
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_minimal_data():
    """Seed minimal data for the dashboard to work."""
    logger.info("Starting minimal data seeding...")
    
    conn = db.engine.connect()
    
    # 1. Add a test user if none exists
    user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
    
    user_id = None
    if user_count == 0:
        logger.info("Creating test user...")
        result = conn.execute(
            text("""
                INSERT INTO users 
                (username, email, name, phone_number, role, is_verified, created_at)
                VALUES ('testadmin', 'test@example.com', 'Test Admin', '+1234567890', 'admin', true, NOW())
                RETURNING id
            """)
        )
        user_id = result.scalar()
        logger.info(f"Created test user with ID: {user_id}")
    else:
        result = conn.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = result.scalar()
        logger.info(f"Using existing user with ID: {user_id}")
    
    # 2. Add body parts if none exist
    body_parts = {}
    body_part_count = conn.execute(text("SELECT COUNT(*) FROM body_parts")).scalar()
    
    if body_part_count == 0:
        logger.info("Adding body parts...")
        for name in ["Face", "Breast", "Body"]:
            result = conn.execute(
                text("""
                    INSERT INTO body_parts (name, description, created_at)
                    VALUES (:name, :description, NOW())
                    RETURNING id
                """),
                {"name": name, "description": f"The {name.lower()} area"}
            )
            body_parts[name] = result.scalar()
            logger.info(f"Added body part: {name}")
    else:
        result = conn.execute(text("SELECT id, name FROM body_parts"))
        for row in result:
            body_parts[row[1]] = row[0]
        logger.info(f"Using existing body parts: {list(body_parts.keys())}")
    
    # 3. Add categories if none exist
    categories = {}
    category_count = conn.execute(text("SELECT COUNT(*) FROM categories")).scalar()
    
    if category_count == 0:
        logger.info("Adding categories...")
        category_data = {
            "Face": "Facial Procedures",
            "Breast": "Breast Augmentation",
            "Body": "Body Contouring"
        }
        
        for body_part, category_name in category_data.items():
            body_part_id = body_parts.get(body_part)
            if body_part_id:
                result = conn.execute(
                    text("""
                        INSERT INTO categories (name, body_part_id, description, created_at)
                        VALUES (:name, :body_part_id, :description, NOW())
                        RETURNING id
                    """),
                    {"name": category_name, "body_part_id": body_part_id, "description": f"{category_name} for {body_part}"}
                )
                categories[category_name] = result.scalar()
                logger.info(f"Added category: {category_name}")
    else:
        result = conn.execute(text("SELECT id, name FROM categories"))
        for row in result:
            categories[row[1]] = row[0]
        logger.info(f"Using existing categories: {list(categories.keys())}")
    
    # 4. Add procedures (at least 5 needed for the dashboard)
    procedure_count = conn.execute(text("SELECT COUNT(*) FROM procedures")).scalar()
    
    procedures = []
    if procedure_count < 5:
        # Add our required procedures
        logger.info("Adding procedures...")
        procedures_to_add = []
        
        # Get category IDs
        face_category_id = categories.get("Facial Procedures")
        breast_category_id = categories.get("Breast Augmentation")
        
        if face_category_id and breast_category_id:
            # 4 face procedures and 1 breast procedure (minimum needed for dashboard)
            procedures_to_add = [
                {
                    "name": "Rhinoplasty",
                    "body_part": "Face",
                    "category_id": face_category_id,
                    "min_cost": 5000,
                    "max_cost": 10000
                },
                {
                    "name": "Facelift",
                    "body_part": "Face",
                    "category_id": face_category_id,
                    "min_cost": 7000,
                    "max_cost": 12000
                },
                {
                    "name": "Botox",
                    "body_part": "Face",
                    "category_id": face_category_id,
                    "min_cost": 300,
                    "max_cost": 1000
                },
                {
                    "name": "Eyelid Surgery",
                    "body_part": "Face",
                    "category_id": face_category_id,
                    "min_cost": 4000,
                    "max_cost": 8000
                },
                {
                    "name": "Breast Augmentation",
                    "body_part": "Breast",
                    "category_id": breast_category_id,
                    "min_cost": 6000,
                    "max_cost": 12000
                }
            ]
            
            for proc in procedures_to_add:
                # Check if procedure already exists
                result = conn.execute(
                    text("SELECT id FROM procedures WHERE procedure_name = :name"),
                    {"name": proc["name"]}
                )
                existing_id = result.scalar()
                
                if existing_id:
                    procedures.append(existing_id)
                    logger.info(f"Using existing procedure: {proc['name']}")
                else:
                    result = conn.execute(
                        text("""
                            INSERT INTO procedures 
                            (procedure_name, short_description, overview, procedure_details, ideal_candidates, 
                            recovery_time, min_cost, max_cost, risks, procedure_types, category_id, body_part, created_at)
                            VALUES 
                            (:name, :short_desc, :overview, :details, :candidates, 
                            :recovery, :min_cost, :max_cost, :risks, :types, :category_id, :body_part, NOW())
                            RETURNING id
                        """),
                        {
                            "name": proc["name"],
                            "short_desc": f"A procedure for {proc['body_part'].lower()}",
                            "overview": f"This procedure focuses on enhancing the {proc['body_part'].lower()}.",
                            "details": f"The {proc['name']} procedure involves advanced techniques.",
                            "candidates": f"Ideal candidates for {proc['name']} are individuals who wish to improve their appearance.",
                            "recovery": f"{7} days",
                            "min_cost": proc["min_cost"],
                            "max_cost": proc["max_cost"],
                            "risks": "Infection, scarring, anesthesia risks",
                            "types": f"{proc['name']} Standard",
                            "category_id": proc["category_id"],
                            "body_part": proc["body_part"]
                        }
                    )
                    proc_id = result.scalar()
                    procedures.append(proc_id)
                    logger.info(f"Added procedure: {proc['name']} with ID: {proc_id}")
    else:
        # Get IDs of existing procedures
        result = conn.execute(text("SELECT id FROM procedures LIMIT 5"))
        for row in result:
            procedures.append(row[0])
        logger.info(f"Using existing procedures: {procedures}")
    
    # 5. Add threads if none exist (6 needed for dashboard)
    thread_count = conn.execute(text("SELECT COUNT(*) FROM threads")).scalar()
    
    if thread_count < 6 and len(procedures) >= 5:
        logger.info("Adding threads...")
        
        # Create thread data - 5 Face threads, 1 Breast thread
        # Two threads containing "cost" keyword
        threads_to_add = [
            {
                "title": "Test Thread",
                "content": "This is a test thread for the community analytics dashboard.",
                "keywords": "{test,community,dashboard}",
                "procedure_id": procedures[0],
                "view_count": 50,
                "reply_count": 5,
                "created_at": (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "title": "My rhinoplasty experience - recovery tips",
                "content": "I recently had a rhinoplasty procedure and wanted to share my recovery experience.",
                "keywords": "{rhinoplasty,recovery,swelling,bruising,pain}",
                "procedure_id": procedures[0],
                "view_count": 100,
                "reply_count": 10,
                "created_at": (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "title": "How much does a facelift cost?",
                "content": "I'm considering a facelift but need to understand the costs involved.",
                "keywords": "{facelift,cost,pricing,fees,finances}",
                "procedure_id": procedures[1],
                "view_count": 150,
                "reply_count": 20,
                "created_at": (datetime.utcnow() - timedelta(days=20)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "title": "Does breast augmentation cost justify the results?",
                "content": "I'm debating whether the cost of breast augmentation is worth it for the results.",
                "keywords": "{breast,augmentation,cost,results,satisfaction}",
                "procedure_id": procedures[4],
                "view_count": 80,
                "reply_count": 8,
                "created_at": (datetime.utcnow() - timedelta(days=15)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "title": "Best doctors for face lift in my area?",
                "content": "I'm looking for recommendations for face lift surgeons in my area.",
                "keywords": "{face,lift,doctors,surgeon,recommendations}",
                "procedure_id": procedures[1],
                "view_count": 60,
                "reply_count": 6,
                "created_at": (datetime.utcnow() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "title": "Botox vs Surgery for forehead lines?",
                "content": "I'm debating between regular Botox treatments or a surgical option like a brow lift.",
                "keywords": "{botox,forehead,lines,brow,surgery}",
                "procedure_id": procedures[2],
                "view_count": 120,
                "reply_count": 12,
                "created_at": (datetime.utcnow() - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        thread_ids = []
        for thread in threads_to_add:
            result = conn.execute(
                text("""
                    INSERT INTO threads 
                    (title, content, created_at, procedure_id, view_count, reply_count, keywords, user_id)
                    VALUES 
                    (:title, :content, :created_at, :procedure_id, :view_count, :reply_count, :keywords, :user_id)
                    RETURNING id
                """),
                {
                    "title": thread["title"],
                    "content": thread["content"],
                    "created_at": thread["created_at"],
                    "procedure_id": thread["procedure_id"],
                    "view_count": thread["view_count"],
                    "reply_count": thread["reply_count"],
                    "keywords": thread["keywords"],
                    "user_id": user_id
                }
            )
            thread_id = result.scalar()
            thread_ids.append(thread_id)
            logger.info(f"Added thread: {thread['title']} with ID: {thread_id}")
        
        # 6. Add ThreadAnalytics for each thread
        for i, thread_id in enumerate(thread_ids):
            thread = threads_to_add[i]
            
            # Simple calculations for analytics values
            engagement_score = float(thread["view_count"]) / 10.0
            trending_score = float(thread["reply_count"]) / 10.0
            
            # Extract first 3 keywords for topic categories
            topic_arr = thread["keywords"].replace("{", "").replace("}", "").split(",")[:3]
            topic_categories = "{" + ",".join(topic_arr) + "}"
            
            # Random sentiment between -1 and 1
            sentiment_score = 0.5  # Neutral-positive
            
            conn.execute(
                text("""
                    INSERT INTO thread_analytics
                    (thread_id, engagement_score, trending_score, topic_categories, sentiment_score, created_at)
                    VALUES 
                    (:thread_id, :engagement_score, :trending_score, :topic_categories, :sentiment_score, NOW())
                """),
                {
                    "thread_id": thread_id,
                    "engagement_score": engagement_score,
                    "trending_score": trending_score,
                    "topic_categories": topic_categories,
                    "sentiment_score": sentiment_score
                }
            )
            logger.info(f"Added analytics for thread ID: {thread_id}")
    else:
        logger.info(f"Using existing threads ({thread_count} found)")
    
    conn.close()
    logger.info("Minimal data seeding completed successfully!")

def main():
    """Run the seeding script."""
    try:
        seed_minimal_data()
        return 0
    except Exception as e:
        logger.error(f"Error seeding minimal data: {str(e)}")
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