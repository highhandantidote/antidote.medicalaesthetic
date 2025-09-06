#!/usr/bin/env python3
"""
High-quality banner optimizer that preserves maximum image quality
"""

import os
import sys
from PIL import Image
import shutil

def create_high_quality_banners():
    """Create high-quality WebP versions preserving maximum quality"""
    
    # Source banner file (from the database path)
    source_banner = "static/uploads/banners/20250714081643_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.webp"
    
    # Target paths
    desktop_target = "static/uploads/banners/hero-banner-optimized.webp"
    mobile_target = "static/uploads/banners/hero-banner-mobile-optimized.webp"
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(desktop_target), exist_ok=True)
    
    if not os.path.exists(source_banner):
        print(f"Source banner not found: {source_banner}")
        # Try alternative sources
        alternatives = [
            "static/uploads/banners/20250714081643_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.png",
            "static/uploads/banners/20250709092520_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.png"
        ]
        
        for alt in alternatives:
            if os.path.exists(alt):
                source_banner = alt
                print(f"Using alternative source: {source_banner}")
                break
        else:
            print("No source banner found")
            return
    
    try:
        # Load the source image
        with Image.open(source_banner) as img:
            print(f"Source image: {img.size[0]}x{img.size[1]} pixels")
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Desktop version - maximum quality preservation
            desktop_img = img.copy()
            desktop_img.save(desktop_target, 'WEBP', quality=98, optimize=True, method=6, lossless=False)
            
            # Mobile version - high quality with appropriate dimensions
            # Keep aspect ratio but optimize for mobile
            original_width, original_height = img.size
            aspect_ratio = original_width / original_height
            
            # Target mobile dimensions (maintaining aspect ratio)
            mobile_width = 1200
            mobile_height = int(mobile_width / aspect_ratio)
            
            mobile_img = img.resize((mobile_width, mobile_height), Image.Resampling.LANCZOS)
            mobile_img.save(mobile_target, 'WEBP', quality=95, optimize=True, method=6, lossless=False)
            
            # Get file sizes
            desktop_size = os.path.getsize(desktop_target)
            mobile_size = os.path.getsize(mobile_target)
            original_size = os.path.getsize(source_banner)
            
            print(f"High-quality banners created:")
            print(f"  Desktop: {desktop_target} ({desktop_size:,} bytes, {desktop_size/1024:.1f} KB)")
            print(f"  Mobile: {mobile_target} ({mobile_size:,} bytes, {mobile_size/1024:.1f} KB)")
            print(f"  Original: {source_banner} ({original_size:,} bytes, {original_size/1024:.1f} KB)")
            print(f"  Desktop reduction: {((original_size - desktop_size) / original_size * 100):.1f}%")
            print(f"  Mobile reduction: {((original_size - mobile_size) / original_size * 100):.1f}%")
            
    except Exception as e:
        print(f"Error creating high-quality banners: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_high_quality_banners()