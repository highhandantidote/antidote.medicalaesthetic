#!/usr/bin/env python3
"""
Maximum quality banner optimizer - preserves original quality as much as possible
"""

import os
from PIL import Image

def create_maximum_quality_banners():
    """Create maximum quality WebP versions"""
    
    # Try to find the highest quality source (PNG first, then WebP)
    source_candidates = [
        "static/uploads/banners/20250714081643_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.png",
        "static/uploads/banners/20250709092520_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.png",
        "static/uploads/banners/20250714081643_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.webp"
    ]
    
    source_banner = None
    for candidate in source_candidates:
        if os.path.exists(candidate):
            source_banner = candidate
            break
    
    if not source_banner:
        print("No source banner found")
        return
    
    # Target paths
    desktop_target = "static/uploads/banners/hero-banner-optimized.webp"
    mobile_target = "static/uploads/banners/hero-banner-mobile-optimized.webp"
    
    print(f"Using source: {source_banner}")
    
    try:
        with Image.open(source_banner) as img:
            print(f"Source image: {img.size[0]}x{img.size[1]} pixels, mode: {img.mode}")
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Desktop version - maximum quality (near-lossless)
            desktop_img = img.copy()
            desktop_img.save(desktop_target, 'WEBP', quality=100, optimize=True, method=6, lossless=True)
            
            # Mobile version - very high quality
            mobile_img = img.resize((1200, int(1200 * img.size[1] / img.size[0])), Image.Resampling.LANCZOS)
            mobile_img.save(mobile_target, 'WEBP', quality=100, optimize=True, method=6, lossless=True)
            
            # Get file sizes
            desktop_size = os.path.getsize(desktop_target)
            mobile_size = os.path.getsize(mobile_target)
            original_size = os.path.getsize(source_banner)
            
            print(f"Maximum quality banners created:")
            print(f"  Desktop: {desktop_size:,} bytes ({desktop_size/1024:.1f} KB)")
            print(f"  Mobile: {mobile_size:,} bytes ({mobile_size/1024:.1f} KB)")
            print(f"  Original: {original_size:,} bytes ({original_size/1024:.1f} KB)")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_maximum_quality_banners()