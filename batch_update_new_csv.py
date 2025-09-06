#!/usr/bin/env python3
"""
Update categories in smaller batches with NEW CSV images.
"""

import os
import csv
import psycopg2
import requests
import re
import time
from urllib.parse import urlparse, parse_qs
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def extract_google_drive_id(url):
    if 'drive.google.com' not in url:
        return None
    
    if '/file/d/' in url:
        return url.split('/file/d/')[1].split('/')[0]
    elif 'open?id=' in url:
        return url.split('open?id=')[1].split('&')[0]
    elif 'id=' in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get('id', [None])[0]
    
    return None

def convert_to_direct_url(drive_url):
    file_id = extract_google_drive_id(drive_url)
    if file_id:
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return drive_url

def download_image(url, filename):
    try:
        direct_url = convert_to_direct_url(url)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = requests.get(direct_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"✅ Downloaded {os.path.basename(filename)} ({len(response.content)/1024:.0f}KB)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download {url}: {str(e)}")
        return False

def main():
    conn = get_db_connection()
    
    # Load NEW CSV data
    csv_data = {}
    with open('attached_assets/new_category_images - Sheet1.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            category_name = row['category_name'].strip()
            image_url = row['image_url'].strip()
            csv_data[category_name.lower()] = {'name': category_name, 'url': image_url}
    
    # Process next 10 categories that need updates
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, name FROM categories 
            WHERE name NOT IN ('Abdominoplasty', 'Acne Treatments')
            ORDER BY name LIMIT 10
        """)
        categories_to_update = cursor.fetchall()
    
    logger.info(f"🔄 Processing next {len(categories_to_update)} categories with NEW CSV images...")
    
    updated_count = 0
    
    for cat_id, cat_name in categories_to_update:
        # Find matching CSV entry
        cat_name_lower = cat_name.lower()
        csv_match = None
        
        # Try exact match first
        if cat_name_lower in csv_data:
            csv_match = csv_data[cat_name_lower]
        else:
            # Try smart partial matching
            for csv_key, csv_info in csv_data.items():
                if (csv_key in cat_name_lower or cat_name_lower in csv_key or
                    any(word in cat_name_lower for word in csv_key.split() if len(word) > 3)):
                    csv_match = csv_info
                    break
        
        if csv_match:
            safe_name = re.sub(r'[^\w\s-]', '', cat_name).lower().replace(' ', '_')
            local_filename = f"static/images/categories/{safe_name}.jpg"
            local_path = f"/static/images/categories/{safe_name}.jpg"
            
            logger.info(f"📥 Downloading '{cat_name}' from NEW CSV...")
            
            if download_image(csv_match['url'], local_filename):
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE categories SET image_url = %s WHERE id = %s", (local_path, cat_id))
                
                updated_count += 1
                logger.info(f"✅ Updated '{cat_name}' with NEW image ({updated_count}/{len(categories_to_update)})")
            
            time.sleep(2)  # Be gentle with Google Drive
        else:
            logger.warning(f"⚠️  No match found in NEW CSV for '{cat_name}'")
    
    conn.commit()
    conn.close()
    
    logger.info(f"🎉 Batch completed! Updated {updated_count} more categories with NEW images!")

if __name__ == "__main__":
    main()