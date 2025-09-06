#!/usr/bin/env python3
"""
Add packages for ZOH Aesthetic Clinic from CSV file
CSV format: package_name,treatment_name,price,discount
"""

import os
import sys
import csv
from datetime import datetime
from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")

def create_slug(title, clinic_id=196):
    """Create a unique URL-friendly slug from title"""
    base_slug = title.lower().replace(' ', '-').replace('&', 'and')
    base_slug = ''.join(c for c in base_slug if c.isalnum() or c == '-')
    # Add clinic identifier to make it unique
    slug = f"zoh-{base_slug}"
    return slug

def add_packages_from_csv(csv_file_path):
    """Add packages from CSV file"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return
    
    engine = create_engine(DATABASE_URL)
    clinic_id = 196  # ZOH Aesthetic Clinic ID
    packages_added = 0
    
    print(f"Reading packages from: {csv_file_path}")
    print("=" * 50)
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Extract data from CSV
                    package_name = row['package_name'].strip()
                    treatment_name = row['treatment_name'].strip()
                    price = float(row['price'])
                    discount_pct = int(row.get('discount', 0))
                    
                    if not package_name or not treatment_name or price <= 0:
                        print(f"⚠️  Skipping invalid row: {row}")
                        continue
                    
                    # Calculate discounted price
                    discounted_price = price * (1 - discount_pct / 100) if discount_pct > 0 else None
                    
                    # Generate unique slug for ZOH clinic
                    slug = create_slug(package_name, clinic_id)
                    
                    # Create description
                    description = f"Professional {treatment_name} treatment at ZOH Aesthetic Clinic, Nallagandla. "
                    if discount_pct > 0:
                        description += f"Special offer with {discount_pct}% discount! "
                    description += f"Expert care with modern techniques and personalized treatment plans."
                    
                    # Auto-categorize based on treatment name
                    treatment_lower = treatment_name.lower()
                    if any(word in treatment_lower for word in ['botox', 'filler', 'injectable', 'dermal']):
                        category = 'Non-Surgical Treatments'
                    elif any(word in treatment_lower for word in ['laser', 'ipl', 'light', 'rf']):
                        category = 'Laser Treatments'
                    elif any(word in treatment_lower for word in ['facial', 'peel', 'hydra', 'clean']):
                        category = 'Skin Treatments'
                    elif any(word in treatment_lower for word in ['hair', 'transplant', 'fue', 'prp']):
                        category = 'Hair Treatments'
                    elif any(word in treatment_lower for word in ['surgery', 'lift', 'augmentation', 'plastic']):
                        category = 'Surgical Procedures'
                    elif any(word in treatment_lower for word in ['thread', 'pdos', 'lift']):
                        category = 'Thread Lift'
                    else:
                        category = 'General Aesthetic'
                    
                    # Create about_procedure text
                    about_procedure = f"""
                    <h3>About {treatment_name}</h3>
                    <p>Our {treatment_name} treatment is performed by experienced professionals at ZOH Aesthetic Clinic using the latest techniques and equipment. We ensure safe, effective, and comfortable procedures with excellent results.</p>
                    
                    <h4>Treatment Benefits:</h4>
                    <ul>
                    <li>Professional medical expertise</li>
                    <li>State-of-the-art equipment</li>
                    <li>Personalized treatment approach</li>
                    <li>Safe and hygienic environment</li>
                    <li>Follow-up care and support</li>
                    </ul>
                    
                    <h4>Why Choose ZOH Aesthetic Clinic?</h4>
                    <ul>
                    <li>Highly rated clinic (4.9/5 stars)</li>
                    <li>Experienced medical professionals</li>
                    <li>Modern facilities in Nallagandla</li>
                    <li>Comprehensive aesthetic solutions</li>
                    </ul>
                    """
                    
                    # Insert package
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
                        'recommended_for': 'Adults seeking aesthetic enhancement and improvement',
                        'downtime': 'Minimal to no downtime required',
                        'duration': '30-90 minutes depending on treatment',
                        'precautions': 'Follow post-treatment care instructions provided',
                        'is_active': True,
                        'created_at': datetime.utcnow(),
                        'clinic_address': "3rd Floor, AJ Nidhi, Aparna Cyberlife Rd, Nallagandla, Hyderabad",
                        'whatsapp_number': "9000112433",
                        'clinic_latitude': 17.4695542,
                        'clinic_longitude': 78.3097463
                    })
                    
                    package_id = result.fetchone()[0]
                    print(f"✅ Added: {package_name} - ₹{price:,.0f} ({discount_pct}% off) - ID: {package_id}")
                    packages_added += 1
            
            trans.commit()
            print(f"\n🎉 Successfully added {packages_added} packages to ZOH Aesthetic Clinic!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error adding packages: {e}")
            raise

def create_sample_csv():
    """Create a sample CSV file for reference"""
    sample_data = [
        ['package_name', 'treatment_name', 'price', 'discount'],
        ['Premium Botox Treatment', 'Botox Injections', '12000', '15'],
        ['HydraFacial Glow Package', 'HydraFacial Treatment', '8500', '20'],
        ['Laser Hair Removal - Full Body', 'Diode Laser Hair Removal', '45000', '25'],
        ['Dermal Filler Lips', 'Hyaluronic Acid Lip Fillers', '18000', '10'],
        ['Chemical Peel Treatment', 'Glycolic Acid Peel', '6500', '0'],
        ['PRP Hair Treatment', 'Platelet Rich Plasma Therapy', '15000', '20']
    ]
    
    with open('zoh_packages_sample.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(sample_data)
    
    print("✅ Created sample CSV file: zoh_packages_sample.csv")
    print("Edit this file with your actual package data!")

if __name__ == "__main__":
    print("ZOH Aesthetic Clinic - CSV Package Import Tool")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        add_packages_from_csv(csv_file)
    else:
        print("Usage options:")
        print("1. python add_packages_from_csv.py your_file.csv")
        print("2. Create sample CSV file first")
        
        choice = input("\nCreate sample CSV file? (y/n): ").lower().strip()
        if choice == 'y':
            create_sample_csv()
            print("\nNow edit 'zoh_packages_sample.csv' with your data and run:")
            print("python add_packages_from_csv.py zoh_packages_sample.csv")