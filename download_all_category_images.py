#!/usr/bin/env python3
"""
Download all category images from Google Drive to local storage.

This script downloads all category images from the database to fix the display issue.
Images will be stored in static/images/categories/ directory.
"""

import os
import psycopg2
import requests
import logging
from urllib.parse import urlparse, parse_qs
import time
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        return psycopg2.connect(os.environ.get('DATABASE_URL'))
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def sanitize_filename(name):
    """Convert category name to a safe filename."""
    # Remove special characters and replace spaces with underscores
    filename = re.sub(r'[^\w\s-]', '', name)
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename.lower()

def extract_file_id_from_google_drive_url(url):
    """Extract the file ID from a Google Drive URL."""
    try:
        # Handle different Google Drive URL formats
        if 'drive.google.com' in url:
            if '/file/d/' in url:
                file_id = url.split('/file/d/')[1].split('/')[0]
            elif 'id=' in url:
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                file_id = query_params.get('id', [None])[0]
            else:
                logger.warning(f"Could not extract file ID from URL: {url}")
                return None
            return file_id
        return None
    except Exception as e:
        logger.error(f"Error extracting file ID from URL {url}: {e}")
        return None

def download_image(url, filename, max_retries=3):
    """Download an image from Google Drive URL."""
    try:
        file_id = extract_file_id_from_google_drive_url(url)
        if not file_id:
            logger.error(f"Could not extract file ID from URL: {url}")
            return False
        
        # Use the direct download URL format
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading {filename} (attempt {attempt + 1}/{max_retries})")
                
                response = requests.get(download_url, timeout=30)
                response.raise_for_status()
                
                # Check if we got a valid image response
                content_type = response.headers.get('content-type', '').lower()
                if 'image' not in content_type and len(response.content) < 1000:
                    logger.warning(f"Response might not be an image for {filename}")
                
                # Create the images directory if it doesn't exist
                os.makedirs('static/images/categories', exist_ok=True)
                
                # Save the image
                filepath = f'static/images/categories/{filename}'
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Verify the file was created and has content
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    logger.info(f"✅ Successfully downloaded {filename} ({len(response.content)} bytes)")
                    return True
                else:
                    logger.error(f"❌ Failed to save {filename}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Download attempt {attempt + 1} failed for {filename}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    logger.error(f"❌ All download attempts failed for {filename}")
                    return False
                    
    except Exception as e:
        logger.error(f"Error downloading {filename}: {e}")
        return False

def update_database_with_local_paths():
    """Update the database to use local image paths instead of Google Drive URLs."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Get all categories with images
            cursor.execute("SELECT id, name, image_url FROM categories WHERE image_url IS NOT NULL")
            categories = cursor.fetchall()
            
            updated_count = 0
            
            for category_id, name, image_url in categories:
                filename = sanitize_filename(name) + '.jpg'
                local_path = f'/static/images/categories/{filename}'
                
                # Check if the local file exists
                if os.path.exists(f'static/images/categories/{filename}'):
                    cursor.execute(
                        "UPDATE categories SET image_url = %s WHERE id = %s",
                        (local_path, category_id)
                    )
                    updated_count += 1
                    logger.info(f"✅ Updated database path for {name}")
            
            conn.commit()
            logger.info(f"🎉 Updated {updated_count} categories with local image paths")
            
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()

def download_all_category_images():
    """Download all category images from the database."""
    try:
        logger.info("🚀 Starting category image download process...")
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT name, image_url FROM categories WHERE image_url IS NOT NULL ORDER BY name")
            categories = cursor.fetchall()
        
        conn.close()
        
        logger.info(f"Found {len(categories)} categories with images to download")
        
        downloaded_count = 0
        skipped_count = 0
        failed_count = 0
        
        for name, image_url in categories:
            filename = sanitize_filename(name) + '.jpg'
            filepath = f'static/images/categories/{filename}'
            
            # Skip if file already exists and has content
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                logger.info(f"⏭️ Skipping {name} - file already exists")
                skipped_count += 1
                continue
            
            # Download the image
            if download_image(image_url, filename):
                downloaded_count += 1
            else:
                failed_count += 1
            
            # Small delay between downloads to be respectful
            time.sleep(1)
        
        logger.info(f"📊 Download Summary:")
        logger.info(f"   ✅ Downloaded: {downloaded_count}")
        logger.info(f"   ⏭️ Skipped: {skipped_count}")
        logger.info(f"   ❌ Failed: {failed_count}")
        logger.info(f"   📁 Total: {len(categories)}")
        
        # Update database with local paths
        logger.info("🔄 Updating database with local image paths...")
        update_database_with_local_paths()
        
        logger.info("🎉 Category image download process completed!")
        return True
        
    except Exception as e:
        logger.error(f"Fatal error in download process: {e}")
        return False

if __name__ == "__main__":
    success = download_all_category_images()
    if success:
        print("✅ All category images downloaded successfully!")
        print("🎨 Your beautiful medical procedure images should now display properly!")
    else:
        print("❌ Some issues occurred during download. Check the logs above.")