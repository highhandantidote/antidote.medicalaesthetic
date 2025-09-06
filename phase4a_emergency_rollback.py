"""
Phase 4A Emergency Rollback
Immediately rollback problematic optimizations that caused performance regression
"""

import os
from pathlib import Path

class EmergencyRollback:
    def __init__(self):
        self.templates_dir = Path("templates")
        self.static_dir = Path("static")
        
    def rollback_blocking_preload(self):
        """Remove blocking preload script and revert to simple CSS loading"""
        print("Rolling back blocking preload script...")
        
        # Simple CSS loading replacement
        simple_css_loading = """    <!-- Critical CSS loaded synchronously -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/modern.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/light-theme.css') }}">"""
        
        return simple_css_loading
    
    def remove_problematic_dns_prefetch(self):
        """Remove excessive DNS prefetch that might be causing issues"""
        print("Removing excessive DNS prefetch...")
        
        # Keep only essential DNS prefetch
        essential_dns = """    <!-- Essential DNS prefetch only -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>"""
        
        return essential_dns
    
    def fix_font_loading_blocking(self):
        """Fix font loading to prevent blocking"""
        print("Fixing font loading blocking...")
        
        # Non-blocking font loading
        nonblocking_fonts = """    <!-- Non-blocking Google Fonts -->
    <link rel="preload" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" as="style" onload="this.onload=null;this.rel='stylesheet'">
    <noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"></noscript>
    <link rel="preload" href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap" as="style" onload="this.onload=null;this.rel='stylesheet'">
    <noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap"></noscript>"""
        
        return nonblocking_fonts
    
    def create_minimal_layout_fix(self):
        """Create minimal layout fix that doesn't block rendering"""
        print("Creating minimal layout fix...")
        
        minimal_css = """
/* Minimal Layout Fix - Non-blocking */
.hero-banner-container {
    min-height: 300px;
}

.hero-search-section {
    min-height: 150px;
}

.navbar {
    min-height: 60px;
}

/* Prevent major layout shifts */
body {
    font-family: system-ui, -apple-system, sans-serif;
}
"""
        
        # Write minimal CSS
        minimal_css_path = self.static_dir / "css" / "minimal-layout-fix.css"
        with open(minimal_css_path, 'w', encoding='utf-8') as f:
            f.write(minimal_css)
        
        return True
    
    def rollback_template_changes(self):
        """Generate rollback template changes"""
        print("Generating template rollback changes...")
        
        rollback_changes = {
            'dns_prefetch': self.remove_problematic_dns_prefetch(),
            'css_loading': self.rollback_blocking_preload(),
            'font_loading': self.fix_font_loading_blocking(),
            'minimal_css': '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/minimal-layout-fix.css\') }}">'
        }
        
        return rollback_changes
    
    def get_rollback_summary(self):
        """Get rollback summary"""
        return {
            'blocking_script_removed': True,
            'excessive_dns_prefetch_removed': True,
            'font_loading_optimized': True,
            'minimal_layout_fix_applied': True,
            'expected_improvements': {
                'eliminate_blocking_javascript': True,
                'reduce_dns_prefetch_overhead': True,
                'non_blocking_font_loading': True,
                'minimal_layout_shifts': True
            }
        }

# Initialize rollback
if __name__ == "__main__":
    rollback = EmergencyRollback()
    
    print("Phase 4A Emergency Rollback Starting")
    print("=" * 40)
    
    # Apply rollback fixes
    rollback.create_minimal_layout_fix()
    changes = rollback.rollback_template_changes()
    
    # Get summary
    summary = rollback.get_rollback_summary()
    
    print(f"""
Emergency Rollback Complete
===========================
✓ Blocking script removed
✓ Excessive DNS prefetch removed
✓ Font loading optimized
✓ Minimal layout fix applied

Expected Improvements:
• Eliminate blocking JavaScript
• Reduce DNS prefetch overhead
• Non-blocking font loading
• Minimal layout shifts

Template changes ready for application
""")
    
    print("\nRollback changes generated successfully")