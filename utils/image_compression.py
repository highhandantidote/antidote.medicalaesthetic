#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Compression Utility

This module provides server-side image compression capabilities
to handle large image uploads for face analysis.
"""

import os
import logging
from PIL import Image, ImageOps
from typing import Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

def compress_image(input_path: str, output_path: str = None, max_width: int = 1200, 
                  quality: int = 85, max_file_size_mb: int = 5) -> str:
    """
    Compress an image file to reduce its size while maintaining quality.
    
    Args:
        input_path: Path to the input image
        output_path: Path for the compressed output (optional)
        max_width: Maximum width for the compressed image
        quality: JPEG quality (1-100)
        max_file_size_mb: Maximum file size in MB
        
    Returns:
        Path to the compressed image
    """
    try:
        # Generate output path if not provided
        if not output_path:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_compressed{ext}"
        
        # Open and process the image
        with Image.open(input_path) as image:
            # Convert to RGB if necessary (for JPEG compatibility)
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Auto-orient the image based on EXIF data
            image = ImageOps.exif_transpose(image)
            
            # Calculate new dimensions while maintaining aspect ratio
            original_width, original_height = image.size
            if original_width > max_width:
                new_width = max_width
                new_height = int((original_height * max_width) / original_width)
            else:
                new_width, new_height = original_width, original_height
            
            # Resize the image
            if (new_width, new_height) != (original_width, original_height):
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {original_width}x{original_height} to {new_width}x{new_height}")
            
            # Save with compression
            save_kwargs = {
                'format': 'JPEG',
                'quality': quality,
                'optimize': True,
                'progressive': True
            }
            
            # Try different quality levels if file is still too large
            max_file_size_bytes = max_file_size_mb * 1024 * 1024
            current_quality = quality
            
            while current_quality > 20:  # Don't go below 20% quality
                image.save(output_path, **save_kwargs)
                
                # Check file size
                file_size = os.path.getsize(output_path)
                if file_size <= max_file_size_bytes:
                    logger.info(f"Compressed image saved: {output_path} ({file_size/1024/1024:.1f}MB, quality: {current_quality})")
                    return output_path
                
                # Reduce quality and try again
                current_quality -= 10
                save_kwargs['quality'] = current_quality
            
            # If still too large, try reducing dimensions further
            if os.path.getsize(output_path) > max_file_size_bytes:
                max_width = int(max_width * 0.8)  # Reduce by 20%
                if max_width > 400:  # Don't go below 400px width
                    logger.warning(f"File still too large, reducing width to {max_width}")
                    return compress_image(input_path, output_path, max_width, 75, max_file_size_mb)
            
            return output_path
            
    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        return input_path  # Return original path if compression fails

def get_image_info(image_path: str) -> Tuple[int, int, float]:
    """
    Get basic information about an image file.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (width, height, file_size_mb)
    """
    try:
        with Image.open(image_path) as image:
            width, height = image.size
            file_size = os.path.getsize(image_path)
            file_size_mb = file_size / (1024 * 1024)
            return width, height, file_size_mb
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        return 0, 0, 0.0

def optimize_face_analysis_image(input_path: str) -> str:
    """
    Optimize an image specifically for face analysis.
    
    Args:
        input_path: Path to the input image
        
    Returns:
        Path to the optimized image
    """
    try:
        # Check current image info
        width, height, file_size_mb = get_image_info(input_path)
        logger.info(f"Original image: {width}x{height}, {file_size_mb:.1f}MB")
        
        # If image is already small enough, return as-is
        if file_size_mb <= 3 and width <= 1200:
            logger.info("Image already optimized")
            return input_path
        
        # Compress for face analysis (higher quality for facial features)
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_optimized{ext}"
        
        # Use higher quality but smaller dimensions for face analysis
        compressed_path = compress_image(
            input_path=input_path,
            output_path=output_path,
            max_width=1000,  # Good resolution for face analysis
            quality=90,      # High quality for facial features
            max_file_size_mb=3  # Keep under 3MB
        )
        
        # Log the optimization results
        opt_width, opt_height, opt_size_mb = get_image_info(compressed_path)
        logger.info(f"Optimized image: {opt_width}x{opt_height}, {opt_size_mb:.1f}MB")
        
        return compressed_path
        
    except Exception as e:
        logger.error(f"Error optimizing image for face analysis: {e}")
        return input_path


# Test function for development
if __name__ == "__main__":
    test_image = "static/uploads/face_analysis/test_image.jpg"
    if os.path.exists(test_image):
        optimized = optimize_face_analysis_image(test_image)
        print(f"Optimized image: {optimized}")
    else:
        print(f"Test image not found: {test_image}")