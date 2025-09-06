#!/usr/bin/env python3
"""
Create optimized WebP banners for performance optimization
"""

import os
import sys
from PIL import Image
import shutil

def create_optimized_banners():
    """Create optimized WebP versions of existing banners"""
    
    # Source banner file (from the database path)
    source_banner = "static/uploads/banners/20250714081643_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.webp"
    
    # Target paths
    desktop_target = "static/uploads/banners/hero-banner-optimized.webp"
    mobile_target = "static/uploads/banners/hero-banner-mobile-optimized.webp"
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(desktop_target), exist_ok=True)
    
    if not os.path.exists(source_banner):
        print(f"Source banner not found: {source_banner}")
        # Create a fallback banner
        create_fallback_banner(desktop_target, mobile_target)
        return
    
    try:
        # Load the source image
        with Image.open(source_banner) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Desktop version (high quality, lossless optimization)
            desktop_img = img.copy()
            desktop_img.save(desktop_target, 'WEBP', quality=95, optimize=True, method=6)
            
            # Mobile version (high quality but smaller dimensions)
            mobile_img = img.resize((1200, 600), Image.Resampling.LANCZOS)
            mobile_img.save(mobile_target, 'WEBP', quality=90, optimize=True, method=6)
            
            print(f"Created optimized banners:")
            print(f"  Desktop: {desktop_target} ({os.path.getsize(desktop_target)} bytes)")
            print(f"  Mobile: {mobile_target} ({os.path.getsize(mobile_target)} bytes)")
            
    except Exception as e:
        print(f"Error creating optimized banners: {e}")
        create_fallback_banner(desktop_target, mobile_target)

def create_fallback_banner(desktop_target, mobile_target):
    """Create a simple fallback banner"""
    print("Creating fallback banner...")
    
    # Create a simple gradient banner
    desktop_img = Image.new('RGB', (1920, 600), color='#00A0B0')
    mobile_img = Image.new('RGB', (800, 400), color='#00A0B0')
    
    # Save as WebP
    desktop_img.save(desktop_target, 'WEBP', quality=85, optimize=True)
    mobile_img.save(mobile_target, 'WEBP', quality=75, optimize=True)
    
    print(f"Created fallback banners:")
    print(f"  Desktop: {desktop_target}")
    print(f"  Mobile: {mobile_target}")

if __name__ == "__main__":
    create_optimized_banners()