#!/usr/bin/env python3
"""
Add test data to the database for development and testing.

This script adds test procedures, doctors, users, and community threads to the database.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, Column, Integer, Text, Float, Boolean, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database engine using DATABASE_URL
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Define models to match the application models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(Text, unique=True, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    first_name = Column(Text)
    last_name = Column(Text)
    phone = Column(Text)
    role = Column(Text, default='user')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_verified = Column(Boolean, default=False)

class Doctor(Base):
    __tablename__ = 'doctors'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(Text, nullable=False)
    specialty = Column(Text, nullable=False)
    qualification = Column(Text, nullable=False)
    experience = Column(Integer)
    bio = Column(Text)
    clinic_address = Column(Text)
    profile_photo = Column(Text)
    consultation_fee = Column(Float)
    availability = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    avg_rating = Column(Float, default=4.5)

class BodyPart(Base):
    __tablename__ = 'body_parts'
    
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    display_name = Column(Text)
    description = Column(Text)

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    display_name = Column(Text)
    description = Column(Text)
    body_part_id = Column(Integer, ForeignKey('body_parts.id'))

class Procedure(Base):
    __tablename__ = 'procedures'
    
    id = Column(Integer, primary_key=True)
    procedure_name = Column(Text, nullable=False, unique=True)
    short_description = Column(Text, nullable=False)
    overview = Column(Text, nullable=False)
    procedure_details = Column(Text, nullable=False)
    ideal_candidates = Column(Text, nullable=False)
    recovery_process = Column(Text)
    risks = Column(Text)
    benefits = Column(Text)
    min_cost = Column(Integer)
    max_cost = Column(Integer)
    category_id = Column(Integer, ForeignKey('categories.id'))
    body_part = Column(Text)
    thumbnail = Column(Text)
    avg_rating = Column(Float, default=4.2)
    created_at = Column(DateTime, default=datetime.utcnow)

class Thread(Base):
    __tablename__ = 'threads'
    
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_anonymous = Column(Boolean, default=False)
    image_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    view_count = Column(Integer, default=0)
    is_resolved = Column(Boolean, default=False)
    tags = Column(ARRAY(Text))

class Reply(Base):
    __tablename__ = 'replies'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    thread_id = Column(Integer, ForeignKey('threads.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('replies.id'))
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_helpful = Column(Boolean, default=False)
    is_doctor_reply = Column(Boolean, default=False)

def add_test_users():
    """Add test users with different roles."""
    users = [
        {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'userpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '9876543210',
            'role': 'user',
            'is_verified': True
        },
        {
            'username': 'testdoctor',
            'email': 'testdoctor@example.com',
            'password': 'doctorpass123',
            'first_name': 'Doctor',
            'last_name': 'Test',
            'phone': '9876543211',
            'role': 'doctor',
            'is_verified': True
        },
        {
            'username': 'testadmin',
            'email': 'testadmin@example.com',
            'password': 'adminpass123',
            'first_name': 'Admin',
            'last_name': 'User',
            'phone': '9876543212',
            'role': 'admin',
            'is_verified': True
        }
    ]
    
    added_users = []
    
    for user_data in users:
        # Check if user already exists
        existing_user = session.query(User).filter_by(email=user_data['email']).first()
        if existing_user:
            logger.info(f"User {user_data['email']} already exists, skipping...")
            added_users.append(existing_user)
            continue
        
        # Create new user
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password_hash=generate_password_hash(user_data['password']),
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            phone=user_data['phone'],
            role=user_data['role'],
            is_verified=user_data['is_verified']
        )
        
        session.add(user)
        logger.info(f"Added user: {user_data['email']} with role {user_data['role']}")
        
        # Flush to get the user ID for the doctor profile
        session.flush()
        added_users.append(user)
    
    # Create doctor profile for the doctor user
    doctor_user = next((u for u in added_users if u.role == 'doctor'), None)
    if doctor_user:
        # Check if doctor profile already exists
        existing_doctor = session.query(Doctor).filter_by(user_id=doctor_user.id).first()
        if existing_doctor:
            logger.info(f"Doctor profile for user_id {doctor_user.id} already exists, skipping...")
        else:
            doctor = Doctor(
                user_id=doctor_user.id,
                name=f"Dr. {doctor_user.first_name} {doctor_user.last_name}",
                specialty="Plastic Surgeon",
                qualification="MBBS, MS, MCh (Plastic Surgery)",
                experience=12,
                bio="Experienced plastic surgeon specializing in facial reconstruction and aesthetic procedures.",
                clinic_address="123 Medical Center, Mumbai, India",
                consultation_fee=1500.0,
                availability="Mon-Fri: 10:00 AM - 5:00 PM"
            )
            
            session.add(doctor)
            logger.info(f"Added doctor profile for {doctor_user.email}")
    
    session.commit()
    return added_users

def add_body_parts_and_categories():
    """Add body parts and categories for procedures."""
    body_parts = [
        {
            'name': 'face',
            'display_name': 'Face',
            'description': 'Procedures related to facial features and appearance'
        },
        {
            'name': 'head',
            'display_name': 'Head & Hair',
            'description': 'Procedures related to the head, scalp, and hair'
        },
        {
            'name': 'body',
            'display_name': 'Body',
            'description': 'Procedures for body contouring and enhancement'
        },
        {
            'name': 'skin',
            'display_name': 'Skin',
            'description': 'Procedures targeting skin conditions and appearance'
        }
    ]
    
    added_body_parts = {}
    
    for bp_data in body_parts:
        # Check if body part already exists
        existing_bp = session.query(BodyPart).filter_by(name=bp_data['name']).first()
        if existing_bp:
            logger.info(f"Body part {bp_data['name']} already exists, skipping...")
            added_body_parts[bp_data['name']] = existing_bp
            continue
        
        # Create new body part
        body_part = BodyPart(
            name=bp_data['name'],
            display_name=bp_data['display_name'],
            description=bp_data['description']
        )
        
        session.add(body_part)
        session.flush()
        added_body_parts[bp_data['name']] = body_part
        logger.info(f"Added body part: {bp_data['name']}")
    
    # Categories for each body part
    categories = [
        {
            'name': 'rhinoplasty',
            'display_name': 'Rhinoplasty',
            'description': 'Nose reshaping procedures',
            'body_part': 'face'
        },
        {
            'name': 'facelift',
            'display_name': 'Facelift',
            'description': 'Facial rejuvenation procedures',
            'body_part': 'face'
        },
        {
            'name': 'hair_transplant',
            'display_name': 'Hair Transplant',
            'description': 'Hair restoration procedures',
            'body_part': 'head'
        },
        {
            'name': 'liposuction',
            'display_name': 'Liposuction',
            'description': 'Fat removal procedures',
            'body_part': 'body'
        },
        {
            'name': 'scar_revision',
            'display_name': 'Scar Revision',
            'description': 'Scar treatment procedures',
            'body_part': 'skin'
        }
    ]
    
    added_categories = {}
    
    for cat_data in categories:
        # Check if category already exists
        existing_cat = session.query(Category).filter_by(name=cat_data['name']).first()
        if existing_cat:
            logger.info(f"Category {cat_data['name']} already exists, skipping...")
            added_categories[cat_data['name']] = existing_cat
            continue
        
        # Get body part ID
        body_part = added_body_parts.get(cat_data['body_part'])
        if not body_part:
            logger.warning(f"Body part {cat_data['body_part']} not found, skipping category {cat_data['name']}...")
            continue
        
        # Create new category
        category = Category(
            name=cat_data['name'],
            display_name=cat_data['display_name'],
            description=cat_data['description'],
            body_part_id=body_part.id
        )
        
        session.add(category)
        session.flush()
        added_categories[cat_data['name']] = category
        logger.info(f"Added category: {cat_data['name']}")
    
    session.commit()
    return added_body_parts, added_categories

def add_procedures(categories):
    """Add test procedures."""
    procedures = [
        {
            'name': 'Rhinoplasty',
            'short_description': 'Nose reshaping surgery to improve appearance and function',
            'overview': 'Rhinoplasty is a surgical procedure that changes the shape of the nose. The motivation for rhinoplasty may be to change the appearance of the nose, improve breathing or both.',
            'procedure_details': 'During rhinoplasty, the surgeon makes incisions to access the bones and cartilage that support the nose. Depending on the desired result, some bone and cartilage may be removed, or tissue may be added. After the surgeon has rearranged and reshaped the bone and cartilage, the skin and tissue is redraped over the structure of the nose.',
            'ideal_candidates': 'People with facial growth completion, generally over 16 years old. You should be physically healthy and have realistic goals for improvement of your appearance.',
            'recovery_process': 'Most patients can return to work or school in 1-2 weeks. Strenuous activity should be avoided for 3-6 weeks. Final results may take up to a year as subtle swelling resolves.',
            'risks': 'Bleeding, infection, adverse reaction to anesthesia, temporary or permanent numbness, difficulty breathing, unsatisfactory results requiring revision surgery.',
            'benefits': 'Improved appearance, better breathing, increased self-confidence.',
            'min_cost': 80000,
            'max_cost': 150000,
            'category': 'rhinoplasty',
            'body_part': 'Nose'
        },
        {
            'name': 'Hair Transplant (FUE)',
            'short_description': 'Modern follicular unit extraction technique for natural-looking hair restoration',
            'overview': 'Follicular Unit Extraction (FUE) is a minimally invasive hair transplantation technique that involves extracting individual hair follicles from the donor part of the body and moving them to a bald or balding part.',
            'procedure_details': 'In FUE hair transplant, individual follicular units containing 1-4 hairs are removed under local anesthesia. These units are then transplanted to the balding areas of the scalp. The procedure is performed using a specialized punch device.',
            'ideal_candidates': 'Men and women with androgenic alopecia (pattern baldness), thinning hair, or those who want to restore receding hairlines.',
            'recovery_process': 'Recovery is relatively quick with minimal discomfort. Most patients can return to work within 2-3 days. The transplanted hair will shed within 2-3 weeks, and new growth usually begins in 3-4 months.',
            'risks': 'Infection, bleeding, scarring, unnatural-looking hair patterns, poor hair growth.',
            'benefits': 'Natural-looking results, minimal scarring, faster recovery time compared to traditional methods.',
            'min_cost': 100000,
            'max_cost': 300000,
            'category': 'hair_transplant',
            'body_part': 'Scalp'
        },
        {
            'name': 'Facelift (Rhytidectomy)',
            'short_description': 'Surgical procedure to reduce sagging and wrinkles for a more youthful appearance',
            'overview': 'A facelift, or rhytidectomy, is a surgical procedure that improves visible signs of aging in the face and neck. It addresses sagging facial skin, deep creases, and lost muscle tone.',
            'procedure_details': 'During a facelift, the surgeon makes incisions around the hairline and ears, then lifts and tightens the underlying facial muscles and tissues. Excess skin is removed, and the remaining skin is repositioned over the newly tightened facial tissues.',
            'ideal_candidates': 'Adults with facial skin laxity, deep lines, and wrinkles who are generally healthy and non-smokers.',
            'recovery_process': 'Recovery typically takes 2-3 weeks. Bruising and swelling are common in the first week. Most patients can resume normal activities after 2 weeks, though final results may take several months as swelling resolves.',
            'risks': 'Scarring, nerve injury, hair loss around incisions, skin necrosis, asymmetry.',
            'benefits': 'Younger-looking appearance, improved facial contours, long-lasting results (5-10 years).',
            'min_cost': 150000,
            'max_cost': 350000,
            'category': 'facelift',
            'body_part': 'Face'
        },
        {
            'name': 'Liposuction',
            'short_description': 'Surgical fat removal procedure for body contouring',
            'overview': 'Liposuction is a cosmetic procedure that removes fat deposits using suction. It is not a weight-loss method but rather a body contouring technique.',
            'procedure_details': 'During liposuction, small incisions are made in the target area. A thin tube called a cannula is inserted through these incisions and connected to a vacuum device, which suctions out the fat.',
            'ideal_candidates': 'Adults within 30% of their ideal weight with firm, elastic skin and good muscle tone. Best for those with localized fat deposits that don\'t respond to diet and exercise.',
            'recovery_process': 'Recovery varies depending on the extent of the procedure. Expect to wear compression garments for several weeks. Most patients return to work within a week, but should avoid strenuous activity for 2-4 weeks.',
            'risks': 'Contour irregularities, fluid accumulation, infection, internal puncture, fat embolism, thermal burns.',
            'benefits': 'Improved body contours, removal of stubborn fat deposits, long-lasting results with weight maintenance.',
            'min_cost': 60000,
            'max_cost': 200000,
            'category': 'liposuction',
            'body_part': 'Body'
        },
        {
            'name': 'Scar Revision',
            'short_description': 'Procedures to improve the appearance of scars',
            'overview': 'Scar revision is a procedure to minimize a scar so that it is less conspicuous and blends in with the surrounding skin tone and texture.',
            'procedure_details': 'Techniques include surgical excision, laser treatments, dermabrasion, microneedling, and injectable treatments. The method chosen depends on the scar\'s size, type, location, and individual factors.',
            'ideal_candidates': 'Anyone with a scar that is cosmetically concerning. Best results in non-smokers with good general health and realistic expectations.',
            'recovery_process': 'Recovery varies depending on the technique used. Surgical revision may require 1-2 weeks, while less invasive techniques may have minimal downtime.',
            'risks': 'Infection, bleeding, scarring (possibility of worse scarring), skin discoloration, asymmetry.',
            'benefits': 'Improved scar appearance, enhanced self-confidence, reduction in physical discomfort from tight scars.',
            'min_cost': 20000,
            'max_cost': 100000,
            'category': 'scar_revision',
            'body_part': 'Skin'
        }
    ]
    
    added_procedures = []
    
    for proc_data in procedures:
        # Check if procedure already exists
        existing_proc = session.query(Procedure).filter_by(procedure_name=proc_data['name']).first()
        if existing_proc:
            logger.info(f"Procedure {proc_data['name']} already exists, skipping...")
            added_procedures.append(existing_proc)
            continue
        
        # Get category
        category = categories.get(proc_data['category'])
        if not category:
            logger.warning(f"Category {proc_data['category']} not found, adding procedure without category...")
        
        # Create new procedure
        procedure = Procedure(
            procedure_name=proc_data['name'],
            short_description=proc_data['short_description'],
            overview=proc_data['overview'],
            procedure_details=proc_data['procedure_details'],
            ideal_candidates=proc_data['ideal_candidates'],
            recovery_process=proc_data['recovery_process'],
            risks=proc_data['risks'],
            benefits=proc_data['benefits'],
            min_cost=proc_data['min_cost'],
            max_cost=proc_data['max_cost'],
            category_id=category.id if category else None,
            body_part=proc_data['body_part']
        )
        
        session.add(procedure)
        added_procedures.append(procedure)
        logger.info(f"Added procedure: {proc_data['name']}")
    
    session.commit()
    return added_procedures

def add_community_threads(users, procedures):
    """Add community threads and replies."""
    # Get user IDs
    user_ids = {user.role: user.id for user in users}
    
    # Create threads
    threads = [
        {
            'title': 'My rhinoplasty experience - so happy with the results!',
            'content': 'I had a rhinoplasty procedure done last month and I\'m absolutely thrilled with the results. My nose looks so natural and it\'s made a huge difference to my confidence. I was nervous about the recovery but it was much easier than I expected. Happy to answer any questions!',
            'user_id': user_ids.get('user'),
            'is_anonymous': False,
            'tags': ['rhinoplasty', 'success story', 'recovery']
        },
        {
            'title': 'Questions about hair transplant procedure',
            'content': 'I\'m considering a hair transplant but I have a few questions:\n\n1. How painful is the procedure?\n2. How long before I see results?\n3. How natural will it look?\n4. What\'s the maintenance like afterward?\n\nIf anyone has experience with this, I\'d appreciate your insights!',
            'user_id': user_ids.get('user'),
            'is_anonymous': True,
            'tags': ['hair transplant', 'questions', 'advice needed']
        },
        {
            'title': 'Recommendations for facial scar treatment',
            'content': 'I have a scar on my cheek from an accident when I was younger. It\'s about 3cm long and quite noticeable. I\'m looking into treatments to reduce its appearance. Has anyone had experience with scar revision surgery or alternative treatments like laser therapy? Any recommendations on doctors or clinics in Mumbai that specialize in this?',
            'user_id': user_ids.get('user'),
            'is_anonymous': False,
            'tags': ['scar revision', 'recommendations', 'treatment options']
        }
    ]
    
    added_threads = []
    
    for thread_data in threads:
        # Create new thread
        thread = Thread(
            title=thread_data['title'],
            content=thread_data['content'],
            user_id=thread_data['user_id'],
            is_anonymous=thread_data['is_anonymous'],
            tags=thread_data['tags'],
            created_at=datetime.utcnow() - timedelta(days=6),
            view_count=54
        )
        
        session.add(thread)
        session.flush()
        added_threads.append(thread)
        logger.info(f"Added thread: {thread_data['title']}")
    
    # Add replies to threads
    doctor_user_id = user_ids.get('doctor')
    
    replies = [
        {
            'thread_id': added_threads[0].id,
            'content': 'So glad to hear your rhinoplasty went well! I\'m considering this procedure too. Did you have any breathing issues afterward?',
            'user_id': user_ids.get('user'),
            'is_anonymous': False
        },
        {
            'thread_id': added_threads[0].id,
            'content': 'Thank you for sharing your experience! As a plastic surgeon, I always appreciate hearing positive outcomes. Rhinoplasty recovery varies from person to person, but most patients are very satisfied with the results after the initial swelling subsides. If you have any concerns during your continued recovery, don\'t hesitate to contact your surgeon.',
            'user_id': doctor_user_id,
            'is_anonymous': False,
            'is_doctor_reply': True,
            'is_helpful': True
        },
        {
            'thread_id': added_threads[1].id,
            'content': 'I had an FUE hair transplant about a year ago. To answer your questions:\n\n1. The procedure itself isn\'t very painful as they use local anesthesia. There\'s some discomfort for the first few days afterward.\n2. You\'ll see initial growth around 3-4 months, but the full results take about a year.\n3. Mine looks completely natural - no one can tell I had it done unless I tell them.\n4. Maintenance is minimal - just treat it like your normal hair.',
            'user_id': user_ids.get('user'),
            'is_anonymous': False
        },
        {
            'thread_id': added_threads[2].id,
            'content': 'I\'ve treated many patients with facial scars similar to what you\'ve described. There are several effective options including surgical revision, laser therapy, and microneedling. The best approach depends on the scar\'s age, depth, and your skin type. I\'d recommend consulting with a plastic surgeon or dermatologist who specializes in scar revision for a personalized assessment. If you\'d like to discuss your case further, feel free to book a consultation.',
            'user_id': doctor_user_id,
            'is_anonymous': False,
            'is_doctor_reply': True,
            'is_helpful': True
        }
    ]
    
    for reply_data in replies:
        # Create new reply
        reply = Reply(
            content=reply_data['content'],
            user_id=reply_data['user_id'],
            thread_id=reply_data['thread_id'],
            is_anonymous=reply_data['is_anonymous'],
            is_doctor_reply=reply_data.get('is_doctor_reply', False),
            is_helpful=reply_data.get('is_helpful', False),
            created_at=datetime.utcnow() - timedelta(days=4)
        )
        
        session.add(reply)
        logger.info(f"Added reply to thread ID {reply_data['thread_id']}")
    
    session.commit()
    return added_threads

def main():
    """Main function to add test data."""
    try:
        # Add test users
        users = add_test_users()
        
        # Add body parts and categories
        body_parts, categories = add_body_parts_and_categories()
        
        # Add procedures
        procedures = add_procedures(categories)
        
        # Add community threads and replies
        threads = add_community_threads(users, procedures)
        
        # Print user credentials for testing
        print("\n===== TEST ACCOUNT CREDENTIALS =====")
        print("Regular user:")
        print("  Email: testuser@example.com")
        print("  Password: userpass123")
        print("\nDoctor:")
        print("  Email: testdoctor@example.com")
        print("  Password: doctorpass123")
        print("\nAdmin:")
        print("  Email: testadmin@example.com")
        print("  Password: adminpass123")
        
        print("\n===== DATA SUMMARY =====")
        print(f"Added {len(users)} users")
        print(f"Added {len(body_parts)} body parts")
        print(f"Added {len(categories)} categories")
        print(f"Added {len(procedures)} procedures")
        print(f"Added {len(threads)} community threads with replies")
        
        print("\nTest data added successfully!")
        return 0
    
    except Exception as e:
        logger.error(f"Error adding test data: {str(e)}")
        session.rollback()
        return 1

if __name__ == "__main__":
    sys.exit(main())