#!/usr/bin/env python3
"""
Batch update categories with CSV images - processes in small batches to avoid timeouts.
"""

import os
import csv
import requests
import psycopg2
import time

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def safe_filename(name):
    """Convert category name to safe filename."""
    return name.lower().replace(' ', '_').replace(',', '').replace('&', 'and').replace('-', '_').replace('(', '').replace(')', '')

def extract_file_id(url):
    """Extract Google Drive file ID from URL."""
    if '/file/d/' in url:
        return url.split('/file/d/')[1].split('/')[0]
    elif 'id=' in url:
        return url.split('id=')[1].split('&')[0]
    return None

def download_image(url, filepath):
    """Download image from Google Drive URL."""
    try:
        file_id = extract_file_id(url)
        if not file_id:
            return False
        
        download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(download_url, timeout=10, stream=True)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(filepath)
        print(f"✅ Downloaded {os.path.basename(filepath)} ({file_size // 1024}KB)")
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def process_batch():
    """Process remaining categories in a small batch."""
    
    # Load CSV data
    csv_data = {}
    with open('attached_assets/new_category_images - Sheet1.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            category_name = row['category_name'].strip()
            image_url = row['image_url'].strip()
            csv_data[category_name] = image_url
    
    conn = get_db_connection()
    updated_count = 0
    
    try:
        with conn.cursor() as cursor:
            # Get categories that still need updating (limit to 10 per batch)
            cursor.execute("""
                SELECT id, name FROM categories 
                WHERE image_url = '/static/images/categories/default-procedure.jpg' 
                   OR image_url IS NULL
                ORDER BY name
                LIMIT 10
            """)
            categories = cursor.fetchall()
            
            if not categories:
                print("🎉 All categories already have beautiful images!")
                return 0
            
            print(f"🔄 Processing batch of {len(categories)} categories...")
            
            for cat_id, cat_name in categories:
                # Find matching image in CSV
                image_url = None
                
                if cat_name in csv_data:
                    image_url = csv_data[cat_name]
                else:
                    # Try partial matches
                    for csv_name, csv_url in csv_data.items():
                        if cat_name.lower() in csv_name.lower() or csv_name.lower() in cat_name.lower():
                            image_url = csv_url
                            break
                
                if image_url:
                    safe_name = safe_filename(cat_name)
                    filename = f"{safe_name}.jpg"
                    filepath = f"static/images/categories/{filename}"
                    local_url = f"/static/images/categories/{filename}"
                    
                    print(f"🔄 Updating '{cat_name}'...")
                    
                    if download_image(image_url, filepath):
                        cursor.execute(
                            "UPDATE categories SET image_url = %s WHERE id = %s",
                            (local_url, cat_id)
                        )
                        updated_count += 1
                        print(f"✅ Updated '{cat_name}'")
                    else:
                        print(f"⚠️ Failed to download '{cat_name}'")
                else:
                    print(f"⚠️ No match found for '{cat_name}'")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return updated_count

def show_progress():
    """Show current progress."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url != '/static/images/categories/default-procedure.jpg' AND image_url IS NOT NULL")
            with_images = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM categories")
            total = cursor.fetchone()[0]
            
            print(f"📊 Progress: {with_images}/{total} categories have beautiful images ({(with_images/total)*100:.1f}%)")
            
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Processing category images in batches...")
    
    total_updated = 0
    while True:
        updated = process_batch()
        total_updated += updated
        
        if updated == 0:
            break
        
        show_progress()
        print(f"Batch complete! Continuing with next batch...\n")
    
    print(f"\n🎉 All Done! Updated {total_updated} categories with beautiful images")
    show_progress()