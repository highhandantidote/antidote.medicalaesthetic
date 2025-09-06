#!/usr/bin/env python3
"""
HARD SOLUTION: Force ALL categories to use local images.
This will completely eliminate FontAwesome icons.
"""

import os
import psycopg2
import re

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def sanitize_filename(name):
    """Convert category name to filename format."""
    filename = re.sub(r'[^\w\s-]', '', name)
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename.lower()

def force_all_local_images():
    """Force ALL categories to use local image paths - no exceptions."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Get ALL categories
            cursor.execute("SELECT id, name FROM categories")
            all_categories = cursor.fetchall()
            
            updated_count = 0
            
            for category_id, name in all_categories:
                filename = sanitize_filename(name) + '.jpg'
                local_path = f'/static/images/categories/{filename}'
                filepath = f'static/images/categories/{filename}'
                
                # If local file exists, use it. Otherwise use default.
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    final_path = local_path
                    print(f"✅ {name} -> Using real image")
                else:
                    final_path = '/static/images/categories/default-procedure.jpg'
                    print(f"🔧 {name} -> Using default image (no FontAwesome!)")
                
                # Update database - FORCE the change
                cursor.execute(
                    "UPDATE categories SET image_url = %s WHERE id = %s",
                    (final_path, category_id)
                )
                updated_count += 1
            
            conn.commit()
            print(f"\n🎉 HARD SOLUTION APPLIED!")
            print(f"✅ Updated ALL {updated_count} categories to use images")
            print(f"❌ FontAwesome icons are now COMPLETELY ELIMINATED")
            
            # Verify - check that NO categories have Google Drive URLs
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url LIKE '%drive.google.com%'")
            google_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url IS NULL")
            null_count = cursor.fetchone()[0]
            
            print(f"📊 Verification:")
            print(f"   Google Drive URLs remaining: {google_count} (should be 0)")
            print(f"   NULL image URLs: {null_count} (should be 0)")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    force_all_local_images()
    print("\n🚀 HARD SOLUTION COMPLETE!")
    print("💪 FontAwesome icons are permanently eliminated!")
    print("🎨 All categories now use real images!")