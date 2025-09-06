#!/usr/bin/env python3
"""
Fast category image updater - processes in smaller batches to avoid timeouts.
"""

import os
import csv
import logging
import psycopg2
from urllib.parse import urlparse, parse_qs
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection."""
    database_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    return conn

def convert_google_drive_url(drive_url):
    """Convert Google Drive URL to direct image URL."""
    if 'drive.google.com' not in drive_url:
        return drive_url
    
    # Extract file ID
    file_id = None
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_url)
    if match:
        file_id = match.group(1)
    else:
        parsed = urlparse(drive_url)
        query_params = parse_qs(parsed.query)
        if 'id' in query_params:
            file_id = query_params['id'][0]
    
    if file_id:
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    return drive_url

def update_category_images():
    """Update category images efficiently."""
    csv_file_path = 'attached_assets/category_images - Sheet1.csv'
    
    conn = get_db_connection()
    updated_count = 0
    
    try:
        # First, clear all existing images
        with conn.cursor() as cursor:
            cursor.execute("UPDATE categories SET image_url = NULL")
            conn.commit()
            logger.info("Cleared all existing category images")
        
        # Read CSV and prepare updates
        updates = []
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                category_name = row['category_name'].strip()
                image_url = row['image_url'].strip()
                
                if not category_name or not image_url:
                    continue
                
                # Extract body part from parentheses
                body_part = None
                match = re.search(r'\(([^)]+)\)$', category_name)
                if match:
                    body_part = match.group(1).strip()
                    clean_name = re.sub(r'\s*\([^)]+\)$', '', category_name).strip()
                else:
                    clean_name = category_name
                
                direct_url = convert_google_drive_url(image_url)
                updates.append((clean_name, body_part, direct_url, category_name))
        
        # Process updates
        with conn.cursor() as cursor:
            for clean_name, body_part, direct_url, original_name in updates:
                try:
                    # Try to find matching category
                    if body_part:
                        # Look for category with body part context
                        cursor.execute("""
                            SELECT c.id, c.name FROM categories c
                            JOIN body_parts bp ON c.body_part_id = bp.id
                            WHERE (LOWER(c.name) LIKE LOWER(%s) OR LOWER(%s) LIKE LOWER(c.name))
                            AND LOWER(bp.name) LIKE LOWER(%s)
                            LIMIT 1
                        """, (f"%{clean_name}%", f"%{clean_name}%", f"%{body_part}%"))
                    else:
                        # Look for category by name only
                        cursor.execute("""
                            SELECT c.id, c.name FROM categories c
                            WHERE LOWER(c.name) LIKE LOWER(%s) OR LOWER(%s) LIKE LOWER(c.name)
                            LIMIT 1
                        """, (f"%{clean_name}%", f"%{clean_name}%"))
                    
                    result = cursor.fetchone()
                    if result:
                        category_id, db_name = result
                        cursor.execute("UPDATE categories SET image_url = %s WHERE id = %s", (direct_url, category_id))
                        logger.info(f"✅ Updated '{db_name}' with image from '{original_name}'")
                        updated_count += 1
                    else:
                        logger.warning(f"❌ No match found for '{original_name}'")
                
                except Exception as e:
                    logger.error(f"Error updating '{original_name}': {e}")
                    continue
        
        conn.commit()
        logger.info(f"🎉 Successfully updated {updated_count} category images!")
        
        # Show final status
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url IS NOT NULL")
            total_with_images = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM categories")
            total_categories = cursor.fetchone()[0]
            logger.info(f"📊 Final status: {total_with_images}/{total_categories} categories have images")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_category_images()