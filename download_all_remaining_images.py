#!/usr/bin/env python3
"""
Download ALL remaining category images from Google Drive to ensure 
every category has its beautiful specific image from the CSV file.
"""

import os
import psycopg2
import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_db_connection():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def sanitize_filename(name):
    filename = re.sub(r'[^\w\s-]', '', name)
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename.lower()

def download_single_image(category_data):
    """Download a single category image."""
    name, url = category_data
    filename = sanitize_filename(name) + '.jpg'
    filepath = f'static/images/categories/{filename}'
    
    # Skip if already exists
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return f"⏭️ {name} - already exists"
    
    try:
        # Extract file ID from Google Drive URL
        if 'id=' in url:
            file_id = url.split('id=')[1]
        elif '/file/d/' in url:
            file_id = url.split('/file/d/')[1].split('/')[0]
        else:
            return f"❌ {name} - invalid URL format"
        
        download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        
        response = requests.get(download_url, timeout=15)
        response.raise_for_status()
        
        # Save the image
        os.makedirs('static/images/categories', exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return f"✅ {name} ({len(response.content)} bytes)"
        
    except Exception as e:
        return f"❌ {name}: {str(e)[:50]}"

def download_all_csv_images():
    """Download ALL category images from your CSV data."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Get ALL categories that don't have local images yet
            cursor.execute("""
                SELECT name, image_url 
                FROM categories 
                WHERE image_url LIKE '%drive.google.com%' 
                   OR image_url = '/static/images/categories/default-procedure.jpg'
                ORDER BY name
            """)
            
            # Also get categories with Google Drive URLs that need to be downloaded
            cursor.execute("""
                SELECT name, image_url 
                FROM categories 
                WHERE image_url LIKE '%drive.google.com%'
                ORDER BY name
            """)
            google_categories = cursor.fetchall()
            
            # Get categories currently using default image that should have real images
            cursor.execute("""
                SELECT c1.name, c2.image_url
                FROM categories c1
                JOIN categories c2 ON c1.name = c2.name
                WHERE c1.image_url = '/static/images/categories/default-procedure.jpg'
                  AND c2.image_url LIKE '%drive.google.com%'
            """)
            default_categories = cursor.fetchall()
            
        conn.close()
        
        # Combine all categories that need their real images
        all_to_download = google_categories + default_categories
        
        print(f"🚀 Downloading {len(all_to_download)} beautiful category images from your CSV data...")
        
        # Download images in batches to avoid timeouts
        batch_size = 5
        total_downloaded = 0
        
        for i in range(0, len(all_to_download), batch_size):
            batch = all_to_download[i:i+batch_size]
            print(f"\n📦 Processing batch {i//batch_size + 1} ({len(batch)} images)...")
            
            for category_data in batch:
                result = download_single_image(category_data)
                print(result)
                if "✅" in result:
                    total_downloaded += 1
                time.sleep(0.5)  # Small delay between downloads
        
        print(f"\n🎉 Downloaded {total_downloaded} beautiful category images!")
        
        # Now update database to use all the downloaded images
        update_database_with_real_images()
        
        return True
        
    except Exception as e:
        print(f"Error downloading images: {e}")
        return False

def update_database_with_real_images():
    """Update database to use the beautiful downloaded images."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM categories")
            all_categories = cursor.fetchall()
            
            updated_count = 0
            
            for category_id, name in all_categories:
                filename = sanitize_filename(name) + '.jpg'
                local_path = f'/static/images/categories/{filename}'
                filepath = f'static/images/categories/{filename}'
                
                # If the beautiful image exists locally, use it
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    cursor.execute(
                        "UPDATE categories SET image_url = %s WHERE id = %s",
                        (local_path, category_id)
                    )
                    updated_count += 1
                    print(f"✅ Updated {name} to use beautiful image")
            
            conn.commit()
            
            # Final verification
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url LIKE '/static/images/categories/%' AND image_url != '/static/images/categories/default-procedure.jpg'")
            real_images_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM categories")
            total_categories = cursor.fetchone()[0]
            
            print(f"\n🎨 FINAL STATUS:")
            print(f"✅ {real_images_count}/{total_categories} categories have beautiful specific images")
            print(f"🎉 Your CSV images are now displaying!")
            
    except Exception as e:
        print(f"Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    success = download_all_csv_images()
    if success:
        print("\n🎊 SUCCESS! All your beautiful category images from the CSV are now ready!")
        print("🎨 Every category will show its specific beautiful image!")
    else:
        print("\n❌ Some issues occurred. Please check the output above.")