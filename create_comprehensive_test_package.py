"""
Create a comprehensive test package with all enhanced fields to demonstrate
the new package detail page functionality.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def create_comprehensive_test_package():
    """Create a comprehensive test package with all enhanced fields."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First, get a clinic to associate with the package
        cursor.execute("SELECT id, name, city FROM clinics WHERE is_verified = true LIMIT 1")
        clinic = cursor.fetchone()
        
        if not clinic:
            logger.error("No verified clinic found. Please create a clinic first.")
            return
        
        clinic_id = clinic['id']
        
        # Sample key highlights
        key_highlights = {
            "Dosage": "1ml Premium Hyaluronic Acid Filler",
            "Recovery": "2-3 days minimal downtime",
            "Duration": "45 minutes procedure time",
            "Results": "6-12 months lasting effects",
            "Type": "Non-surgical enhancement",
            "Anesthesia": "Topical numbing cream"
        }
        
        # Sample procedure breakdown
        procedure_breakdown = [
            {
                "name": "Complete Rhinoplasty Package",
                "price_actual": 185000,
                "price_discounted": 150000,
                "discount_percentage": 20,
                "description": "Main surgical rhinoplasty procedure with premium techniques"
            },
            {
                "name": "Pre & Post Consultation",
                "price_actual": 25000,
                "price_discounted": 20000,
                "discount_percentage": 20,
                "description": "Comprehensive consultation including 3D imaging and follow-up"
            },
            {
                "name": "Aftercare & Follow-up",
                "price_actual": 15000,
                "price_discounted": 12000,
                "discount_percentage": 20,
                "description": "Post-operative care including medications and check-ups"
            }
        ]
        
        # Sample results gallery
        results_gallery = [
            {
                "title": "Rhinoplasty - Natural Enhancement",
                "doctor_name": "Dr. Sam Morgan",
                "description": "I chose this procedure to achieve a more refined nasal profile that would compliment my facial features. My surgeon used precision technique to create natural-looking results that enhanced my overall appearance without looking artificial.",
                "before_image": "/static/images/demo/before1.jpg",
                "after_image": "/static/images/demo/after1.jpg"
            },
            {
                "title": "Rhinoplasty - Functional & Aesthetic",
                "doctor_name": "Dr. Park Ye-young",
                "description": "The procedure addressed both functional and aesthetic concerns. My breathing improved significantly while achieving the desired cosmetic enhancement. The recovery was smoother than expected.",
                "before_image": "/static/images/demo/before2.jpg",
                "after_image": "/static/images/demo/after2.jpg"
            },
            {
                "title": "Rhinoplasty - Premium Enhancement",
                "doctor_name": "Dr. Lee Min-ho",
                "description": "I wanted a subtle but noticeable improvement to my nose shape. The surgeon delivered exactly what I envisioned with minimal scarring and natural healing process.",
                "before_image": "/static/images/demo/before3.jpg",
                "after_image": "/static/images/demo/after3.jpg"
            }
        ]
        
        # Create the comprehensive package
        package_sql = """
            INSERT INTO packages (
                clinic_id, title, slug, description, price_actual, price_discounted, 
                discount_percentage, category, about_procedure, key_highlights, 
                procedure_breakdown, vat_amount, anesthetic_type, aftercare_kit,
                recommended_for, downtime, duration, downtime_description, precautions,
                results_gallery, whatsapp_number, custom_phone_number, 
                chat_message_template, call_message_template, clinic_latitude, 
                clinic_longitude, clinic_address, is_active, created_at
            ) VALUES (
                %(clinic_id)s, %(title)s, %(slug)s, %(description)s, %(price_actual)s, %(price_discounted)s,
                %(discount_percentage)s, %(category)s, %(about_procedure)s, %(key_highlights)s,
                %(procedure_breakdown)s, %(vat_amount)s, %(anesthetic_type)s, %(aftercare_kit)s,
                %(recommended_for)s, %(downtime)s, %(duration)s, %(downtime_description)s, %(precautions)s,
                %(results_gallery)s, %(whatsapp_number)s, %(custom_phone_number)s,
                %(chat_message_template)s, %(call_message_template)s, %(clinic_latitude)s,
                %(clinic_longitude)s, %(clinic_address)s, %(is_active)s, %(created_at)s
            ) RETURNING id
        """
        
        package_data = {
            'clinic_id': clinic_id,
            'title': 'Complete Rhinoplasty Package',
            'slug': 'complete-rhinoplasty-package',
            'description': 'Comprehensive rhinoplasty package designed for natural enhancement and improved facial harmony.',
            'price_actual': 225000.00,
            'price_discounted': 185000.00,
            'discount_percentage': 18,
            'category': 'Rhinoplasty',
            'about_procedure': '''Comprehensive complete rhinoplasty package using premium hyaluronic acid fillers and advanced injection technique for natural-looking results. Our expert practitioners use the latest technology and advanced cartilage sculpting techniques to minimize bruising and ensure optimal healing for the best possible outcomes.

The procedure involves precision reshaping of nasal cartilage and bone structure to achieve desired aesthetic goals while maintaining or improving nasal function. We utilize state-of-the-art 3D imaging technology to preview results and ensure patient satisfaction.

Our surgical approach combines traditional techniques with modern innovations, including ultrasonic bone sculpting and advanced suturing methods that promote faster healing and reduced scarring. The procedure is performed under controlled anesthesia with continuous monitoring for maximum safety.''',
            'key_highlights': json.dumps(key_highlights),
            'procedure_breakdown': json.dumps(procedure_breakdown),
            'vat_amount': 33300.00,  # 18% VAT on discounted price
            'anesthetic_type': 'General anesthesia with local numbing',
            'aftercare_kit': 'Premium healing package including antibiotics, pain relief, nasal splints, and cleaning solutions',
            'recommended_for': '''Individuals seeking natural nose enhancement and improved facial harmony. Those with functional breathing issues that can be addressed simultaneously. People looking to correct nasal asymmetry or refine nose shape from previous injuries.

Candidates who desire subtle, natural-looking results that complement their facial features. Suitable for first-time rhinoplasty patients as well as revision cases. Ideal for patients who have realistic expectations and are committed to proper post-operative care.

Best suited for individuals in good overall health who understand the recovery process and can dedicate time for proper healing. Not recommended for those with unrealistic expectations or serious underlying medical conditions.''',
            'downtime': '7-14 days',
            'duration': '2-3 hours',
            'downtime_description': 'Initial swelling and bruising for 7-10 days. Nasal splint removal after 1 week. Avoid strenuous exercise for 3-4 weeks. Complete healing and final results visible after 6-12 months.',
            'precautions': '''Temporary swelling, bruising, and nasal congestion are normal for the first 2 weeks. Avoid blood-thinning medications 2 weeks prior to surgery. Rare risks include infection, asymmetry, or need for revision surgery.

Do not blow nose forcefully for 4 weeks post-surgery. Sleep with head elevated for 2 weeks. Avoid direct sun exposure to reduce swelling. Follow all post-operative instructions carefully to ensure optimal healing.

Contact your surgeon immediately if you experience excessive bleeding, severe pain not controlled by medication, signs of infection, or any unusual symptoms during recovery.''',
            'results_gallery': json.dumps(results_gallery),
            'whatsapp_number': '+919876543210',
            'custom_phone_number': '+911234567890',
            'chat_message_template': 'Hi! I\'m interested in the Complete Rhinoplasty Package. Could you provide more information about the procedure, recovery timeline, and schedule a consultation to discuss my specific goals?',
            'call_message_template': 'I would like to inquire about the Complete Rhinoplasty Package and discuss scheduling a detailed consultation to review my case and desired outcomes.',
            'clinic_latitude': 28.7041,  # Delhi coordinates
            'clinic_longitude': 77.1025,
            'clinic_address': f'{clinic["name"]}, {clinic["city"]}, Advanced Cosmetic Surgery Center, Plot No. 123, Sector 44, Near Metro Station',
            'is_active': True,
            'created_at': datetime.utcnow()
        }
        
        cursor.execute(package_sql, package_data)
        package_result = cursor.fetchone()
        package_id = package_result['id']
        
        conn.commit()
        
        logger.info(f"Comprehensive test package created successfully with ID: {package_id}")
        logger.info(f"Package URL: /packages/{package_id}/enhanced")
        logger.info(f"Associated with clinic: {clinic['name']} in {clinic['city']}")
        
        return package_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating comprehensive test package: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    try:
        package_id = create_comprehensive_test_package()
        print(f"✅ Comprehensive test package created successfully!")
        print(f"📦 Package ID: {package_id}")
        print(f"🔗 Access URL: /packages/{package_id}/enhanced")
        print(f"🎯 Features demonstrated:")
        print("   • Complete package header with pricing")
        print("   • Before/after results gallery with descriptions")
        print("   • Detailed procedure information")
        print("   • Key highlights section")
        print("   • Procedure breakdown with individual pricing")
        print("   • VAT, anesthetic, and aftercare information")
        print("   • Comprehensive recommended for section")
        print("   • Detailed downtime and precautions")
        print("   • Interactive map with clinic location")
        print("   • Custom WhatsApp and phone contact")
        print("   • Message templates for inquiries")
        print("   • Sticky action buttons")
    except Exception as e:
        print(f"❌ Error creating test package: {e}")