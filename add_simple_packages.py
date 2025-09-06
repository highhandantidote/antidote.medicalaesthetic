#!/usr/bin/env python3
"""
Simple Package Addition Script for ZOH Aesthetic Clinic
Add packages with minimal data: package name, treatment name, price, discount
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
import json

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not found!")
    sys.exit(1)

def create_slug(title):
    """Create a URL-friendly slug from title"""
    slug = title.lower().replace(' ', '-').replace('&', 'and')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    return slug

def add_packages_for_zoh_clinic(packages_data):
    """
    Add packages to ZOH Aesthetic Clinic
    
    packages_data should be a list of dictionaries with keys:
    - package_name: Display name of the package
    - treatment_name: Real medical treatment name
    - price: Original price (numeric)
    - discount: Discount percentage (0-100)
    """
    
    engine = create_engine(DATABASE_URL)
    clinic_id = 196  # ZOH Aesthetic Clinic ID
    
    print(f"Adding {len(packages_data)} packages for ZOH Aesthetic Clinic...")
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            for pkg in packages_data:
                # Extract data
                package_name = pkg['package_name'].strip()
                treatment_name = pkg['treatment_name'].strip()
                price = float(pkg['price'])
                discount_pct = int(pkg.get('discount', 0))
                
                # Calculate discounted price
                discounted_price = price * (1 - discount_pct / 100) if discount_pct > 0 else None
                
                # Generate slug
                slug = create_slug(package_name)
                
                # Create comprehensive description
                description = f"Professional {treatment_name} treatment at ZOH Aesthetic Clinic, Nallagandla. "
                if discount_pct > 0:
                    description += f"Special offer with {discount_pct}% discount! "
                description += f"Expert care with modern techniques and personalized treatment plans."
                
                # Determine category based on treatment name
                treatment_lower = treatment_name.lower()
                if any(word in treatment_lower for word in ['botox', 'filler', 'injectable']):
                    category = 'Non-Surgical Treatments'
                elif any(word in treatment_lower for word in ['laser', 'ipl', 'light']):
                    category = 'Laser Treatments'
                elif any(word in treatment_lower for word in ['facial', 'peel', 'hydra']):
                    category = 'Skin Treatments'
                elif any(word in treatment_lower for word in ['hair', 'transplant', 'fue']):
                    category = 'Hair Treatments'
                elif any(word in treatment_lower for word in ['surgery', 'lift', 'augmentation']):
                    category = 'Surgical Procedures'
                else:
                    category = 'General Aesthetic'
                
                # Create basic about_procedure text
                about_procedure = f"""
                <h3>About {treatment_name}</h3>
                <p>Our {treatment_name} treatment is performed by experienced professionals using the latest techniques and equipment. We ensure safe, effective, and comfortable procedures with excellent results.</p>
                
                <h4>Treatment Benefits:</h4>
                <ul>
                <li>Professional medical expertise</li>
                <li>Modern equipment and techniques</li>
                <li>Personalized treatment approach</li>
                <li>Safe and comfortable environment</li>
                <li>Follow-up care included</li>
                </ul>
                """
                
                # Insert package into database
                insert_sql = """
                    INSERT INTO packages (
                        clinic_id, title, slug, description, price_actual, price_discounted,
                        discount_percentage, category, about_procedure, 
                        recommended_for, downtime, duration, precautions,
                        is_active, created_at, clinic_address,
                        whatsapp_number, clinic_latitude, clinic_longitude
                    ) VALUES (
                        :clinic_id, :title, :slug, :description, :price_actual, :price_discounted,
                        :discount_percentage, :category, :about_procedure,
                        :recommended_for, :downtime, :duration, :precautions,
                        :is_active, :created_at, :clinic_address,
                        :whatsapp_number, :clinic_latitude, :clinic_longitude
                    ) RETURNING id
                """
                
                result = conn.execute(text(insert_sql), {
                    'clinic_id': clinic_id,
                    'title': package_name,
                    'slug': slug,
                    'description': description,
                    'price_actual': price,
                    'price_discounted': discounted_price,
                    'discount_percentage': discount_pct if discount_pct > 0 else None,
                    'category': category,
                    'about_procedure': about_procedure,
                    'recommended_for': 'Adults seeking aesthetic enhancement',
                    'downtime': 'Minimal to no downtime',
                    'duration': '30-60 minutes',
                    'precautions': 'Follow post-treatment care instructions',
                    'is_active': True,
                    'created_at': datetime.utcnow(),
                    'clinic_address': "3rd Floor, AJ Nidhi, Aparna Cyberlife Rd, Nallagandla, Hyderabad",
                    'whatsapp_number': "9000112433",
                    'clinic_latitude': 17.4695542,
                    'clinic_longitude': 78.3097463
                })
                
                package_id = result.fetchone()[0]
                print(f"✅ Added package: {package_name} (ID: {package_id})")
            
            # Commit all packages
            trans.commit()
            print(f"\n🎉 Successfully added {len(packages_data)} packages to ZOH Aesthetic Clinic!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error adding packages: {e}")
            raise

# Sample data format - you can modify this with your actual data
SAMPLE_PACKAGES = [
    {
        'package_name': 'Premium Botox Treatment',
        'treatment_name': 'Botox Injections',
        'price': 12000,
        'discount': 15
    },
    {
        'package_name': 'Hydrafacial Glow Package',
        'treatment_name': 'HydraFacial Treatment',
        'price': 8500,
        'discount': 20
    },
    {
        'package_name': 'Laser Hair Removal - Full Body',
        'treatment_name': 'Diode Laser Hair Removal',
        'price': 45000,
        'discount': 25
    }
]

if __name__ == "__main__":
    print("ZOH Aesthetic Clinic Package Addition Tool")
    print("=" * 50)
    
    # You can replace SAMPLE_PACKAGES with your actual data
    # Or modify the script to read from a CSV/JSON file
    
    choice = input("Use sample data? (y/n): ").lower().strip()
    
    if choice == 'y':
        add_packages_for_zoh_clinic(SAMPLE_PACKAGES)
    else:
        print("\nTo add your own packages, modify the SAMPLE_PACKAGES list in this script")
        print("Each package should have:")
        print("- package_name: Display name")
        print("- treatment_name: Medical treatment name")  
        print("- price: Original price (number)")
        print("- discount: Discount percentage (0-100)")
        print("\nExample:")
        print("""
        {
            'package_name': 'Premium Botox Treatment',
            'treatment_name': 'Botox Injections',
            'price': 12000,
            'discount': 15
        }
        """)