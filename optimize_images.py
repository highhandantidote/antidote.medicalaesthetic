"""
Image Optimization System
Optimizes large images identified in PageSpeed Insights
"""

import os
import sys
from PIL import Image
import requests
from io import BytesIO

class ImageOptimizer:
    """Optimizes large images for better performance"""
    
    def __init__(self):
        self.static_dir = "static"
        self.optimized_dir = os.path.join(self.static_dir, "optimized")
        os.makedirs(self.optimized_dir, exist_ok=True)
        
        # Large images identified in PageSpeed Insights
        self.large_images = [
            {
                "path": "static/uploads/banners/20250714081643_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.png",
                "name": "hero_banner",
                "max_width": 1200,
                "quality": 85
            },
            {
                "path": "static/images/hero_bottom_image.jpg", 
                "name": "hero_bottom",
                "max_width": 800,
                "quality": 80
            },
            {
                "path": "static/images/antidote-logo-updated.svg",
                "name": "logo_updated",
                "max_width": 200,
                "quality": 90
            },
            {
                "path": "static/images/antidote-logo-original.svg",
                "name": "logo_original", 
                "max_width": 200,
                "quality": 90
            }
        ]
    
    def optimize_image(self, image_info):
        """Optimize a single image"""
        try:
            image_path = image_info["path"]
            if not os.path.exists(image_path):
                print(f"⚠️ Image not found: {image_path}")
                return None
            
            print(f"Optimizing {image_path}...")
            
            # Skip SVG files (they're already optimized)
            if image_path.endswith('.svg'):
                print(f"  Skipping SVG file: {image_path}")
                return None
            
            # Open and process the image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Get original size
                original_size = os.path.getsize(image_path)
                original_dimensions = img.size
                
                # Resize if too large
                max_width = image_info["max_width"]
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.LANCZOS)
                
                # Save optimized versions
                name = image_info["name"]
                quality = image_info["quality"]
                
                # Save optimized JPEG
                jpeg_path = os.path.join(self.optimized_dir, f"{name}.jpg")
                img.save(jpeg_path, "JPEG", quality=quality, optimize=True)
                
                # Save WebP version
                webp_path = os.path.join(self.optimized_dir, f"{name}.webp")
                img.save(webp_path, "WebP", quality=quality, optimize=True)
                
                # Get optimized sizes
                jpeg_size = os.path.getsize(jpeg_path)
                webp_size = os.path.getsize(webp_path)
                
                print(f"  Original: {original_size:,} bytes ({original_dimensions[0]}x{original_dimensions[1]})")
                print(f"  JPEG: {jpeg_size:,} bytes ({img.size[0]}x{img.size[1]}) - {((original_size - jpeg_size) / original_size * 100):.1f}% smaller")
                print(f"  WebP: {webp_size:,} bytes ({img.size[0]}x{img.size[1]}) - {((original_size - webp_size) / original_size * 100):.1f}% smaller")
                
                return {
                    'original_size': original_size,
                    'jpeg_size': jpeg_size,
                    'webp_size': webp_size,
                    'jpeg_path': jpeg_path,
                    'webp_path': webp_path
                }
                
        except Exception as e:
            print(f"Error optimizing {image_path}: {e}")
            return None
    
    def optimize_all_images(self):
        """Optimize all large images"""
        print("🖼️ Starting image optimization...")
        
        total_original_size = 0
        total_optimized_size = 0
        optimized_count = 0
        
        for image_info in self.large_images:
            result = self.optimize_image(image_info)
            if result:
                total_original_size += result['original_size']
                total_optimized_size += result['webp_size']  # Use WebP for calculations
                optimized_count += 1
        
        if optimized_count > 0:
            savings = total_original_size - total_optimized_size
            savings_percent = (savings / total_original_size * 100)
            
            print(f"\n📊 Image Optimization Summary:")
            print(f"  Images optimized: {optimized_count}")
            print(f"  Total original size: {total_original_size:,} bytes")
            print(f"  Total optimized size: {total_optimized_size:,} bytes")
            print(f"  Total savings: {savings:,} bytes ({savings_percent:.1f}%)")
            print(f"  Optimized images saved to: {self.optimized_dir}")
        
        return optimized_count > 0

def main():
    """Main execution function"""
    optimizer = ImageOptimizer()
    
    # Optimize all images
    success = optimizer.optimize_all_images()
    
    if success:
        print("\n🎯 Image optimization completed successfully!")
    else:
        print("\n❌ No images were optimized")

if __name__ == "__main__":
    main()