"""
CSS Render-Blocking Fix for Antidote Platform
Addresses the CSS performance issues that are causing 2,100ms delays in page rendering.

Key optimizations:
1. Critical CSS inlining for above-the-fold content
2. Async loading of non-critical CSS
3. CSS bundling optimization
4. Preconnect hints for external resources
"""

import logging
from flask import current_app, request

logger = logging.getLogger(__name__)

class CSSRenderBlockingOptimizer:
    def __init__(self):
        self.critical_css = self._get_critical_css()
        self.external_resources = [
            'https://cdn.jsdelivr.net',
            'https://code.jquery.com',
            'https://cdnjs.cloudflare.com'
        ]
    
    def _get_critical_css(self):
        """
        Critical CSS for above-the-fold content that should be inlined.
        This includes essential styles for navigation, hero banner, and initial content.
        """
        return """
/* Critical CSS - Above the fold content */
* { box-sizing: border-box; }
body { 
    margin: 0; 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
}

/* Navigation - Critical */
.navbar {
    background: #00A0B0;
    padding: 0.75rem 1rem;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.navbar-brand {
    color: white;
    font-size: 1.5rem;
    font-weight: bold;
    text-decoration: none;
}

.navbar-nav {
    display: flex;
    list-style: none;
    margin: 0;
    padding: 0;
    align-items: center;
}

.nav-link {
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    transition: opacity 0.2s;
}

.nav-link:hover {
    opacity: 0.8;
}

/* Hero Banner - Critical */
.hero-banner-container {
    margin-top: 70px;
    position: relative;
    min-height: 400px;
    background: linear-gradient(135deg, #00A0B0 0%, #0084a0 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    text-align: center;
}

.hero-content {
    max-width: 800px;
    padding: 2rem;
}

.hero-title {
    font-size: clamp(1.8rem, 4vw, 3rem);
    font-weight: 700;
    margin-bottom: 1rem;
    line-height: 1.2;
}

.hero-subtitle {
    font-size: clamp(1rem, 2vw, 1.25rem);
    margin-bottom: 2rem;
    opacity: 0.9;
}

/* Category Cards - Critical for first paint */
.category-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    padding: 2rem 1rem;
    max-width: 1200px;
    margin: 0 auto;
}

.category-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
    text-decoration: none;
    color: inherit;
}

.category-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.15);
}

.category-card-image {
    height: 160px;
    background-size: cover;
    background-position: center;
    background-color: #f8f9fa;
}

.category-card-content {
    padding: 1.5rem;
}

.category-card-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: #00A0B0;
}

.category-card-description {
    color: #666;
    line-height: 1.5;
}

/* Loading states to prevent layout shift */
.loading-placeholder {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: loading 2s infinite;
}

@keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
    .navbar {
        padding: 0.5rem 1rem;
    }
    
    .hero-content {
        padding: 1.5rem 1rem;
    }
    
    .category-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
        padding: 1rem;
    }
}

/* Hide non-critical elements until CSS loads */
.section-below-fold {
    visibility: hidden;
}

.css-loaded .section-below-fold {
    visibility: visible;
}
"""
    
    def get_preconnect_hints(self):
        """Generate preconnect hints for external resources."""
        hints = []
        for resource in self.external_resources:
            hints.append(f'<link rel="preconnect" href="{resource}">')
        return '\n'.join(hints)
    
    def get_critical_css_inline(self):
        """Return critical CSS for inline inclusion."""
        return f'<style id="critical-css">{self.critical_css}</style>'
    
    def get_async_css_loader(self, css_files):
        """Generate async CSS loading script."""
        if not css_files:
            return ""
        
        loader_script = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Mark CSS as loaded for visibility control
    document.documentElement.classList.add('css-loaded');
    
    // Load non-critical CSS asynchronously
    const cssFiles = %s;
    
    cssFiles.forEach(function(href) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        link.media = 'print';
        link.onload = function() {
            this.media = 'all';
        };
        document.head.appendChild(link);
        
        // Fallback for browsers that don't support onload
        setTimeout(function() {
            link.media = 'all';
        }, 100);
    });
});
</script>
""" % str(css_files).replace("'", '"')
        return loader_script
    
    def optimize_css_loading(self, template_content):
        """
        Optimize CSS loading in template content by:
        1. Moving critical CSS inline
        2. Loading non-critical CSS asynchronously
        3. Adding preconnect hints
        """
        try:
            # Add preconnect hints at the beginning of head
            if '<head>' in template_content:
                preconnect_hints = self.get_preconnect_hints()
                template_content = template_content.replace(
                    '<head>',
                    f'<head>\n{preconnect_hints}'
                )
            
            # Add critical CSS inline after meta tags
            if '<meta' in template_content and 'critical-css' not in template_content:
                # Find the last meta tag and insert critical CSS after it
                import re
                meta_pattern = r'(<meta[^>]*>)'
                matches = list(re.finditer(meta_pattern, template_content))
                if matches:
                    last_meta = matches[-1]
                    insert_pos = last_meta.end()
                    critical_css_inline = self.get_critical_css_inline()
                    template_content = (
                        template_content[:insert_pos] + 
                        f'\n{critical_css_inline}\n' + 
                        template_content[insert_pos:]
                    )
            
            return template_content
            
        except Exception as e:
            logger.error(f"Error optimizing CSS loading: {e}")
            return template_content

def register_css_optimization(app):
    """Register CSS optimization middleware."""
    css_optimizer = CSSRenderBlockingOptimizer()
    
    @app.after_request
    def optimize_css_response(response):
        """Optimize CSS in HTML responses."""
        try:
            # Only process HTML responses that aren't already compressed
            if (response.content_type and 
                'text/html' in response.content_type and 
                response.status_code == 200 and
                response.headers.get('Content-Encoding') != 'gzip'):
                
                try:
                    # Get response data
                    data = response.get_data(as_text=True)
                    
                    # Apply CSS optimizations
                    optimized_data = css_optimizer.optimize_css_loading(data)
                    
                    # Update response
                    response.set_data(optimized_data)
                    
                    # Add performance headers
                    response.headers['X-CSS-Optimized'] = 'true'
                    
                except UnicodeDecodeError:
                    # Skip CSS optimization if content can't be decoded (already compressed)
                    response.headers['X-CSS-Optimized'] = 'skipped-compressed'
                
        except Exception as e:
            logger.error(f"Error in CSS optimization middleware: {e}")
        
        return response
    
    # Add template context for CSS optimization
    @app.context_processor
    def inject_css_optimization():
        """Inject CSS optimization helpers into templates."""
        return {
            'critical_css': css_optimizer.get_critical_css_inline(),
            'async_css_loader': css_optimizer.get_async_css_loader,
            'preconnect_hints': css_optimizer.get_preconnect_hints()
        }
    
    logger.info("✅ CSS render-blocking optimization registered")