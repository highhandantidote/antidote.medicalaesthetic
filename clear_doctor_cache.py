#!/usr/bin/env python3
"""
Clear the doctor cache to force reloading with the corrected profile_image field
"""

def clear_doctor_cache():
    """Clear the doctor cache to force reload with correct profile_image"""
    try:
        from phase1_performance_cache import phase1_cache
        
        # Clear the doctors cache specifically
        phase1_cache.invalidate("homepage_doctors")
        
        # Clear all cache to be safe
        phase1_cache.clear_all()
        
        print("✅ Successfully cleared doctor cache!")
        print("🔄 Next homepage request will reload doctors with profile_image data")
        
        return True
    except Exception as e:
        print(f"❌ Error clearing cache: {str(e)}")
        return False

if __name__ == "__main__":
    clear_doctor_cache()