#!/usr/bin/env python3
"""
Advanced solution for doctor profile images with built-in verification and SVG fallback.

This script implements a comprehensive approach to fixing doctor profile images:
1. Creates a local SVG image for each doctor using their initials and name
2. Downloads high-quality images and stores them locally with proper verification
3. Updates doctor profiles to use these verified images
"""

import os
import csv
import json
import logging
import requests
import random
import time
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import urlparse
import psycopg2
import re

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to CSV file
DOCTORS_CSV = "attached_assets/new_doctors_profiles2 - Sheet1.csv"
IMAGE_DIR = "static/images/doctors"
AVATAR_DIR = "static/images/avatars"

# Color palette for SVG backgrounds
COLORS = [
    "#4285F4",  # Google Blue
    "#34A853",  # Google Green
    "#FBBC05",  # Google Yellow
    "#EA4335",  # Google Red
    "#5C2D91",  # Purple
    "#0078D7",  # Blue
    "#008272",  # Teal
    "#107C10",  # Green
]

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def get_initials(name):
    """Extract initials from a name."""
    words = re.findall(r'\b\w', name)
    return ''.join(words[:2]).upper()

def create_svg_avatar(name, size=200):
    """Create an SVG avatar with initials for the doctor."""
    initials = get_initials(name)
    color = random.choice(COLORS)
    
    svg = f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
    <rect width="{size}" height="{size}" fill="{color}"/>
    <text x="{size//2}" y="{size//2}" font-family="Arial, sans-serif" font-size="{size//3}" 
          font-weight="bold" fill="white" text-anchor="middle" dominant-baseline="middle">
        {initials}
    </text>
    <text x="{size//2}" y="{size*3//4}" font-family="Arial, sans-serif" font-size="{size//10}" 
          fill="white" text-anchor="middle" dominant-baseline="middle">
        Dr. {name.split()[-1]}
    </text>
</svg>"""
    
    return svg

def save_svg_avatar(name, doctor_id):
    """Save an SVG avatar for a doctor."""
    # Create directory if needed
    os.makedirs(AVATAR_DIR, exist_ok=True)
    
    # Create SVG content
    svg_content = create_svg_avatar(name)
    
    # Create a safe filename
    safe_name = ''.join(c if c.isalnum() else '_' for c in name)
    filename = f"avatar_{doctor_id}_{safe_name}.svg"
    filepath = os.path.join(AVATAR_DIR, filename)
    
    # Save the SVG
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    return f"/{filepath}"

def download_and_verify_image(image_url, doctor_id, doctor_name):
    """Download, verify, and save a doctor's profile image."""
    if not image_url or not image_url.strip():
        logger.warning(f"No image URL provided for {doctor_name}")
        return None
    
    image_url = image_url.strip()
    
    # Create directories if needed
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    # Generate a safe filename
    parsed_url = urlparse(image_url)
    path = parsed_url.path
    
    # Get file extension from URL or default to .jpg
    ext = os.path.splitext(path)[1].lower()
    if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        ext = '.jpg'
    
    safe_name = ''.join(c if c.isalnum() else '_' for c in doctor_name)
    filename = f"verified_{doctor_id}_{safe_name}{ext}"
    filepath = os.path.join(IMAGE_DIR, filename)
    
    # Try different methods to download the image
    for attempt in range(3):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }
            
            # Add random query param to bypass caching
            if '?' in image_url:
                download_url = f"{image_url}&nocache={random.randint(1, 100000)}"
            else:
                download_url = f"{image_url}?nocache={random.randint(1, 100000)}"
            
            response = requests.get(download_url, headers=headers, timeout=10, stream=True)
            
            if response.status_code == 200:
                # Verify it's actually an image by trying to open it with PIL
                try:
                    img = Image.open(io.BytesIO(response.content))
                    img.verify()  # Verify the image
                    
                    # Save the verified image
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"Successfully downloaded and verified image for {doctor_name}: {filepath}")
                    return f"/{filepath}"
                except Exception as img_err:
                    logger.warning(f"Downloaded file for {doctor_name} is not a valid image: {str(img_err)}")
            else:
                logger.warning(f"Failed to download image for {doctor_name}: HTTP {response.status_code}")
        
        except Exception as e:
            logger.warning(f"Error downloading image for {doctor_name} (attempt {attempt+1}): {str(e)}")
        
        # Wait before retrying
        time.sleep(1)
    
    # If we get here, all attempts failed
    logger.error(f"All download attempts failed for {doctor_name}")
    return None

def create_data_uri_from_url(image_url):
    """Create a data URI from an image URL."""
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            encoded = base64.b64encode(response.content).decode('utf-8')
            return f"data:{content_type};base64,{encoded}"
        return None
    except Exception as e:
        logger.error(f"Error creating data URI: {str(e)}")
        return None

def fix_all_doctor_images():
    """Fix doctor profile images with a comprehensive approach."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # Load doctors from CSV
        doctors_from_csv = {}
        try:
            with open(DOCTORS_CSV, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    name = row.get('Doctor Name', '').strip()
                    image_url = row.get('Profile Image', '').strip()
                    if name:
                        doctors_from_csv[name] = image_url
        except Exception as e:
            logger.error(f"Error reading CSV: {str(e)}")
            return False
        
        logger.info(f"Loaded {len(doctors_from_csv)} doctors from CSV")
        
        # Get all doctors from database
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM doctors")
            db_doctors = cur.fetchall()
        
        if not db_doctors:
            logger.warning("No doctors found in database")
            return False
        
        logger.info(f"Found {len(db_doctors)} doctors in database")
        
        # Process each doctor
        for doctor_id, doctor_name in db_doctors:
            # 1. Create a guaranteed SVG avatar
            svg_path = save_svg_avatar(doctor_name, doctor_id)
            logger.info(f"Created SVG avatar for {doctor_name}: {svg_path}")
            
            # 2. Try to find image URL in CSV
            image_url = None
            for csv_name, url in doctors_from_csv.items():
                if doctor_name.lower() == csv_name.lower() or doctor_name.lower() in csv_name.lower():
                    image_url = url
                    break
            
            # 3. Try different methods to get a working image
            final_image_path = svg_path  # Default to SVG
            
            # Method A: Try direct download and verification
            if image_url:
                downloaded_path = download_and_verify_image(image_url, doctor_id, doctor_name)
                if downloaded_path:
                    final_image_path = downloaded_path
                    logger.info(f"Using downloaded image for {doctor_name}")
                else:
                    # Method B: Try data URI if download fails
                    data_uri = create_data_uri_from_url(image_url)
                    if data_uri:
                        final_image_path = data_uri
                        logger.info(f"Using data URI for {doctor_name}")
                    else:
                        logger.info(f"Using SVG fallback for {doctor_name}")
            
            # 4. Update the doctor record
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE doctors 
                    SET profile_image = %s, 
                        image_url = %s
                    WHERE id = %s
                """, (final_image_path, image_url, doctor_id))
            
            conn.commit()
            logger.info(f"Updated profile image for {doctor_name}")
        
        return True
    except Exception as e:
        logger.error(f"Error in fix_all_doctor_images: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def ensure_image_fields_exist():
    """Ensure the image_url field exists in the doctors table."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        with conn.cursor() as cur:
            # Check if image_url field exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'doctors' AND column_name = 'image_url'
            """)
            
            if not cur.fetchone():
                # Add image_url field
                logger.info("Adding image_url field to doctors table")
                cur.execute("""
                    ALTER TABLE doctors 
                    ADD COLUMN image_url TEXT
                """)
                
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error ensuring image fields exist: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting advanced doctor image solution...")
    
    # Ensure needed fields exist
    if ensure_image_fields_exist():
        # Fix all doctor images
        if fix_all_doctor_images():
            logger.info("Doctor images fixed successfully with advanced approach")
        else:
            logger.error("Failed to fix doctor images")
    else:
        logger.error("Failed to ensure required database fields exist")