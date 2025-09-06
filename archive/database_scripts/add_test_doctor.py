"""
Add a test doctor account for development and testing purposes.

This script creates a test doctor user with:
- Email: testdoctor@antidote.com
- Password: doctorpass123
- Associated doctor profile with proper specialization
- Link to a procedure (Rhinoplasty)
"""
from app import db
from main import app
from models import User, Doctor, DoctorProcedure, Procedure, DoctorCategory, Category
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_doctor():
    """Create a test doctor account with proper setup."""
    # Use the existing Flask application
    with app.app_context():
        # Check if test doctor user already exists
        existing_user = User.query.filter_by(email='testdoctor@antidote.com').first()
        if existing_user:
            logger.info("Test doctor user already exists. Updating...")
            user = existing_user
            user.name = 'Test Doctor'
            user.role = 'doctor'
            user.phone_number = '1234567890'
            user.is_verified = True
            user.set_password('doctorpass123')
        else:
            # Create test doctor user
            logger.info("Creating new test doctor user...")
            user = User(
                email='testdoctor@antidote.com',
                name='Test Doctor',
                role='doctor',
                phone_number='1234567890',
                is_verified=True
            )
            user.set_password('doctorpass123')
            db.session.add(user)
        
        db.session.commit()
        logger.info(f"Test doctor user created/updated with ID: {user.id}")
        
        # Check if doctor profile already exists for this user
        existing_doctor = Doctor.query.filter_by(user_id=user.id).first()
        if existing_doctor:
            logger.info("Doctor profile already exists. Updating...")
            doctor = existing_doctor
            doctor.name = 'Dr. Test'
            doctor.specialty = 'Plastic Surgery'
            doctor.experience = 10
            doctor.city = 'New Delhi'
            doctor.state = 'Delhi'
            doctor.hospital = 'Test Hospital'
            doctor.consultation_fee = 2000
            doctor.is_verified = True
            doctor.rating = 4.5
            doctor.review_count = 10
            doctor.bio = 'Experienced plastic surgeon with expertise in facial rejuvenation.'
        else:
            # Create associated doctor profile
            logger.info("Creating new doctor profile...")
            doctor = Doctor(
                user_id=user.id,
                name='Dr. Test',
                specialty='Plastic Surgery',
                experience=10,
                city='New Delhi',
                state='Delhi',
                hospital='Test Hospital',
                consultation_fee=2000,
                is_verified=True,
                rating=4.5,
                review_count=10,
                bio='Experienced plastic surgeon with expertise in facial rejuvenation.'
            )
            db.session.add(doctor)
        
        db.session.commit()
        logger.info(f"Doctor profile created/updated with ID: {doctor.id}")
        
        # Create or get a procedure
        procedure = Procedure.query.filter_by(procedure_name='Rhinoplasty').first()
        if not procedure:
            logger.info("Creating new Rhinoplasty procedure...")
            procedure = Procedure(
                procedure_name='Rhinoplasty',
                short_description='Reshapes the nose for improved appearance and function',
                overview='Rhinoplasty is a surgical procedure that changes the shape of your nose by modifying the bone or cartilage.',
                procedure_details='The surgeon makes cuts within the nostrils or across the base of the nose, then reshapes the inner bone and cartilage to produce a more pleasing appearance.',
                ideal_candidates='People who are physically healthy, don\'t smoke, and have a positive outlook and realistic goals.',
                recovery_process='Swelling and bruising around the eyes and nose for 1-2 weeks. Final result visible after 1 year when all swelling subsides.',
                recovery_time='1-2 weeks for initial recovery, 6-12 months for complete healing',
                results_duration='Permanent',
                min_cost=35000,
                max_cost=105000,
                benefits='Improved appearance, better breathing, enhanced self-confidence',
                benefits_detailed='Better facial harmony and proportions. Can fix breathing problems caused by structural defects.',
                risks='Bleeding, infection, adverse anesthesia reactions, changes in skin sensation, nasal septal perforation',
                procedure_types='Open rhinoplasty, closed rhinoplasty, revision rhinoplasty',
                alternative_procedures='Non-surgical rhinoplasty using fillers (temporary results)',
                category_id=1,  # Will be created if doesn't exist
                popularity_score=100,
                body_part='Face',
                tags=['Surgical', 'Cosmetic']
            )
            db.session.add(procedure)
            db.session.commit()
            logger.info(f"Rhinoplasty procedure created with ID: {procedure.id}")
        
        # Make sure we have at least one category to work with
        category = Category.query.first()
        if not category:
            # Check if we have a body part
            from models import BodyPart
            body_part = BodyPart.query.first()
            if not body_part:
                body_part = BodyPart(
                    name="Face",
                    description="Facial procedures and treatments"
                )
                db.session.add(body_part)
                db.session.commit()
            
            # Create a category
            category = Category(
                name="Facial Procedures",
                body_part_id=body_part.id,
                description="Procedures that modify the face"
            )
            db.session.add(category)
            db.session.commit()
            logger.info(f"Created category: {category.name} with ID: {category.id}")
            
            # Update procedure with category if needed
            if procedure.category_id is None:
                procedure.category_id = category.id
                db.session.commit()
        
        # Link doctor to category (specialization)
        doctor_category = DoctorCategory.query.filter_by(
            doctor_id=doctor.id, 
            category_id=category.id
        ).first()
        
        if not doctor_category:
            doctor_category = DoctorCategory(
                doctor_id=doctor.id,
                category_id=category.id,
                is_verified=True
            )
            db.session.add(doctor_category)
            db.session.commit()
            logger.info(f"Linked doctor to category: {category.name}")
        
        # Link doctor to procedure
        doctor_procedure = DoctorProcedure.query.filter_by(
            doctor_id=doctor.id, 
            procedure_id=procedure.id
        ).first()
        
        if not doctor_procedure:
            doctor_procedure = DoctorProcedure(
                doctor_id=doctor.id, 
                procedure_id=procedure.id
            )
            db.session.add(doctor_procedure)
            db.session.commit()
            logger.info(f"Linked doctor to procedure: {procedure.procedure_name}")
            
        return {
            "user_id": user.id,
            "doctor_id": doctor.id,
            "procedure_id": procedure.id,
            "email": user.email,
            "password": "doctorpass123"
        }

if __name__ == "__main__":
    result = create_test_doctor()
    print(f"Test doctor created/updated successfully!")
    print(f"Email: {result['email']}")
    print(f"Password: {result['password']}")
    print(f"Doctor ID: {result['doctor_id']}")
    print(f"User ID: {result['user_id']}")
    print(f"To access dashboard: http://localhost:5000/dashboard/doctor/{result['doctor_id']}")