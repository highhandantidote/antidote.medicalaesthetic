"""
Performance Configuration System
Allows seamless switching between optimized and regular templates
"""
import os
from flask import current_app

class PerformanceConfig:
    """Configuration for performance optimizations"""
    
    # Performance feature flags
    ENABLE_CSS_BUNDLING = True
    ENABLE_IMAGE_OPTIMIZATION = True
    ENABLE_COMPRESSION = True
    ENABLE_CACHE_HEADERS = True
    
    # Template selection
    USE_OPTIMIZED_TEMPLATES = True
    
    @classmethod
    def get_base_template(cls):
        """Get the appropriate base template"""
        if cls.USE_OPTIMIZED_TEMPLATES:
            return 'base_optimized.html'
        return 'base.html'
    
    @classmethod
    def should_use_webp(cls):
        """Check if WebP images should be used"""
        return cls.ENABLE_IMAGE_OPTIMIZATION
    
    @classmethod
    def get_css_bundle_path(cls, bundle_name):
        """Get path to CSS bundle"""
        if cls.ENABLE_CSS_BUNDLING:
            return f'optimized/{bundle_name}-bundle.css'
        return None

# Flask context processor to make config available in templates
def register_performance_context(app):
    """Register performance config in template context"""
    
    @app.context_processor
    def inject_performance_config():
        return {
            'performance_config': PerformanceConfig,
            'base_template': PerformanceConfig.get_base_template()
        }
    
    return PerformanceConfig