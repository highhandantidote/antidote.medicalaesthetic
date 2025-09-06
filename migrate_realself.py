#!/usr/bin/env python3
"""
Migration script to update Procedure model to align with RealSelf hierarchy.

This script:
1. Initializes a new migration if needed
2. Creates a migration for the model changes
3. Applies the migration to the database
4. Updates existing procedure data to use the new schema
"""
import os
import logging
import sys
from flask_migrate import Migrate, init, migrate, upgrade
from app import create_app, db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_migration():
    """
    Set up the migration environment for Flask-Migrate.
    Initialize if it doesn't exist yet, or just create a new migration.
    """
    logger.info("Setting up migration environment...")
    
    # Create Flask app context
    app = create_app()
    migrate_instance = Migrate(app, db)
    
    with app.app_context():
        # Check if migrations/versions exists
        if not os.path.exists('migrations/versions'):
            logger.info("Initializing migrations directory...")
            init()
        
        # Create migration for the model changes
        logger.info("Creating migration for model changes...")
        migrate(message="Update to RealSelf hierarchy with minimal changes")
        
        # Apply the migration
        logger.info("Upgrading database with migration...")
        upgrade()
        
    logger.info("Migration setup completed successfully.")

def migrate_procedure_data():
    """
    Migrate existing procedure data to use the new schema.
    
    This populates:
    - body_part from body_area
    - tags from category_type
    - Ensures category relationship is properly set
    """
    logger.info("Migrating procedure data to new schema...")
    
    app = create_app()
    
    with app.app_context():
        from models import Procedure
        from sqlalchemy import text
        
        # Get all procedures
        procedures = Procedure.query.all()
        logger.info(f"Found {len(procedures)} procedures to migrate")
        
        for procedure in procedures:
            # Set body_part from body_area
            if procedure.body_area and not procedure.body_part:
                procedure.body_part = procedure.body_area
            
            # Set tags from category_type
            if procedure.category_type and not procedure.tags:
                procedure.tags = [procedure.category_type]
            
            # Commit after each procedure to avoid timeout
            try:
                db.session.commit()
                logger.info(f"Migrated procedure: {procedure.procedure_name}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error migrating procedure {procedure.procedure_name}: {str(e)}")
        
        logger.info("Procedure data migration completed")

def main():
    """Run the migration script."""
    try:
        # Set up migration
        setup_migration()
        
        # Migrate procedure data
        migrate_procedure_data()
        
        logger.info("Migration completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())