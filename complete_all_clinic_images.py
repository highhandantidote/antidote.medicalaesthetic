#!/usr/bin/env python3
"""
Complete clinic image import from ALL CSV files.
This script will process every CSV file and import all available clinic images.
"""

import csv
import os
import psycopg2
import logging
from glob import glob
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(database_url)

def process_csv_file(csv_file_path):
    """Process a single CSV file and import images."""
    logger.info(f"Processing {csv_file_path}")
    
    if not os.path.exists(csv_file_path):
        logger.warning(f"File not found: {csv_file_path}")
        return 0, 0, 0

    conn = get_db_connection()
    cursor = conn.cursor()
    
    updated_count = 0
    total_count = 0
    images_found = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                total_count += 1
                name = row.get('name', '').strip()
                profile_image = row.get('profile_image', '').strip()
                
                if not name:
                    continue
                
                # Check for valid image URLs
                if profile_image and (
                    profile_image.startswith('https://lh3.googleusercontent.com') or 
                    profile_image.startswith('https://streetviewpixels-pa.googleapis.com') or
                    profile_image.startswith('https://lh5.googleusercontent.com') or
                    profile_image.startswith('https://maps.gstatic.com') or
                    profile_image.startswith('https://lh4.googleusercontent.com')
                ):
                    images_found += 1
                    
                    # Try to match by exact name first
                    cursor.execute("""
                        UPDATE clinics 
                        SET profile_image = %s 
                        WHERE name = %s AND (profile_image IS NULL OR profile_image = '')
                    """, (profile_image, name))
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
                    else:
                        # Try fuzzy matching if exact match fails
                        cursor.execute("""
                            UPDATE clinics 
                            SET profile_image = %s 
                            WHERE LOWER(name) LIKE %s AND (profile_image IS NULL OR profile_image = '')
                        """, (profile_image, f"%{name.lower()}%"))
                        
                        if cursor.rowcount > 0:
                            updated_count += 1
                    
                    if updated_count % 25 == 0:
                        logger.info(f"Updated {updated_count} clinics from {csv_file_path}")
        
        conn.commit()
        logger.info(f"✓ {csv_file_path}: {updated_count} clinics updated ({images_found} images found, {total_count} total)")
        
    except Exception as e:
        logger.error(f"Error processing {csv_file_path}: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return updated_count, images_found, total_count

def main():
    """Complete image import from all CSV files."""
    # Find all CSV files with clinic data
    csv_files = [
        './sample_clinics.csv',
        './bengaluru_clinics.csv',
        './mumbai_clinics.csv',
        './delhi_clinics.csv',
        './gurugram_clinics.csv',
        './kolkata_clinics.csv',
        './chennai_clinics.csv',
        './ahmedabad_clinics.csv',
        './hyderabad_clinics.csv',
        './jaipur_clinics.csv'
    ]
    
    # Also check for any additional CSV files
    additional_files = glob('*_clinics.csv')
    additional_files.extend(glob('*clinics.csv'))
    
    # Combine and remove duplicates
    all_files = list(set(csv_files + additional_files))
    
    logger.info(f"Found {len(all_files)} CSV files to process")
    
    total_updated = 0
    total_images_found = 0
    total_records = 0
    
    for csv_file in all_files:
        if os.path.exists(csv_file):
            updated, images, records = process_csv_file(csv_file)
            total_updated += updated
            total_images_found += images
            total_records += records
            
            # Small delay between files
            time.sleep(1)
        else:
            logger.warning(f"File not found: {csv_file}")
    
    logger.info(f"\n=== FINAL SUMMARY ===")
    logger.info(f"Total CSV files processed: {len([f for f in all_files if os.path.exists(f)])}")
    logger.info(f"Total records processed: {total_records}")
    logger.info(f"Total images found in CSV: {total_images_found}")
    logger.info(f"Total clinics updated: {total_updated}")
    
    # Check final database status
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as total_clinics, 
               COUNT(CASE WHEN profile_image IS NOT NULL AND profile_image != '' THEN 1 END) as clinics_with_images,
               COUNT(CASE WHEN profile_image IS NULL OR profile_image = '' THEN 1 END) as clinics_without_images
        FROM clinics
    """)
    
    result = cursor.fetchone()
    logger.info(f"Final database status:")
    logger.info(f"  Total clinics: {result[0]}")
    logger.info(f"  Clinics with images: {result[1]}")
    logger.info(f"  Clinics without images: {result[2]}")
    logger.info(f"  Coverage: {(result[1]/result[0]*100):.1f}%")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()