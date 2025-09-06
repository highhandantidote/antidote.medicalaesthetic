
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
