"""
Quick seed script with minimal data for testing autocomplete.
"""

from app import db, create_app
from models import Procedure, Doctor, Thread, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask application
app = create_app()

def add_test_data():
    """Add minimal test data directly to test search and autocomplete."""
    with app.app_context():
        # Check if data already exists
        if Procedure.query.count() > 0:
            logger.info("Data already exists in the database. Skipping seeding.")
            return
            
        # Create a test user
        test_user = User(
            username="testuser",
            name="Test User",
            email="test@example.com",
            phone_number="+1234567890",
            role="user"
        )
        db.session.add(test_user)
        db.session.commit()
        
        # Create some procedures for search/autocomplete
        procedures = [
            Procedure(
                procedure_name="Rhinoplasty",
                short_description="Reshape the nose for improved appearance",
                overview="Rhinoplasty is a surgical procedure that changes the shape of the nose.",
                procedure_details="The surgery can change the size, shape, or proportions of your nose.",
                ideal_candidates="People who are unhappy with the appearance of their nose.",
                risks="Infection, scarring, breathing difficulties.",
                body_part="Face",
                min_cost=5000,
                max_cost=15000,
                recovery_time="1-2 weeks",
                procedure_types="Surgical"
            ),
            Procedure(
                procedure_name="Mini Rhinoplasty",
                short_description="Less invasive nose reshaping",
                overview="Mini rhinoplasty focuses on small modifications to the nose.",
                procedure_details="This procedure makes subtle changes to the nose with less recovery time.",
                ideal_candidates="People seeking minor nose adjustments.",
                risks="Swelling, bruising, incomplete correction.",
                body_part="Face",
                min_cost=3000,
                max_cost=8000,
                recovery_time="3-5 days",
                procedure_types="Surgical"
            ),
            Procedure(
                procedure_name="Breast Augmentation",
                short_description="Enhance breast size and shape",
                overview="Breast augmentation increases the size and improves the shape of the breasts.",
                procedure_details="The procedure involves placing implants to enhance breast size.",
                ideal_candidates="Women who desire larger breasts or want to restore breast volume.",
                risks="Capsular contracture, implant leakage, asymmetry.",
                body_part="Breast",
                min_cost=6000,
                max_cost=12000,
                recovery_time="4-6 weeks",
                procedure_types="Surgical"
            )
        ]
        db.session.add_all(procedures)
        db.session.commit()
        
        # Create a doctor
        doctor = Doctor(
            name="Dr. Smith",
            user_id=test_user.id,
            specialty="Rhinoplasty Specialist",
            bio="Experienced rhinoplasty specialist with over 15 years of experience.",
            experience=15,
            city="New York",
            state="NY",
            verified=True,
            rating=4.8,
            reviews_count=120
        )
        db.session.add(doctor)
        db.session.commit()
        
        # Create a few community threads
        threads = [
            Thread(
                title="My Rhinoplasty Experience",
                content="Just had rhinoplasty and wanted to share my experience. The recovery was easier than expected.",
                user_id=test_user.id,
                procedure_id=procedures[0].id,
                view_count=45,
                reply_count=5,
                keywords=["rhinoplasty", "experience", "recovery"]
            ),
            Thread(
                title="Rhinoplasty vs Mini Rhinoplasty",
                content="Trying to decide between a full rhinoplasty or a mini rhinoplasty. What are the key differences?",
                user_id=test_user.id,
                procedure_id=procedures[1].id,
                view_count=32,
                reply_count=3,
                keywords=["rhinoplasty", "mini rhinoplasty", "comparison"]
            )
        ]
        db.session.add_all(threads)
        db.session.commit()
        
        logger.info("Added test data for search autocomplete")
        logger.info(f"Created {len(procedures)} procedures, 1 doctor, {len(threads)} threads")

if __name__ == "__main__":
    add_test_data()