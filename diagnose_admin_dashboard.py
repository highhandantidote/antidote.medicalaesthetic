"""
Script to diagnose admin dashboard database access issues.
This script directly queries the database and logs the results
to help diagnose why data isn't showing in the admin dashboard.
"""

import os
import logging
import datetime
from dotenv import load_dotenv
from app import app, db
from models import User, Doctor, Procedure, Lead, Review, Community, BodyPart, Category, Thread

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('admin_dashboard_diagnosis')

def check_database_tables():
    """
    Check all relevant database tables and log the contents.
    This helps diagnose if data exists but isn't being displayed.
    """
    logger.info("=== STARTING ADMIN DASHBOARD DIAGNOSIS ===")
    
    # Check users
    try:
        logger.info("Checking User table...")
        users = User.query.all()
        logger.info(f"Found {len(users)} users:")
        for user in users:
            logger.info(f"  User ID: {user.id}, Name: {getattr(user, 'username', 'N/A')}, Email: {getattr(user, 'email', 'N/A')}, Role: {getattr(user, 'role', 'N/A')}")
    except Exception as e:
        logger.error(f"Error querying User table: {e}")
    
    # Check doctors
    try:
        logger.info("Checking Doctor table...")
        doctors = Doctor.query.all()
        logger.info(f"Found {len(doctors)} doctors:")
        for doctor in doctors:
            logger.info(f"  Doctor ID: {doctor.id}, Name: {getattr(doctor, 'name', 'N/A')}, Specialty: {getattr(doctor, 'specialty', 'N/A')}")
    except Exception as e:
        logger.error(f"Error querying Doctor table: {e}")
    
    # Check procedures
    try:
        logger.info("Checking Procedure table...")
        procedures = Procedure.query.all()
        logger.info(f"Found {len(procedures)} procedures:")
        for procedure in procedures:
            logger.info(f"  Procedure ID: {procedure.id}, Name: {getattr(procedure, 'procedure_name', 'N/A')}")
    except Exception as e:
        logger.error(f"Error querying Procedure table: {e}")
    
    # Check leads
    try:
        logger.info("Checking Lead table...")
        leads = Lead.query.all()
        logger.info(f"Found {len(leads)} leads:")
        for lead in leads:
            logger.info(f"  Lead ID: {lead.id}, Status: {getattr(lead, 'status', 'N/A')}")
    except Exception as e:
        logger.error(f"Error querying Lead table: {e}")
    
    # Check reviews
    try:
        logger.info("Checking Review table...")
        reviews = Review.query.all()
        logger.info(f"Found {len(reviews)} reviews:")
        for review in reviews:
            logger.info(f"  Review ID: {review.id}, Rating: {getattr(review, 'rating', 'N/A')}")
    except Exception as e:
        logger.error(f"Error querying Review table: {e}")
        
    # Check community posts
    try:
        logger.info("Checking Community table...")
        posts = Community.query.all()
        logger.info(f"Found {len(posts)} community posts:")
        for post in posts:
            logger.info(f"  Post ID: {post.id}, Title: {getattr(post, 'title', 'N/A')}")
    except Exception as e:
        logger.error(f"Error querying Community table: {e}")
    
    # Check categories
    try:
        logger.info("Checking Category table...")
        categories = Category.query.all()
        logger.info(f"Found {len(categories)} categories:")
        for category in categories:
            logger.info(f"  Category ID: {category.id}, Name: {getattr(category, 'name', 'N/A')}")
    except Exception as e:
        logger.error(f"Error querying Category table: {e}")
        
    # Check body parts
    try:
        logger.info("Checking BodyPart table...")
        body_parts = BodyPart.query.all()
        logger.info(f"Found {len(body_parts)} body parts:")
        for body_part in body_parts:
            logger.info(f"  BodyPart ID: {body_part.id}, Name: {getattr(body_part, 'name', 'N/A')}")
    except Exception as e:
        logger.error(f"Error querying BodyPart table: {e}")
    
    # Check threads
    try:
        logger.info("Checking Thread table...")
        threads = Thread.query.all()
        logger.info(f"Found {len(threads)} threads:")
        for thread in threads:
            logger.info(f"  Thread ID: {thread.id}, Title: {getattr(thread, 'title', 'N/A')}")
    except Exception as e:
        logger.error(f"Error querying Thread table: {e}")
        
    logger.info("=== DIAGNOSIS COMPLETE ===")
    
if __name__ == "__main__":
    logger.info("Starting diagnosis script...")
    with app.app_context():
        check_database_tables()