#!/usr/bin/env python3
"""
Add doctors to the database with proper data formatting.
"""

import os
import logging
import psycopg2
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url)

def add_doctors():
    """Add essential doctors to the database."""
    
    doctors = [
        {
            'user_id': 1,
            'name': 'Dr. Anand Sharma',
            'specialty': 'Plastic Surgery',
            'experience': 15,
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'hospital': 'Apollo Hospital',
            'consultation_fee': 2000,
            'rating': 4.8,
            'review_count': 156
        },
        {
            'user_id': 2,
            'name': 'Dr. Bhavna Patel',
            'specialty': 'Dermatology',
            'experience': 12,
            'city': 'Delhi',
            'state': 'Delhi',
            'hospital': 'Max Hospital',
            'consultation_fee': 1500,
            'rating': 4.7,
            'review_count': 203
        },
        {
            'user_id': 3,
            'name': 'Dr. Chetan Desai',
            'specialty': 'Cosmetic Surgery',
            'experience': 18,
            'city': 'Bangalore',
            'state': 'Karnataka',
            'hospital': 'Fortis Hospital',
            'consultation_fee': 2500,
            'rating': 4.9,
            'review_count': 134
        },
        {
            'user_id': 10,
            'name': 'Dr. Sameer Karkhanis',
            'specialty': 'Aesthetic Medicine',
            'experience': 10,
            'city': 'Chennai',
            'state': 'Tamil Nadu',
            'hospital': 'Government General Hospital',
            'consultation_fee': 1800,
            'rating': 4.6,
            'review_count': 89
        },
        {
            'user_id': 11,
            'name': 'Dr. Karthik Ram',
            'specialty': 'Hair Restoration',
            'experience': 14,
            'city': 'Pune',
            'state': 'Maharashtra',
            'hospital': 'Ruby Hall Clinic',
            'consultation_fee': 2200,
            'rating': 4.5,
            'review_count': 167
        }
    ]
    
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            for doctor in doctors:
                cursor.execute("""
                    INSERT INTO doctors (user_id, name, specialty, experience, city, state, hospital, 
                                       consultation_fee, is_verified, rating, review_count, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    doctor['user_id'], doctor['name'], doctor['specialty'], doctor['experience'],
                    doctor['city'], doctor['state'], doctor['hospital'],
                    doctor['consultation_fee'], True, doctor['rating'],
                    doctor['review_count'], datetime.now()
                ))
            
            conn.commit()
            logger.info(f"Successfully added {len(doctors)} doctors to the database")
    
    except Exception as e:
        logger.error(f"Error adding doctors: {str(e)}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    add_doctors()
    logger.info("✅ Doctors added successfully!")