#!/usr/bin/env python3
"""
Restore users and doctors with constraint handling.
"""

import json
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url)

def restore_users_and_doctors():
    """Restore users and doctors with proper constraint handling."""
    
    # Load backup data
    with open("attached_assets/antidote_backup_20250527_180345.json", 'r') as f:
        backup_data = json.load(f)
    
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            # Restore users with default phone numbers for null values
            users_data = backup_data['tables']['users']['data']
            logger.info(f"Restoring {len(users_data)} users...")
            
            user_success = 0
            for i, user in enumerate(users_data):
                try:
                    # Handle null phone numbers
                    phone_number = user.get('phone_number') or f"+919999{str(i).zfill(6)}"
                    
                    cursor.execute("""
                        INSERT INTO users (id, phone_number, firebase_uid, name, email, role, username, 
                                         password_hash, role_type, bio, badge, created_at, last_login_at, 
                                         is_verified, saved_items, points)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        user['id'], phone_number, user.get('firebase_uid'),
                        user['name'], user['email'], user['role'], user['username'],
                        user.get('password_hash'), user.get('role_type'), user.get('bio'),
                        user.get('badge'), user['created_at'], user.get('last_login_at'),
                        user.get('is_verified', True), user.get('saved_items'), user.get('points')
                    ))
                    user_success += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to insert user {i+1}: {str(e)}")
                    continue
            
            conn.commit()
            logger.info(f"Users restored: {user_success}/{len(users_data)}")
            
            # Restore doctors
            doctors_data = backup_data['tables']['doctors']['data']
            logger.info(f"Restoring {len(doctors_data)} doctors...")
            
            doctor_success = 0
            for i, doctor in enumerate(doctors_data):
                try:
                    cursor.execute("""
                        INSERT INTO doctors (id, user_id, name, specialty, experience, city, state, 
                                           hospital, consultation_fee, is_verified, rating, review_count,
                                           created_at, bio, certifications, video_url, success_stories,
                                           education, profile_image, image_url, medical_license_number,
                                           qualification, practice_location, verification_status,
                                           verification_date, verification_notes, credentials_url, aadhaar_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        doctor['id'], doctor.get('user_id'), doctor['name'], 
                        doctor.get('specialty'), doctor.get('experience'), doctor.get('city'),
                        doctor.get('state'), doctor.get('hospital'), doctor.get('consultation_fee'),
                        doctor.get('is_verified', True), doctor.get('rating'), doctor.get('review_count'),
                        doctor['created_at'], doctor.get('bio'), doctor.get('certifications'),
                        doctor.get('video_url'), doctor.get('success_stories'), doctor.get('education'),
                        doctor.get('profile_image'), doctor.get('image_url'), doctor.get('medical_license_number'),
                        doctor.get('qualification'), doctor.get('practice_location'), doctor.get('verification_status'),
                        doctor.get('verification_date'), doctor.get('verification_notes'), 
                        doctor.get('credentials_url'), doctor.get('aadhaar_number')
                    ))
                    doctor_success += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to insert doctor {i+1}: {str(e)}")
                    continue
            
            conn.commit()
            logger.info(f"Doctors restored: {doctor_success}/{len(doctors_data)}")
            
    except Exception as e:
        logger.error(f"Error during restoration: {str(e)}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    restore_users_and_doctors()
    logger.info("✅ Users and doctors restoration completed!")