#!/usr/bin/env python3
"""
Import real clinic images from CSV files to database.

This script reads the CSV files containing clinic data with real Google images
and updates the database with the actual image URLs that were missing.
"""

import csv
import os
import psycopg2
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection using environment variable."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    return psycopg2.connect(database_url)

def import_images_from_csv(csv_file_path):
    """Import clinic images from a CSV file."""
    logger.info(f"Processing {csv_file_path}")
    
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
                
                if profile_image and (profile_image.startswith('https://lh3.googleusercontent.com') or 
                                    profile_image.startswith('https://streetviewpixels-pa.googleapis.com')):
                    images_found += 1
                    
                    # Update the clinic with the image URL
                    cursor.execute("""
                        UPDATE clinics 
                        SET profile_image = %s 
                        WHERE name = %s AND (profile_image IS NULL OR profile_image = '')
                    """, (profile_image, name))
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
                        logger.info(f"Updated image for: {name}")
        
        conn.commit()
        logger.info(f"File {csv_file_path}: {updated_count} clinics updated out of {images_found} with images ({total_count} total)")
        
    except Exception as e:
        logger.error(f"Error processing {csv_file_path}: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return updated_count, images_found, total_count

def main():
    """Main function to import all clinic images."""
    csv_files = [
        'mumbai_clinics.csv',
        'bengaluru_clinics.csv', 
        'delhi_clinics.csv',
        'gurugram_clinics.csv'
    ]
    
    total_updated = 0
    total_images = 0
    total_clinics = 0
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            updated, images, total = import_images_from_csv(csv_file)
            total_updated += updated
            total_images += images
            total_clinics += total
        else:
            logger.warning(f"CSV file not found: {csv_file}")
    
    logger.info(f"SUMMARY: Updated {total_updated} clinics with real images")
    logger.info(f"Total clinics with images in CSV: {total_images}")
    logger.info(f"Total clinics processed: {total_clinics}")
    
    # Verify the import
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clinics WHERE profile_image IS NOT NULL AND profile_image != ''")
    final_count = cursor.fetchone()[0]
    logger.info(f"Final count of clinics with images in database: {final_count}")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()