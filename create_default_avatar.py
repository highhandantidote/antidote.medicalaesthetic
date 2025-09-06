#!/usr/bin/env python3
"""
Create a default doctor avatar image.

This script creates a simple default doctor avatar image 
that will be used when a doctor's profile image is not available.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_AVATAR_PATH = "static/images/default-doctor-avatar.png"

def create_default_avatar():
    """Create a simple default avatar image."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(DEFAULT_AVATAR_PATH), exist_ok=True)
        
        # Create a 200x200 blue image
        img = Image.new('RGB', (200, 200), color=(0, 100, 190))
        draw = ImageDraw.Draw(img)
        
        # Draw a circle for the doctor icon
        draw.ellipse((50, 50, 150, 150), fill=(255, 255, 255))
        
        # Draw a simplified doctor silhouette
        draw.rectangle((85, 70, 115, 110), fill=(0, 100, 190))  # head
        draw.rectangle((75, 110, 125, 160), fill=(0, 100, 190))  # body
        
        # Save the image
        img.save(DEFAULT_AVATAR_PATH)
        logger.info(f"Default avatar created successfully: {DEFAULT_AVATAR_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error creating default avatar: {str(e)}")
        return False

if __name__ == "__main__":
    create_default_avatar()