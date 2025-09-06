#!/usr/bin/env python3
"""
Update all category images from CSV file.

This script:
1. Clears all existing category image_url fields
2. Updates them with new images from the CSV file
3. Handles category name mapping with body part extraction
4. Converts Google Drive URLs to direct image URLs
"""

import os
import csv
import logging
import psycopg2
from urllib.parse import urlparse, parse_qs
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def convert_google_drive_url(drive_url):
    """Convert Google Drive share URL to direct image URL."""
    if 'drive.google.com' not in drive_url:
        return drive_url
    
    # Extract file ID from various Google Drive URL formats
    file_id = None
    
    # Format 1: https://drive.google.com/file/d/{file_id}/view
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_url)
    if match:
        file_id = match.group(1)
    
    # Format 2: https://drive.google.com/open?id={file_id}
    if not file_id:
        parsed = urlparse(drive_url)
        query_params = parse_qs(parsed.query)
        if 'id' in query_params:
            file_id = query_params['id'][0]
    
    if file_id:
        # Convert to direct download URL
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    
    logger.warning(f"Could not extract file ID from Google Drive URL: {drive_url}")
    return drive_url

def extract_body_part_from_category(category_name):
    """Extract body part from category name in parentheses."""
    # Look for text in parentheses at the end
    match = re.search(r'\(([^)]+)\)$', category_name.strip())
    if match:
        return match.group(1).strip()
    return None

def normalize_name(name):
    """Normalize name for comparison."""
    return name.lower().strip().replace('&', 'and').replace(',', '').replace('  ', ' ')

def clear_all_category_images():
    """Clear all existing category image URLs."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE categories SET image_url = NULL")
            cleared_count = cursor.rowcount
            conn.commit()
            logger.info(f"Cleared {cleared_count} existing category images")
            return cleared_count
    except Exception as e:
        conn.rollback()
        logger.error(f"Error clearing category images: {e}")
        raise
    finally:
        conn.close()

def get_database_categories():
    """Get all categories with their body parts from database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.name, bp.name as body_part_name
                FROM categories c
                JOIN body_parts bp ON c.body_part_id = bp.id
                ORDER BY c.name
            """)
            
            categories = {}
            for row in cursor.fetchall():
                cat_id, cat_name, bp_name = row
                categories[normalize_name(cat_name)] = {
                    'id': cat_id,
                    'name': cat_name,
                    'body_part': bp_name
                }
            
            logger.info(f"Found {len(categories)} categories in database")
            return categories
    except Exception as e:
        logger.error(f"Error getting database categories: {e}")
        raise
    finally:
        conn.close()

def find_matching_category(csv_category_name, db_categories):
    """Find matching category in database for CSV category name."""
    # Extract body part from CSV category name
    csv_body_part = extract_body_part_from_category(csv_category_name)
    
    # Clean category name (remove body part in parentheses)
    clean_csv_name = re.sub(r'\s*\([^)]+\)$', '', csv_category_name).strip()
    
    # Try different matching strategies
    normalized_csv_name = normalize_name(clean_csv_name)
    
    # Strategy 1: Direct match on cleaned name
    if normalized_csv_name in db_categories:
        return db_categories[normalized_csv_name]
    
    # Strategy 2: Try with body part context
    if csv_body_part:
        normalized_body_part = normalize_name(csv_body_part)
        
        for db_key, db_cat in db_categories.items():
            db_body_part = normalize_name(db_cat['body_part'])
            
            # Check if names match and body parts are compatible
            if normalized_csv_name in db_key or db_key in normalized_csv_name:
                if (normalized_body_part in db_body_part or 
                    db_body_part in normalized_body_part or
                    normalized_body_part == db_body_part):
                    return db_cat
    
    # Strategy 3: Partial name matching
    for db_key, db_cat in db_categories.items():
        # Try partial matches
        if (normalized_csv_name in db_key or 
            db_key in normalized_csv_name or
            any(word in db_key for word in normalized_csv_name.split() if len(word) > 3)):
            return db_cat
    
    return None

def update_category_images_from_csv():
    """Update category images from CSV file."""
    csv_file_path = 'attached_assets/category_images - Sheet1.csv'
    
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        return False
    
    # Get all database categories
    db_categories = get_database_categories()
    
    updated_count = 0
    error_count = 0
    
    conn = get_db_connection()
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            with conn.cursor() as cursor:
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        category_name = row['category_name'].strip()
                        image_url = row['image_url'].strip()
                        
                        if not category_name or not image_url:
                            logger.warning(f"Row {row_num}: Missing category_name or image_url")
                            error_count += 1
                            continue
                        
                        # Find matching category in database
                        matching_category = find_matching_category(category_name, db_categories)
                        
                        if not matching_category:
                            logger.warning(f"Row {row_num}: No matching category found for '{category_name}'")
                            error_count += 1
                            continue
                        
                        # Convert Google Drive URL to direct URL
                        direct_url = convert_google_drive_url(image_url)
                        
                        # Update category image
                        cursor.execute(
                            "UPDATE categories SET image_url = %s WHERE id = %s",
                            (direct_url, matching_category['id'])
                        )
                        
                        logger.info(f"Updated '{matching_category['name']}' (body part: {matching_category['body_part']}) with image")
                        updated_count += 1
                        
                    except Exception as e:
                        logger.error(f"Row {row_num}: Error processing row: {e}")
                        error_count += 1
                        continue
        
        conn.commit()
        logger.info(f"Successfully updated {updated_count} category images")
        logger.info(f"Errors encountered: {error_count}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating category images: {e}")
        return False
    finally:
        conn.close()

def verify_updates():
    """Verify the image updates."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Count categories with images
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url IS NOT NULL")
            with_images = cursor.fetchone()[0]
            
            # Count total categories
            cursor.execute("SELECT COUNT(*) FROM categories")
            total_categories = cursor.fetchone()[0]
            
            logger.info(f"Verification: {with_images}/{total_categories} categories now have images")
            
            # Show some examples
            cursor.execute("""
                SELECT c.name, bp.name, c.image_url
                FROM categories c
                JOIN body_parts bp ON c.body_part_id = bp.id
                WHERE c.image_url IS NOT NULL
                LIMIT 5
            """)
            
            examples = cursor.fetchall()
            logger.info("Sample updated categories:")
            for cat_name, bp_name, img_url in examples:
                logger.info(f"  - {cat_name} ({bp_name}): {img_url[:60]}...")
                
    except Exception as e:
        logger.error(f"Error verifying updates: {e}")
    finally:
        conn.close()

def main():
    """Main function to update all category images."""
    try:
        logger.info("Starting category image update process...")
        
        # Step 1: Clear existing images
        logger.info("Step 1: Clearing all existing category images...")
        cleared_count = clear_all_category_images()
        
        # Step 2: Update with new images
        logger.info("Step 2: Updating categories with new images from CSV...")
        success = update_category_images_from_csv()
        
        if success:
            # Step 3: Verify updates
            logger.info("Step 3: Verifying updates...")
            verify_updates()
            
            logger.info("✅ Category image update completed successfully!")
        else:
            logger.error("❌ Category image update failed!")
            
    except Exception as e:
        logger.error(f"Fatal error in main process: {e}")
        raise

if __name__ == "__main__":
    main()