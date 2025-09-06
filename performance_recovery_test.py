
import time
import requests
import sys

def test_performance_recovery():
    """Test if performance has recovered after rollback"""
    print("Testing performance recovery after emergency rollback...")
    
    try:
        # Test homepage response time
        start_time = time.time()
        response = requests.get("http://localhost:5000/", timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        print(f"Homepage response time: {response_time:.2f}ms")
        print(f"Response status: {response.status_code}")
        
        # Performance targets after rollback
        if response_time < 400:  # Should be under 400ms
            print("✓ Server response time: GOOD")
        else:
            print("⚠️ Server response time: Still slow")
        
        if response.status_code == 200:
            print("✓ Server status: HEALTHY")
        else:
            print("⚠️ Server status: Issues detected")
        
        # Check content size
        content_size = len(response.content)
        print(f"Content size: {content_size:,} bytes")
        
        return response_time < 400 and response.status_code == 200
        
    except Exception as e:
        print(f"⚠️ Performance test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_performance_recovery()
    if success:
        print("\n✅ Performance recovery test PASSED")
        sys.exit(0)
    else:
        print("\n❌ Performance recovery test FAILED")
        sys.exit(1)
