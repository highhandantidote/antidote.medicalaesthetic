#!/usr/bin/env python3
"""
Create an admin user for the Antidote platform.

This script creates an admin user with the required fields in the database.
"""
import logging
from app import create_app, db
from models import User
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_user():
    """Create an admin user in the database."""
    
    # Create app
    app = create_app()
    
    # Admin user details
    admin_details = {
        'name': 'Admin User',
        'email': 'admin@antidote.com',
        'username': 'admin',
        'phone_number': '9999999999',  # Placeholder phone number
        'role': 'admin',
        'role_type': 'admin',
        'is_verified': True,
        'password': 'Admin1234'
    }
    
    try:
        with app.app_context():
            # Check if the admin user already exists
            existing_user = User.query.filter_by(email=admin_details['email']).first()
            if existing_user:
                logger.info("Admin user with email %s already exists", admin_details['email'])
                existing_user.role = 'admin'  # Ensure the role is set to admin
                existing_user.is_verified = True
                db.session.commit()
                logger.info("Updated existing user to admin role")
                return existing_user
            
            # Create a new admin user
            admin_user = User(
                name=admin_details['name'],
                email=admin_details['email'],
                username=admin_details['username'],
                phone_number=admin_details['phone_number'],
                role=admin_details['role'],
                role_type=admin_details['role_type'],
                is_verified=admin_details['is_verified']
            )
            admin_user.set_password(admin_details['password'])
            
            # Add and commit to database
            db.session.add(admin_user)
            db.session.commit()
            logger.info("Created new admin user with email %s", admin_details['email'])
            return admin_user
    except Exception as e:
        logger.error("Error creating admin user: %s", str(e))
        return None

if __name__ == "__main__":
    admin_user = create_admin_user()
    if admin_user:
        logger.info("Admin user creation/update successful")
        logger.info("ID: %s, Name: %s, Email: %s", admin_user.id, admin_user.name, admin_user.email)
        logger.info("Log in with email: %s and password: Admin1234", admin_user.email)
    else:
        logger.error("Failed to create admin user")