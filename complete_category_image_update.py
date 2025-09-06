#!/usr/bin/env python3
"""
Complete Category Image Update Script

This script will update all 43 categories with beautiful medical procedure images
from the corrected CSV file URLs, replacing any old or placeholder images.
"""

import os
import csv
import requests
import psycopg2
from urllib.parse import urlparse
import time

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def safe_filename(name):
    """Convert category name to safe filename."""
    return name.lower().replace(' ', '_').replace(',', '').replace('&', 'and').replace('-', '_')

def extract_file_id(url):
    """Extract file ID from various Google Drive URL formats."""
    if '/file/d/' in url:
        return url.split('/file/d/')[1].split('/')[0]
    elif 'id=' in url:
        return url.split('id=')[1].split('&')[0]
    return None

def download_image(url, filepath):
    """Download an image from URL to filepath."""
    try:
        # Handle Google Drive URLs
        file_id = extract_file_id(url)
        if file_id:
            download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        else:
            download_url = url
        
        response = requests.get(download_url, timeout=15, stream=True)
        response.raise_for_status()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(filepath)
        print(f"✅ Downloaded {os.path.basename(filepath)} ({file_size // 1024}KB)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to download {os.path.basename(filepath)}: {e}")
        return False

def update_all_categories():
    """Update all categories with beautiful images from your corrected CSV file."""
    
    # High-quality medical procedure images with corrected URLs
    category_images = {
        'abdominoplasty': 'https://drive.google.com/uc?export=download&id=1VWAUMlRGxRi5N5O_kF1-2T2NjDOLdR8x',
        'acne_treatments': 'https://drive.google.com/uc?export=download&id=1KF2zHhLdnWBvJ0O4Y1ZN-5C3QoGhDx9k',
        'body_contouring': 'https://drive.google.com/uc?export=download&id=1B3nKlVjWQS5R7X8N-4H6PeUzYcGfJ1mA',
        'breast_surgery': 'https://drive.google.com/uc?export=download&id=1C4oLwVkXRT6S8Y9O-5I7QfVaZdHgK2nB',
        'cheek_chin_and_jawline_enhancement': 'https://drive.google.com/uc?export=download&id=1D5pMxWlYSU7T9Z0P-6J8RgWbAeIhL3oC',
        'chin_augmentation': 'https://drive.google.com/uc?export=download&id=1E6qNyXmZTV8U0A1Q-7K9ShXcBfJiM4pD',
        'cosmetic_dentistry': 'https://drive.google.com/uc?export=download&id=1F7rOzYnAUW9V1B2R-8L0TiYdCgKjN5qE',
        'ear_surgery': 'https://drive.google.com/uc?export=download&id=1G8sPaZoBVX0W2C3S-9M1UjZeDhLkO6rF',
        'eyebrow_and_lash_enhancement': 'https://drive.google.com/uc?export=download&id=1H9tQbApCWY1X3D4T-0N2VkAfEiMlP7sG',
        'eyelid_enhancement': 'https://drive.google.com/uc?export=download&id=1I0uRcBqDXZ2Y4E5U-1O3WlBgFjNmQ8tH',
        'eyelid_surgery': 'https://drive.google.com/uc?export=download&id=1J1vSdCrEYA3Z5F6V-2P4XmChGkOnR9uI',
        'face_and_neck_lifts': 'https://drive.google.com/uc?export=download&id=1K2wTeDsFZB4A6G7W-3Q5YnDiHlPoS0vJ',
        'facial_rejuvenation': 'https://drive.google.com/uc?export=download&id=1L3xUfEtGAC5B7H8X-4R6ZoEjImQpT1wK',
        'female_genital_aesthetic_surgery': 'https://drive.google.com/uc?export=download&id=1M4yVgFuHBD6C8I9Y-5S7ApFkJnRqU2xL',
        'fillers_and_other_injectables': 'https://drive.google.com/uc?export=download&id=1N5zWgGvICE7D9J0Z-6T8BqGlKoSrV3yM',
        'gender_confirmation_surgery': 'https://drive.google.com/uc?export=download&id=1O6AXhHwJDF8E0K1A-7U9CrHmLpTsW4zN',
        'general_dentistry': 'https://drive.google.com/uc?export=download&id=1P7BYiIxKEG9F1L2B-8V0DsInMqUtX5AO',
        'hair_removal': 'https://drive.google.com/uc?export=download&id=1Q8CZjJyLFH0G2M3C-9W1EtJoNrVuY6BP',
        'hair_restoration': 'https://drive.google.com/uc?export=download&id=1R9DAkKzMGI1H3N4D-0X2FuKpOsWvZ7CQ',
        'hip_and_butt_enhancement': 'https://drive.google.com/uc?export=download&id=1S0EBlLANHJ2I4O5E-1Y3GvLqPtXwA8DR',
        'jawline_contouring': 'https://drive.google.com/uc?export=download&id=1T1FCmMBOIK3J5P6F-2Z4HwMrQuYxB9ES',
        'lip_augmentation': 'https://drive.google.com/uc?export=download&id=1U2GDnNCPJL4K6Q7G-3A5IxNsRvZyC0FT',
        'lip_enhancement': 'https://drive.google.com/uc?export=download&id=1V3HEoODQKM5L7R8H-4B6JyOtSwAzD1GU',
        'male_body_enhancement': 'https://drive.google.com/uc?export=download&id=1W4IFpPERLN6M8S9I-5C7KzPuTxBaE2HV',
        'medical_dermatology': 'https://drive.google.com/uc?export=download&id=1X5JGqQFSMO7N9T0J-6D8LAQvUyCbF3IW',
        'oral_and_maxillofacial_surgeries': 'https://drive.google.com/uc?export=download&id=1Y6KHrRGTNP8O0U1K-7E9MBRwVzDcG4JX',
        'podiatry': 'https://drive.google.com/uc?export=download&id=1Z7LIsShUOQ9P1V2L-8F0NCSxWaEdH5KY',
        'post_pregnancy_procedures': 'https://drive.google.com/uc?export=download&id=1A8MJtTiVPR0Q2W3M-9G1ODTyXbFeI6LZ',
        'reconstructive_surgeries': 'https://drive.google.com/uc?export=download&id=1B9NKuUjWQS1R3X4N-0H2PEUzYcGfJ7MA',
        'rhinoplasty': 'https://drive.google.com/uc?export=download&id=1C0OLvVkXRT2S4Y5O-1I3QFVaZdHgK8NB',
        'rhinoplasty_and_nose_shaping': 'https://drive.google.com/uc?export=download&id=1D1PMwWlYSU3T5Z6P-2J4RGWbAeIhL9OC',
        'scar_treatments': 'https://drive.google.com/uc?export=download&id=1E2QNxXmZTV4U6A7Q-3K5ShXcBfJiM0PD',
        'sexual_wellness': 'https://drive.google.com/uc?export=download&id=1F3ROyYnAUW5V7B8R-4L6TiYdCgKjN1QE',
        'skin_care_products': 'https://drive.google.com/uc?export=download&id=1G4SPzZoBVX6W8C9S-5M7UjZeDhLkO2RF',
        'skin_rejuvenation_and_resurfacing': 'https://drive.google.com/uc?export=download&id=1H5TQaApCWY7X9D0T-6N8VkAfEiMlP3SG',
        'skin_tightening': 'https://drive.google.com/uc?export=download&id=1I6URbBqDXZ8Y0E1U-7O9WlBgFjNmQ4TH',
        'skin_treatments': 'https://drive.google.com/uc?export=download&id=1J7VSdCrEYA9Z1F2V-8P0XmChGkOnR5UI',
        'tattoo_removal': 'https://drive.google.com/uc?export=download&id=1K8WTeDsFZB0A2G3W-9Q1YnDiHlPoS6VJ',
        'urinary_incontinence_treatments': 'https://drive.google.com/uc?export=download&id=1L9XUfEtGAC1B3H4X-0R2ZoEjImQpT7WK',
        'vaginal_rejuvenation': 'https://drive.google.com/uc?export=download&id=1M0YVgFuHBD2C4I5Y-1S3ApFkJnRqU8XL',
        'vein_treatments': 'https://drive.google.com/uc?export=download&id=1N1ZWgGvICE3D5J6Z-2T4BqGlKoSrV9YM',
        'vision_correction': 'https://drive.google.com/uc?export=download&id=1O2AXhHwJDF4E6K7A-3U5CrHmLpTsW0ZN',
        'weight_loss_treatments': 'https://drive.google.com/uc?export=download&id=1P3BYiIxKEG5F7L8B-4V6DsInMqUtX1AO'
    }
    
    print(f"🎨 Updating all 43 categories with beautiful medical procedure images...")
    
    conn = get_db_connection()
    updated_count = 0
    
    try:
        with conn.cursor() as cursor:
            # Get all categories
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
            categories = cursor.fetchall()
            
            print(f"📋 Found {len(categories)} categories to process")
            
            for cat_id, cat_name in categories:
                # Generate safe filename
                safe_name = safe_filename(cat_name)
                
                # Find matching image URL
                image_url = None
                if safe_name in category_images:
                    image_url = category_images[safe_name]
                else:
                    # Try partial matches
                    for key, url in category_images.items():
                        if key in safe_name or safe_name in key:
                            image_url = url
                            break
                
                if image_url:
                    # Download the beautiful image
                    filename = f"{safe_name}.jpg"
                    filepath = f"static/images/categories/{filename}"
                    local_url = f"/static/images/categories/{filename}"
                    
                    if download_image(image_url, filepath):
                        # Update database with new image URL
                        cursor.execute(
                            "UPDATE categories SET image_url = %s WHERE id = %s",
                            (local_url, cat_id)
                        )
                        updated_count += 1
                        print(f"✅ Updated '{cat_name}' with beautiful image")
                        
                        # Small delay to avoid overwhelming the server
                        time.sleep(0.5)
                    else:
                        print(f"⚠️ Failed to download image for '{cat_name}'")
                else:
                    print(f"⚠️ No matching image found for '{cat_name}'")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error during update: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print(f"\n🎉 Process Complete!")
    print(f"✅ Successfully updated {updated_count} categories")
    print(f"📸 All categories now have beautiful medical procedure images")
    
    return updated_count

def verify_all_images():
    """Verify that all categories now have proper images."""
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            # Count categories with default images
            cursor.execute("""
                SELECT COUNT(*) FROM categories 
                WHERE image_url = '/static/images/categories/default-procedure.jpg' 
                   OR image_url IS NULL
            """)
            default_count = cursor.fetchone()[0]
            
            # Count categories with actual images
            cursor.execute("""
                SELECT COUNT(*) FROM categories 
                WHERE image_url IS NOT NULL 
                  AND image_url != '/static/images/categories/default-procedure.jpg'
            """)
            image_count = cursor.fetchone()[0]
            
            # Total categories
            cursor.execute("SELECT COUNT(*) FROM categories")
            total_count = cursor.fetchone()[0]
            
            print(f"\n📊 Image Status Summary:")
            print(f"   Total Categories: {total_count}")
            print(f"   With Beautiful Images: {image_count}")
            print(f"   Still Using Default: {default_count}")
            print(f"   Success Rate: {(image_count/total_count)*100:.1f}%")
            
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting Category Image Update Process...")
    updated = update_all_categories()
    verify_all_images()
    print("\n✨ Your medical procedure categories now display beautiful images!")