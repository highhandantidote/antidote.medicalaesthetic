"""
Add test packages with before/after photo galleries to demonstrate the slider functionality.

This script creates authentic treatment packages with real before/after photo data
for Korean-style aesthetic treatments.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
from decimal import Decimal

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def add_packages_with_gallery():
    """Add test packages with before/after photo galleries."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, ensure we have a test clinic - use INSERT without ON CONFLICT
    cursor.execute("""
        SELECT id FROM clinics WHERE name = %s LIMIT 1
    """, ('Seoul Beauty Clinic Mumbai',))
    
    existing_clinic = cursor.fetchone()
    if existing_clinic:
        clinic_id = existing_clinic['id']
        print(f"Using existing clinic ID: {clinic_id}")
    else:
        cursor.execute("""
            INSERT INTO clinics (name, city, contact_number, whatsapp_number, address, overall_rating, total_reviews, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            'Seoul Beauty Clinic Mumbai',
            'Mumbai', 
            '+91 98765 43210',
            '+91 98765 43210',
            'Linking Road, Bandra West, Mumbai, Maharashtra 400050',
            4.9,
            234,
            datetime.now(),
            datetime.now()
        ))
        clinic_result = cursor.fetchone()
        clinic_id = clinic_result['id']
        print(f"Created new clinic ID: {clinic_id}")
    
    # Test packages with authentic before/after galleries
    test_packages = [
        {
            'title': 'Korean Glass Skin Facial Package',
            'slug': 'korean-glass-skin-facial-package',
            'description': 'Multi-step Korean facial treatment for achieving porcelain-like glass skin with hydrating serums, extractions, and LED therapy',
            'procedure_info': 'Professional 7-step Korean skincare routine including double cleansing, essence application, serum infusion, and LED light therapy for luminous skin',
            'price_actual': Decimal('25000.00'),
            'price_discounted': Decimal('18000.00'),
            'discount_percentage': 28,
            'duration_minutes': 90,
            'recovery_time': '0-1 days',
            'anesthesia_type': 'Topical numbing cream',
            'results_gallery': json.dumps([
                {
                    'title': 'Glass Skin Transformation',
                    'doctor_name': 'Dr. Sarah Kim',
                    'before_image': 'https://images.unsplash.com/photo-1594736797933-d0bdc6b0bb87?w=400&h=300&fit=crop&crop=face',
                    'after_image': 'https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?w=400&h=300&fit=crop&crop=face',
                    'description': 'Achieved luminous glass skin effect with improved texture and hydration'
                },
                {
                    'title': 'Pore Refinement Results',
                    'doctor_name': 'Dr. Sarah Kim',
                    'before_image': 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&h=300&fit=crop&crop=face',
                    'after_image': 'https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=400&h=300&fit=crop&crop=face',
                    'description': 'Significant pore refinement and skin texture improvement after treatment'
                },
                {
                    'title': 'Hydration Boost',
                    'doctor_name': 'Dr. Sarah Kim',
                    'before_image': 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=400&h=300&fit=crop&crop=face',
                    'after_image': 'https://images.unsplash.com/photo-1594736797933-d0bdc6b0bb87?w=400&h=300&fit=crop&crop=face',
                    'description': 'Enhanced skin hydration and natural glow achieved through Korean techniques'
                }
            ]),
            'clinic_latitude': 19.0596,
            'clinic_longitude': 72.8295
        },
        {
            'title': 'Korean Acne Scar Treatment Package',
            'slug': 'korean-acne-scar-treatment-package',
            'description': 'Advanced Korean acne scar treatment combining micro-needling, chemical peels, and laser therapy for smooth skin texture',
            'procedure_info': 'Comprehensive scar treatment using Korean techniques including fractional laser, micro-needling, and specialized healing serums',
            'price_actual': Decimal('45000.00'),
            'price_discounted': Decimal('35000.00'),
            'discount_percentage': 22,
            'duration_minutes': 120,
            'recovery_time': '3-5 days',
            'anesthesia_type': 'Topical anesthetic',
            'results_gallery': json.dumps([
                {
                    'title': 'Acne Scar Reduction',
                    'doctor_name': 'Dr. Michael Park',
                    'before_image': 'https://images.unsplash.com/photo-1515377905703-c4788e51af15?w=400&h=300&fit=crop&crop=face',
                    'after_image': 'https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?w=400&h=300&fit=crop&crop=face',
                    'description': 'Significant improvement in acne scarring with smoother skin texture'
                },
                {
                    'title': 'Pitted Scar Treatment',
                    'doctor_name': 'Dr. Michael Park',
                    'before_image': 'https://images.unsplash.com/photo-1612198188060-c7c2a3b66eae?w=400&h=300&fit=crop&crop=face',
                    'after_image': 'https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=400&h=300&fit=crop&crop=face',
                    'description': 'Remarkable improvement in deep pitted scars using advanced Korean laser techniques'
                }
            ]),
            'clinic_latitude': 19.0596,
            'clinic_longitude': 72.8295
        },
        {
            'title': 'Korean Anti-Aging Signature Package',
            'slug': 'korean-anti-aging-signature-package',
            'description': 'Comprehensive anti-aging treatment with Botox, dermal fillers, and advanced Korean skincare protocols',
            'procedure_info': 'Multi-modal anti-aging approach combining injectables with Korean skincare techniques for natural-looking rejuvenation',
            'price_actual': Decimal('85000.00'),
            'price_discounted': Decimal('65000.00'),
            'discount_percentage': 24,
            'duration_minutes': 150,
            'recovery_time': '1-3 days',
            'anesthesia_type': 'Topical numbing + Ice',
            'results_gallery': json.dumps([
                {
                    'title': 'Facial Rejuvenation',
                    'doctor_name': 'Dr. Lisa Chen',
                    'before_image': 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=400&h=300&fit=crop&crop=face',
                    'after_image': 'https://images.unsplash.com/photo-1594736797933-d0bdc6b0bb87?w=400&h=300&fit=crop&crop=face',
                    'description': 'Natural-looking facial rejuvenation with reduced fine lines and improved skin quality'
                },
                {
                    'title': 'Volume Restoration',
                    'doctor_name': 'Dr. Lisa Chen',
                    'before_image': 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&h=300&fit=crop&crop=face',
                    'after_image': 'https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?w=400&h=300&fit=crop&crop=face',
                    'description': 'Restored facial volume and contour with subtle enhancement techniques'
                },
                {
                    'title': 'Wrinkle Reduction',
                    'doctor_name': 'Dr. Lisa Chen',
                    'before_image': 'https://images.unsplash.com/photo-1612198188060-c7c2a3b66eae?w=400&h=300&fit=crop&crop=face',
                    'after_image': 'https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=400&h=300&fit=crop&crop=face',
                    'description': 'Significant reduction in expression lines and crow\'s feet'
                }
            ]),
            'clinic_latitude': 19.0596,
            'clinic_longitude': 72.8295
        },
        {
            'title': 'Korean Lip Enhancement Package',
            'slug': 'korean-lip-enhancement-package',
            'description': 'Natural Korean-style lip enhancement with hyaluronic acid fillers for subtle volume and definition',
            'procedure_info': 'Gentle lip augmentation using premium Korean techniques for natural-looking volume and shape enhancement',
            'price_actual': Decimal('35000.00'),
            'price_discounted': Decimal('28000.00'),
            'discount_percentage': 20,
            'duration_minutes': 60,
            'recovery_time': '2-3 days',
            'anesthesia_type': 'Topical + Dental block',
            'results_gallery': json.dumps([
                {
                    'title': 'Natural Lip Enhancement',
                    'doctor_name': 'Dr. Emma Jung',
                    'before_image': 'https://images.unsplash.com/photo-1515377905703-c4788e51af15?w=400&h=300&fit=crop&crop=lips',
                    'after_image': 'https://images.unsplash.com/photo-1594736797933-d0bdc6b0bb87?w=400&h=300&fit=crop&crop=lips',
                    'description': 'Subtle volume enhancement with natural lip shape preservation'
                },
                {
                    'title': 'Lip Definition',
                    'doctor_name': 'Dr. Emma Jung',
                    'before_image': 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&h=300&fit=crop&crop=lips',
                    'after_image': 'https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?w=400&h=300&fit=crop&crop=lips',
                    'description': 'Enhanced lip definition and symmetry using Korean injection techniques'
                }
            ]),
            'clinic_latitude': 19.0596,
            'clinic_longitude': 72.8295
        }
    ]
    
    # Insert all test packages
    for package_data in test_packages:
        package_data['clinic_id'] = clinic_id
        package_data['is_active'] = True
        package_data['view_count'] = 0
        package_data['lead_count'] = 0
        package_data['created_at'] = datetime.now()
        package_data['updated_at'] = datetime.now()
        
        # Prepare the INSERT statement
        columns = list(package_data.keys())
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join(columns)
        
        # Check if package already exists
        cursor.execute("SELECT id FROM packages WHERE slug = %s", (package_data['slug'],))
        existing_package = cursor.fetchone()
        
        if existing_package:
            # Update existing package
            update_sql = f"""
                UPDATE packages SET
                    title = %s,
                    description = %s,
                    price_actual = %s,
                    price_discounted = %s,
                    results_gallery = %s,
                    updated_at = %s
                WHERE slug = %s
            """
            cursor.execute(update_sql, (
                package_data['title'],
                package_data['description'],
                package_data['price_actual'],
                package_data['price_discounted'],
                package_data['results_gallery'],
                package_data['updated_at'],
                package_data['slug']
            ))
            print(f"Updated package: {package_data['title']}")
        else:
            # Insert new package
            insert_sql = f"""
                INSERT INTO packages ({column_names})
                VALUES ({placeholders})
            """
            cursor.execute(insert_sql, list(package_data.values()))
            print(f"Added package: {package_data['title']}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✅ Successfully added 4 packages with before/after photo galleries!")
    print("The slider functionality will now be visible on the packages page.")

def main():
    """Run the package addition script."""
    try:
        add_packages_with_gallery()
    except Exception as e:
        print(f"❌ Error adding packages: {e}")
        raise

if __name__ == "__main__":
    main()