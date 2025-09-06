"""
Category Image Optimization System
Optimizes category section images for better performance
"""

import os
import sys
from PIL import Image
import requests
from io import BytesIO

class CategoryImageOptimizer:
    """Optimizes category images for better performance"""
    
    def __init__(self):
        self.static_dir = "static"
        self.images_dir = os.path.join(self.static_dir, "images", "categories")
        self.optimized_dir = os.path.join(self.static_dir, "images", "categories", "optimized")
        
        # Create optimized directory if it doesn't exist
        os.makedirs(self.optimized_dir, exist_ok=True)
        
        # Target size for category images (displayed at 90x79)
        self.target_size = (180, 158)  # 2x for retina displays
        self.webp_quality = 85
        self.jpeg_quality = 85
    
    def optimize_image(self, image_path, output_name):
        """Optimize a single image"""
        try:
            print(f"Optimizing {image_path}...")
            
            # Open and process the image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Get original size
                original_size = os.path.getsize(image_path)
                original_dimensions = img.size
                
                # Resize to target size
                img_resized = img.resize(self.target_size, Image.LANCZOS)
                
                # Save optimized JPEG
                jpeg_path = os.path.join(self.optimized_dir, f"{output_name}.jpg")
                img_resized.save(jpeg_path, "JPEG", quality=self.jpeg_quality, optimize=True)
                
                # Save WebP version
                webp_path = os.path.join(self.optimized_dir, f"{output_name}.webp")
                img_resized.save(webp_path, "WebP", quality=self.webp_quality, optimize=True)
                
                # Get optimized sizes
                jpeg_size = os.path.getsize(jpeg_path)
                webp_size = os.path.getsize(webp_path)
                
                print(f"  Original: {original_size:,} bytes ({original_dimensions[0]}x{original_dimensions[1]})")
                print(f"  JPEG: {jpeg_size:,} bytes ({self.target_size[0]}x{self.target_size[1]}) - {((original_size - jpeg_size) / original_size * 100):.1f}% smaller")
                print(f"  WebP: {webp_size:,} bytes ({self.target_size[0]}x{self.target_size[1]}) - {((original_size - webp_size) / original_size * 100):.1f}% smaller")
                
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
    
    def optimize_all_category_images(self):
        """Optimize all category images"""
        print("🖼️ Starting category image optimization...")
        
        # List of category images to optimize
        category_images = [
            ("rhinoplasty_and_nose_shaping.jpg", "rhinoplasty_and_nose_shaping"),
            ("eyelid_surgery.jpg", "eyelid_surgery"),
            ("fillers_and_other_injectables.jpg", "fillers_and_other_injectables"),
            ("face_and_neck_lifts.jpg", "face_and_neck_lifts"),
            ("facial_rejuvenation.jpg", "facial_rejuvenation"),
            ("eyelid_enhancement.jpg", "eyelid_enhancement"),
        ]
        
        total_original_size = 0
        total_optimized_size = 0
        optimized_count = 0
        
        for image_filename, output_name in category_images:
            image_path = os.path.join(self.images_dir, image_filename)
            
            if os.path.exists(image_path):
                result = self.optimize_image(image_path, output_name)
                if result:
                    total_original_size += result['original_size']
                    total_optimized_size += result['webp_size']  # Use WebP for calculations
                    optimized_count += 1
            else:
                print(f"⚠️ Image not found: {image_path}")
        
        if optimized_count > 0:
            savings = total_original_size - total_optimized_size
            savings_percent = (savings / total_original_size * 100)
            
            print(f"\n📊 Optimization Summary:")
            print(f"  Images optimized: {optimized_count}")
            print(f"  Total original size: {total_original_size:,} bytes")
            print(f"  Total optimized size: {total_optimized_size:,} bytes")
            print(f"  Total savings: {savings:,} bytes ({savings_percent:.1f}%)")
            print(f"  Optimized images saved to: {self.optimized_dir}")
        
        return optimized_count > 0
    
    def create_responsive_css(self):
        """Create CSS for responsive optimized images"""
        css_content = """
/* Optimized Category Images */
.category-image-optimized {
    width: 90px;
    height: 79px;
    object-fit: cover;
    border-radius: 12px;
}

/* WebP support with JPEG fallback */
.category-card .category-image {
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    width: 90px;
    height: 79px;
    border-radius: 12px;
    display: block;
}

/* Responsive image loading */
@media (max-width: 768px) {
    .category-image-optimized {
        width: 75px;
        height: 66px;
    }
    .category-card .category-image {
        width: 75px;
        height: 66px;
    }
}
"""
        
        css_path = os.path.join(self.static_dir, "css", "category-image-optimization.css")
        with open(css_path, "w") as f:
            f.write(css_content)
        
        print(f"✅ Created responsive CSS: {css_path}")
        return css_path

def main():
    """Main execution function"""
    optimizer = CategoryImageOptimizer()
    
    # Optimize all category images
    success = optimizer.optimize_all_category_images()
    
    if success:
        # Create responsive CSS
        optimizer.create_responsive_css()
        print("\n🎯 Category image optimization completed successfully!")
        print("\nNext steps:")
        print("1. Update templates to use optimized images")
        print("2. Add WebP support with JPEG fallback")
        print("3. Include the new CSS file in templates")
    else:
        print("\n❌ No images were optimized")

if __name__ == "__main__":
    main()