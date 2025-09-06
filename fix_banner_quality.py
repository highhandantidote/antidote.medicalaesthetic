#!/usr/bin/env python3
"""
Fix banner quality by using original PNG files directly
"""

import os
import shutil

def fix_banner_quality():
    """Copy original PNG files to replace compressed versions"""
    
    # Source PNG file (highest quality)
    source_png = "static/uploads/banners/20250714081643_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.png"
    
    # Target paths - replace WebP with PNG
    desktop_target = "static/uploads/banners/hero-banner-optimized.png"
    mobile_target = "static/uploads/banners/hero-banner-mobile-optimized.png"
    
    if os.path.exists(source_png):
        # Copy original PNG for desktop (no compression)
        shutil.copy2(source_png, desktop_target)
        
        # Copy original PNG for mobile too (same quality)
        shutil.copy2(source_png, mobile_target)
        
        print("Original PNG files copied with no quality loss:")
        print(f"  Desktop: {desktop_target}")
        print(f"  Mobile: {mobile_target}")
        
        # Show file sizes
        original_size = os.path.getsize(source_png)
        print(f"  File size: {original_size:,} bytes ({original_size/1024:.1f} KB)")
        
        return True
    else:
        print("Original PNG file not found")
        return False

if __name__ == "__main__":
    fix_banner_quality()