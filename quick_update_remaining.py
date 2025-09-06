#!/usr/bin/env python3
"""
Quick update of remaining categories with NEW CSV images.
"""

import os
import csv
import psycopg2
import requests
import re
import time
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

# Priority categories that need NEW images
priority_updates = [
    ('Breast Surgery', 'https://drive.google.com/file/d/1eGllh63v6N5LwC8BDYk6zBU7wLDyhVLF/view?usp=drive_link'),
    ('Hip & Butt Enhancement', 'https://drive.google.com/file/d/13rRnQ6cRxJwz8KFbrecWYcSN66OTH6sN/view?usp=drive_link'),
    ('Rhinoplasty', 'https://drive.google.com/file/d/1czF_4Cz6_V-U5Z-1AFcSoLF6Jq9rYhVS/view?usp=drive_link'),
    ('Body Contouring', 'https://drive.google.com/file/d/1LpOOgl1y61p6i4mma4AaxUIRW5haePDx/view?usp=drive_link'),
    ('Face And Neck Lifts', 'https://drive.google.com/file/d/1j1iSf4JOMU7oTrnSculxioKPMhsN8LRl/view?usp=sharing'),
    ('Hair Restoration', 'https://drive.google.com/file/d/1efiOM4elujOAn79UA25u1A33q55beDvW/view?usp=sharing'),
    ('Skin Treatments', 'https://drive.google.com/file/d/1rzA-IYJHvsGtbuZMPVcQjb-LL0zqxyh0/view?usp=sharing'),
    ('Lip Augmentation', 'https://drive.google.com/file/d/1HqUaTC1_OaeKDNwBcRNMs8CHbJPm5INA/view?usp=drive_link')
]

def main():
    conn = get_db_connection()
    
    updated_count = 0
    
    for category_name, image_url in priority_updates:
        # Find category in database
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM categories WHERE name ILIKE %s", (f'%{category_name}%',))
            result = cursor.fetchone()
            
            if result:
                cat_id = result[0]
                safe_name = re.sub(r'[^\w\s-]', '', category_name).lower().replace(' ', '_').replace('&', 'and')
                local_filename = f"static/images/categories/{safe_name}.jpg"
                local_path = f"/static/images/categories/{safe_name}.jpg"
                
                logger.info(f"📥 Downloading '{category_name}' from NEW CSV...")
                
                if download_image(image_url, local_filename):
                    cursor.execute("UPDATE categories SET image_url = %s WHERE id = %s", (local_path, cat_id))
                    updated_count += 1
                    logger.info(f"✅ Updated '{category_name}' with NEW image ({updated_count}/8)")
                
                time.sleep(2)
            else:
                logger.warning(f"⚠️  Category '{category_name}' not found in database")
    
    conn.commit()
    conn.close()
    
    logger.info(f"🎉 Updated {updated_count} priority categories with NEW beautiful images!")

if __name__ == "__main__":
    main()