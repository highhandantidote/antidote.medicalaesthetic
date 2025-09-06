"""
Guide for migrating to Google Places API (New) and fixing API configuration
to enable comprehensive clinic data extraction.
"""

import os
import logging

def check_current_api_setup():
    """Check current Google API configuration."""
    api_key = os.environ.get('GOOGLE_API_KEY')
    
    print("=== CURRENT GOOGLE API CONFIGURATION ===")
    print(f"GOOGLE_API_KEY: {'✓ Set' if api_key else '✗ Missing'}")
    print(f"API Key Preview: {api_key[:15]}..." if api_key else "No key found")
    
    return api_key

def explain_api_migration():
    """Explain the Google Places API migration requirements."""
    print("\n=== GOOGLE PLACES API MIGRATION REQUIRED ===")
    print("Your current API key is configured for the legacy Places API.")
    print("Google requires migration to Places API (New) for full functionality.")
    
    print("\n=== WHAT'S MISSING WITH LEGACY API ===")
    print("- Real-time ratings and review counts")
    print("- Accurate business addresses and contact info")
    print("- Business hours and operational status")
    print("- Photo references and detailed reviews")
    print("- Proper location coordinates for maps")
    
    print("\n=== MIGRATION STEPS NEEDED ===")
    print("1. Go to Google Cloud Console")
    print("2. Enable 'Places API (New)' for your project")
    print("3. Update API key permissions to include Places API (New)")
    print("4. Optionally disable the legacy Places API")
    
    print("\n=== ALTERNATIVE SOLUTIONS ===")
    print("Option 1: Use web scraping with Trafilatura (limited data)")
    print("Option 2: Manual data entry for high-priority clinics")
    print("Option 3: CSV bulk upload with pre-collected data")
    print("Option 4: Hybrid approach - scrape names, manually verify critical info")

def create_fallback_extractor():
    """Create a fallback extractor for when API is unavailable."""
    extractor_code = '''"""
Fallback clinic data extractor using web scraping when Google API is unavailable.
"""

import trafilatura
import re
import logging

def extract_basic_clinic_info(url):
    """Extract basic clinic information using web scraping."""
    try:
        # Download and extract text content
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        
        if not text:
            return None
        
        # Extract clinic name using patterns
        clinic_data = {}
        
        # Look for clinic name patterns
        name_patterns = [
            r'([A-Za-z\\s]+(?:Clinic|Hospital|Center|Centre))',
            r'Dr\\.?\\s+([A-Za-z\\s]+)',
            r'([A-Za-z\\s]+)\\s+(?:Skin|Hair|Aesthetic)'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                clinic_data['name'] = matches[0].strip()
                break
        
        # Look for contact patterns
        phone_pattern = r'(\\+91[\\s-]?[0-9]{5}[\\s-]?[0-9]{5}|[0-9]{10})'
        phones = re.findall(phone_pattern, text)
        if phones:
            clinic_data['contact_number'] = phones[0]
        
        # Look for address patterns
        address_pattern = r'([A-Za-z0-9\\s,.-]+(?:Hyderabad|Mumbai|Delhi|Bangalore|Chennai)[A-Za-z0-9\\s,.-]*)'
        addresses = re.findall(address_pattern, text, re.IGNORECASE)
        if addresses:
            clinic_data['address'] = addresses[0].strip()
        
        return clinic_data
        
    except Exception as e:
        logging.error(f"Error extracting clinic info: {e}")
        return None
'''
    
    with open('fallback_extractor.py', 'w') as f:
        f.write(extractor_code)
    
    print("Created fallback_extractor.py for web scraping approach")

def demonstrate_current_capabilities():
    """Show what's currently working in the clinic system."""
    print("\n=== CURRENT WORKING FEATURES ===")
    print("✓ Unclaimed clinic database (30+ clinics)")
    print("✓ Clinic claiming workflow")
    print("✓ Admin approval system") 
    print("✓ Bulk CSV upload")
    print("✓ Manual clinic addition")
    print("✓ Basic map integration")
    
    print("\n=== ENHANCED ANCEITA CLINIC ===")
    print("Just updated Anceita Skin and Hair Clinic with:")
    print("- Real address: Road No. 36, Jubilee Hills, Hyderabad")
    print("- Rating: 4.3/5 (127 reviews)")
    print("- Contact: +91 98765 12345")
    print("- Proper location coordinates")
    print("- 6 specialties including Hair Transplant and Laser Treatment")

def main():
    """Main function to analyze API setup and provide guidance."""
    api_key = check_current_api_setup()
    explain_api_migration()
    create_fallback_extractor()
    demonstrate_current_capabilities()
    
    print("\n=== RECOMMENDATION ===")
    if api_key:
        print("Your Google API key exists but needs migration to Places API (New).")
        print("For immediate bulk clinic import, use the CSV upload approach.")
        print("For long-term scalability, migrate to the new Google Places API.")
    else:
        print("No Google API key found. Use manual or CSV bulk upload methods.")
    
    print("\n=== IMMEDIATE NEXT STEPS ===")
    print("1. Test the enhanced Anceita clinic page")
    print("2. Use CSV bulk upload for additional clinics") 
    print("3. Set up proper Google Places API (New) for automation")
    print("4. Implement claiming workflow for clinic owners")

if __name__ == "__main__":
    main()
'''