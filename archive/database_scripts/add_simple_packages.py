"""
Add simplified Korean-style treatment packages to the database.
"""

import os
import psycopg2
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    return psycopg2.connect(DATABASE_URL)

def add_packages():
    """Add Korean-style treatment packages."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get clinic IDs
        cursor.execute("SELECT id, name FROM clinics WHERE is_verified = true LIMIT 5")
        clinics = cursor.fetchall()
        
        if not clinics:
            logger.error("No verified clinics found")
            return
        
        # Create packages
        packages = [
            (clinics[0][0], 'Premium Rhinoplasty Package', 'premium-rhinoplasty-package', 
             'Complete nose reshaping with advanced Korean techniques', 280000.00, 238000.00, 15,
             'Rhinoplasty', '7-10 days', '2-3 hours', True),
            
            (clinics[1][0], 'V-Line Facial Contouring', 'v-line-facial-contouring',
             'Create the perfect V-shaped jawline with Korean contouring', 450000.00, 382500.00, 15,
             'Facial Contouring', '14-21 days', '3-4 hours', True),
            
            (clinics[2][0], 'Natural Double Eyelid Surgery', 'natural-double-eyelid-surgery',
             'Create natural-looking double eyelids with Korean techniques', 85000.00, 72250.00, 15,
             'Eyelid Surgery', '3-5 days', '30-45 minutes', True),
             
            (clinics[3][0], 'Premium Botox Package', 'premium-botox-package',
             'Anti-aging botox treatment for forehead and crow\'s feet', 25000.00, 21250.00, 15,
             'Botox & Fillers', 'None', '15-20 minutes', True),
             
            (clinics[4][0], 'Korean Glass Skin Treatment', 'korean-glass-skin-treatment',
             'Achieve the coveted Korean glass skin with our premium package', 45000.00, 36000.00, 20,
             'Skin Treatments', '1-2 days', '1.5 hours', True)
        ]
        
        for package in packages:
            cursor.execute("""
                INSERT INTO packages (
                    clinic_id, title, slug, description, price_actual, price_discounted, 
                    discount_percentage, category, downtime, duration, is_featured, 
                    is_active, view_count, lead_count, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true, 0, 0, %s)
            """, package + (datetime.utcnow(),))
        
        conn.commit()
        logger.info(f"Successfully added {len(packages)} Korean clinic packages")
        
        # Summary
        cursor.execute("SELECT COUNT(*) FROM packages WHERE is_active = true")
        total = cursor.fetchone()[0]
        logger.info(f"Total active packages: {total}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_packages()