#!/usr/bin/env python3
"""
Mobile Optimization System
Implements comprehensive mobile performance improvements
"""

import os
import subprocess
from PIL import Image
import shutil
from pathlib import Path

class MobileOptimizationSystem:
    def __init__(self):
        self.banner_dir = Path("static/uploads/banners")
        self.images_dir = Path("static/images")
        self.optimized_dir = Path("static/images/optimized")
        self.mobile_optimized_dir = Path("static/images/mobile-optimized")
        
        # Create directories
        self.optimized_dir.mkdir(exist_ok=True)
        self.mobile_optimized_dir.mkdir(exist_ok=True)

    def optimize_banner_image(self, original_path, output_path_webp, mobile_output_path_webp):
        """Convert banner PNG to WebP with desktop and mobile versions"""
        try:
            with Image.open(original_path) as img:
                # Desktop version (maintain quality but reduce size)
                desktop_img = img.copy()
                desktop_img.save(output_path_webp, 'WebP', quality=85, optimize=True)
                
                # Mobile version (smaller dimensions and more aggressive compression)
                mobile_img = img.copy()
                # Resize for mobile (max width 800px)
                if mobile_img.width > 800:
                    ratio = 800 / mobile_img.width
                    new_height = int(mobile_img.height * ratio)
                    mobile_img = mobile_img.resize((800, new_height), Image.Resampling.LANCZOS)
                
                mobile_img.save(mobile_output_path_webp, 'WebP', quality=75, optimize=True)
                
                # Get file sizes
                original_size = os.path.getsize(original_path)
                desktop_size = os.path.getsize(output_path_webp)
                mobile_size = os.path.getsize(mobile_output_path_webp)
                
                return {
                    'original_size': original_size,
                    'desktop_size': desktop_size,
                    'mobile_size': mobile_size,
                    'desktop_savings': ((original_size - desktop_size) / original_size) * 100,
                    'mobile_savings': ((original_size - mobile_size) / original_size) * 100
                }
        except Exception as e:
            print(f"Error optimizing {original_path}: {e}")
            return None

    def optimize_hero_image(self):
        """Optimize hero bottom image for mobile"""
        hero_path = self.images_dir / "hero_bottom_image.jpg"
        if hero_path.exists():
            desktop_output = self.optimized_dir / "hero_bottom_image_desktop.webp"
            mobile_output = self.mobile_optimized_dir / "hero_bottom_image_mobile.webp"
            
            with Image.open(hero_path) as img:
                # Desktop version
                img.save(desktop_output, 'WebP', quality=85, optimize=True)
                
                # Mobile version (smaller and more compressed)
                mobile_img = img.copy()
                if mobile_img.width > 600:
                    ratio = 600 / mobile_img.width
                    new_height = int(mobile_img.height * ratio)
                    mobile_img = mobile_img.resize((600, new_height), Image.Resampling.LANCZOS)
                
                mobile_img.save(mobile_output, 'WebP', quality=70, optimize=True)
                
                return {
                    'original_size': os.path.getsize(hero_path),
                    'desktop_size': os.path.getsize(desktop_output),
                    'mobile_size': os.path.getsize(mobile_output)
                }
        return None

    def optimize_main_banner(self):
        """Optimize the main 624KB banner"""
        banner_path = self.banner_dir / "20250714081643_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.png"
        
        if banner_path.exists():
            desktop_output = self.optimized_dir / "main_banner_desktop.webp"
            mobile_output = self.mobile_optimized_dir / "main_banner_mobile.webp"
            
            result = self.optimize_banner_image(banner_path, desktop_output, mobile_output)
            if result:
                print(f"✅ Main Banner Optimization Complete:")
                print(f"   Original: {result['original_size'] / 1024:.1f}KB")
                print(f"   Desktop WebP: {result['desktop_size'] / 1024:.1f}KB ({result['desktop_savings']:.1f}% savings)")
                print(f"   Mobile WebP: {result['mobile_size'] / 1024:.1f}KB ({result['mobile_savings']:.1f}% savings)")
                
                return {
                    'desktop_path': desktop_output,
                    'mobile_path': mobile_output,
                    'stats': result
                }
        return None

    def create_responsive_image_helper(self):
        """Create a helper function for responsive images"""
        helper_code = '''
def get_responsive_image_url(image_path, is_mobile=False):
    """
    Returns appropriate image URL based on device type
    """
    from flask import request
    
    # Check if it's a mobile device
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile_device = any(mobile in user_agent for mobile in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])
    
    # Check if mobile-optimized version exists
    if is_mobile_device or is_mobile:
        mobile_path = image_path.replace('/static/images/', '/static/images/mobile-optimized/')
        mobile_path = mobile_path.replace('/static/uploads/', '/static/uploads/mobile-optimized/')
        mobile_path = mobile_path.rsplit('.', 1)[0] + '.webp'
        
        # Check if file exists
        if os.path.exists(mobile_path.replace('/static/', 'static/')):
            return mobile_path
    
    # Return desktop optimized version
    desktop_path = image_path.replace('/static/images/', '/static/images/optimized/')
    desktop_path = desktop_path.replace('/static/uploads/', '/static/uploads/optimized/')
    desktop_path = desktop_path.rsplit('.', 1)[0] + '.webp'
    
    if os.path.exists(desktop_path.replace('/static/', 'static/')):
        return desktop_path
    
    return image_path  # Fallback to original
'''
        
        with open('utils/responsive_images.py', 'w') as f:
            f.write(helper_code)
        
        return helper_code

if __name__ == "__main__":
    optimizer = MobileOptimizationSystem()
    
    print("🚀 Starting Mobile Optimization System...")
    print("=" * 50)
    
    # Optimize main banner
    banner_result = optimizer.optimize_main_banner()
    
    # Optimize hero image
    hero_result = optimizer.optimize_hero_image()
    if hero_result:
        print(f"✅ Hero Image Optimization Complete:")
        print(f"   Original: {hero_result['original_size'] / 1024:.1f}KB")
        print(f"   Desktop WebP: {hero_result['desktop_size'] / 1024:.1f}KB")
        print(f"   Mobile WebP: {hero_result['mobile_size'] / 1024:.1f}KB")
    
    # Create responsive image helper
    optimizer.create_responsive_image_helper()
    print("✅ Responsive image helper created")
    
    print("=" * 50)
    print("🎯 Mobile Optimization Phase 1 Complete!")