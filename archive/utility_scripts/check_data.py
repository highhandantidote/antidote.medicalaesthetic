#!/usr/bin/env python3
"""
Check data in the database for Antidote platform.

This script queries all relevant models and prints counts and details
to verify data presence in the database.
"""
import os
import logging
from app import create_app, db
from models import User, Doctor, Procedure, Category, BodyPart, Review, Community

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_data():
    """Check data in the database and print counts and details."""
    # Create the Flask app context
    app = create_app()
    
    with app.app_context():
        print("\n===== DATABASE DATA CHECK =====\n")
        
        # Check users
        users = User.query.all()
        print(f"Users: {len(users)}")
        for user in users:
            print(f"  {user.email or 'No email'} - {user.role or 'No role'} - {user.name or 'No name'}")
        print()
        
        # Check doctors
        doctors = Doctor.query.all()
        print(f"Doctors: {len(doctors)}")
        for doctor in doctors:
            doctor_name = doctor.name or (doctor.user.name if doctor.user else 'N/A')
            print(f"  {doctor_name} - {doctor.specialty or 'No specialty'}")
        print()
        
        # Check procedures
        procedures = Procedure.query.all()
        print(f"Procedures: {len(procedures)}")
        for procedure in procedures[:10]:  # Limit to first 10 to avoid overwhelming output
            category_name = procedure.category.name if procedure.category else 'N/A'
            print(f"  {procedure.name or 'No name'} - {category_name}")
        if len(procedures) > 10:
            print(f"  ... and {len(procedures) - 10} more procedures")
        print()
        
        # Check categories
        categories = Category.query.all()
        print(f"Categories: {len(categories)}")
        for category in categories:
            print(f"  {category.name or 'No name'}")
        print()
        
        # Check body parts
        body_parts = BodyPart.query.all()
        print(f"Body Parts: {len(body_parts)}")
        for body_part in body_parts:
            print(f"  {body_part.name or 'No name'}")
        print()
        
        # Check reviews
        reviews = Review.query.all()
        print(f"Reviews: {len(reviews)}")
        for review in reviews[:10]:  # Limit to first 10
            print(f"  Rating: {review.rating} - {review.content[:50] if review.content else 'No content'}...")
        if len(reviews) > 10:
            print(f"  ... and {len(reviews) - 10} more reviews")
        print()
        
        # Check community threads
        threads = Community.query.all()
        print(f"Community Threads: {len(threads)}")
        for thread in threads[:10]:  # Limit to first 10
            print(f"  {thread.title or 'No title'} - {thread.category or 'No category'}")
        if len(threads) > 10:
            print(f"  ... and {len(threads) - 10} more threads")
            
        print("\n===== END OF DATABASE CHECK =====\n")

if __name__ == '__main__':
    check_data()