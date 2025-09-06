#!/usr/bin/env python3
"""
Option to use original PNG banner with zero compression - maximum quality
"""

import os
import shutil

def use_original_png_banner():
    """Copy original PNG banner for zero quality loss"""
    
    # Source PNG file
    source_png = "static/uploads/banners/20250714081643_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.png"
    
    # Target paths
    desktop_target = "static/uploads/banners/hero-banner-optimized.webp"
    mobile_target = "static/uploads/banners/hero-banner-mobile-optimized.webp"
    
    if os.path.exists(source_png):
        # Copy original PNG as desktop version (rename to .webp for consistency)
        shutil.copy2(source_png, desktop_target.replace('.webp', '.png'))
        shutil.copy2(source_png, mobile_target.replace('.webp', '.png'))
        
        print("Original PNG files copied:")
        print(f"  Desktop: {desktop_target.replace('.webp', '.png')}")
        print(f"  Mobile: {mobile_target.replace('.webp', '.png')}")
        print(f"  Size: {os.path.getsize(source_png):,} bytes ({os.path.getsize(source_png)/1024:.1f} KB)")
        print("\nTo use original PNG quality, update the banner API to serve .png files instead of .webp")
    else:
        print("Original PNG file not found")

if __name__ == "__main__":
    use_original_png_banner()