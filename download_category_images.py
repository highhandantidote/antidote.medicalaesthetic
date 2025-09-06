#!/usr/bin/env python3
"""
Download category images from Google Drive and store them locally.

This script downloads all category images from Google Drive links and 
updates the database to use local file paths instead.
"""

import os
import sys
import requests
import psycopg2
from urllib.parse import urlparse, parse_qs
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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
    elif 'id=' in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get('id', [None])[0]
    
    return None

def download_image(google_drive_url, local_filename):
    """Download image from Google Drive URL to local file."""
    try:
        # Extract file ID
        file_id = extract_google_drive_id(google_drive_url)
        if not file_id:
            logger.error(f"Could not extract file ID from URL: {google_drive_url}")
            return False
        
        # Create direct download URL
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        # Download the image
        response = requests.get(download_url, stream=True)
        
        if response.status_code == 200:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_filename), exist_ok=True)
            
            # Save the image
            with open(local_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Downloaded: {local_filename}")
            return True
        else:
            logger.error(f"❌ Failed to download from {download_url}, status: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error downloading {google_drive_url}: {e}")
        return False

def sanitize_filename(category_name):
    """Create a safe filename from category name."""
    # Remove special characters and replace spaces with underscores
    safe_name = "".join(c for c in category_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_').lower()
    return safe_name

def download_all_category_images():
    """Download all category images and update database."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        with conn.cursor() as cursor:
            # Get all categories with Google Drive image URLs
            cursor.execute("""
                SELECT id, name, image_url 
                FROM categories 
                WHERE image_url IS NOT NULL 
                AND image_url LIKE '%drive.google.com%'
                ORDER BY name
            """)
            
            categories = cursor.fetchall()
            logger.info(f"Found {len(categories)} categories with Google Drive images")
            
            successful_downloads = 0
            failed_downloads = 0
            
            for category_id, category_name, google_drive_url in categories:
                logger.info(f"Processing: {category_name}")
                
                # Create local filename
                safe_name = sanitize_filename(category_name)
                local_filename = f"static/images/categories/{safe_name}.jpg"
                
                # Download the image
                if download_image(google_drive_url, local_filename):
                    # Update database with local path
                    local_url = f"/static/images/categories/{safe_name}.jpg"
                    cursor.execute("""
                        UPDATE categories 
                        SET image_url = %s 
                        WHERE id = %s
                    """, (local_url, category_id))
                    
                    successful_downloads += 1
                    logger.info(f"✅ Updated database for {category_name}")
                else:
                    failed_downloads += 1
                    logger.error(f"❌ Failed to download image for {category_name}")
            
            # Commit all changes
            conn.commit()
            
            logger.info(f"🎉 Download complete!")
            logger.info(f"✅ Successful: {successful_downloads}")
            logger.info(f"❌ Failed: {failed_downloads}")
            
            return successful_downloads > 0
            
    except Exception as e:
        logger.error(f"Error during download process: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function to download category images."""
    logger.info("=== Downloading Category Images from Google Drive ===")
    
    if download_all_category_images():
        logger.info("🎉 Category image download completed successfully!")
        logger.info("Your beautiful medical procedure images are now stored locally")
        logger.info("and should display properly in the category slider!")
    else:
        logger.error("❌ Category image download failed")

if __name__ == "__main__":
    main()