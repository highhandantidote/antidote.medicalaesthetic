"""
Safe Performance Optimization Activation
This script provides a safe way to test the performance optimizations
"""
import os
import shutil
from pathlib import Path

def create_backup():
    """Create backup of original templates"""
    print("📁 Creating backup of original templates...")
    
    # Create backup directory
    backup_dir = Path("template_backup")
    backup_dir.mkdir(exist_ok=True)
    
    # Backup original templates
    templates_to_backup = [
        "templates/base.html",
        "templates/index.html"
    ]
    
    for template in templates_to_backup:
        if Path(template).exists():
            backup_path = backup_dir / Path(template).name
            shutil.copy2(template, backup_path)
            print(f"✅ Backed up {template} to {backup_path}")
    
    print("✅ Backup completed!")

def activate_performance_optimization():
    """Activate performance optimization safely"""
    print("🚀 Activating performance optimization...")
    
    # Step 1: Update performance config to use optimized template
    config_file = Path("performance_config.py")
    if config_file.exists():
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Enable optimized templates
        content = content.replace(
            'USE_OPTIMIZED_TEMPLATES = True',
            'USE_OPTIMIZED_TEMPLATES = True'
        )
        
        with open(config_file, 'w') as f:
            f.write(content)
        
        print("✅ Performance config updated")
    
    # Step 2: Create a test route for comparison
    test_route = """
# Add this route to your main app for testing
@app.route('/test-performance')
def test_performance():
    \"\"\"Test route to compare performance\"\"\"
    return render_template('base_optimized_complete.html', 
                         title='Performance Test',
                         meta_description='Testing performance optimization')
"""
    
    with open("test_route.py", "w") as f:
        f.write(test_route)
    
    print("✅ Test route created in test_route.py")
    
    # Step 3: Instructions for safe testing
    print("\n🔬 SAFE TESTING INSTRUCTIONS:")
    print("1. Copy the test route from test_route.py to your main app")
    print("2. Visit /test-performance to see the optimized version")
    print("3. Compare it with your current homepage")
    print("4. If it looks identical, you can proceed with full activation")
    print("5. If there are issues, revert using restore_backup()")

def restore_backup():
    """Restore original templates from backup"""
    print("🔄 Restoring original templates...")
    
    backup_dir = Path("template_backup")
    if not backup_dir.exists():
        print("❌ No backup found!")
        return
    
    # Restore templates
    templates_to_restore = [
        "base.html",
        "index.html"
    ]
    
    for template in templates_to_restore:
        backup_path = backup_dir / template
        if backup_path.exists():
            target_path = Path("templates") / template
            shutil.copy2(backup_path, target_path)
            print(f"✅ Restored {template}")
    
    print("✅ Backup restored!")

def full_activation():
    """Full activation after testing confirms compatibility"""
    print("🎯 Full performance optimization activation...")
    
    # Replace base.html with optimized version
    optimized_path = Path("templates/base_optimized_complete.html")
    base_path = Path("templates/base.html")
    
    if optimized_path.exists():
        # Create final backup
        shutil.copy2(base_path, Path("templates/base_original.html"))
        
        # Replace with optimized version
        shutil.copy2(optimized_path, base_path)
        
        print("✅ base.html replaced with optimized version")
        print("✅ Original saved as base_original.html")
        print("🎉 Performance optimization fully activated!")
    else:
        print("❌ Optimized template not found!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "activate":
            create_backup()
            activate_performance_optimization()
        elif sys.argv[1] == "restore":
            restore_backup()
        elif sys.argv[1] == "full":
            full_activation()
        else:
            print("Usage: python safe_performance_activation.py [activate|restore|full]")
    else:
        print("🛡️ Safe Performance Optimization Tool")
        print("Usage:")
        print("  python safe_performance_activation.py activate  - Create backup and prepare for testing")
        print("  python safe_performance_activation.py restore   - Restore from backup")
        print("  python safe_performance_activation.py full      - Full activation after testing")