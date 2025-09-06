"""
Advanced Performance System
Implements critical CSS inlining, resource hints, and optimized loading
"""

import os
import json
import time
from flask import Flask, render_template_string, request, make_response
from pathlib import Path

class AdvancedPerformanceSystem:
    """Manages advanced performance optimizations"""
    
    def __init__(self):
        self.css_dir = Path("static/css/bundled")
        self.optimized_dir = Path("static/optimized")
        self.manifest_path = self.css_dir / "manifest.json"
        self.bundles = self.load_bundle_manifest()
        
    def load_bundle_manifest(self):
        """Load CSS bundle manifest"""
        try:
            if self.manifest_path.exists():
                with open(self.manifest_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading bundle manifest: {e}")
        return {}
    
    def get_critical_css_content(self):
        """Get critical CSS content for inlining"""
        try:
            critical_file = self.bundles.get('critical')
            if critical_file:
                critical_path = self.css_dir / critical_file
                if critical_path.exists():
                    with open(critical_path, 'r') as f:
                        return f.read()
        except Exception as e:
            print(f"Error reading critical CSS: {e}")
        return ""
    
    def generate_preload_hints(self):
        """Generate preload hints for bundled CSS and optimized images"""
        preload_hints = []
        
        # Preload bundled CSS files
        for bundle_type, filename in self.bundles.items():
            if bundle_type != 'critical':  # Critical CSS is inlined
                preload_hints.append(f'<link rel="preload" href="/static/css/bundled/{filename}" as="style" onload="this.onload=null;this.rel=\'stylesheet\'">')
        
        # Preload optimized images
        optimized_images = [
            "hero_banner.webp",
            "hero_bottom.webp"
        ]
        
        for image in optimized_images:
            image_path = self.optimized_dir / image
            if image_path.exists():
                preload_hints.append(f'<link rel="preload" href="/static/optimized/{image}" as="image" type="image/webp">')
        
        return "\n    ".join(preload_hints)
    
    def generate_optimized_template_head(self):
        """Generate optimized template head section"""
        critical_css = self.get_critical_css_content()
        preload_hints = self.generate_preload_hints()
        
        template = f"""
    <!-- Critical CSS Inlined -->
    <style>
    {critical_css}
    </style>
    
    <!-- Resource Preload Hints -->
    {preload_hints}
    
    <!-- Non-critical CSS loaded asynchronously -->
    <noscript>
        <link rel="stylesheet" href="/static/css/bundled/{self.bundles.get('mobile', '')}" media="screen and (max-width: 768px)">
        <link rel="stylesheet" href="/static/css/bundled/{self.bundles.get('components', '')}" media="screen">
    </noscript>
    
    <!-- Optimized Image Loading -->
    <script>
    // Preload critical images
    (function() {{
        const criticalImages = [
            '/static/optimized/hero_banner.webp',
            '/static/optimized/hero_bottom.webp'
        ];
        
        criticalImages.forEach(function(src) {{
            const img = new Image();
            img.src = src;
        }});
    }})();
    </script>
"""
        return template
    
    def apply_image_optimizations(self, template_content):
        """Apply image optimizations to template content"""
        # Replace hero banner with optimized version
        template_content = template_content.replace(
            '/static/uploads/banners/20250714081643_YouTube_Banner_-_Connecting_You_with_Cosmetic_Treatments_Providers_8.png',
            '/static/optimized/hero_banner.webp'
        )
        
        # Replace hero bottom image with optimized version
        template_content = template_content.replace(
            '/static/images/hero_bottom_image.jpg',
            '/static/optimized/hero_bottom.webp'
        )
        
        return template_content
    
    def register_performance_middleware(self, app):
        """Register performance middleware with Flask app"""
        
        @app.before_request
        def before_request():
            """Pre-request performance optimizations"""
            # Add performance timing headers
            request.start_time = time.time()
        
        @app.after_request
        def after_request(response):
            """Post-request performance optimizations"""
            # Add performance headers
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Add timing headers
            if hasattr(request, 'start_time'):
                duration = (time.time() - request.start_time) * 1000
                response.headers['X-Response-Time'] = f'{duration:.2f}ms'
            
            return response
        
        print("✅ Advanced performance middleware registered")

def create_optimized_base_template():
    """Create optimized base template with performance enhancements"""
    perf_system = AdvancedPerformanceSystem()
    optimized_head = perf_system.generate_optimized_template_head()
    
    # Save optimized template
    optimized_template_path = Path("templates/base_optimized.html")
    
    # Read current base template
    with open("templates/base.html", 'r') as f:
        base_content = f.read()
    
    # Apply image optimizations
    base_content = perf_system.apply_image_optimizations(base_content)
    
    # Replace CSS section with optimized version
    css_section_start = base_content.find('<!-- Bootstrap CSS (Light Theme) -->')
    css_section_end = base_content.find('{% block extra_css %}{% endblock %}') + len('{% block extra_css %}{% endblock %}')
    
    if css_section_start != -1 and css_section_end != -1:
        optimized_content = (
            base_content[:css_section_start] +
            optimized_head +
            '\n    {% block extra_css %}{% endblock %}'
            + base_content[css_section_end:]
        )
        
        # Save optimized template
        with open(optimized_template_path, 'w') as f:
            f.write(optimized_content)
        
        print(f"✅ Created optimized base template: {optimized_template_path}")
        return True
    
    return False

def register_advanced_performance_optimizations(app):
    """Register all advanced performance optimizations"""
    import time
    
    perf_system = AdvancedPerformanceSystem()
    perf_system.register_performance_middleware(app)
    
    # Create optimized template
    create_optimized_base_template()
    
    print("🚀 Advanced performance optimizations registered successfully")

if __name__ == "__main__":
    create_optimized_base_template()
    print("🎯 Advanced performance system setup completed!")