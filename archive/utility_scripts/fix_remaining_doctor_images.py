#!/usr/bin/env python3
"""
Fix remaining doctor profile images with enhanced name matching.

This script uses fuzzy matching and name variations to find more doctor images
from the CSV file for doctors that didn't get matched in the first pass.
"""

import os
import csv
import logging
import psycopg2
import re
from difflib import SequenceMatcher

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

def normalize_name(name):
    """Normalize a doctor name for better matching."""
    if not name:
        return ""
    
    # Remove common prefixes and suffixes
    name = re.sub(r'^(Dr\.?|Doctor)\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*(M\.?S\.?|M\.?Ch\.?|M\.?D\.?|Ph\.?D\.?|MBBS|MS|MCh|MD|PhD).*$', '', name, flags=re.IGNORECASE)
    
    # Remove extra whitespace and normalize
    name = ' '.join(name.split())
    return name.strip()

def similarity(a, b):
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def load_csv_doctor_images_enhanced():
    """Load doctor image URLs from CSV with enhanced name processing."""
    doctor_images = {}
    
    try:
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row.get('Name', '').strip()
                profile_image = row.get('Profile Image', '').strip()
                
                if name and profile_image:
                    # Store both original and normalized names
                    doctor_images[name] = profile_image
                    normalized_name = normalize_name(name)
                    if normalized_name and normalized_name != name:
                        doctor_images[normalized_name] = profile_image
        
        logger.info(f"Loaded {len(doctor_images)} doctor image variations from CSV")
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

def find_best_match(doctor_name, csv_images):
    """Find the best matching image for a doctor using fuzzy matching."""
    best_match = None
    best_score = 0.0
    best_url = None
    
    # Normalize the target name
    normalized_target = normalize_name(doctor_name)
    
    # First try exact matches
    if doctor_name in csv_images:
        return doctor_name, 1.0, csv_images[doctor_name]
    
    if normalized_target in csv_images:
        return normalized_target, 1.0, csv_images[normalized_target]
    
    # Try fuzzy matching
    for csv_name, image_url in csv_images.items():
        # Compare original names
        score1 = similarity(doctor_name, csv_name)
        
        # Compare normalized names
        normalized_csv = normalize_name(csv_name)
        score2 = similarity(normalized_target, normalized_csv)
        
        # Take the best score
        score = max(score1, score2)
        
        if score > best_score and score >= 0.8:  # 80% similarity threshold
            best_match = csv_name
            best_score = score
            best_url = image_url
    
    return best_match, best_score, best_url

def update_remaining_doctor_images():
    """Update doctors with missing profile images using enhanced matching."""
    # Get doctor image URLs from CSV
    csv_images = load_csv_doctor_images_enhanced()
    
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
        no_match_count = 0
        
        for doctor in doctors_without_images:
            name = doctor['name']
            doctor_id = doctor['id']
            
            # Find best match using fuzzy matching
            match_name, score, image_url = find_best_match(name, csv_images)
            
            if match_name and image_url and score >= 0.8:
                # Update doctor's profile image
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE doctors
                        SET profile_image = %s
                        WHERE id = %s
                    """, (image_url, doctor_id))
                    
                    updated_count += 1
                    logger.info(f"Updated image for doctor: {name} (matched with {match_name}, score: {score:.2f})")
                
                # Commit after each update
                conn.commit()
            else:
                logger.warning(f"No good match found for doctor: {name}")
                no_match_count += 1
        
        logger.info(f"Updated images for {updated_count} doctors")
        logger.info(f"Could not find matches for {no_match_count} doctors")
        
        return updated_count
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating doctor images: {str(e)}")
        return 0
        
    finally:
        conn.close()

def check_final_results():
    """Check final results after updating doctor images."""
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

def show_remaining_doctors():
    """Show details of remaining doctors without images."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM doctors 
                WHERE profile_image IS NULL OR profile_image = ''
                ORDER BY name
                LIMIT 10
            """)
            
            remaining = cursor.fetchall()
            if remaining:
                logger.info("Sample of remaining doctors without images:")
                for i, (name,) in enumerate(remaining, 1):
                    logger.info(f"  {i}. {name}")
                
                if len(remaining) == 10:
                    cursor.execute("""
                        SELECT COUNT(*) FROM doctors 
                        WHERE profile_image IS NULL OR profile_image = ''
                    """)
                    total_remaining = cursor.fetchone()[0]
                    if total_remaining > 10:
                        logger.info(f"  ... and {total_remaining - 10} more")
    
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting enhanced fix for remaining doctor profile images")
    
    # Get initial stats
    initial_stats = check_final_results()
    logger.info(f"Initial stats: {initial_stats['with_image']} doctors with images, " +
                f"{initial_stats['without_image']} without images " +
                f"({initial_stats['coverage']}% coverage)")
    
    # Update doctor images with enhanced matching
    updated_count = update_remaining_doctor_images()
    
    # Get final stats
    final_stats = check_final_results()
    logger.info(f"Final stats: {final_stats['with_image']} doctors with images, " +
               f"{final_stats['without_image']} without images " +
               f"({final_stats['coverage']}% coverage)")
    
    # Print summary
    print("\n" + "="*50)
    print("ENHANCED DOCTOR IMAGE UPDATE SUMMARY")
    print("="*50)
    print(f"✅ Updated images for {updated_count} additional doctors")
    print(f"📊 Initial image coverage: {initial_stats['coverage']}%")
    print(f"📈 Final image coverage: {final_stats['coverage']}%")
    print(f"🎯 Coverage improvement: +{final_stats['coverage'] - initial_stats['coverage']}%")
    print(f"⚠️  Remaining doctors without images: {final_stats['without_image']}")
    print("="*50)
    
    if final_stats['without_image'] > 0:
        print("\nRemaining doctors without images:")
        show_remaining_doctors()