"""
Add enhancement fields to packages table for comprehensive package details.
This script adds all the missing fields required for the enhanced package detail page.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def add_package_enhancement_fields():
    """Add all enhancement fields to packages table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Add new fields for comprehensive package details
        new_fields = [
            # About procedure and highlights
            "ADD COLUMN IF NOT EXISTS about_procedure TEXT",
            "ADD COLUMN IF NOT EXISTS key_highlights JSON", # {dosage, recovery, duration, results}
            
            # Procedure information and pricing (multiple procedures)
            "ADD COLUMN IF NOT EXISTS procedure_breakdown JSON", # [{name, price_actual, price_discounted, discount_percentage, description}]
            
            # Additional billing info
            "ADD COLUMN IF NOT EXISTS vat_amount NUMERIC(10,2)",
            "ADD COLUMN IF NOT EXISTS anesthetic_type TEXT",
            "ADD COLUMN IF NOT EXISTS aftercare_kit TEXT",
            
            # Downtime details
            "ADD COLUMN IF NOT EXISTS downtime_description TEXT",
            
            # Precautions and side effects
            "ADD COLUMN IF NOT EXISTS precautions TEXT",
            
            # Before/After results with detailed structure
            "ADD COLUMN IF NOT EXISTS results_gallery JSON", # [{title, doctor_name, before_image, after_image, before_video, after_video, description}]
            
            # Contact customization
            "ADD COLUMN IF NOT EXISTS whatsapp_number TEXT",
            "ADD COLUMN IF NOT EXISTS custom_phone_number TEXT",
            "ADD COLUMN IF NOT EXISTS chat_message_template TEXT",
            "ADD COLUMN IF NOT EXISTS call_message_template TEXT",
            
            # Map and location
            "ADD COLUMN IF NOT EXISTS clinic_latitude DECIMAL(10,8)",
            "ADD COLUMN IF NOT EXISTS clinic_longitude DECIMAL(11,8)",
            "ADD COLUMN IF NOT EXISTS clinic_address TEXT"
        ]
        
        for field in new_fields:
            try:
                cursor.execute(f"ALTER TABLE packages {field}")
                logger.info(f"Added field: {field}")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"Field already exists: {field}")
                else:
                    logger.error(f"Error adding field {field}: {e}")
        
        conn.commit()
        logger.info("All package enhancement fields added successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding package enhancement fields: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_package_enhancement_fields()