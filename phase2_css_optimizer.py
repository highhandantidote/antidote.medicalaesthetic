"""
Phase 2: Non-Bundling CSS Optimization
Implements critical CSS extraction and async loading without bundling
"""

import os
import re
import gzip
from pathlib import Path
from flask import Flask

class CSSOptimizer:
    def __init__(self):
        self.static_dir = Path("static")
        self.css_dir = self.static_dir / "css"
        self.critical_css = ""
        
    def extract_critical_css(self):
        """Extract above-the-fold critical CSS"""
        critical_files = [
            "modern.css",
            "style.css", 
            "light-theme.css",
            "banner-slider.css",
            "navbar-autocomplete.css"
        ]
        
        critical_css_content = []
        
        for file in critical_files:
            file_path = self.css_dir / file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract only critical rules (above-the-fold)
                    critical_rules = self._extract_above_fold_css(content)
                    if critical_rules:
                        critical_css_content.append(f"/* From {file} */\n{critical_rules}")
        
        self.critical_css = "\n".join(critical_css_content)
        return self.critical_css
    
    def _extract_above_fold_css(self, css_content):
        """Extract CSS rules that affect above-the-fold content"""
        critical_selectors = [
            # Navigation
            r'\.navbar[^{]*{[^}]*}',
            r'\.nav-[^{]*{[^}]*}',
            r'\.navbar-brand[^{]*{[^}]*}',
            r'\.navbar-toggler[^{]*{[^}]*}',
            
            # Hero banner
            r'\.hero[^{]*{[^}]*}',
            r'\.banner[^{]*{[^}]*}',
            r'\.carousel[^{]*{[^}]*}',
            
            # Search
            r'\.search[^{]*{[^}]*}',
            r'\.form-control[^{]*{[^}]*}',
            r'\.btn[^{]*{[^}]*}',
            
            # Typography
            r'body[^{]*{[^}]*}',
            r'html[^{]*{[^}]*}',
            r'h1[^{]*{[^}]*}',
            r'h2[^{]*{[^}]*}',
            r'\.text-[^{]*{[^}]*}',
            
            # Container
            r'\.container[^{]*{[^}]*}',
            r'\.container-fluid[^{]*{[^}]*}',
            r'\.row[^{]*{[^}]*}',
            r'\.col[^{]*{[^}]*}',
        ]
        
        critical_css = []
        for selector_pattern in critical_selectors:
            matches = re.findall(selector_pattern, css_content, re.IGNORECASE | re.DOTALL)
            critical_css.extend(matches)
        
        return "\n".join(critical_css)
    
    def minify_css_files(self):
        """Minify individual CSS files without bundling"""
        for css_file in self.css_dir.glob("*.css"):
            if css_file.name.endswith('.min.css'):
                continue
                
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple minification
            minified = self._minify_css(content)
            
            # Save minified version
            minified_path = css_file.with_suffix('.min.css')
            with open(minified_path, 'w', encoding='utf-8') as f:
                f.write(minified)
            
            # Create gzipped version
            with gzip.open(str(minified_path) + '.gz', 'wt', encoding='utf-8') as f:
                f.write(minified)
    
    def _minify_css(self, css_content):
        """Simple CSS minification"""
        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Remove extra whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        
        # Remove spaces around specific characters
        css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)
        
        # Remove trailing semicolons
        css_content = re.sub(r';}', '}', css_content)
        
        return css_content.strip()
    
    def get_critical_css_inline(self):
        """Get critical CSS for inline embedding"""
        if not self.critical_css:
            self.extract_critical_css()
        
        return self._minify_css(self.critical_css)
    
    def get_non_critical_css_files(self):
        """Get list of non-critical CSS files for async loading"""
        all_css_files = [
            "typography-optimization.css",
            "unified-mobile.css",
            "mobile-borderless.css",
            "comma-fixes.css",
            "search-fixes.css",
            "comma-emergency-fix.css",
            "remove-available-badge.css",
            "thread-suggestions.css",
            "mobile-bottom-nav.css",
            "mobile-nav-fix.css",
            "mobile-search-compact.css",
            "clinic-directory-mobile.css",
            "search-placeholder.css",
            "desktop-optimization.css",
            "mobile-horizontal-fix.css",
            "search-dropdown-fix.css",
            "mobile-logo-hide.css",
            "footer-hide.css",
            "category-image-optimization.css",
            "tab-underline.css",
            "custom-gradients.css"
        ]
        
        return [f for f in all_css_files if (self.css_dir / f).exists()]

# Initialize CSS optimizer
css_optimizer = CSSOptimizer()