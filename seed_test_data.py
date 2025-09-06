"""
Seed test data for the Antidote platform.

This script adds a small set of procedures, doctors, and community threads
to demonstrate the search and autocomplete functionality.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import models and database
from app import db, create_app
from models import User, BodyPart, Category, Procedure, Doctor, Thread

# Create the Flask application
app = create_app()

def create_users():
    """Create test users."""
    users = []
    
    # Create admin user
    admin = User(
        username="admin",
        name="Admin User",
        email="admin@antidote.com",
        phone_number="+1234567890",
        role="admin"
    )
    users.append(admin)
    
    # Create regular users
    for i in range(1, 4):
        user = User(
            username=f"user{i}",
            name=f"User {i}",
            email=f"user{i}@example.com",
            phone_number=f"+1234567{i:03d}",
            role="user"
        )
        users.append(user)
        
    # Create doctor users
    for i in range(1, 4):
        doctor_user = User(
            username=f"doctor{i}",
            name=f"Doctor {i}",
            email=f"doctor{i}@hospital.com",
            phone_number=f"+9876543{i:03d}",
            role="doctor"
        )
        users.append(doctor_user)
    
    db.session.add_all(users)
    db.session.commit()
    logger.info(f"Created {len(users)} users")
    return users

def create_body_parts():
    """Create body parts for procedures."""
    body_parts = [
        BodyPart(name="Face", description="Facial procedures including nose, chin, cheeks"),
        BodyPart(name="Breast", description="Breast enhancement, reduction, and reconstruction"),
        BodyPart(name="Body", description="Body contouring including tummy tuck, liposuction"),
        BodyPart(name="Skin", description="Skin treatments including chemical peels, laser resurfacing")
    ]
    
    db.session.add_all(body_parts)
    db.session.commit()
    logger.info(f"Created {len(body_parts)} body parts")
    return body_parts

def create_categories(body_parts):
    """Create procedure categories."""
    categories = []
    
    # Face categories
    face = body_parts[0]
    categories.extend([
        Category(name="Nose", description="Rhinoplasty and related procedures", body_part_id=face.id),
        Category(name="Facial Contouring", description="Procedures for facial structure", body_part_id=face.id)
    ])
    
    # Breast categories
    breast = body_parts[1]
    categories.extend([
        Category(name="Breast Augmentation", description="Procedures to increase breast size", body_part_id=breast.id),
        Category(name="Breast Reduction", description="Procedures to reduce breast size", body_part_id=breast.id)
    ])
    
    # Body categories
    body = body_parts[2]
    categories.extend([
        Category(name="Body Contouring", description="Procedures to reshape the body", body_part_id=body.id),
        Category(name="Fat Reduction", description="Procedures to reduce fat", body_part_id=body.id)
    ])
    
    # Skin categories
    skin = body_parts[3]
    categories.extend([
        Category(name="Skin Resurfacing", description="Procedures to improve skin texture", body_part_id=skin.id),
        Category(name="Anti-Aging", description="Procedures to reduce signs of aging", body_part_id=skin.id)
    ])
    
    db.session.add_all(categories)
    db.session.commit()
    logger.info(f"Created {len(categories)} categories")
    return categories

def create_procedures(categories):
    """Create procedures."""
    procedures = []
    
    # Nose procedures
    nose_category = categories[0]
    procedures.extend([
        Procedure(
            procedure_name="Rhinoplasty",
            short_description="Reshape the nose for improved appearance",
            overview="Rhinoplasty is a surgical procedure that changes the shape of the nose.",
            procedure_details="The surgery can change the size, shape, or proportions of your nose.",
            ideal_candidates="People who are unhappy with the appearance of their nose.",
            risks="Infection, scarring, breathing difficulties.",
            body_part=nose_category.body_part.name,
            category_id=nose_category.id,
            min_cost=5000,
            max_cost=15000,
            recovery_time="1-2 weeks",
            procedure_types="Surgical"
        ),
        Procedure(
            procedure_name="Non-Surgical Rhinoplasty",
            short_description="Temporarily reshape the nose with fillers",
            overview="Non-surgical rhinoplasty is a medical procedure in which injectable fillers are used to alter and shape a person's nose without invasive surgery.",
            procedure_details="The procedure involves injecting fillers to change the appearance of the nose.",
            ideal_candidates="People seeking temporary changes to their nose without surgery.",
            risks="Bruising, swelling, filler migration, vascular complications.",
            body_part=nose_category.body_part.name,
            category_id=nose_category.id,
            min_cost=800,
            max_cost=2000,
            recovery_time="1-2 days",
            procedure_types="Non-Surgical"
        )
    ])
    
    # Facial Contouring procedures
    facial_category = categories[1]
    procedures.extend([
        Procedure(
            procedure_name="Chin Augmentation",
            short_description="Enhance chin projection for facial harmony",
            overview="Chin augmentation is a surgical procedure to reshape or enhance the size of the chin.",
            procedure_details="It may be done either by inserting an implant or by moving or reshaping bones.",
            ideal_candidates="People with recessed or weak chins seeking better facial balance.",
            risks="Infection, implant displacement, numbness.",
            body_part=facial_category.body_part.name,
            category_id=facial_category.id,
            min_cost=2500,
            max_cost=7500,
            recovery_time="1-2 weeks",
            procedure_types="Surgical"
        ),
        Procedure(
            procedure_name="Cheek Augmentation",
            short_description="Enhance cheek volume for a youthful appearance",
            overview="Cheek augmentation is a procedure that adds volume to areas of the face that may have lost their fullness due to aging.",
            procedure_details="It can be performed using solid implants, fat grafting, or injectable fillers.",
            ideal_candidates="People with flat cheeks or facial volume loss.",
            risks="Infection, asymmetry, implant shifting.",
            body_part=facial_category.body_part.name,
            category_id=facial_category.id,
            min_cost=2000,
            max_cost=6000,
            recovery_time="1-2 weeks",
            procedure_types="Surgical,Non-Surgical"
        )
    ])
    
    # Breast Augmentation procedures
    breast_aug_category = categories[2]
    procedures.extend([
        Procedure(
            procedure_name="Breast Implants",
            short_description="Enhance breast size and shape with implants",
            overview="Breast implant surgery involves using implants to increase breast size or restore breast volume.",
            procedure_details="The surgery involves placing silicone or saline implants under breast tissue or chest muscles.",
            ideal_candidates="People who desire larger breasts or want to restore breast volume.",
            risks="Capsular contracture, implant rupture, infection.",
            body_part=breast_aug_category.body_part.name,
            category_id=breast_aug_category.id,
            min_cost=5000,
            max_cost=10000,
            recovery_time="4-6 weeks",
            procedure_types="Surgical"
        ),
        Procedure(
            procedure_name="Fat Transfer Breast Augmentation",
            short_description="Use your own fat to enhance breast size",
            overview="Fat transfer breast augmentation uses liposuction to take fat from other parts of your body and inject it into your breasts.",
            procedure_details="This is a natural alternative to implants, using fat from your own body.",
            ideal_candidates="People wanting modest breast enhancement using natural tissue.",
            risks="Fat reabsorption, asymmetry, cysts.",
            body_part=breast_aug_category.body_part.name,
            category_id=breast_aug_category.id,
            min_cost=6000,
            max_cost=12000,
            recovery_time="2-3 weeks",
            procedure_types="Surgical"
        )
    ])
    
    # Add more procedures for other categories
    for category in categories[3:]:
        for i in range(1, 3):
            procedures.append(
                Procedure(
                    procedure_name=f"{category.name} Procedure {i}",
                    short_description=f"Sample {category.name.lower()} procedure {i}",
                    overview=f"This is a sample {category.name.lower()} procedure for testing.",
                    procedure_details="Detailed procedure information would go here.",
                    ideal_candidates="People seeking this specific treatment.",
                    risks="Standard risks include infection and adverse reactions.",
                    body_part=category.body_part.name,
                    category_id=category.id,
                    min_cost=1000 * i,
                    max_cost=5000 * i,
                    recovery_time=f"{i} weeks",
                    procedure_types="Surgical" if i % 2 == 0 else "Non-Surgical"
                )
            )
    
    db.session.add_all(procedures)
    db.session.commit()
    logger.info(f"Created {len(procedures)} procedures")
    return procedures

def create_doctors(users, procedures):
    """Create doctors."""
    doctors = []
    doctor_users = [user for user in users if user.role == "doctor"]
    
    specialties = [
        "Facial Plastic Surgery",
        "Breast and Body Contouring",
        "Rhinoplasty Specialist"
    ]
    
    cities = ["New York", "Los Angeles", "Chicago", "Miami", "Dallas"]
    states = ["NY", "CA", "IL", "FL", "TX"]
    
    for i, doctor_user in enumerate(doctor_users):
        # Pick a primary specialty for this doctor
        specialty = specialties[i % len(specialties)]
        city = cities[i % len(cities)]
        state = states[i % len(states)]
        
        # Create the doctor profile
        doctor = Doctor(
            name=f"Dr. {doctor_user.username.capitalize()}",
            user_id=doctor_user.id,
            specialty=specialty,
            bio=f"Experienced {specialty.lower()} specialist with over {random.randint(5, 20)} years of experience.",
            city=city,
            state=state,
            verified=True,
            rating=round(random.uniform(4.0, 5.0), 1),
            reviews_count=random.randint(10, 100)
        )
        
        # Associate some procedures with this doctor
        if procedures:
            # Pick 2-4 procedures for this doctor
            doctor_procedures = random.sample(procedures, min(random.randint(2, 4), len(procedures)))
            doctor.procedures = doctor_procedures
        
        doctors.append(doctor)
    
    db.session.add_all(doctors)
    db.session.commit()
    logger.info(f"Created {len(doctors)} doctors")
    return doctors

def create_threads(users, procedures):
    """Create community threads."""
    threads = []
    regular_users = [user for user in users if user.role == "user"]
    
    thread_titles = [
        "My Rhinoplasty Experience",
        "Considering Breast Augmentation - Advice?",
        "Chin Implant vs. Fillers - Which is Better?",
        "Recovery After Cheek Augmentation",
        "Fat Transfer vs. Implants for Breast Augmentation",
        "How to Choose the Right Plastic Surgeon"
    ]
    
    for i, title in enumerate(thread_titles):
        # Create a thread
        user = random.choice(regular_users)
        procedure = random.choice(procedures) if procedures else None
        
        created_at = datetime.now() - timedelta(days=random.randint(1, 30))
        
        thread = Thread(
            title=title,
            content=f"This is a sample thread about {title.lower()}. It contains information about the procedure, recovery, and results.",
            user_id=user.id,
            procedure_id=procedure.id if procedure else None,
            created_at=created_at,
            view_count=random.randint(10, 100),
            reply_count=random.randint(0, 10),
            keywords=["plastic surgery", procedure.procedure_name.lower() if procedure else "procedure"] + title.lower().split()[:2]
        )
        
        threads.append(thread)
    
    db.session.add_all(threads)
    db.session.commit()
    logger.info(f"Created {len(threads)} community threads")
    return threads

def main():
    """Seed the database with test data."""
    with app.app_context():
        try:
            # Check if data already exists
            existing_procedures = Procedure.query.count()
            existing_doctors = Doctor.query.count()
            existing_threads = Thread.query.count()
            
            if existing_procedures > 0 or existing_doctors > 0 or existing_threads > 0:
                logger.info("Data already exists in the database. Skipping seeding.")
                logger.info(f"Existing records: {existing_procedures} procedures, {existing_doctors} doctors, {existing_threads} threads")
                return
            
            # Create test data
            users = create_users()
            body_parts = create_body_parts()
            categories = create_categories(body_parts)
            procedures = create_procedures(categories)
            doctors = create_doctors(users, procedures)
            threads = create_threads(users, procedures)
            
            logger.info("Database seeded successfully!")
            logger.info(f"Created {len(users)} users, {len(body_parts)} body parts, {len(categories)} categories")
            logger.info(f"Created {len(procedures)} procedures, {len(doctors)} doctors, {len(threads)} threads")
            
        except Exception as e:
            logger.error(f"Error seeding database: {str(e)}")
            db.session.rollback()
            raise e

if __name__ == "__main__":
    main()