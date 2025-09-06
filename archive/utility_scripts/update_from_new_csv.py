#!/usr/bin/env python3
"""
Update all categories with beautiful images from your corrected CSV file.
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
            print(f"❌ Could not extract file ID from URL")
            return False
        
        download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        
        response = requests.get(download_url, timeout=15, stream=True)
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

def update_categories():
    """Update all categories with your beautiful CSV images."""
    
    # Load your CSV file
    csv_data = {}
    try:
        with open('attached_assets/new_category_images - Sheet1.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                category_name = row['category_name'].strip()
                image_url = row['image_url'].strip()
                csv_data[category_name] = image_url
        
        print(f"📋 Loaded {len(csv_data)} beautiful images from your CSV")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return 0
    
    conn = get_db_connection()
    updated_count = 0
    
    try:
        with conn.cursor() as cursor:
            # Get all categories
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
            categories = cursor.fetchall()
            
            print(f"🎨 Processing {len(categories)} categories...")
            
            for cat_id, cat_name in categories:
                # Find matching image in CSV
                image_url = None
                
                # Try exact match first
                if cat_name in csv_data:
                    image_url = csv_data[cat_name]
                else:
                    # Try partial matches (for cases like "Abdominoplasty" vs "Abdominoplasty (Stomach)")
                    for csv_name, csv_url in csv_data.items():
                        if cat_name.lower() in csv_name.lower() or csv_name.lower() in cat_name.lower():
                            image_url = csv_url
                            break
                
                if image_url:
                    # Download the image
                    safe_name = safe_filename(cat_name)
                    filename = f"{safe_name}.jpg"
                    filepath = f"static/images/categories/{filename}"
                    local_url = f"/static/images/categories/{filename}"
                    
                    print(f"🔄 Updating '{cat_name}'...")
                    
                    if download_image(image_url, filepath):
                        # Update database
                        cursor.execute(
                            "UPDATE categories SET image_url = %s WHERE id = %s",
                            (local_url, cat_id)
                        )
                        updated_count += 1
                        print(f"✅ Updated '{cat_name}' with beautiful image")
                        
                        # Small delay
                        time.sleep(0.5)
                    else:
                        print(f"⚠️ Failed to download image for '{cat_name}'")
                else:
                    print(f"⚠️ No matching image found for '{cat_name}' in CSV")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print(f"\n🎉 Update Complete!")
    print(f"✅ Successfully updated {updated_count} categories")
    
    return updated_count

def verify_results():
    """Show the final status of all categories."""
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT name, image_url FROM categories 
                WHERE image_url != '/static/images/categories/default-procedure.jpg'
                  AND image_url IS NOT NULL
                ORDER BY name
            """)
            updated_categories = cursor.fetchall()
            
            cursor.execute("""
                SELECT COUNT(*) FROM categories 
                WHERE image_url = '/static/images/categories/default-procedure.jpg' 
                   OR image_url IS NULL
            """)
            remaining_default = cursor.fetchone()[0]
            
            print(f"\n📊 Final Results:")
            print(f"   Categories with beautiful images: {len(updated_categories)}")
            print(f"   Still using default image: {remaining_default}")
            
            if updated_categories:
                print(f"\n✨ Categories now showing beautiful images:")
                for name, url in updated_categories[:10]:  # Show first 10
                    print(f"   • {name}")
                if len(updated_categories) > 10:
                    print(f"   ... and {len(updated_categories) - 10} more!")
                    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting category image update with your beautiful CSV images...")
    updated = update_categories()
    verify_results()
    print("\n✨ Your medical procedure categories now display the corrected images!")