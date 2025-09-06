#!/usr/bin/env python3
"""
Download priority category images that are currently visible on homepage.

Focus on the 6 categories shown in the slider to get immediate results.
"""

import os
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
        file_id = extract_google_drive_id(google_drive_url)
        if not file_id:
            logger.error(f"Could not extract file ID from URL: {google_drive_url}")
            return False
        
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(download_url, stream=True, timeout=10)
        
        if response.status_code == 200:
            os.makedirs(os.path.dirname(local_filename), exist_ok=True)
            
            with open(local_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Downloaded: {local_filename}")
            return True
        else:
            logger.error(f"❌ Failed to download, status: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error downloading: {e}")
        return False

def sanitize_filename(category_name):
    """Create a safe filename from category name."""
    safe_name = "".join(c for c in category_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_').lower()
    return safe_name

def download_priority_images():
    """Download images for categories currently showing on homepage."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    # Priority categories (the ones showing on homepage)
    priority_categories = [
        'Gender Confirmation Surgery',
        'General Dentistry', 
        'Male Body Enhancement',
        'Oral And Maxillofacial Surgeries',
        'Podiatry',
        'Reconstructive Surgeries'
    ]
    
    try:
        with conn.cursor() as cursor:
            successful_downloads = 0
            
            for category_name in priority_categories:
                logger.info(f"Processing priority category: {category_name}")
                
                # Get category info
                cursor.execute("""
                    SELECT id, image_url 
                    FROM categories 
                    WHERE name = %s AND image_url LIKE '%drive.google.com%'
                """, (category_name,))
                
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"Category not found or no Google Drive URL: {category_name}")
                    continue
                
                category_id, google_drive_url = result
                
                # Create local filename
                safe_name = sanitize_filename(category_name)
                local_filename = f"static/images/categories/{safe_name}.jpg"
                
                # Skip if already downloaded
                if os.path.exists(local_filename):
                    logger.info(f"⏭️ Already exists: {local_filename}")
                    # Update database anyway
                    local_url = f"/static/images/categories/{safe_name}.jpg"
                    cursor.execute("UPDATE categories SET image_url = %s WHERE id = %s", (local_url, category_id))
                    continue
                
                # Download the image
                if download_image(google_drive_url, local_filename):
                    # Update database with local path
                    local_url = f"/static/images/categories/{safe_name}.jpg"
                    cursor.execute("UPDATE categories SET image_url = %s WHERE id = %s", (local_url, category_id))
                    successful_downloads += 1
                    logger.info(f"✅ Updated database for {category_name}")
                else:
                    logger.error(f"❌ Failed to download image for {category_name}")
            
            # Commit all changes
            conn.commit()
            
            logger.info(f"🎉 Priority download complete!")
            logger.info(f"✅ Successful: {successful_downloads} categories")
            
            return successful_downloads > 0
            
    except Exception as e:
        logger.error(f"Error during download process: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function to download priority images."""
    logger.info("=== Downloading Priority Category Images ===")
    
    if download_priority_images():
        logger.info("🎉 Priority images downloaded successfully!")
        logger.info("Your homepage category slider should now show beautiful medical images!")
    else:
        logger.error("❌ Priority image download failed")

if __name__ == "__main__":
    main()