#!/usr/bin/env python3
"""
Mobile CSS Optimization System
Implements non-blocking CSS loading for mobile devices
"""

import os
from flask import Flask, request, g
from pathlib import Path

class MobileCSSOptimizer:
    def __init__(self):
        self.critical_css = self.load_critical_css()
        self.non_critical_css_files = self.get_non_critical_css_files()
    
    def load_critical_css(self):
        """Load critical CSS that should be inlined"""
        critical_css_path = Path("static/css/mobile-critical-styles.css")
        if critical_css_path.exists():
            with open(critical_css_path, 'r') as f:
                return f.read()
        return ""
    
    def get_non_critical_css_files(self):
        """Get list of non-critical CSS files that can be loaded asynchronously"""
        return [
            'css/thread-suggestions.css',
            'css/tab-underline.css',
            'css/custom-gradients.css',
            'css/typography-optimization.css',
            'css/unified-mobile.css',
            'css/mobile-borderless.css',
            'css/comma-fixes.css',
            'css/search-fixes.css',
            'css/comma-emergency-fix.css',
            'css/remove-available-badge.css',
            'css/mobile-bottom-nav.css',
            'css/mobile-nav-fix.css',
            'css/mobile-search-compact.css',
            'css/clinic-directory-mobile.css',
            'css/search-placeholder.css',
            'css/desktop-optimization.css',
            'css/mobile-horizontal-fix.css',
            'css/search-dropdown-fix.css',
            'css/mobile-logo-hide.css',
            'css/footer-hide.css',
            'css/category-image-optimization.css'
        ]
    
    def generate_mobile_css_loading_script(self):
        """Generate JavaScript for mobile CSS loading"""
        script = """
        <!-- Mobile CSS Loading Optimization -->
        <script>
        (function() {
            function loadCSS(href) {
                var link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = href;
                document.head.appendChild(link);
            }
            
            function isMobile() {
                return window.innerWidth <= 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            }
            
            // Load non-critical CSS after page load
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    if (isMobile()) {
                        setTimeout(function() {
                            // Load mobile-specific CSS files
                            var mobileCSS = [
                                '{{ url_for("static", filename="css/mobile-bottom-nav.css") }}',
                                '{{ url_for("static", filename="css/mobile-nav-fix.css") }}',
                                '{{ url_for("static", filename="css/mobile-search-compact.css") }}',
                                '{{ url_for("static", filename="css/mobile-logo-hide.css") }}',
                                '{{ url_for("static", filename="css/mobile-horizontal-fix.css") }}'
                            ];
                            
                            mobileCSS.forEach(function(css) {
                                loadCSS(css);
                            });
                        }, 100);
                    }
                });
            }
        })();
        </script>
        """
        return script
    
    def create_mobile_css_template(self):
        """Create mobile-optimized CSS template"""
        template = """
        <!-- Mobile CSS Optimization -->
        {% if request.headers.get('User-Agent', '').lower() | select('mobile') %}
        <style id="mobile-critical-css">
            /* Mobile Critical CSS - Inlined for immediate rendering */
            @media (max-width: 768px) {
                .hero-banner-container { min-height: 300px; background-size: cover; }
                .hero-search-section { min-height: 150px; padding: 1rem; }
                .navbar { min-height: 60px; }
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                .btn-primary { background-color: #00A0B0; border-color: #00A0B0; }
                .container { max-width: 100%; padding: 0 1rem; }
            }
        </style>
        {% endif %}
        
        <!-- Load critical CSS synchronously -->
        <link rel="stylesheet" href="{{ url_for('static', filename='css/modern.css') }}">
        <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
        <link rel="stylesheet" href="{{ url_for('static', filename='css/banner-slider.css') }}">
        <link rel="stylesheet" href="{{ url_for('static', filename='css/navbar-autocomplete.css') }}">
        
        <!-- Load non-critical CSS asynchronously -->
        <script>
        (function() {
            function loadCSS(href) {
                var link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = href;
                link.media = 'print';
                link.onload = function() { this.media = 'all'; };
                document.head.appendChild(link);
            }
            
            // Load after DOM is ready
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(function() {
                    var cssFiles = [
                        '{{ url_for("static", filename="css/thread-suggestions.css") }}',
                        '{{ url_for("static", filename="css/typography-optimization.css") }}',
                        '{{ url_for("static", filename="css/mobile-bottom-nav.css") }}',
                        '{{ url_for("static", filename="css/mobile-nav-fix.css") }}',
                        '{{ url_for("static", filename="css/search-dropdown-fix.css") }}',
                        '{{ url_for("static", filename="css/footer-hide.css") }}'
                    ];
                    
                    cssFiles.forEach(function(css) {
                        loadCSS(css);
                    });
                }, 50);
            });
        })();
        </script>
        """
        return template

def optimize_mobile_css_loading(app):
    """Optimize CSS loading for mobile devices"""
    
    optimizer = MobileCSSOptimizer()
    
    @app.before_request
    def check_mobile_device():
        """Check if request is from mobile device"""
        user_agent = request.headers.get('User-Agent', '').lower()
        g.is_mobile = any(mobile in user_agent for mobile in [
            'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
        ])
    
    @app.template_global()
    def mobile_css_optimization():
        """Template helper for mobile CSS optimization"""
        if g.get('is_mobile'):
            return optimizer.create_mobile_css_template()
        return ""
    
    @app.template_global()
    def is_mobile_request():
        """Template helper to check if request is from mobile"""
        return g.get('is_mobile', False)
    
    return app

if __name__ == "__main__":
    print("Mobile CSS Optimization System")
    print("Features:")
    print("- Critical CSS inlining for mobile devices")
    print("- Non-blocking CSS loading for secondary styles")
    print("- Mobile-specific CSS optimization")
    print("- Reduced render-blocking resources for mobile")
    
    optimizer = MobileCSSOptimizer()
    print(f"Critical CSS size: {len(optimizer.critical_css)} bytes")
    print(f"Non-critical CSS files: {len(optimizer.non_critical_css_files)}")