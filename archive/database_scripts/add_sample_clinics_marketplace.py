#!/usr/bin/env python3
"""
Add sample clinics and packages for the Korean-style marketplace
"""

import sys
import os
from datetime import datetime
import random

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Clinic, Package, CreditTransaction
import main

def add_sample_clinics():
    """Add sample clinics with Korean aesthetic clinic style."""
    
    with app.app_context():
        print("Adding sample clinics for marketplace...")
        
        # Sample clinic data with Korean aesthetic clinic names and descriptions
        clinics_data = [
            {
                'name': 'Seoul Beauty Clinic Mumbai',
                'slug': 'seoul-beauty-clinic-mumbai',
                'address': 'Linking Road, Bandra West',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400050',
                'contact_number': '9876543210',
                'email': 'info@seoulbeauty.in',
                'description': 'Premium Korean aesthetic treatments with advanced K-beauty techniques. Specializing in non-surgical face lifts, skin rejuvenation, and anti-aging treatments.',
                'specialties': ['Korean Face Lift', 'Skin Rejuvenation', 'Anti-Aging', 'Botox'],
                'services_offered': ['Botox', 'Fillers', 'Face Lift', 'Skin Treatment'],
                'rating': 4.8,
                'review_count': 156,
                'is_approved': True,
                'verification_status': 'verified',
                'credit_balance': 5000,
                'view_count': 1200,
                'lead_count': 89
            },
            {
                'name': 'Gangnam Style Aesthetics Delhi',
                'slug': 'gangnam-style-aesthetics-delhi',
                'address': 'CP, Connaught Place',
                'city': 'Delhi',
                'state': 'Delhi',
                'pincode': '110001',
                'contact_number': '9876543211',
                'email': 'contact@gangnamaesthetics.in',
                'description': 'Authentic Korean aesthetic procedures with celebrity-grade treatments. Experience the luxury of Korean beauty standards.',
                'specialties': ['Korean Rhinoplasty', 'Double Eyelid Surgery', 'Jaw Contouring'],
                'services_offered': ['Rhinoplasty', 'Eyelid Surgery', 'Jaw Surgery', 'Facial Contouring'],
                'rating': 4.9,
                'review_count': 203,
                'is_approved': True,
                'verification_status': 'verified',
                'credit_balance': 7500,
                'view_count': 1800,
                'lead_count': 134
            },
            {
                'name': 'K-Beauty Clinic Bangalore',
                'slug': 'k-beauty-clinic-bangalore',
                'address': 'MG Road, Brigade Road',
                'city': 'Bangalore',
                'state': 'Karnataka',
                'pincode': '560001',
                'contact_number': '9876543212',
                'email': 'hello@kbeauty.in',
                'description': 'Modern Korean skincare and aesthetic treatments. Glass skin perfection with advanced Korean technology.',
                'specialties': ['Glass Skin Treatment', 'Korean Facial', 'Acne Treatment'],
                'services_offered': ['Facial Treatment', 'Acne Care', 'Skin Brightening', 'Anti-Aging'],
                'rating': 4.7,
                'review_count': 178,
                'is_approved': True,
                'verification_status': 'verified',
                'credit_balance': 4200,
                'view_count': 950,
                'lead_count': 67
            },
            {
                'name': 'Seoul Glow Aesthetic Center',
                'slug': 'seoul-glow-aesthetic-center',
                'address': 'Park Street, Park Circus',
                'city': 'Kolkata',
                'state': 'West Bengal',
                'pincode': '700016',
                'contact_number': '9876543213',
                'email': 'info@seoulglow.in',
                'description': 'Premium Korean beauty treatments with expert Korean-trained doctors. Achieve that perfect Korean glow.',
                'specialties': ['Korean Glow Treatment', 'V-Shape Face', 'Skin Whitening'],
                'services_offered': ['Glow Treatment', 'Face Shaping', 'Whitening', 'Korean Facial'],
                'rating': 4.6,
                'review_count': 112,
                'is_approved': True,
                'verification_status': 'verified',
                'credit_balance': 3800,
                'view_count': 720,
                'lead_count': 45
            },
            {
                'name': 'Hallyu Beauty Hub Chennai',
                'slug': 'hallyu-beauty-hub-chennai',
                'address': 'Anna Nagar, Chennai',
                'city': 'Chennai',
                'state': 'Tamil Nadu',
                'pincode': '600040',
                'contact_number': '9876543214',
                'email': 'contact@hallyubeauty.in',
                'description': 'Korean wave aesthetic treatments inspired by K-pop beauty standards. Transform with Korean beauty secrets.',
                'specialties': ['K-Pop Makeover', 'Korean Eye Surgery', 'Skin Perfection'],
                'services_offered': ['Eye Surgery', 'Skin Treatment', 'Beauty Makeover', 'Korean Procedures'],
                'rating': 4.5,
                'review_count': 89,
                'is_approved': True,
                'verification_status': 'verified',
                'credit_balance': 2900,
                'view_count': 580,
                'lead_count': 32
            }
        ]
        
        # Add clinics to database
        for clinic_data in clinics_data:
            existing_clinic = Clinic.query.filter_by(slug=clinic_data['slug']).first()
            if not existing_clinic:
                clinic = Clinic(**clinic_data)
                db.session.add(clinic)
                print(f"Added clinic: {clinic_data['name']}")
        
        db.session.commit()
        print(f"Successfully added {len(clinics_data)} sample clinics!")

def add_sample_packages():
    """Add sample packages for the clinics."""
    
    with app.app_context():
        print("Adding sample packages...")
        
        clinics = Clinic.query.all()
        if not clinics:
            print("No clinics found. Please add clinics first.")
            return
        
        # Sample package data with Korean aesthetic treatments
        packages_templates = [
            {
                'title': 'Korean Glass Skin Package',
                'description': 'Achieve that perfect Korean glass skin with our comprehensive 6-session treatment including hydrafacial, chemical peels, and Korean skincare products.',
                'category': 'Skin Treatment',
                'price_original': 25000,
                'price_discounted': 18999,
                'duration_days': 45,
                'sessions_included': 6,
                'is_active': True
            },
            {
                'title': 'Double Eyelid Surgery Package',
                'description': 'Complete double eyelid surgery with Korean techniques, including consultation, surgery, aftercare, and follow-up sessions.',
                'category': 'Eye Surgery',
                'price_original': 85000,
                'price_discounted': 69999,
                'duration_days': 90,
                'sessions_included': 4,
                'is_active': True
            },
            {
                'title': 'Korean Rhinoplasty Complete',
                'description': 'Full nose reshaping with Korean surgical techniques, including pre-op consultation, surgery, and post-op care.',
                'category': 'Nose Surgery',
                'price_original': 150000,
                'price_discounted': 125000,
                'duration_days': 120,
                'sessions_included': 5,
                'is_active': True
            },
            {
                'title': 'V-Shape Face Contouring',
                'description': 'Achieve the perfect V-shaped face with non-surgical contouring using Korean techniques and premium fillers.',
                'category': 'Face Contouring',
                'price_original': 45000,
                'price_discounted': 35999,
                'duration_days': 60,
                'sessions_included': 3,
                'is_active': True
            },
            {
                'title': 'Korean Anti-Aging Package',
                'description': 'Comprehensive anti-aging treatment with Botox, fillers, and Korean skincare routine for youthful appearance.',
                'category': 'Anti-Aging',
                'price_original': 35000,
                'price_discounted': 27999,
                'duration_days': 75,
                'sessions_included': 4,
                'is_active': True
            }
        ]
        
        # Add packages for each clinic
        for clinic in clinics:
            for i, package_template in enumerate(packages_templates):
                slug = f"{package_template['title'].lower().replace(' ', '-')}-{clinic.city.lower()}"
                existing_package = Package.query.filter_by(slug=slug).first()
                
                if not existing_package:
                    package_data = package_template.copy()
                    package_data.update({
                        'clinic_id': clinic.id,
                        'slug': slug,
                        'view_count': random.randint(50, 300),
                        'lead_count': random.randint(5, 25)
                    })
                    
                    package = Package(**package_data)
                    db.session.add(package)
                    print(f"Added package: {package_data['title']} for {clinic.name}")
        
        db.session.commit()
        print("Successfully added sample packages!")

if __name__ == '__main__':
    print("Setting up Korean-style clinic marketplace with sample data...")
    add_sample_clinics()
    add_sample_packages()
    print("Korean clinic marketplace setup complete!")