"""
Add authentic Korean-style treatment packages to the database.
This script creates real treatment packages with proper Korean clinic pricing and formatting.
"""

import os
import psycopg2
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable not set")
        
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def add_authentic_packages():
    """Add authentic Korean-style treatment packages to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get clinic IDs from existing clinics
        cursor.execute("SELECT id, name FROM clinics WHERE is_verified = true LIMIT 10")
        clinics = cursor.fetchall()
        
        if not clinics:
            logger.error("No verified clinics found. Please add clinics first.")
            return
        
        # Authentic Korean clinic packages with real pricing
        packages_data = [
            # Rhinoplasty packages
            {
                'clinic_id': clinics[0][0],
                'title': 'Premium Rhinoplasty Package',
                'slug': 'premium-rhinoplasty-package',
                'description': 'Complete nose reshaping with advanced Korean techniques',
                'procedure_info': '<p>Our premium rhinoplasty package includes consultation, surgery, post-operative care, and follow-up visits. Using advanced Korean techniques for natural-looking results.</p>',
                'price_actual': 280000.00,
                'price_discounted': 238000.00,
                'discount_percentage': 15,
                'category': 'Rhinoplasty',
                'tags': ['15% OFF', 'Popular', 'Premium'],
                'side_effects': 'Mild swelling and bruising for 7-10 days',
                'recommended_for': 'Those seeking nose bridge enhancement or tip refinement',
                'downtime': '7-10 days',
                'duration': '2-3 hours',
                'anesthetic': 'General anesthesia included',
                'featured_image': '/static/images/packages/rhinoplasty-premium.jpg',
                'gallery_images': ['/static/images/packages/rhino-1.jpg', '/static/images/packages/rhino-2.jpg'] if 'gallery_images' in locals() else None,
                'is_featured': True,
                'meta_title': 'Premium Rhinoplasty Package - Korean Clinic',
                'meta_description': 'Advanced Korean rhinoplasty techniques for natural-looking nose enhancement'
            },
            {
                'clinic_id': clinics[1][0],
                'title': 'Natural Rhinoplasty',
                'slug': 'natural-rhinoplasty',
                'description': 'Subtle nose enhancement for natural-looking results',
                'procedure_info': '<p>Our natural rhinoplasty focuses on subtle changes to enhance your natural features without dramatic alterations.</p>',
                'price_actual': 220000.00,
                'price_discounted': 198000.00,
                'discount_percentage': 10,
                'category': 'Rhinoplasty',
                'tags': ['10% OFF', 'Natural'],
                'side_effects': 'Minimal swelling, temporary numbness',
                'recommended_for': 'First-time rhinoplasty patients seeking subtle changes',
                'downtime': '5-7 days',
                'duration': '1.5-2 hours',
                'anesthetic': 'Local anesthesia with sedation',
                'featured_image': '/static/images/packages/rhinoplasty-natural.jpg',
                'is_featured': False
            },
            
            # Facial contouring packages
            {
                'clinic_id': clinics[2][0],
                'title': 'V-Line Facial Contouring',
                'slug': 'v-line-facial-contouring',
                'description': 'Create the perfect V-shaped jawline with Korean contouring',
                'procedure_info': '<p>Advanced jaw contouring surgery to create the coveted V-line face shape popular in Korean beauty standards.</p>',
                'price_actual': 450000.00,
                'price_discounted': 382500.00,
                'discount_percentage': 15,
                'category': 'Facial Contouring',
                'tags': ['15% OFF', 'V-Line', 'Premium'],
                'side_effects': 'Swelling for 2-3 weeks, temporary numbness',
                'recommended_for': 'Those seeking dramatic jawline refinement',
                'downtime': '14-21 days',
                'duration': '3-4 hours',
                'anesthetic': 'General anesthesia included',
                'featured_image': '/static/images/packages/v-line-contouring.jpg',
                'is_featured': True
            },
            
            # Double eyelid packages
            {
                'clinic_id': clinics[3][0],
                'title': 'Natural Double Eyelid Surgery',
                'slug': 'natural-double-eyelid-surgery',
                'description': 'Create natural-looking double eyelids with Korean techniques',
                'procedure_info': '<p>Non-incision or incision method to create beautiful, natural double eyelids that enhance your eye shape.</p>',
                'price_actual': 85000.00,
                'price_discounted': 72250.00,
                'discount_percentage': 15,
                'category': 'Eyelid Surgery',
                'tags': ['15% OFF', 'Natural', 'Quick Recovery'],
                'side_effects': 'Minor swelling for 3-5 days',
                'recommended_for': 'Those wanting to enhance eye shape naturally',
                'downtime': '3-5 days',
                'duration': '30-45 minutes',
                'anesthetic': 'Local anesthesia',
                'featured_image': '/static/images/packages/double-eyelid.jpg',
                'is_featured': True
            },
            
            # Botox and filler packages
            {
                'clinic_id': clinics[4][0],
                'title': 'Premium Botox Package',
                'slug': 'premium-botox-package',
                'description': 'Anti-aging botox treatment for forehead and crow\'s feet',
                'procedure_info': '<p>Premium botox treatment using authentic Korean products for natural anti-aging results.</p>',
                'price_actual': 25000.00,
                'price_discounted': 21250.00,
                'discount_percentage': 15,
                'category': 'Botox & Fillers',
                'tags': ['15% OFF', 'Anti-aging', 'Quick'],
                'side_effects': 'Minimal bruising, temporary redness',
                'recommended_for': 'Adults 25+ seeking wrinkle prevention',
                'downtime': 'None',
                'duration': '15-20 minutes',
                'anesthetic': 'Topical numbing cream',
                'featured_image': '/static/images/packages/botox-premium.jpg',
                'is_featured': True
            },
            
            {
                'clinic_id': clinics[5][0],
                'title': 'Hyaluronic Acid Filler',
                'slug': 'hyaluronic-acid-filler',
                'description': 'Premium lip and cheek enhancement with Korean fillers',
                'procedure_info': '<p>High-quality hyaluronic acid fillers for natural lip and cheek enhancement.</p>',
                'price_actual': 35000.00,
                'price_discounted': 29750.00,
                'discount_percentage': 15,
                'category': 'Botox & Fillers',
                'tags': ['15% OFF', 'Natural Enhancement'],
                'side_effects': 'Temporary swelling, mild bruising',
                'recommended_for': 'Those seeking subtle lip or cheek enhancement',
                'downtime': '1-2 days',
                'duration': '30 minutes',
                'anesthetic': 'Topical numbing cream',
                'featured_image': '/static/images/packages/ha-filler.jpg',
                'is_featured': False
            },
            
            # Skin treatment packages
            {
                'clinic_id': clinics[6][0],
                'title': 'Korean Glass Skin Treatment',
                'slug': 'korean-glass-skin-treatment',
                'description': 'Achieve the coveted Korean glass skin with our premium package',
                'procedure_info': '<p>Multi-step treatment including chemical peels, laser therapy, and hydrating treatments for flawless skin.</p>',
                'price_actual': 45000.00,
                'price_discounted': 36000.00,
                'discount_percentage': 20,
                'category': 'Skin Treatments',
                'tags': ['20% OFF', 'Glass Skin', 'Popular'],
                'side_effects': 'Mild redness for 24-48 hours',
                'recommended_for': 'All skin types seeking radiant, clear skin',
                'downtime': '1-2 days',
                'duration': '1.5 hours',
                'anesthetic': 'Topical numbing cream',
                'featured_image': '/static/images/packages/glass-skin.jpg',
                'is_featured': True
            },
            
            # Breast surgery packages
            {
                'clinic_id': clinics[7][0],
                'title': 'Natural Breast Augmentation',
                'slug': 'natural-breast-augmentation',
                'description': 'Korean-style natural breast enhancement',
                'procedure_info': '<p>Natural breast augmentation using premium implants with Korean surgical techniques for natural-looking results.</p>',
                'price_actual': 380000.00,
                'price_discounted': 323000.00,
                'discount_percentage': 15,
                'category': 'Breast Surgery',
                'tags': ['15% OFF', 'Natural', 'Premium'],
                'side_effects': 'Swelling and discomfort for 1-2 weeks',
                'recommended_for': 'Women seeking natural breast enhancement',
                'downtime': '7-14 days',
                'duration': '2-3 hours',
                'anesthetic': 'General anesthesia included',
                'featured_image': '/static/images/packages/breast-augmentation.jpg',
                'is_featured': True
            },
            
            # Body contouring packages
            {
                'clinic_id': clinics[8][0],
                'title': 'Liposuction Package',
                'slug': 'liposuction-package',
                'description': 'Advanced liposuction for body contouring',
                'procedure_info': '<p>Safe and effective liposuction using Korean techniques for precise body contouring.</p>',
                'price_actual': 180000.00,
                'price_discounted': 153000.00,
                'discount_percentage': 15,
                'category': 'Body Contouring',
                'tags': ['15% OFF', 'Body Sculpting'],
                'side_effects': 'Swelling and bruising for 1-2 weeks',
                'recommended_for': 'Those with stubborn fat deposits',
                'downtime': '5-7 days',
                'duration': '1-3 hours',
                'anesthetic': 'Local or general anesthesia',
                'featured_image': '/static/images/packages/liposuction.jpg',
                'is_featured': False
            },
            
            # Hair transplant packages
            {
                'clinic_id': clinics[9][0] if len(clinics) > 9 else clinics[0][0],
                'title': 'Korean Hair Transplant',
                'slug': 'korean-hair-transplant',
                'description': 'Advanced FUE hair transplant with Korean techniques',
                'procedure_info': '<p>State-of-the-art FUE hair transplant using Korean precision techniques for natural-looking results.</p>',
                'price_actual': 320000.00,
                'price_discounted': 272000.00,
                'discount_percentage': 15,
                'category': 'Hair Restoration',
                'tags': ['15% OFF', 'FUE Method'],
                'side_effects': 'Mild scalp irritation for 3-5 days',
                'recommended_for': 'Men and women experiencing hair loss',
                'downtime': '3-5 days',
                'duration': '4-6 hours',
                'anesthetic': 'Local anesthesia',
                'featured_image': '/static/images/packages/hair-transplant.jpg',
                'is_featured': True
            }
        ]
        
        # Insert packages
        for package in packages_data:
            cursor.execute("""
                INSERT INTO packages (
                    clinic_id, title, slug, description, procedure_info,
                    price_actual, price_discounted, discount_percentage,
                    category, tags, side_effects, recommended_for,
                    downtime, duration, anesthetic, featured_image,
                    gallery_images, is_featured, meta_title, meta_description,
                    is_active, view_count, lead_count, created_at
                ) VALUES (
                    %(clinic_id)s, %(title)s, %(slug)s, %(description)s, %(procedure_info)s,
                    %(price_actual)s, %(price_discounted)s, %(discount_percentage)s,
                    %(category)s, %(tags)s, %(side_effects)s, %(recommended_for)s,
                    %(downtime)s, %(duration)s, %(anesthetic)s, %(featured_image)s,
                    %(gallery_images)s, %(is_featured)s, %(meta_title)s, %(meta_description)s,
                    true, 0, 0, %(created_at)s
                )
            """, {**package, 'created_at': datetime.utcnow()})
        
        conn.commit()
        logger.info(f"Successfully added {len(packages_data)} authentic Korean clinic packages")
        
        # Display summary
        cursor.execute("SELECT COUNT(*) FROM packages WHERE is_active = true")
        total_packages = cursor.fetchone()[0]
        
        cursor.execute("SELECT category, COUNT(*) FROM packages GROUP BY category ORDER BY COUNT(*) DESC")
        category_counts = cursor.fetchall()
        
        logger.info(f"Total active packages: {total_packages}")
        logger.info("Packages by category:")
        for category, count in category_counts:
            logger.info(f"  {category}: {count}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding packages: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the package addition script."""
    try:
        add_authentic_packages()
        logger.info("Package addition completed successfully!")
    except Exception as e:
        logger.error(f"Package addition failed: {e}")

if __name__ == "__main__":
    main()