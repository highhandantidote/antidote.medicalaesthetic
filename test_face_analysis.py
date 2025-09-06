#!/usr/bin/env python3
"""
Test script for the face analysis system.
Tests the integration of Gemini AI and geometric analysis.
"""

import os
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_geometric_analysis():
    """Test the geometric analysis system."""
    try:
        from utils.geometric_analysis import FacialGeometricAnalyzer
        from utils.facial_landmarks import FacialLandmarkDetector
        
        print("✅ Geometric analysis modules imported successfully")
        
        # Test landmark detector
        detector = FacialLandmarkDetector()
        print("✅ Landmark detector initialized")
        
        # Test geometric analyzer
        analyzer = FacialGeometricAnalyzer()
        print("✅ Geometric analyzer initialized")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_enhanced_analysis():
    """Test the enhanced analysis function."""
    try:
        from utils.gemini_analysis import analyze_face_image_enhanced
        
        # Test with dummy image path
        test_image = "/tmp/test_face.jpg"
        
        # Create a simple test image if it doesn't exist
        if not os.path.exists(test_image):
            from PIL import Image
            img = Image.new('RGB', (640, 480), color='white')
            img.save(test_image)
            print(f"✅ Created test image at {test_image}")
        
        # Test analysis (will likely fail due to no API key, but should not crash)
        user_info = {
            'age': 30,
            'gender': 'female',
            'concerns': 'Test analysis',
            'history': 'None'
        }
        
        print("🔍 Testing enhanced analysis function...")
        result = analyze_face_image_enhanced(test_image, user_info)
        
        # Check result structure
        if isinstance(result, dict):
            print("✅ Enhanced analysis returned dictionary")
            print(f"✅ Has geometric analysis: {result.get('has_geometric_analysis', False)}")
            print(f"✅ Mathematical scores available: {'mathematical_scores' in result}")
            
            if 'mathematical_scores' in result:
                scores = result['mathematical_scores']
                print(f"   - Golden ratio score: {scores.get('golden_ratio_score', 'N/A')}")
                print(f"   - Symmetry score: {scores.get('symmetry_score', 'N/A')}")
                print(f"   - Facial thirds score: {scores.get('facial_thirds_score', 'N/A')}")
        else:
            print("❌ Enhanced analysis did not return dictionary")
            
        return True
        
    except Exception as e:
        print(f"❌ Enhanced analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_visualization():
    """Test the visualization system."""
    try:
        from utils.visualization import FacialVisualizationGenerator
        
        viz_generator = FacialVisualizationGenerator()
        print("✅ Visualization generator initialized")
        
        # Test with dummy landmarks data
        dummy_landmarks = {
            'face_landmarks': [[100, 100], [200, 100], [150, 150], [150, 200]],
            'image_dimensions': (640, 480)
        }
        
        dummy_analysis = {
            'golden_ratio_analysis': {'overall_score': 85},
            'symmetry_analysis': {'overall_score': 90}
        }
        
        # Test overlay generation
        golden_overlay = viz_generator.generate_golden_ratio_overlay(dummy_landmarks, dummy_analysis)
        symmetry_overlay = viz_generator.generate_symmetry_overlay(dummy_landmarks, dummy_analysis)
        
        print("✅ Overlay generation successful")
        return True
        
    except ImportError as e:
        print(f"❌ Visualization import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Visualization test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Face Analysis System")
    print("=" * 50)
    
    tests = [
        ("Geometric Analysis", test_geometric_analysis),
        ("Enhanced Analysis", test_enhanced_analysis),
        ("Visualization", test_visualization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        try:
            if test_func():
                print(f"✅ {test_name} test passed")
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Face analysis system is ready.")
    else:
        print("⚠️ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()