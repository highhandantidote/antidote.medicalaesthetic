"""
Add test packages to the database for testing the enhanced package detail functionality.
This script creates realistic Korean-style treatment packages with all enhanced fields.
"""
import os
import json
from datetime import datetime
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def add_test_packages():
    """Add comprehensive test packages with all enhanced fields."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First ensure we have a test clinic
    cursor.execute("""
        INSERT INTO clinics (name, city, contact_number, whatsapp_number, address, overall_rating, total_reviews, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (name) DO UPDATE SET
            contact_number = EXCLUDED.contact_number,
            updated_at = EXCLUDED.updated_at
        RETURNING id
    """, (
        'Premium Beauty Clinic Seoul',
        'Mumbai', 
        '+91 98765 43210',
        '+91 98765 43210',
        '123 Beauty Street, Bandra West, Mumbai - 400050',
        4.8,
        156,
        datetime.now(),
        datetime.now()
    ))
    
    clinic_result = cursor.fetchone()
    clinic_id = clinic_result['id']
    
    # Test packages with comprehensive enhanced fields
    test_packages = [
        {
            'title': 'Premium Korean Glass Skin Facial',
            'slug': 'premium-korean-glass-skin-facial',
            'description': 'Advanced multi-step Korean facial treatment for achieving glass skin effect with hydrating serums and LED therapy',
            'procedure_info': 'Professional Korean-style facial using premium K-beauty products and advanced techniques for luminous, porcelain-like skin',
            'price_actual': Decimal('45000.00'),
            'price_discounted': Decimal('35000.00'),
            'discount_percentage': 22,
            'category': 'Facial Rejuvenation',
            'tags': 'Korean facial, glass skin, hydrating, LED therapy',
            'side_effects': 'Mild redness may occur for 1-2 hours post-treatment',
            'recommended_for': 'All skin types seeking hydration and glow',
            'downtime': '0-2 hours',
            'duration': '90 minutes',
            'anesthetic': 'None required',
            'results': 'Immediate glow with progressive improvement over 7-14 days',
            'vat_included': True,
            'terms_conditions': 'Valid for 6 months from purchase date. Cannot be combined with other offers.',
            'key_highlights': json.dumps({
                'instant_glow': 'Immediate radiant complexion',
                'deep_hydration': '72-hour moisture retention',
                'pore_minimizing': 'Visible pore size reduction',
                'anti_aging': 'Collagen stimulation for firmer skin'
            }),
            'procedure_breakdown': json.dumps([
                {'step': 'Deep Cleansing', 'duration': '15 min', 'price': 5000},
                {'step': 'Exfoliation & Extraction', 'duration': '20 min', 'price': 8000},
                {'step': 'Hydrating Mask', 'duration': '25 min', 'price': 12000},
                {'step': 'LED Light Therapy', 'duration': '20 min', 'price': 7000},
                {'step': 'Serum Application', 'duration': '10 min', 'price': 3000}
            ]),
            'results_gallery': json.dumps([
                {
                    'before_image': '/static/images/results/glass_skin_before_1.jpg',
                    'after_image': '/static/images/results/glass_skin_after_1.jpg',
                    'description': '3 weeks post-treatment showing enhanced glow'
                },
                {
                    'before_image': '/static/images/results/glass_skin_before_2.jpg',
                    'after_image': '/static/images/results/glass_skin_after_2.jpg',
                    'description': '1 month results with improved texture'
                }
            ]),
            'about_procedure': 'Our signature Korean Glass Skin Facial combines traditional K-beauty techniques with modern technology to achieve the coveted glass skin effect. This comprehensive treatment includes deep cleansing, gentle exfoliation, hydrating masks, and LED therapy.',
            'vat_amount': Decimal('6300.00'),
            'anesthetic_type': 'None',
            'aftercare_kit': 'Includes: Hydrating mist, gentle cleanser, and SPF 50 sunscreen',
            'downtime_description': 'Minimal to no downtime. Slight redness may occur immediately after treatment.',
            'precautions': 'Avoid direct sun exposure for 24 hours. Use provided SPF religiously.',
            'whatsapp_number': '+91 98765 43210',
            'custom_phone_number': '+91 98765 43210',
            'chat_message_template': 'Hi! I\'m interested in the Korean Glass Skin Facial. Can you share more details about the treatment process?',
            'call_message_template': 'Hello, I\'d like to book a consultation for the Korean Glass Skin Facial package.',
            'clinic_latitude': 19.0596,
            'clinic_longitude': 72.8295
        },
        {
            'title': 'Advanced Korean Rhinoplasty Package',
            'slug': 'advanced-korean-rhinoplasty-package',
            'description': 'Comprehensive nose reshaping surgery using advanced Korean techniques for natural-looking results',
            'procedure_info': 'State-of-the-art rhinoplasty procedure following Korean aesthetic principles for harmonious facial balance',
            'price_actual': Decimal('450000.00'),
            'price_discounted': Decimal('380000.00'),
            'discount_percentage': 16,
            'category': 'Rhinoplasty',
            'tags': 'Korean rhinoplasty, nose surgery, facial harmony, permanent results',
            'side_effects': 'Swelling, bruising, temporary numbness around nose area',
            'recommended_for': 'Adults 18+ seeking nose reshaping for aesthetic or functional improvement',
            'downtime': '2-3 weeks',
            'duration': '3-4 hours',
            'anesthetic': 'General anesthesia',
            'results': 'Final results visible after 6-12 months with initial improvement at 2-3 weeks',
            'vat_included': True,
            'terms_conditions': 'Includes pre-operative consultation, surgery, post-op care for 6 months.',
            'key_highlights': json.dumps({
                'korean_technique': 'Advanced Korean surgical methods',
                'natural_results': 'Subtle, harmonious enhancement',
                'experienced_surgeon': 'Board-certified plastic surgeon',
                'comprehensive_care': '6-month follow-up included'
            }),
            'procedure_breakdown': json.dumps([
                {'step': 'Pre-operative Consultation', 'duration': '60 min', 'price': 15000},
                {'step': 'Anesthesia Administration', 'duration': '30 min', 'price': 25000},
                {'step': 'Surgical Procedure', 'duration': '180 min', 'price': 280000},
                {'step': 'Recovery & Monitoring', 'duration': '120 min', 'price': 35000},
                {'step': 'Post-op Care Package', 'duration': '6 months', 'price': 25000}
            ]),
            'results_gallery': json.dumps([
                {
                    'before_image': '/static/images/results/rhinoplasty_before_1.jpg',
                    'after_image': '/static/images/results/rhinoplasty_after_1.jpg',
                    'description': '6 months post-surgery showing refined bridge'
                },
                {
                    'before_image': '/static/images/results/rhinoplasty_before_2.jpg',
                    'after_image': '/static/images/results/rhinoplasty_after_2.jpg',
                    'description': '1 year results with improved tip definition'
                }
            ]),
            'about_procedure': 'Our Korean Rhinoplasty technique focuses on creating natural-looking results that enhance facial harmony. Using advanced surgical methods and 3D imaging, we customize each procedure to suit individual facial features.',
            'vat_amount': Decimal('68400.00'),
            'anesthetic_type': 'General Anesthesia',
            'aftercare_kit': 'Includes: Nasal splint, pain medication, antibiotic ointment, care instructions',
            'downtime_description': 'Initial recovery 7-10 days with splint removal. Swelling subsides over 2-3 weeks.',
            'precautions': 'No strenuous activity for 4 weeks. Avoid sun exposure. Follow all post-op instructions.',
            'whatsapp_number': '+91 98765 43210',
            'custom_phone_number': '+91 98765 43210',
            'chat_message_template': 'Hi! I\'m considering rhinoplasty and would like to know more about your Korean technique approach.',
            'call_message_template': 'Hello, I\'d like to schedule a consultation for rhinoplasty surgery.',
            'clinic_latitude': 19.0596,
            'clinic_longitude': 72.8295
        },
        {
            'title': 'Korean Double Eyelid Surgery',
            'slug': 'korean-double-eyelid-surgery',
            'description': 'Precise double eyelid creation using Korean techniques for natural-looking, youthful eyes',
            'procedure_info': 'Advanced blepharoplasty procedure creating natural double eyelid fold for enhanced eye appearance',
            'price_actual': Decimal('85000.00'),
            'price_discounted': Decimal('68000.00'),
            'discount_percentage': 20,
            'category': 'Eyelid Surgery',
            'tags': 'double eyelid, Korean surgery, eye enhancement, blepharoplasty',
            'side_effects': 'Temporary swelling, bruising, dry eyes for 1-2 weeks',
            'recommended_for': 'Adults seeking enhanced eye definition and youthful appearance',
            'downtime': '7-14 days',
            'duration': '60-90 minutes',
            'anesthetic': 'Local anesthesia with sedation',
            'results': 'Natural double eyelid fold with enhanced eye shape',
            'vat_included': True,
            'terms_conditions': 'Includes consultation, surgery, and 3-month follow-up care.',
            'key_highlights': json.dumps({
                'minimally_invasive': 'Advanced suture technique',
                'quick_recovery': 'Faster healing process',
                'natural_results': 'Subtle, authentic appearance',
                'experienced_team': 'Specialized eye surgery experts'
            }),
            'procedure_breakdown': json.dumps([
                {'step': 'Consultation & Marking', 'duration': '30 min', 'price': 8000},
                {'step': 'Anesthesia', 'duration': '15 min', 'price': 12000},
                {'step': 'Surgical Procedure', 'duration': '60 min', 'price': 40000},
                {'step': 'Recovery & Care', 'duration': '30 min', 'price': 8000}
            ]),
            'results_gallery': json.dumps([
                {
                    'before_image': '/static/images/results/eyelid_before_1.jpg',
                    'after_image': '/static/images/results/eyelid_after_1.jpg',
                    'description': '3 weeks post-surgery showing natural fold'
                },
                {
                    'before_image': '/static/images/results/eyelid_before_2.jpg',
                    'after_image': '/static/images/results/eyelid_after_2.jpg',
                    'description': '2 months results with enhanced eye definition'
                }
            ]),
            'about_procedure': 'Korean Double Eyelid Surgery creates a natural-looking crease that enhances eye definition. Our technique ensures symmetrical results that complement your facial features.',
            'vat_amount': Decimal('12240.00'),
            'anesthetic_type': 'Local with Sedation',
            'aftercare_kit': 'Includes: Eye drops, cold compress, healing ointment, care instructions',
            'downtime_description': 'Swelling peaks at 2-3 days, subsides over 1-2 weeks. Stitches removed after 5-7 days.',
            'precautions': 'Keep eyes clean and dry. Avoid makeup for 1 week. No heavy lifting for 2 weeks.',
            'whatsapp_number': '+91 98765 43210',
            'custom_phone_number': '+91 98765 43210',
            'chat_message_template': 'Hi! I\'m interested in double eyelid surgery. Can you provide more information about the Korean technique?',
            'call_message_template': 'Hello, I\'d like to book a consultation for double eyelid surgery.',
            'clinic_latitude': 19.0596,
            'clinic_longitude': 72.8295
        },
        {
            'title': 'Korean V-Line Jaw Contouring',
            'slug': 'korean-v-line-jaw-contouring',
            'description': 'Advanced jaw contouring surgery to create the coveted Korean V-line facial shape',
            'procedure_info': 'Comprehensive jaw reduction and contouring procedure for achieving refined facial proportions',
            'price_actual': Decimal('650000.00'),
            'price_discounted': Decimal('520000.00'),
            'discount_percentage': 20,
            'category': 'Jawline Contouring',
            'tags': 'V-line surgery, jaw contouring, facial reshaping, Korean beauty',
            'side_effects': 'Swelling, bruising, temporary numbness, difficulty chewing initially',
            'recommended_for': 'Adults with square or wide jawline seeking refined facial contour',
            'downtime': '3-4 weeks',
            'duration': '4-5 hours',
            'anesthetic': 'General anesthesia',
            'results': 'Refined V-shaped jawline with improved facial harmony',
            'vat_included': True,
            'terms_conditions': 'Includes pre-op imaging, surgery, hospital stay, and 6-month follow-up.',
            'key_highlights': json.dumps({
                'v_line_effect': 'Creates coveted V-shaped jawline',
                '3d_planning': 'Advanced surgical planning technology',
                'expert_surgeon': 'Specialized facial contouring expert',
                'comprehensive_care': 'Full recovery support included'
            }),
            'procedure_breakdown': json.dumps([
                {'step': '3D Imaging & Planning', 'duration': '90 min', 'price': 25000},
                {'step': 'Anesthesia & Preparation', 'duration': '60 min', 'price': 35000},
                {'step': 'Surgical Contouring', 'duration': '240 min', 'price': 400000},
                {'step': 'Recovery & Monitoring', 'duration': '180 min', 'price': 60000}
            ]),
            'results_gallery': json.dumps([
                {
                    'before_image': '/static/images/results/vline_before_1.jpg',
                    'after_image': '/static/images/results/vline_after_1.jpg',
                    'description': '6 months post-surgery showing refined jawline'
                },
                {
                    'before_image': '/static/images/results/vline_before_2.jpg',
                    'after_image': '/static/images/results/vline_after_2.jpg',
                    'description': '1 year results with improved facial proportions'
                }
            ]),
            'about_procedure': 'Korean V-Line surgery reshapes the jawbone to create a more refined, feminine facial contour. Using advanced techniques and 3D planning, we achieve natural-looking results that enhance your facial harmony.',
            'vat_amount': Decimal('93600.00'),
            'anesthetic_type': 'General Anesthesia',
            'aftercare_kit': 'Includes: Compression garment, pain medication, liquid diet guide, care instructions',
            'downtime_description': 'Initial swelling peaks at 3-5 days. Major swelling subsides in 2-3 weeks.',
            'precautions': 'Liquid diet for 1 week, soft foods for 2-3 weeks. No strenuous activity for 6 weeks.',
            'whatsapp_number': '+91 98765 43210',
            'custom_phone_number': '+91 98765 43210',
            'chat_message_template': 'Hi! I\'m interested in V-line jaw contouring. Can you provide details about the procedure and recovery?',
            'call_message_template': 'Hello, I\'d like to schedule a consultation for V-line jaw contouring surgery.',
            'clinic_latitude': 19.0596,
            'clinic_longitude': 72.8295
        },
        {
            'title': 'Korean Skin Brightening Treatment',
            'slug': 'korean-skin-brightening-treatment',
            'description': 'Advanced multi-session treatment for achieving radiant, even-toned skin using Korean skincare technology',
            'procedure_info': 'Comprehensive brightening protocol with vitamin C, glutathione, and advanced laser technology',
            'price_actual': Decimal('75000.00'),
            'price_discounted': Decimal('60000.00'),
            'discount_percentage': 20,
            'category': 'Skin Rejuvenation',
            'tags': 'skin brightening, pigmentation, Korean skincare, laser treatment',
            'side_effects': 'Mild redness, temporary dryness, slight peeling',
            'recommended_for': 'All skin types with pigmentation concerns and dullness',
            'downtime': '2-3 days',
            'duration': '6 sessions over 3 months',
            'anesthetic': 'Topical numbing cream',
            'results': 'Brighter, more even skin tone with reduced pigmentation',
            'vat_included': True,
            'terms_conditions': 'Package includes 6 sessions. Must be completed within 6 months.',
            'key_highlights': json.dumps({
                'advanced_technology': 'Latest Korean laser systems',
                'customized_protocol': 'Tailored to individual skin needs',
                'progressive_results': 'Gradual, natural improvement',
                'maintenance_plan': 'Long-term skin health strategy'
            }),
            'procedure_breakdown': json.dumps([
                {'step': 'Skin Analysis', 'duration': '30 min', 'price': 5000},
                {'step': 'Deep Cleansing', 'duration': '20 min', 'price': 3000},
                {'step': 'Laser Treatment', 'duration': '45 min', 'price': 25000},
                {'step': 'Vitamin Infusion', 'duration': '30 min', 'price': 15000},
                {'step': 'Hydrating Mask', 'duration': '25 min', 'price': 7000},
                {'step': 'Post-care Application', 'duration': '10 min', 'price': 5000}
            ]),
            'results_gallery': json.dumps([
                {
                    'before_image': '/static/images/results/brightening_before_1.jpg',
                    'after_image': '/static/images/results/brightening_after_1.jpg',
                    'description': 'After 3 sessions showing improved brightness'
                },
                {
                    'before_image': '/static/images/results/brightening_before_2.jpg',
                    'after_image': '/static/images/results/brightening_after_2.jpg',
                    'description': 'Final results after 6 sessions'
                }
            ]),
            'about_procedure': 'Our Korean Skin Brightening Treatment combines advanced laser technology with potent brightening agents to achieve luminous, even-toned skin. The progressive approach ensures natural-looking results.',
            'vat_amount': Decimal('10800.00'),
            'anesthetic_type': 'Topical Numbing',
            'aftercare_kit': 'Includes: Brightening serum, gentle cleanser, SPF 50, hydrating cream',
            'downtime_description': 'Minimal downtime with possible mild redness for 24-48 hours post-treatment.',
            'precautions': 'Strict sun protection required. Use only recommended skincare products during treatment.',
            'whatsapp_number': '+91 98765 43210',
            'custom_phone_number': '+91 98765 43210',
            'chat_message_template': 'Hi! I\'m interested in the skin brightening treatment. Can you explain the process and expected results?',
            'call_message_template': 'Hello, I\'d like to book a consultation for the Korean skin brightening treatment package.',
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
        
        insert_sql = f"""
            INSERT INTO packages ({column_names})
            VALUES ({placeholders})
            ON CONFLICT (slug) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                price_actual = EXCLUDED.price_actual,
                price_discounted = EXCLUDED.price_discounted,
                updated_at = EXCLUDED.updated_at
        """
        
        cursor.execute(insert_sql, list(package_data.values()))
        print(f"Added package: {package_data['title']}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Successfully added {len(test_packages)} test packages to the database!")

if __name__ == '__main__':
    add_test_packages()