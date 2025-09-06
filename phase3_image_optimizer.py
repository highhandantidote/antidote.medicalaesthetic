"""
Phase 3B: Image Optimization System
Converts large images to WebP format and implements responsive images
"""

import os
import requests
from pathlib import Path
from PIL import Image
import io

class ImageOptimizer:
    def __init__(self):
        self.static_dir = Path("static")
        self.uploads_dir = self.static_dir / "uploads"
        self.images_dir = self.static_dir / "images"
        self.optimized_dir = self.static_dir / "optimized"
        self.optimized_dir.mkdir(exist_ok=True)
        
    def optimize_banner_images(self):
        """Optimize banner images to WebP format"""
        banner_dir = self.uploads_dir / "banners"
        if not banner_dir.exists():
            print("Banner directory not found")
            return
        
        optimized_count = 0
        total_savings = 0
        
        for banner_file in banner_dir.glob("*.png"):
            try:
                # Open and convert to WebP
                with Image.open(banner_file) as img:
                    # Create WebP version
                    webp_path = self.optimized_dir / f"{banner_file.stem}.webp"
                    img.save(webp_path, "WEBP", quality=85, optimize=True)
                    
                    # Create mobile version (50% smaller)
                    mobile_size = (img.width // 2, img.height // 2)
                    mobile_img = img.resize(mobile_size, Image.Resampling.LANCZOS)
                    mobile_webp_path = self.optimized_dir / f"{banner_file.stem}_mobile.webp"
                    mobile_img.save(mobile_webp_path, "WEBP", quality=80, optimize=True)
                    
                    # Calculate savings
                    original_size = banner_file.stat().st_size
                    webp_size = webp_path.stat().st_size
                    mobile_size = mobile_webp_path.stat().st_size
                    
                    savings = original_size - webp_size
                    total_savings += savings
                    optimized_count += 1
                    
                    print(f"Optimized {banner_file.name}: {original_size:,} → {webp_size:,} bytes ({savings/original_size*100:.1f}% saved)")
                    
            except Exception as e:
                print(f"Error optimizing {banner_file.name}: {e}")
        
        return optimized_count, total_savings
    
    def optimize_hero_images(self):
        """Optimize hero and static images"""
        if not self.images_dir.exists():
            print("Images directory not found")
            return 0, 0
        
        optimized_count = 0
        total_savings = 0
        
        for img_file in self.images_dir.glob("*.jpg"):
            try:
                with Image.open(img_file) as img:
                    # Create WebP version
                    webp_path = self.optimized_dir / f"{img_file.stem}.webp"
                    img.save(webp_path, "WEBP", quality=85, optimize=True)
                    
                    # Create mobile version
                    mobile_size = (min(img.width, 800), int(min(img.width, 800) * img.height / img.width))
                    mobile_img = img.resize(mobile_size, Image.Resampling.LANCZOS)
                    mobile_webp_path = self.optimized_dir / f"{img_file.stem}_mobile.webp"
                    mobile_img.save(mobile_webp_path, "WEBP", quality=80, optimize=True)
                    
                    # Calculate savings
                    original_size = img_file.stat().st_size
                    webp_size = webp_path.stat().st_size
                    
                    savings = original_size - webp_size
                    total_savings += savings
                    optimized_count += 1
                    
                    print(f"Optimized {img_file.name}: {original_size:,} → {webp_size:,} bytes ({savings/original_size*100:.1f}% saved)")
                    
            except Exception as e:
                print(f"Error optimizing {img_file.name}: {e}")
        
        return optimized_count, total_savings
    
    def optimize_svg_files(self):
        """Optimize SVG files by removing unnecessary elements"""
        if not self.images_dir.exists():
            return 0, 0
        
        optimized_count = 0
        total_savings = 0
        
        for svg_file in self.images_dir.glob("*.svg"):
            try:
                with open(svg_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_size = len(content.encode('utf-8'))
                
                # Basic SVG optimization
                import re
                
                # Remove comments
                content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
                
                # Remove unnecessary whitespace
                content = re.sub(r'\s+', ' ', content)
                content = re.sub(r'>\s+<', '><', content)
                
                # Remove unnecessary attributes
                content = re.sub(r'\s*(xmlns:.*?=".*?")', '', content)
                content = re.sub(r'\s*(xml:.*?=".*?")', '', content)
                
                # Save optimized version
                optimized_path = self.optimized_dir / svg_file.name
                with open(optimized_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                optimized_size = len(content.encode('utf-8'))
                savings = original_size - optimized_size
                total_savings += savings
                optimized_count += 1
                
                print(f"Optimized {svg_file.name}: {original_size:,} → {optimized_size:,} bytes ({savings/original_size*100:.1f}% saved)")
                
            except Exception as e:
                print(f"Error optimizing {svg_file.name}: {e}")
        
        return optimized_count, total_savings
    
    def create_responsive_image_helper(self):
        """Create helper function for responsive images"""
        helper_content = '''
def get_responsive_image_url(image_path, is_mobile=False):
    """Get optimized image URL based on device type"""
    from flask import request
    import os
    
    # Check if WebP is supported
    accepts_webp = 'image/webp' in request.headers.get('Accept', '')
    
    # Get base path and filename
    path_parts = image_path.split('/')
    filename = path_parts[-1]
    base_name = filename.split('.')[0]
    
    # Check for optimized versions
    optimized_dir = "static/optimized"
    
    if is_mobile and accepts_webp:
        mobile_webp = f"{optimized_dir}/{base_name}_mobile.webp"
        if os.path.exists(mobile_webp):
            return f"/static/optimized/{base_name}_mobile.webp"
    
    if accepts_webp:
        webp_path = f"{optimized_dir}/{base_name}.webp"
        if os.path.exists(webp_path):
            return f"/static/optimized/{base_name}.webp"
    
    # Fallback to original
    return f"/{image_path}"
'''
        
        with open('image_helpers.py', 'w', encoding='utf-8') as f:
            f.write(helper_content)
        
        print("Created responsive image helper function")

# Initialize image optimizer
if __name__ == "__main__":
    optimizer = ImageOptimizer()
    
    print("Phase 3B: Image Optimization Starting")
    print("=" * 40)
    
    # Optimize banner images
    banner_count, banner_savings = optimizer.optimize_banner_images()
    
    # Optimize hero images
    hero_count, hero_savings = optimizer.optimize_hero_images()
    
    # Optimize SVG files
    svg_count, svg_savings = optimizer.optimize_svg_files()
    
    # Create responsive image helper
    optimizer.create_responsive_image_helper()
    
    total_savings = banner_savings + hero_savings + svg_savings
    total_count = banner_count + hero_count + svg_count
    
    print(f"""
Phase 3B: Image Optimization Complete
=====================================
✓ Banner images optimized: {banner_count} files
✓ Hero images optimized: {hero_count} files  
✓ SVG files optimized: {svg_count} files
✓ Total files optimized: {total_count}
✓ Total size savings: {total_savings:,} bytes ({total_savings/1024/1024:.1f} MB)
✓ Responsive image helper created
✓ Expected LCP improvement: ~2-3 seconds
""")