#!/usr/bin/env python3
"""
Quick category image import with batch processing.
"""

import csv
import os
import re
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a fresh database connection."""
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url)

def convert_google_drive_url(sharing_url):
    """Convert Google Drive sharing URL to direct download URL."""
    try:
        # Extract file ID from Google Drive URL
        file_id = None
        
        # Various URL formats
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', sharing_url)
        if match:
            file_id = match.group(1)
        
        if not file_id:
            match = re.search(r'id=([a-zA-Z0-9_-]+)', sharing_url)
            if match:
                file_id = match.group(1)
        
        if not file_id:
            match = re.search(r'open\?id=([a-zA-Z0-9_-]+)', sharing_url)
            if match:
                file_id = match.group(1)
        
        if file_id:
            return f"https://drive.google.com/uc?export=view&id={file_id}"
        
        return sharing_url
        
    except Exception as e:
        logger.error(f"Error converting URL: {e}")
        return sharing_url

def clean_category_name(category_name):
    """Clean category name by removing parentheses content."""
    return re.sub(r'\s*\([^)]+\)$', '', category_name).strip()

def import_batch():
    """Import category images in small batches."""
    csv_file_path = 'attached_assets/category_images - Sheet1.csv'
    
    # Read all mappings from CSV
    mappings = []
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            category_name = row['category_name'].strip()
            image_url = row['image_url'].strip()
            if category_name and image_url:
                clean_name = clean_category_name(category_name)
                direct_url = convert_google_drive_url(image_url)
                mappings.append((clean_name, direct_url, category_name))
    
    updated_count = 0
    
    # Process each mapping individually
    for clean_name, direct_url, original_name in mappings:
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Try exact match first
                cursor.execute(
                    "UPDATE categories SET image_url = %s WHERE LOWER(name) = LOWER(%s)",
                    (direct_url, clean_name)
                )
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Updated '{clean_name}' (exact match)")
                    updated_count += cursor.rowcount
                else:
                    # Try partial match
                    cursor.execute(
                        "UPDATE categories SET image_url = %s WHERE LOWER(name) LIKE LOWER(%s)",
                        (direct_url, f"%{clean_name}%")
                    )
                    
                    if cursor.rowcount > 0:
                        logger.info(f"✅ Updated '{clean_name}' (partial match)")
                        updated_count += cursor.rowcount
                    else:
                        logger.warning(f"❌ No match for '{clean_name}' (original: '{original_name}')")
                
                conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error processing '{clean_name}': {e}")
            if 'conn' in locals():
                conn.close()
    
    logger.info(f"🎉 Total updated: {updated_count} categories")
    
    # Final check
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url IS NOT NULL")
        total_with_images = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        total_categories = cursor.fetchone()[0]
        
        logger.info(f"📊 Final: {total_with_images}/{total_categories} categories have images")
    conn.close()

if __name__ == "__main__":
    import_batch()