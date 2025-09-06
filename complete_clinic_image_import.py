#!/usr/bin/env python3
"""
Complete clinic image import from all CSV files.
This script imports real Google images from all available CSV files.
"""

import csv
import os
import psycopg2
import logging
from glob import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection."""
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
                
                # Check for valid image URLs
                if profile_image and (profile_image.startswith('https://lh3.googleusercontent.com') or 
                                    profile_image.startswith('https://streetviewpixels-pa.googleapis.com')):
                    images_found += 1
                    
                    # Update clinic with image URL
                    cursor.execute("""
                        UPDATE clinics 
                        SET profile_image = %s 
                        WHERE name = %s AND (profile_image IS NULL OR profile_image = '')
                    """, (profile_image, name))
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
                        if updated_count % 50 == 0:
                            logger.info(f"Updated {updated_count} clinics so far...")
        
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
    """Import images from all CSV files."""
    # Find all CSV files with clinic data
    csv_files = glob('*_clinics.csv')
    csv_files.extend(glob('*clinics.csv'))
    
    # Remove duplicates
    csv_files = list(set(csv_files))
    
    logger.info(f"Found {len(csv_files)} CSV files to process")
    
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
    
    logger.info(f"")
    logger.info(f"=== IMPORT SUMMARY ===")
    logger.info(f"Updated {total_updated} clinics with real images")
    logger.info(f"Total clinics with images in CSV: {total_images}")
    logger.info(f"Total clinics processed: {total_clinics}")
    
    # Final verification
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clinics WHERE profile_image IS NOT NULL AND profile_image != ''")
    final_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM clinics WHERE profile_image LIKE 'https://lh3.googleusercontent.com%'")
    google_images_count = cursor.fetchone()[0]
    
    logger.info(f"Final database count: {final_count} clinics with images")
    logger.info(f"Google images imported: {google_images_count}")
    
    # Show some examples
    cursor.execute("""
        SELECT name, profile_image 
        FROM clinics 
        WHERE profile_image LIKE 'https://lh3.googleusercontent.com%' 
        LIMIT 5
    """)
    examples = cursor.fetchall()
    
    logger.info("Examples of imported images:")
    for name, image_url in examples:
        logger.info(f"  - {name}: {image_url[:80]}...")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()