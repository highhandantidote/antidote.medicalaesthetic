#!/usr/bin/env python3
"""
Create community threads for testing
"""
import logging
from datetime import datetime, timedelta
from app import create_app, db
from models import Community, CommunityReply, User, Procedure, Category

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Create community threads for testing."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Creating community threads...")
            
            # Get category, procedure, users
            category = Category.query.first()
            if not category:
                logger.error("No category found")
                return
            
            procedure = Procedure.query.first()
            if not procedure:
                logger.error("No procedure found")
                return
            
            admin = User.query.filter_by(username="admin_test").first()
            doctor = User.query.filter_by(username="doctor_test").first()
            
            if not admin or not doctor:
                logger.error("Admin or doctor user not found")
                return
            
            # Create threads
            threads = [
                {
                    "title": "Rhinoplasty Experience",
                    "content": "I just had rhinoplasty and wanted to share my experience. The recovery was tough but worth it!",
                    "user_id": doctor.id,
                    "category_id": category.id,
                    "procedure_id": procedure.id,
                    "view_count": 120,
                    "reply_count": 3,
                    "featured": True,
                    "tags": ["rhinoplasty", "experience"]
                },
                {
                    "title": "Recovery Questions",
                    "content": "How long did it take for swelling to go down after your procedure?",
                    "user_id": admin.id,
                    "category_id": category.id,
                    "procedure_id": procedure.id,
                    "view_count": 85,
                    "reply_count": 2,
                    "featured": False,
                    "tags": ["recovery", "swelling"]
                }
            ]
            
            created_threads = []
            for thread_data in threads:
                existing = Community.query.filter_by(title=thread_data["title"]).first()
                if not existing:
                    thread = Community(
                        **thread_data,
                        created_at=datetime.utcnow() - timedelta(days=3),
                        updated_at=datetime.utcnow() - timedelta(days=1)
                    )
                    db.session.add(thread)
                    db.session.commit()
                    logger.info(f"Created thread: {thread_data['title']}")
                    created_threads.append(thread)
                else:
                    logger.info(f"Thread {thread_data['title']} already exists")
                    created_threads.append(existing)
            
            # Add replies
            for thread in created_threads:
                existing_reply = CommunityReply.query.filter_by(thread_id=thread.id).first()
                if not existing_reply:
                    reply = CommunityReply(
                        thread_id=thread.id,
                        user_id=admin.id if thread.user_id == doctor.id else doctor.id,
                        content=f"This is a reply to the thread about {thread.title}",
                        is_doctor_response=(thread.user_id != doctor.id),
                        created_at=datetime.utcnow() - timedelta(days=1),
                        upvotes=5
                    )
                    db.session.add(reply)
                    db.session.commit()
                    logger.info(f"Added reply to thread: {thread.title}")
            
            logger.info("Community threads created successfully")
            
        except Exception as e:
            logger.error(f"Error creating community threads: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()