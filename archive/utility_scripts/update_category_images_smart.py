#!/usr/bin/env python3
"""
Smart update of category images using the new CSV file.
Only downloads and updates images that are different or missing.
"""

import os
import csv
import psycopg2
import requests
import re
import time
from urllib.parse import urlparse, parse_qs
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def extract_google_drive_id(url):
    """Extract Google Drive file ID from various URL formats."""
    if 'drive.google.com' not in url:
        return None
    
    # Handle different Google Drive URL formats
    if '/file/d/' in url:
        return url.split('/file/d/')[1].split('/')[0]
    elif 'open?id=' in url:
        return url.split('open?id=')[1].split('&')[0]
    elif 'id=' in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get('id', [None])[0]
    
    return None

def convert_to_direct_url(drive_url):
    """Convert Google Drive sharing URL to direct download URL."""
    file_id = extract_google_drive_id(drive_url)
    if file_id:
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return drive_url

def download_image(url, filename):
    """Download image from URL and save locally."""
    try:
        direct_url = convert_to_direct_url(url)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(direct_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content)
        logger.info(f"✅ Downloaded {os.path.basename(filename)} ({file_size/1024:.0f}KB)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download {url}: {str(e)}")
        return False

def normalize_category_name(name):
    """Normalize category name for matching."""
    return name.lower().strip()

def update_category_images():
    """Update category images using the new CSV file."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        # Read the new CSV file
        csv_file = 'attached_assets/new_category_images - Sheet1.csv'
        
        if not os.path.exists(csv_file):
            logger.error(f"CSV file not found: {csv_file}")
            return False
        
        # Load CSV data
        csv_data = {}
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                category_name = row['category_name'].strip()
                image_url = row['image_url'].strip()
                csv_data[normalize_category_name(category_name)] = {
                    'name': category_name,
                    'url': image_url
                }
        
        logger.info(f"📋 Loaded {len(csv_data)} categories from new CSV")
        
        # Get current categories from database
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, image_url FROM categories ORDER BY name")
            current_categories = cursor.fetchall()
        
        logger.info(f"🗄️  Found {len(current_categories)} categories in database")
        
        updated_count = 0
        downloaded_count = 0
        skipped_count = 0
        
        for cat_id, cat_name, current_image_url in current_categories:
            normalized_name = normalize_category_name(cat_name)
            
            # Find matching CSV entry
            csv_match = None
            for csv_key, csv_info in csv_data.items():
                if (csv_key == normalized_name or 
                    csv_key in normalized_name or 
                    normalized_name in csv_key or
                    any(word in normalized_name for word in csv_key.split() if len(word) > 3)):
                    csv_match = csv_info
                    break
            
            if not csv_match:
                logger.warning(f"⚠️  No CSV match found for category: '{cat_name}'")
                continue
            
            # Create filename for local image
            safe_name = re.sub(r'[^\w\s-]', '', cat_name).lower().replace(' ', '_')
            local_filename = f"static/images/categories/{safe_name}.jpg"
            local_path = f"/static/images/categories/{safe_name}.jpg"
            
            # Check if we need to update
            needs_update = False
            
            if current_image_url != local_path:
                needs_update = True
                logger.info(f"🔄 Different path for '{cat_name}': current='{current_image_url}' vs new='{local_path}'")
            elif not os.path.exists(local_filename):
                needs_update = True
                logger.info(f"📁 Missing file for '{cat_name}': {local_filename}")
            
            if needs_update:
                # Download the new image
                if download_image(csv_match['url'], local_filename):
                    # Update database
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "UPDATE categories SET image_url = %s WHERE id = %s",
                            (local_path, cat_id)
                        )
                    
                    logger.info(f"✅ Updated '{cat_name}' with new image")
                    updated_count += 1
                    downloaded_count += 1
                else:
                    logger.error(f"❌ Failed to update '{cat_name}'")
            else:
                logger.info(f"⏭️  Skipped '{cat_name}' (already correct)")
                skipped_count += 1
        
        conn.commit()
        
        logger.info(f"🎉 Smart update complete!")
        logger.info(f"📊 Updated: {updated_count} categories")
        logger.info(f"⬇️  Downloaded: {downloaded_count} new images")
        logger.info(f"⏭️  Skipped: {skipped_count} already correct")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating category images: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("🚀 Starting smart category image update...")
    success = update_category_images()
    if success:
        logger.info("✅ Smart update completed successfully!")
    else:
        logger.error("❌ Smart update failed!")