#!/usr/bin/env python3
"""
Step 2: Create procedures and community threads
"""
import os
import random
import string
import logging
from datetime import datetime, timedelta
from app import create_app, db
from models import (
    User, Doctor, Procedure, Community, BodyPart, Category, CommunityReply
)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_procedure(name, body_area, category_id, doctor_id, surgical=True):
    """Generate a procedure for testing."""
    description = ''.join(random.choices(string.ascii_letters + ' ', k=100))
    
    return Procedure(
        procedure_name=name,
        short_description=f"{name} - {body_area}",
        overview=f"Overview of {name}. {description[:30]}",
        procedure_details=description,
        ideal_candidates="Adults in good health seeking aesthetic improvement",
        recovery_process="Rest and follow post-procedure care instructions",
        recovery_time="1-4 weeks",
        results_duration="6 months to permanent",
        min_cost=random.randint(5000, 15000),
        max_cost=random.randint(20000, 50000),
        benefits="Improved appearance and confidence",
        benefits_detailed="Enhanced aesthetic appearance, improved self-confidence, and better quality of life",
        risks="Swelling, bruising, and potential complications",
        procedure_types="Type A, Type B" if surgical else "Non-surgical",
        category_id=category_id,
        popularity_score=random.randint(1, 100),
        avg_rating=random.uniform(3.5, 5.0),
        review_count=random.randint(5, 50),
        created_at=datetime.utcnow()
    )

def generate_thread(title, content, category_id, author_id, procedure_id=None):
    """Generate a community thread for testing."""
    return Community(
        title=title,
        content=content,
        category_id=category_id,
        user_id=author_id,
        procedure_id=procedure_id,
        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
        updated_at=datetime.utcnow() - timedelta(days=random.randint(0, 10)),
        view_count=random.randint(10, 200),
        reply_count=random.randint(0, 10),
        featured=random.choice([True, False]),
        tags=["tag1", "tag2", "tag3"]
    )

def create_sample_media_files():
    """Create sample media files for testing."""
    # Create media directory for community threads
    media_dir = os.path.join('static', 'media')
    os.makedirs(media_dir, exist_ok=True)
    
    # Create a sample media file
    media_file_path = os.path.join(media_dir, 'test_image.jpg')
    with open(media_file_path, 'w') as f:
        f.write("This is a sample image file for testing purposes.")
    
    logger.info(f"Created sample media file at {media_file_path}")

def main():
    """Create procedures and threads for testing."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Starting Step 2: Creating procedures and community threads...")
            
            # Create sample media files
            create_sample_media_files()
            
            # Get the existing categories
            categories = Category.query.all()
            if not categories:
                # If no categories exist, create them
                body_part = BodyPart.query.filter_by(name="Face").first()
                if not body_part:
                    body_part = BodyPart(
                        name="Face",
                        description="Facial procedures and treatments",
                        created_at=datetime.utcnow()
                    )
                    db.session.add(body_part)
                    db.session.commit()
                    logger.info("Created body part: Face")
                
                for cat_name in ["Surgical", "Non-Surgical"]:
                    category = Category(
                        name=cat_name,
                        description=f"{cat_name} procedures for face",
                        body_part_id=body_part.id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(category)
                    db.session.commit()
                    logger.info(f"Created category: {cat_name}")
                
                # Refresh categories
                categories = Category.query.all()
            
            # Get admin and doctor users
            admin = User.query.filter_by(username="admin_test").first()
            doctor_user = User.query.filter_by(username="doctor_test").first()
            
            if not admin or not doctor_user:
                logger.error("Admin or doctor user not found. Please run test_data_step1.py first.")
                return
            
            # Get doctor profile
            doctor = Doctor.query.filter_by(user_id=doctor_user.id).first()
            if not doctor:
                logger.error("Doctor profile not found. Please run test_data_step1.py first.")
                return
            
            # Create procedures (5)
            procedure_data = [
                {"name": "Rhinoplasty", "body_area": "Nose", "surgical": True},
                {"name": "Botox", "body_area": "Face", "surgical": False},
                {"name": "Lip Fillers", "body_area": "Lips", "surgical": False},
                {"name": "Facelift", "body_area": "Face", "surgical": True},
                {"name": "Eyelid Surgery", "body_area": "Eyes", "surgical": True}
            ]
            
            created_procedures = []
            for idx, proc in enumerate(procedure_data):
                category_id = categories[0].id if proc["surgical"] else categories[1].id
                procedure = Procedure.query.filter_by(procedure_name=proc["name"]).first()
                if not procedure:
                    procedure = generate_procedure(
                        proc["name"], 
                        proc["body_area"], 
                        category_id, 
                        doctor.id, 
                        proc["surgical"]
                    )
                    db.session.add(procedure)
                    db.session.commit()
                    logger.info(f"Created procedure: {proc['name']}")
                created_procedures.append(procedure)
            
            # Create threads (5)
            thread_data = [
                {"title": "Rhinoplasty Experience", "content": "I just had rhinoplasty and wanted to share my experience.", "procedure_id": created_procedures[0].id},
                {"title": "Botox Questions", "content": "Has anyone tried Botox? What should I expect?", "procedure_id": created_procedures[1].id},
                {"title": "Lip Filler Results", "content": "Just got lip fillers and I'm so happy with the results!", "procedure_id": created_procedures[2].id},
                {"title": "Facelift Recovery Time", "content": "How long does it take to recover from a facelift?", "procedure_id": created_procedures[3].id},
                {"title": "Considering Eyelid Surgery", "content": "I'm thinking about getting eyelid surgery. Any advice?", "procedure_id": created_procedures[4].id}
            ]
            
            created_threads = []
            for idx, thread in enumerate(thread_data):
                new_thread = Community.query.filter_by(title=thread["title"]).first()
                if not new_thread:
                    new_thread = generate_thread(
                        thread["title"],
                        thread["content"],
                        categories[0].id if idx % 2 == 0 else categories[1].id,
                        doctor_user.id if idx % 2 == 0 else admin.id,
                        thread["procedure_id"]
                    )
                    db.session.add(new_thread)
                    db.session.commit()
                    logger.info(f"Created thread: {thread['title']}")
                created_threads.append(new_thread)
            
            # Add a reply to each thread
            for thread in created_threads:
                reply = CommunityReply.query.filter_by(thread_id=thread.id).first()
                if not reply:
                    reply = CommunityReply(
                        thread_id=thread.id,
                        user_id=doctor_user.id if thread.user_id == admin.id else admin.id,
                        content=f"This is a reply to the thread about {thread.title}",
                        is_doctor_response=(thread.user_id != doctor_user.id),
                        created_at=datetime.utcnow(),
                        upvotes=random.randint(1, 10)
                    )
                    db.session.add(reply)
                    db.session.commit()
                    logger.info(f"Added reply to thread: {thread.title}")
            
            logger.info("\nStep 2 completed successfully!")
            logger.info("Created:")
            logger.info(f"- 5 procedures: {', '.join([p.procedure_name for p in created_procedures])}")
            logger.info(f"- 5 community threads with replies")
            
            # Testing instructions
            logger.info("\nTesting Instructions:")
            logger.info("1. Doctor Verification Workflow Test:")
            logger.info("   URL: /dashboard/admin/doctor-verifications")
            logger.info("   Login as: admin_test")
            logger.info("   Expected: Doctor Test appears with pending status")
            
            logger.info("\n2. Procedure Section Test:")
            logger.info("   URL: /procedures")
            logger.info("   Expected: 5 procedures displayed with Doctor Test as the doctor")
            
            logger.info("\n3. Community Section Test:")
            logger.info("   URL: /community")
            logger.info("   Expected: 5 threads displayed with their replies")
            
        except Exception as e:
            logger.error(f"Error in Step 2: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()