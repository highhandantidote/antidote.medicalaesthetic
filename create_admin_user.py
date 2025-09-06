#!/usr/bin/env python3
"""
Create an admin user for testing the comprehensive admin system.
"""
import os
import sys
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_user():
    """Create an admin user in the database."""
    try:
        # Get database URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
        
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if admin user already exists
            result = conn.execute(text("""
                SELECT id FROM users WHERE email = 'admin@antidote.com' OR role = 'admin'
            """))
            
            existing_admin = result.fetchone()
            if existing_admin:
                logger.info("Admin user already exists")
                return True
            
            # Create admin user
            password_hash = generate_password_hash('admin123')
            
            conn.execute(text("""
                INSERT INTO users (username, email, password_hash, role, is_verified, created_at)
                VALUES ('admin', 'admin@antidote.com', :password_hash, 'admin', true, NOW())
            """), {'password_hash': password_hash})
            
            conn.commit()
            logger.info("Admin user created successfully")
            logger.info("Email: admin@antidote.com")
            logger.info("Password: admin123")
            
            return True
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        return False

if __name__ == "__main__":
    success = create_admin_user()
    sys.exit(0 if success else 1)