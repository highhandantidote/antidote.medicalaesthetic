#!/usr/bin/env python3
"""
Create a default medical procedure image for categories without specific images.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_default_medical_image():
    """Create a default medical procedure image."""
    # Create a 300x200 image with medical theme
    width, height = 300, 200
    img = Image.new('RGB', (width, height), color='#f8f9fa')
    draw = ImageDraw.Draw(img)
    
    # Draw a medical cross
    cross_color = '#007bff'
    cross_size = 60
    center_x, center_y = width // 2, height // 2
    
    # Horizontal bar
    draw.rectangle([
        center_x - cross_size//2, center_y - cross_size//6,
        center_x + cross_size//2, center_y + cross_size//6
    ], fill=cross_color)
    
    # Vertical bar
    draw.rectangle([
        center_x - cross_size//6, center_y - cross_size//2,
        center_x + cross_size//6, center_y + cross_size//2
    ], fill=cross_color)
    
    # Add subtle border
    draw.rectangle([0, 0, width-1, height-1], outline='#dee2e6', width=2)
    
    # Save the image
    os.makedirs('static/images/categories', exist_ok=True)
    img.save('static/images/categories/default-procedure.jpg', 'JPEG', quality=85)
    print("✅ Created default medical procedure image")

if __name__ == "__main__":
    create_default_medical_image()