#!/usr/bin/env python3
"""
Download category images in small batches to avoid timeouts.
"""

import os
import psycopg2
import requests
import logging
import re
import time
from urllib.parse import urlparse, parse_qs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def sanitize_filename(name):
    """Convert category name to a safe filename."""
    filename = re.sub(r'[^\w\s-]', '', name)
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename.lower()

def extract_file_id_from_google_drive_url(url):
    """Extract the file ID from a Google Drive URL."""
    try:
        if 'drive.google.com' in url:
            if '/file/d/' in url:
                file_id = url.split('/file/d/')[1].split('/')[0]
            elif 'id=' in url:
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                file_id = query_params.get('id', [None])[0]
            else:
                return None
            return file_id
        return None
    except Exception as e:
        logger.error(f"Error extracting file ID: {e}")
        return None

def download_image(url, filename):
    """Download an image from Google Drive URL."""
    try:
        file_id = extract_file_id_from_google_drive_url(url)
        if not file_id:
            return False
        
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        response = requests.get(download_url, timeout=20)
        response.raise_for_status()
        
        os.makedirs('static/images/categories', exist_ok=True)
        
        filepath = f'static/images/categories/{filename}'
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            logger.info(f"✅ Downloaded {filename} ({len(response.content)} bytes)")
            return True
        return False
        
    except Exception as e:
        logger.error(f"❌ Failed to download {filename}: {e}")
        return False

def download_batch(batch_size=5):
    """Download a batch of category images."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT name, image_url FROM categories WHERE image_url IS NOT NULL ORDER BY name")
            categories = cursor.fetchall()
        conn.close()
        
        downloaded = 0
        skipped = 0
        
        for name, image_url in categories[:batch_size]:
            filename = sanitize_filename(name) + '.jpg'
            filepath = f'static/images/categories/{filename}'
            
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                logger.info(f"⏭️ Skipping {name} - already exists")
                skipped += 1
                continue
            
            if download_image(image_url, filename):
                downloaded += 1
            
            time.sleep(1)  # Small delay between downloads
        
        logger.info(f"📊 Batch complete: {downloaded} downloaded, {skipped} skipped")
        return downloaded > 0
        
    except Exception as e:
        logger.error(f"Error in batch download: {e}")
        return False

if __name__ == "__main__":
    success = download_batch(batch_size=8)
    if success:
        print("✅ Batch download completed!")
    else:
        print("ℹ️ No new images to download or error occurred")