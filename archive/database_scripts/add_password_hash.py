#!/usr/bin/env python3
"""
Add missing password_hash column to users table.
"""
import os
import sys
import logging
from app import create_app, db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_password_hash_column():
    """Add password_hash column to users table if it doesn't exist."""
    app = create_app()
    with app.app_context():
        try:
            # Check if the column already exists
            from sqlalchemy import text
            result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'password_hash'"))
            if not result.fetchone():
                # Add the column
                logger.info("Adding password_hash column to users table...")
                db.session.execute(text("ALTER TABLE users ADD COLUMN password_hash TEXT"))
                db.session.commit()
                logger.info("password_hash column added successfully.")
            else:
                logger.info("password_hash column already exists.")
                
            return True
        except Exception as e:
            logger.error(f"Error adding password_hash column: {str(e)}")
            db.session.rollback()
            return False

def main():
    """Run the migration."""
    if add_password_hash_column():
        logger.info("Migration completed successfully.")
    else:
        logger.error("Migration failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()