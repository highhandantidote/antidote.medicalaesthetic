"""
Critical CSS Bundler - Advanced Performance Optimization
Bundles CSS files to reduce render-blocking requests from 24 to 3 critical files
"""

import os
import re
import hashlib
from pathlib import Path

class CriticalCSSBundler:
    """Bundles CSS files into critical and non-critical categories"""
    
    def __init__(self):
        self.css_dir = Path("static/css")
        self.bundled_dir = Path("static/css/bundled")
        self.bundled_dir.mkdir(exist_ok=True)
        
        # Critical CSS files that must load immediately
        self.critical_css = [
            "modern.css",
            "style.css", 
            "light-theme.css",
            "unified-mobile.css",
            "mobile-bottom-nav.css",
            "banner-slider.css"
        ]
        
        # Mobile-specific CSS files
        self.mobile_css = [
            "mobile-borderless.css",
            "mobile-nav-fix.css",
            "mobile-search-compact.css",
            "mobile-logo-hide.css",
            "mobile-horizontal-fix.css",
            "clinic-directory-mobile.css"
        ]
        
        # Component CSS files (can be deferred)
        self.component_css = [
            "typography-optimization.css",
            "tab-underline.css",
            "custom-gradients.css",
            "thread-suggestions.css",
            "navbar-autocomplete.css",
            "search-placeholder.css",
            "search-fixes.css",
            "search-dropdown-fix.css",
            "comma-fixes.css",
            "comma-emergency-fix.css",
            "remove-available-badge.css",
            "desktop-optimization.css",
            "footer-hide.css",
            "category-image-optimization.css"
        ]
    
    def minify_css(self, css_content):
        """Basic CSS minification"""
        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        # Remove extra whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        # Remove whitespace around specific characters
        css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)
        # Remove trailing semicolons
        css_content = re.sub(r';}', '}', css_content)
        return css_content.strip()
    
    def bundle_css_files(self, file_list, output_name):
        """Bundle multiple CSS files into one"""
        bundled_content = []
        total_size = 0
        processed_files = 0
        
        for css_file in file_list:
            css_path = self.css_dir / css_file
            if css_path.exists():
                try:
                    with open(css_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Add file header comment
                    bundled_content.append(f"/* {css_file} */")
                    bundled_content.append(content)
                    bundled_content.append("")  # Add spacing
                    
                    total_size += len(content)
                    processed_files += 1
                    
                except Exception as e:
                    print(f"⚠️ Error reading {css_file}: {e}")
            else:
                print(f"⚠️ CSS file not found: {css_file}")
        
        if bundled_content:
            # Combine all content
            combined_content = "\n".join(bundled_content)
            
            # Minify the combined content
            minified_content = self.minify_css(combined_content)
            
            # Create version hash
            version_hash = hashlib.md5(minified_content.encode()).hexdigest()[:8]
            versioned_filename = f"{output_name}.{version_hash}.css"
            
            # Save bundled file
            output_path = self.bundled_dir / versioned_filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(minified_content)
            
            original_size = total_size
            bundled_size = len(minified_content)
            compression_ratio = ((original_size - bundled_size) / original_size * 100) if original_size > 0 else 0
            
            print(f"✅ {output_name}: {processed_files} files → {bundled_size:,} bytes ({compression_ratio:.1f}% smaller)")
            return versioned_filename
        
        return None
    
    def create_bundle_manifest(self, bundles):
        """Create a manifest file for the bundles"""
        manifest = {
            'critical': bundles.get('critical'),
            'mobile': bundles.get('mobile'),
            'components': bundles.get('components'),
            'created': str(os.path.getctime(self.bundled_dir))
        }
        
        manifest_path = self.bundled_dir / "manifest.json"
        import json
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return manifest_path
    
    def bundle_all_css(self):
        """Bundle all CSS files into optimized bundles"""
        print("🚀 Starting CSS bundling optimization...")
        
        bundles = {}
        
        # Bundle critical CSS
        critical_bundle = self.bundle_css_files(self.critical_css, "critical")
        if critical_bundle:
            bundles['critical'] = critical_bundle
        
        # Bundle mobile CSS
        mobile_bundle = self.bundle_css_files(self.mobile_css, "mobile")
        if mobile_bundle:
            bundles['mobile'] = mobile_bundle
        
        # Bundle component CSS
        component_bundle = self.bundle_css_files(self.component_css, "components")
        if component_bundle:
            bundles['components'] = component_bundle
        
        if bundles:
            # Create manifest
            manifest_path = self.create_bundle_manifest(bundles)
            
            print(f"\n📊 CSS Bundling Summary:")
            print(f"  Original files: {len(self.critical_css + self.mobile_css + self.component_css)}")
            print(f"  Bundled files: {len(bundles)}")
            print(f"  Reduction: {((len(self.critical_css + self.mobile_css + self.component_css) - len(bundles)) / len(self.critical_css + self.mobile_css + self.component_css) * 100):.1f}%")
            print(f"  Manifest: {manifest_path}")
            
            return bundles
        
        return None

def main():
    """Main execution function"""
    bundler = CriticalCSSBundler()
    
    # Bundle all CSS files
    bundles = bundler.bundle_all_css()
    
    if bundles:
        print("\n🎯 CSS bundling completed successfully!")
        print("\nNext steps:")
        print("1. Update base.html to use bundled CSS files")
        print("2. Implement critical CSS inlining")
        print("3. Add preload hints for bundled files")
        print("4. Test performance improvements")
    else:
        print("\n❌ No CSS bundles were created")

if __name__ == "__main__":
    main()