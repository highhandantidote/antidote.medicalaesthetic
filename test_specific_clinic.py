#!/usr/bin/env python3
"""
Test the specific clinic Place ID provided by user.
"""

from add_clinic_by_place_id import add_clinic_by_place_id

def main():
    place_id = "ChIJ-525K5mXyzsR5yUDZ9b8ROY"
    print(f"Testing clinic import for Place ID: {place_id}")
    
    try:
        result = add_clinic_by_place_id(place_id)
        if result:
            print("✅ Clinic import successful")
            return True
        else:
            print("❌ Clinic import failed")
            return False
    except Exception as e:
        print(f"❌ Exception during import: {str(e)}")
        return False

if __name__ == "__main__":
    main()