#!/usr/bin/env python3
"""
Fix missing doctor profile images.

This script:
1. Identifies doctors with missing profile images
2. Cross-references with CSV data to find correct images
3. Updates database records with proper images
"""

import os
import csv
import logging
import psycopg2
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DOCTORS_CSV_PATH = "./attached_assets/Copy of Plastic surgeons india - Sheet1.csv"

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def load_csv_doctor_images():
    """Load doctor image URLs from CSV."""
    doctor_images = {}
    
    try:
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row.get('Name', '').strip()
                profile_image = row.get('Profile Image', '').strip()
                
                if name and profile_image:
                    doctor_images[name] = profile_image
        
        logger.info(f"Loaded {len(doctor_images)} doctor images from CSV")
        return doctor_images
        
    except Exception as e:
        logger.error(f"Error loading CSV: {str(e)}")
        return {}

def get_doctors_without_images():
    """Get all doctors without profile images."""
    conn = get_db_connection()
    try:
        doctors_without_images = []
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name 
                FROM doctors 
                WHERE profile_image IS NULL OR profile_image = ''
                ORDER BY name
            """)
            
            for doctor_id, name in cursor.fetchall():
                doctors_without_images.append({
                    'id': doctor_id,
                    'name': name
                })
        
        logger.info(f"Found {len(doctors_without_images)} doctors without profile images")
        return doctors_without_images
        
    finally:
        conn.close()

def update_doctor_images():
    """Update doctors with missing profile images."""
    # Get doctor image URLs from CSV
    csv_images = load_csv_doctor_images()
    
    # Get doctors without images
    doctors_without_images = get_doctors_without_images()
    
    if not doctors_without_images:
        logger.info("No doctors with missing images found")
        return 0
    
    # Update doctor images
    conn = get_db_connection()
    try:
        conn.autocommit = False
        updated_count = 0
        not_found_count = 0
        
        for doctor in doctors_without_images:
            name = doctor['name']
            doctor_id = doctor['id']
            
            # Skip if no image found in CSV
            if name not in csv_images:
                logger.warning(f"No image found in CSV for doctor: {name}")
                not_found_count += 1
                continue
            
            image_url = csv_images[name]
            
            # Update doctor's profile image
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE doctors
                    SET profile_image = %s
                    WHERE id = %s
                """, (image_url, doctor_id))
                
                updated_count += 1
                logger.info(f"Updated image for doctor: {name}")
            
            # Commit after each update
            conn.commit()
        
        logger.info(f"Updated images for {updated_count} doctors")
        logger.info(f"Could not find images for {not_found_count} doctors")
        
        return updated_count
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating doctor images: {str(e)}")
        return 0
        
    finally:
        conn.close()

def check_image_update_results():
    """Check results after updating doctor images."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Count doctors with images
            cursor.execute("""
                SELECT COUNT(*) FROM doctors 
                WHERE profile_image IS NOT NULL AND profile_image != ''
            """)
            result = cursor.fetchone()
            with_image = result[0] if result else 0
            
            # Count doctors without images
            cursor.execute("""
                SELECT COUNT(*) FROM doctors 
                WHERE profile_image IS NULL OR profile_image = ''
            """)
            result = cursor.fetchone()
            without_image = result[0] if result else 0
            
            # Count total doctors
            cursor.execute("SELECT COUNT(*) FROM doctors")
            result = cursor.fetchone()
            total = result[0] if result else 0
            
            return {
                'with_image': with_image,
                'without_image': without_image,
                'total': total,
                'coverage': int((with_image / total) * 100) if total > 0 else 0
            }
    
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting fix for missing doctor profile images")
    
    # Get initial stats
    initial_stats = check_image_update_results()
    logger.info(f"Initial stats: {initial_stats['with_image']} doctors with images, " +
                f"{initial_stats['without_image']} without images " +
                f"({initial_stats['coverage']}% coverage)")
    
    # Update doctor images
    updated_count = update_doctor_images()
    
    # Get final stats
    final_stats = check_image_update_results()
    logger.info(f"Final stats: {final_stats['with_image']} doctors with images, " +
               f"{final_stats['without_image']} without images " +
               f"({final_stats['coverage']}% coverage)")
    
    # Print summary
    print("\nDOCTOR IMAGE UPDATE SUMMARY")
    print("==========================")
    print(f"Updated images for {updated_count} doctors")
    print(f"Initial image coverage: {initial_stats['coverage']}%")
    print(f"Final image coverage: {final_stats['coverage']}%")
    print(f"Remaining doctors without images: {final_stats['without_image']}")
    
    if final_stats['without_image'] > 0:
        print("\nNote: Doctors without images may not have images in the CSV file.")
        print("You may need to find alternative image sources for these doctors.")