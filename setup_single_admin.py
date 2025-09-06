"""
Setup single admin account for the Antidote platform.

This script removes all existing admin accounts and creates only one admin account
with the specified credentials.
"""

import os
import sys
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_single_admin():
    """Remove all admin accounts and create only the specified one."""
    
    try:
        app = create_app()
        with app.app_context():
            # Create all database tables
            logger.info("Creating database tables...")
            db.create_all()
            
            # Remove all existing admin accounts
            logger.info("Removing all existing admin accounts...")
            admin_users = User.query.filter(
                (User.role == 'admin') | (User.role_type == 'admin')
            ).all()
            
            for admin in admin_users:
                logger.info(f"Removing admin user: {admin.email}")
                db.session.delete(admin)
            
            # Create the single admin account
            admin_email = "admin@antidote.fit"
            admin_password = "1@coconutwater"
            
            logger.info(f"Creating single admin account: {admin_email}")
            
            # Check if user already exists (just in case)
            existing_user = User.query.filter_by(email=admin_email).first()
            if existing_user:
                logger.info(f"User with email {admin_email} already exists, updating...")
                admin_user = existing_user
            else:
                admin_user = User()
            
            # Set admin user details
            admin_user.name = "Platform Administrator"
            admin_user.email = admin_email
            admin_user.username = "admin"
            admin_user.phone_number = "+1234567890"  # Required field
            admin_user.role = "admin"
            admin_user.role_type = "admin"
            admin_user.is_verified = True
            admin_user.created_at = datetime.utcnow()
            
            # Set password hash
            admin_user.set_password(admin_password)
            
            # Add to database if new user
            if not existing_user:
                db.session.add(admin_user)
            
            # Commit changes
            db.session.commit()
            
            logger.info("✅ Single admin account setup completed successfully!")
            logger.info(f"Admin Email: {admin_email}")
            logger.info(f"Admin Password: {admin_password}")
            
            # Verify the setup
            total_admins = User.query.filter(
                (User.role == 'admin') | (User.role_type == 'admin')
            ).count()
            
            logger.info(f"Total admin accounts in database: {total_admins}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error setting up single admin account: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    success = setup_single_admin()
    if success:
        print("✅ Admin account setup completed successfully!")
        print("Email: admin@antidote.fit")
        print("Password: 1@coconutwater")
    else:
        print("❌ Failed to setup admin account")