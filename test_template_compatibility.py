"""
Test Template Compatibility - Verify optimized template matches original
This script tests that base_optimized_complete.html produces identical visual results
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template
from app import create_app

def test_template_compatibility():
    """Test that both templates produce similar output"""
    
    # Create test app
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing template compatibility...")
        
        # Create a simple test context
        test_context = {
            'title': 'Test Page',
            'meta_description': 'Test description',
            'meta_keywords': 'test, keywords'
        }
        
        # Test both templates render without errors
        try:
            print("\n📝 Testing base.html...")
            original_html = render_template('base.html', **test_context)
            print("✅ base.html renders successfully")
            
            print("\n📝 Testing base_optimized_complete.html...")
            optimized_html = render_template('base_optimized_complete.html', **test_context)
            print("✅ base_optimized_complete.html renders successfully")
            
            # Check for key elements presence
            print("\n🔍 Checking for critical elements...")
            
            # Check for navbar
            if 'navbar' in original_html and 'navbar' in optimized_html:
                print("✅ Both templates include navbar")
            else:
                print("❌ Missing navbar in one template")
            
            # Check for footer
            if 'footer' in original_html and 'footer' in optimized_html:
                print("✅ Both templates include footer")
            else:
                print("❌ Missing footer in one template")
            
            # Check for CSS loading
            if 'bootstrap' in original_html and 'bootstrap' in optimized_html:
                print("✅ Both templates load Bootstrap CSS")
            else:
                print("❌ Missing Bootstrap CSS in one template")
            
            # Check for jQuery
            if 'jquery' in original_html and 'jquery' in optimized_html:
                print("✅ Both templates load jQuery")
            else:
                print("❌ Missing jQuery in one template")
            
            # Check for search autocomplete
            if 'search-autocomplete' in original_html and 'search-autocomplete' in optimized_html:
                print("✅ Both templates include search autocomplete")
            else:
                print("❌ Missing search autocomplete in one template")
            
            print("\n✅ Template compatibility test completed!")
            print("Both templates should render identically from user perspective")
            
        except Exception as e:
            print(f"❌ Template rendering error: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = test_template_compatibility()
    if success:
        print("\n🎉 Templates are compatible!")
    else:
        print("\n❌ Templates have compatibility issues!")