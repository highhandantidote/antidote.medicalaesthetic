
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
