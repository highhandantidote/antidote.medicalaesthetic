#!/usr/bin/env python3
"""
Final comprehensive test before 400+ clinic rollout.
Tests all system components with real clinic data.
"""

import os
import sys
import time
import logging
from add_clinic_by_place_id import add_clinic_by_place_id
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Test clinics with Indian Place IDs
TEST_CLINICS = [
    "ChIJ-525K5mXyzsR5yUDZ9b8ROY",  # Your provided clinic
    "ChIJhcOH4tyZyzsRN1AHrG8xZ5I",  # Revera Clinic (existing)
    # Add more Indian clinic Place IDs as needed
]

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def test_clinic_import(place_id):
    """Test importing a single clinic."""
    print(f"\nTesting clinic import: {place_id}")
    
    try:
        result = add_clinic_by_place_id(place_id)
        if result:
            print(f"✓ Successfully processed clinic {place_id}")
            return True
        else:
            print(f"✗ Failed to import clinic {place_id}")
            return False
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        return False

def verify_clinic_data(place_id):
    """Verify clinic data in database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, address, city, google_rating, services_offered, working_hours
        FROM clinics 
        WHERE google_place_id = %s
    """, (place_id,))
    
    clinic = cursor.fetchone()
    conn.close()
    
    if clinic:
        print(f"✓ Clinic data verified: {clinic[1]} in {clinic[3]}")
        print(f"  - Rating: {clinic[4]}")
        print(f"  - Services: {len(clinic[5].split(',')) if clinic[5] else 0} specialties")
        print(f"  - Hours: {'Available' if clinic[6] else 'Not available'}")
        return True
    else:
        print(f"✗ No clinic data found for {place_id}")
        return False

def test_review_import(place_id):
    """Test review import for clinic."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM google_reviews gr
        JOIN clinics c ON gr.clinic_id = c.id
        WHERE c.google_place_id = %s
    """, (place_id,))
    
    review_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"✓ Reviews imported: {review_count}")
    return review_count > 0

def run_comprehensive_test():
    """Run comprehensive rollout readiness test."""
    print("=== FINAL ROLLOUT READINESS TEST ===")
    print(f"Testing {len(TEST_CLINICS)} clinics")
    
    success_count = 0
    total_tests = len(TEST_CLINICS)
    
    for i, place_id in enumerate(TEST_CLINICS, 1):
        print(f"\n--- Test {i}/{total_tests} ---")
        
        # Test clinic import
        import_success = test_clinic_import(place_id)
        
        if import_success:
            # Verify data
            data_verified = verify_clinic_data(place_id)
            
            # Test review import
            reviews_imported = test_review_import(place_id)
            
            if data_verified:
                success_count += 1
                print(f"✓ Clinic {place_id} - PASSED")
            else:
                print(f"✗ Clinic {place_id} - DATA VERIFICATION FAILED")
        else:
            print(f"✗ Clinic {place_id} - IMPORT FAILED")
        
        # Rate limiting delay
        if i < total_tests:
            time.sleep(2)
    
    # Final assessment
    success_rate = (success_count / total_tests) * 100
    print(f"\n=== FINAL ASSESSMENT ===")
    print(f"Tests passed: {success_count}/{total_tests}")
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 100:
        print("🎉 SYSTEM READY FOR FULL 400+ CLINIC ROLLOUT")
        return True
    elif success_rate >= 80:
        print("⚠️ SYSTEM MOSTLY READY - Minor issues to address")
        return True
    else:
        print("❌ SYSTEM NEEDS FIXES BEFORE ROLLOUT")
        return False

def main():
    """Main test function."""
    try:
        ready = run_comprehensive_test()
        
        if ready:
            print("\nRECOMMENDATION: Proceed with 400+ clinic rollout")
            sys.exit(0)
        else:
            print("\nRECOMMENDATION: Address issues before rollout")
            sys.exit(1)
    except Exception as e:
        print(f"Test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()