"""
Seed script for community analytics data.

This script helps to seed data for community analytics testing.
It creates sample threads with varied body parts and keywords to test the analytics dashboard.
"""

import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from flask import Flask
from app import db
from models import Thread, User, Procedure, Category, CommunityReply

# Create a Flask app context to use models
app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)

def get_random_procedure(session):
    """Get a random procedure from the database."""
    procedure_count = session.query(func.count(Procedure.id)).scalar()
    if procedure_count == 0:
        return None
    
    random_offset = random.randint(0, procedure_count - 1)
    return session.query(Procedure).offset(random_offset).first()

def get_random_user(session):
    """Get a random user from the database."""
    user_count = session.query(func.count(User.id)).scalar()
    if user_count == 0:
        return None
    
    random_offset = random.randint(0, user_count - 1)
    return session.query(User).offset(random_offset).first()

def get_random_date(days_back=30):
    """Get a random date within the specified number of days back."""
    return datetime.now() - timedelta(days=random.randint(1, days_back))

def create_threads(session, count=5):
    """Create the specified number of threads with diverse attributes."""
    # Make sure we have categories
    categories = session.query(Category).all()
    if not categories:
        print("Creating default categories...")
        categories = [
            Category(name="General Questions"),
            Category(name="Recovery"),
            Category(name="Before & After"),
            Category(name="Cost & Financing"),
            Category(name="Doctor Recommendations")
        ]
        session.add_all(categories)
        session.commit()
    
    # Common keywords for thread content
    keywords_by_type = {
        "Rhinoplasty": ["rhinoplasty", "nose", "breathing", "swelling", "recovery", "cost"],
        "Breast Augmentation": ["breast", "implants", "size", "recovery", "cost", "saline", "silicone"],
        "Facelift": ["facelift", "wrinkles", "aging", "recovery", "lifting", "tightening"],
        "Liposuction": ["liposuction", "fat", "removal", "sculpting", "recovery", "results"],
        "Dermal Fillers": ["fillers", "wrinkles", "volume", "lips", "cheeks", "hyaluronic"]
    }
    
    # Create threads for different body parts
    threads_created = 0
    
    for _ in range(count):
        procedure = get_random_procedure(session)
        if not procedure:
            print("No procedures found. Cannot create threads.")
            return 0
        
        user = get_random_user(session)
        if not user:
            print("No users found. Creating a default user...")
            from werkzeug.security import generate_password_hash
            user = User(
                username=f"test_user_{random.randint(1000, 9999)}",
                email=f"test{random.randint(1000, 9999)}@example.com",
                password_hash=generate_password_hash("password123")
            )
            session.add(user)
            session.commit()
        
        # Get keywords based on procedure type or use general keywords
        procedure_type = procedure.procedure_name if procedure else "General"
        available_keywords = []
        for key, keywords in keywords_by_type.items():
            if key in procedure_type:
                available_keywords = keywords
                break
        
        if not available_keywords:
            available_keywords = ["recovery", "cost", "results", "experience", "doctor", "recommendation"]
        
        # Select 2-4 random keywords
        thread_keywords = random.sample(available_keywords, min(random.randint(2, 4), len(available_keywords)))
        
        # Create a title based on procedure and random keywords
        title_templates = [
            f"Question about {procedure.procedure_name} {random.choice(thread_keywords)}",
            f"My {procedure.procedure_name} experience",
            f"Looking for advice on {procedure.procedure_name}",
            f"{procedure.procedure_name} cost in {random.choice(['New York', 'Los Angeles', 'Chicago', 'Miami', 'Houston'])}",
            f"Concerned about {procedure.procedure_name} {random.choice(thread_keywords)}"
        ]
        
        # Create content with keywords embedded
        content_templates = [
            f"I'm considering getting {procedure.procedure_name} and I'm worried about the {thread_keywords[0]}. Has anyone had experience with this? I've heard the {thread_keywords[1]} can be quite difficult.",
            f"Just had my {procedure.procedure_name} done last week. The {thread_keywords[0]} has been manageable but I'm concerned about {thread_keywords[1]}. Any advice?",
            f"Can anyone recommend a good doctor for {procedure.procedure_name} in the area? I'm particularly concerned about {thread_keywords[0]} and {thread_keywords[1]}.",
            f"What was your {thread_keywords[0]} like after {procedure.procedure_name}? I'm scheduled for next month and trying to prepare for {thread_keywords[1]}."
        ]
        
        # Create the thread
        thread = Thread(
            title=random.choice(title_templates),
            content=random.choice(content_templates),
            user_id=user.id,
            procedure_id=procedure.id,
            category_id=random.choice(categories).id,
            is_anonymous=random.choice([True, False]),
            created_at=get_random_date(),
            view_count=random.randint(5, 100),
            reply_count=random.randint(0, 15),
            keywords=thread_keywords
        )
        
        session.add(thread)
        threads_created += 1
    
    session.commit()
    return threads_created

def main():
    """Run the seed script."""
    with app.app_context():
        # Check if we already have threads
        thread_count = db.session.query(func.count(Thread.id)).scalar()
        if thread_count >= 5:
            print(f"Database already has {thread_count} threads. No need to seed more data.")
            return
        
        # Create 5 threads for testing
        threads_created = create_threads(db.session, count=5)
        print(f"Created {threads_created} threads for community analytics testing.")

if __name__ == "__main__":
    main()