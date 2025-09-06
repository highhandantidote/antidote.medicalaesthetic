"""
Database migration script to add Google Places integration fields and tables.
Run this script to update the database schema for Google Reviews feature.
"""
import os
from sqlalchemy import text
from app import create_app, db
import logging

logger = logging.getLogger(__name__)

def migrate_google_reviews():
    """Add Google Places integration fields to clinics table and create google_reviews table."""
    
    app = create_app()
    with app.app_context():
        try:
            # Check if we have database connection
            with db.engine.connect() as conn:
                logger.info("Starting Google Reviews migration...")
                
                # Add Google Places fields to clinics table
                logger.info("Adding Google Places fields to clinics table...")
                
                # Check if columns already exist before adding them
                columns_to_add = [
                    ('google_business_url', 'VARCHAR(500)'),
                    ('google_place_id', 'VARCHAR(200)'),
                    ('google_rating', 'FLOAT'),
                    ('google_review_count', 'INTEGER'),
                    ('last_review_sync', 'TIMESTAMP'),
                    ('google_sync_enabled', 'BOOLEAN DEFAULT FALSE')
                ]
                
                for column_name, column_type in columns_to_add:
                    try:
                        # Try to add the column
                        conn.execute(text(f"""
                            ALTER TABLE clinics 
                            ADD COLUMN {column_name} {column_type}
                        """))
                        logger.info(f"Added column {column_name} to clinics table")
                    except Exception as e:
                        if "already exists" in str(e) or "duplicate column" in str(e):
                            logger.info(f"Column {column_name} already exists, skipping")
                        else:
                            logger.error(f"Error adding column {column_name}: {e}")
                
                # Create google_reviews table
                logger.info("Creating google_reviews table...")
                
                try:
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS google_reviews (
                            id SERIAL PRIMARY KEY,
                            clinic_id INTEGER NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
                            google_review_id VARCHAR(200) UNIQUE NOT NULL,
                            author_name VARCHAR(200) NOT NULL,
                            author_url VARCHAR(500),
                            profile_photo_url VARCHAR(500),
                            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                            text TEXT,
                            language VARCHAR(10),
                            time TIMESTAMP NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            relative_time_description VARCHAR(100),
                            original_data JSONB,
                            is_active BOOLEAN DEFAULT TRUE
                        )
                    """))
                    logger.info("Created google_reviews table successfully")
                    
                    # Create indexes for better performance
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_google_reviews_clinic_id 
                        ON google_reviews(clinic_id)
                    """))
                    
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_google_reviews_time 
                        ON google_reviews(time DESC)
                    """))
                    
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_google_reviews_active 
                        ON google_reviews(clinic_id, is_active, time DESC)
                    """))
                    
                    logger.info("Created indexes for google_reviews table")
                    
                except Exception as e:
                    if "already exists" in str(e):
                        logger.info("google_reviews table already exists")
                    else:
                        logger.error(f"Error creating google_reviews table: {e}")
                
                # Commit all changes
                conn.commit()
                logger.info("Google Reviews migration completed successfully!")
                
                return True
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

def check_migration_status():
    """Check if the Google Reviews migration has been applied."""
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Check if google_business_url column exists in clinics table
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'clinics' 
                    AND column_name = 'google_business_url'
                """)).fetchone()
                
                clinic_fields_exist = result is not None
                
                # Check if google_reviews table exists
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'google_reviews'
                """)).fetchone()
                
                reviews_table_exists = result is not None
                
                if clinic_fields_exist and reviews_table_exists:
                    logger.info("Google Reviews migration already applied")
                    return True
                else:
                    logger.info("Google Reviews migration not yet applied")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Check current status
    if check_migration_status():
        print("✅ Google Reviews migration already applied")
    else:
        print("🔄 Applying Google Reviews migration...")
        if migrate_google_reviews():
            print("✅ Google Reviews migration completed successfully!")
        else:
            print("❌ Google Reviews migration failed!")