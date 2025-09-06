#!/usr/bin/env python3
"""
Import category images from CSV file.

This script reads the category images CSV and updates the database with the image URLs.
Converts Google Drive sharing links to direct download links.
"""

import csv
import os
import re
import psycopg2
from urllib.parse import urlparse, parse_qs
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(database_url)

def convert_google_drive_url(sharing_url):
    """
    Convert Google Drive sharing URL to direct download URL.
    
    Args:
        sharing_url (str): Google Drive sharing URL
        
    Returns:
        str: Direct download URL
    """
    try:
        # Extract file ID from various Google Drive URL formats
        file_id = None
        
        # Format 1: /file/d/{FILE_ID}/view
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', sharing_url)
        if match:
            file_id = match.group(1)
        
        # Format 2: id={FILE_ID}
        if not file_id:
            match = re.search(r'id=([a-zA-Z0-9_-]+)', sharing_url)
            if match:
                file_id = match.group(1)
        
        # Format 3: open?id={FILE_ID}
        if not file_id:
            match = re.search(r'open\?id=([a-zA-Z0-9_-]+)', sharing_url)
            if match:
                file_id = match.group(1)
        
        if file_id:
            # Return direct download URL
            return f"https://drive.google.com/uc?export=view&id={file_id}"
        else:
            logger.warning(f"Could not extract file ID from URL: {sharing_url}")
            return sharing_url
            
    except Exception as e:
        logger.error(f"Error converting Google Drive URL: {e}")
        return sharing_url

def clean_category_name(category_name):
    """
    Clean category name by removing body part references in parentheses.
    
    Args:
        category_name (str): Original category name
        
    Returns:
        str: Cleaned category name
    """
    # Remove text in parentheses (like body part references)
    cleaned = re.sub(r'\s*\([^)]+\)$', '', category_name).strip()
    return cleaned

def update_category_images():
    """Update category images from CSV file."""
    csv_file_path = 'attached_assets/category_images - Sheet1.csv'
    
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        return False
    
    conn = get_db_connection()
    updated_count = 0
    not_found_count = 0
    
    try:
        with conn.cursor() as cursor:
            # Read CSV and update categories
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    category_name = row['category_name'].strip()
                    image_url = row['image_url'].strip()
                    
                    if not category_name or not image_url:
                        continue
                    
                    # Clean the category name
                    clean_name = clean_category_name(category_name)
                    
                    # Convert Google Drive URL to direct download URL
                    direct_url = convert_google_drive_url(image_url)
                    
                    # Try to find and update the category
                    # First try exact match
                    cursor.execute(
                        "UPDATE categories SET image_url = %s WHERE LOWER(name) = LOWER(%s)",
                        (direct_url, clean_name)
                    )
                    
                    if cursor.rowcount > 0:
                        logger.info(f"✅ Updated '{clean_name}' with exact match")
                        updated_count += cursor.rowcount
                    else:
                        # Try partial match
                        cursor.execute(
                            "UPDATE categories SET image_url = %s WHERE LOWER(name) LIKE LOWER(%s)",
                            (direct_url, f"%{clean_name}%")
                        )
                        
                        if cursor.rowcount > 0:
                            logger.info(f"✅ Updated '{clean_name}' with partial match")
                            updated_count += cursor.rowcount
                        else:
                            # Try reverse partial match
                            cursor.execute(
                                "SELECT name FROM categories WHERE LOWER(%s) LIKE LOWER(CONCAT('%%', name, '%%'))",
                                (clean_name,)
                            )
                            
                            matches = cursor.fetchall()
                            if matches:
                                # Update the first match
                                cursor.execute(
                                    "UPDATE categories SET image_url = %s WHERE name = %s",
                                    (direct_url, matches[0][0])
                                )
                                logger.info(f"✅ Updated '{matches[0][0]}' with reverse match for '{clean_name}'")
                                updated_count += cursor.rowcount
                            else:
                                logger.warning(f"❌ No match found for category: '{clean_name}' (original: '{category_name}')")
                                not_found_count += 1
            
            conn.commit()
            
        logger.info(f"🎉 Successfully updated {updated_count} category images!")
        logger.info(f"⚠️  Could not match {not_found_count} categories")
        
        # Show final status
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url IS NOT NULL")
            total_with_images = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM categories")
            total_categories = cursor.fetchone()[0]
            
            logger.info(f"📊 Final status: {total_with_images}/{total_categories} categories have images")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating category images: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function."""
    try:
        logger.info("Starting category image import...")
        success = update_category_images()
        
        if success:
            logger.info("✅ Category image import completed successfully!")
        else:
            logger.error("❌ Category image import failed!")
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()