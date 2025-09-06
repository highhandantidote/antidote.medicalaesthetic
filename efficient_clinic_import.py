#!/usr/bin/env python3
"""
Efficient clinic image import with batch processing and error handling.
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

def truncate_url(url, max_length=255):
    """Truncate URL to fit in database column."""
    if len(url) <= max_length:
        return url
    return url[:max_length]

def process_csv_batch(csv_file_path, batch_size=50):
    """Process CSV file in batches to avoid timeouts."""
    logger.info(f"Processing {csv_file_path}")
    
    if not os.path.exists(csv_file_path):
        logger.warning(f"File not found: {csv_file_path}")
        return 0, 0, 0

    updated_count = 0
    total_count = 0
    images_found = 0
    batch_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            batch_data = []
            
            for row in reader:
                total_count += 1
                name = row.get('name', '').strip()
                profile_image = row.get('profile_image', '').strip()
                
                if not name or not profile_image:
                    continue
                
                # Check for valid image URLs
                if (profile_image.startswith('https://lh3.googleusercontent.com') or 
                    profile_image.startswith('https://streetviewpixels-pa.googleapis.com') or
                    profile_image.startswith('https://lh5.googleusercontent.com') or
                    profile_image.startswith('https://maps.gstatic.com') or
                    profile_image.startswith('https://lh4.googleusercontent.com')):
                    
                    images_found += 1
                    # Truncate URL to fit in database
                    truncated_url = truncate_url(profile_image)
                    batch_data.append((name, truncated_url))
                    
                    # Process batch when it reaches batch_size
                    if len(batch_data) >= batch_size:
                        updated_count += process_batch(batch_data)
                        batch_data = []
                        batch_count += 1
                        logger.info(f"Processed batch {batch_count} from {csv_file_path}")
            
            # Process remaining data
            if batch_data:
                updated_count += process_batch(batch_data)
                batch_count += 1
        
        logger.info(f"✓ {csv_file_path}: {updated_count} clinics updated ({images_found} images found, {total_count} total)")
        
    except Exception as e:
        logger.error(f"Error processing {csv_file_path}: {e}")
    
    return updated_count, images_found, total_count

def process_batch(batch_data):
    """Process a batch of updates."""
    conn = get_db_connection()
    cursor = conn.cursor()
    updated_count = 0
    
    try:
        for name, profile_image in batch_data:
            # Try exact match first
            cursor.execute("""
                UPDATE clinics 
                SET profile_image = %s 
                WHERE name = %s AND (profile_image IS NULL OR profile_image = '')
            """, (profile_image, name))
            
            if cursor.rowcount > 0:
                updated_count += 1
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return updated_count

def main():
    """Main function to import all clinic images efficiently."""
    # Priority CSV files (biggest cities first)
    priority_files = [
        './hyderabad_clinics.csv',
        './bengaluru_clinics.csv',
        './mumbai_clinics.csv',
        './delhi_clinics.csv',
        './gurugram_clinics.csv',
        './kolkata_clinics.csv',
        './chennai_clinics.csv',
        './ahmedabad_clinics.csv',
        './jaipur_clinics.csv'
    ]
    
    logger.info(f"Starting efficient clinic image import")
    
    total_updated = 0
    total_images_found = 0
    total_records = 0
    
    # Process priority files first
    for csv_file in priority_files:
        if os.path.exists(csv_file):
            logger.info(f"Processing priority file: {csv_file}")
            updated, images, records = process_csv_batch(csv_file, batch_size=25)
            total_updated += updated
            total_images_found += images
            total_records += records
            
            # Short delay between files
            time.sleep(0.5)
    
    # Check for any additional CSV files
    additional_files = glob('*_clinics.csv')
    remaining_files = [f for f in additional_files if f not in priority_files and os.path.exists(f)]
    
    for csv_file in remaining_files:
        logger.info(f"Processing additional file: {csv_file}")
        updated, images, records = process_csv_batch(csv_file, batch_size=25)
        total_updated += updated
        total_images_found += images
        total_records += records
        time.sleep(0.5)
    
    logger.info(f"\n=== IMPORT COMPLETE ===")
    logger.info(f"Total files processed: {len(priority_files) + len(remaining_files)}")
    logger.info(f"Total records processed: {total_records}")
    logger.info(f"Total images found: {total_images_found}")
    logger.info(f"Total clinics updated: {total_updated}")
    
    # Check final database status
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as total_clinics, 
                   COUNT(CASE WHEN profile_image IS NOT NULL AND profile_image != '' THEN 1 END) as clinics_with_images
            FROM clinics
        """)
        
        result = cursor.fetchone()
        total_clinics, clinics_with_images = result
        coverage = (clinics_with_images / total_clinics * 100) if total_clinics > 0 else 0
        
        logger.info(f"Final database status:")
        logger.info(f"  Total clinics: {total_clinics}")
        logger.info(f"  Clinics with images: {clinics_with_images}")
        logger.info(f"  Coverage: {coverage:.1f}%")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking final status: {e}")

if __name__ == "__main__":
    main()