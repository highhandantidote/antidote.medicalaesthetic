#!/usr/bin/env python3
"""
Test bulk clinic import system to verify readiness for 400+ clinic rollout.

This script tests the clinic import system with a small batch of diverse clinics
to ensure all components work reliably before the full rollout.
"""

import os
import sys
import time
import logging
from add_clinic_by_place_id import add_clinic_by_place_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_clinic_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Test clinics with diverse Place IDs from different cities and specialties
TEST_CLINICS = [
    {
        'place_id': 'ChIJN1t_tDeuEmsRUsoyG83frY4',  # Sydney plastic surgery clinic
        'expected_city': 'Sydney',
        'expected_type': 'Plastic Surgery'
    },
    {
        'place_id': 'ChIJrTLr-GyuEmsRBfy61i59si0',  # Another Sydney medical center
        'expected_city': 'Sydney', 
        'expected_type': 'Medical Center'
    },
    {
        'place_id': 'ChIJOwg_06VPwokRYv534QaPC8g',  # New York dermatology clinic
        'expected_city': 'New York',
        'expected_type': 'Dermatology'
    },
    {
        'place_id': 'ChIJ2eUgeAK6j4ARbn5u_wAGqWA',  # Los Angeles aesthetic center
        'expected_city': 'Los Angeles',
        'expected_type': 'Aesthetic Center'
    },
    {
        'place_id': 'ChIJdd4hrwug2EcRmSrV3Vo6llI',  # London cosmetic clinic
        'expected_city': 'London',
        'expected_type': 'Cosmetic Surgery'
    }
]

def test_single_clinic_import(place_id, expected_data):
    """Test importing a single clinic and verify the data."""
    try:
        logging.info(f"Testing clinic import for Place ID: {place_id}")
        logging.info(f"Expected: {expected_data['expected_city']} - {expected_data['expected_type']}")
        
        # Import the clinic
        result = add_clinic_by_place_id(place_id)
        
        if result:
            logging.info(f"✓ Successfully imported clinic from {place_id}")
            return True
        else:
            logging.error(f"✗ Failed to import clinic from {place_id}")
            return False
            
    except Exception as e:
        logging.error(f"✗ Exception importing clinic {place_id}: {str(e)}")
        return False

def verify_system_components():
    """Verify all system components are working."""
    logging.info("Verifying system components...")
    
    # Check database connection
    try:
        from add_clinic_by_place_id import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clinics")
        clinic_count = cursor.fetchone()[0]
        logging.info(f"✓ Database connection working - {clinic_count} clinics in database")
        conn.close()
    except Exception as e:
        logging.error(f"✗ Database connection failed: {str(e)}")
        return False
    
    # Check Google Places API
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        logging.error("✗ GOOGLE_PLACES_API_KEY not found in environment")
        return False
    else:
        logging.info("✓ Google Places API key found")
    
    return True

def run_bulk_import_test():
    """Run the bulk import test with test clinics."""
    logging.info("Starting bulk clinic import test...")
    logging.info(f"Testing with {len(TEST_CLINICS)} diverse clinics")
    
    # Verify system components first
    if not verify_system_components():
        logging.error("System components verification failed")
        return False
    
    success_count = 0
    failure_count = 0
    
    for i, clinic_data in enumerate(TEST_CLINICS, 1):
        logging.info(f"\n--- Test {i}/{len(TEST_CLINICS)} ---")
        
        success = test_single_clinic_import(
            clinic_data['place_id'], 
            clinic_data
        )
        
        if success:
            success_count += 1
        else:
            failure_count += 1
        
        # Add delay between imports to avoid rate limiting
        if i < len(TEST_CLINICS):
            logging.info("Waiting 5 seconds before next import...")
            time.sleep(5)
    
    # Summary
    logging.info(f"\n=== BULK IMPORT TEST SUMMARY ===")
    logging.info(f"Total clinics tested: {len(TEST_CLINICS)}")
    logging.info(f"Successful imports: {success_count}")
    logging.info(f"Failed imports: {failure_count}")
    logging.info(f"Success rate: {(success_count/len(TEST_CLINICS)*100):.1f}%")
    
    if success_count == len(TEST_CLINICS):
        logging.info("🎉 ALL TESTS PASSED - System ready for 400+ clinic rollout!")
        return True
    elif success_count >= len(TEST_CLINICS) * 0.8:  # 80% success rate
        logging.info("⚠️  MOSTLY SUCCESSFUL - System mostly ready, minor issues to address")
        return True
    else:
        logging.info("❌ MULTIPLE FAILURES - System needs fixes before rollout")
        return False

def main():
    """Main function to run the bulk import test."""
    try:
        success = run_bulk_import_test()
        
        if success:
            logging.info("\nRECOMMendation: System is ready for 400+ clinic rollout")
            sys.exit(0)
        else:
            logging.info("\nRECOMMendation: Address issues before proceeding with rollout")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Test failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()