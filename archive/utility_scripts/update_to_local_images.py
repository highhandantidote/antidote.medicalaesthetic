#!/usr/bin/env python3
"""
Update database to use local image paths instead of Google Drive URLs.
This will fix the category image display issue.
"""

import os
import psycopg2
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def sanitize_filename(name):
    """Convert category name to filename format."""
    filename = re.sub(r'[^\w\s-]', '', name)
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename.lower()

def update_local_image_paths():
    """Update categories to use local image paths."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Get all categories with Google Drive URLs
            cursor.execute("SELECT id, name, image_url FROM categories WHERE image_url LIKE '%drive.google.com%'")
            categories = cursor.fetchall()
            
            updated_count = 0
            
            for category_id, name, current_url in categories:
                filename = sanitize_filename(name) + '.jpg'
                local_path = f'/static/images/categories/{filename}'
                filepath = f'static/images/categories/{filename}'
                
                # Check if local file exists
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    cursor.execute(
                        "UPDATE categories SET image_url = %s WHERE id = %s",
                        (local_path, category_id)
                    )
                    updated_count += 1
                    logger.info(f"✅ Updated {name} to use local image")
                else:
                    logger.info(f"⏳ {name} - local image not found yet")
            
            conn.commit()
            logger.info(f"🎉 Updated {updated_count} categories to use local images!")
            
            # Show final status
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url LIKE '/static/images/categories/%'")
            local_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url IS NOT NULL")
            total_count = cursor.fetchone()[0]
            
            logger.info(f"📊 Status: {local_count}/{total_count} categories now use local images")
            
    except Exception as e:
        logger.error(f"Error updating image paths: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_local_image_paths()
    print("✅ Database updated to use local images!")
    print("🎨 Category images should now display properly on your website!")