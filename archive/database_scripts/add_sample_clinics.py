"""
Add sample clinic data to demonstrate the clinic management platform.
Creates realistic clinic profiles with Indian market focus.
"""

import os
import sys
sys.path.append('.')

# Import Flask app and database
from flask import Flask
from app import db
from models import Clinic, ClinicSpecialty, ClinicReview, ClinicConsultation, Doctor, Category, User
from datetime import datetime, timedelta
import logging

# Create Flask app context
from main import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_sample_clinics():
    """Add comprehensive sample clinic data for demonstration."""
    try:
        with app.app_context():
            # Check if clinics already exist
            existing_clinics = db.session.query(Clinic).count()
            if existing_clinics > 0:
                logger.info(f"Found {existing_clinics} existing clinics. Skipping clinic creation.")
                return
            
            logger.info("Creating sample clinic data...")
            
            # Get some categories for clinic specialties
            categories = db.session.query(Category).limit(20).all()
            if not categories:
                logger.error("No categories found. Please ensure categories are loaded first.")
                return
            
            # Sample clinic data with Indian market focus
            clinic_data = [
                {
                    'name': 'Apollo Cosmetic Surgery Center',
                    'name_hindi': 'अपोलो कॉस्मेटिक सर्जरी सेंटर',
                    'address': '45, Nelson Manickam Road, Aminjikarai',
                    'area': 'Aminjikarai',
                    'city': 'Chennai',
                    'state': 'Tamil Nadu',
                    'pincode': '600029',
                    'phone_number': '+91-44-2829-3333',
                    'whatsapp_number': '+91-98841-12345',
                    'email': 'info@apollocosmetic.com',
                    'website_url': 'https://apollocosmetic.com',
                    'gstin': '33AABCA1234F1Z5',
                    'medical_license': 'TN/MED/2018/12345',
                    'established_year': 2010,
                    'total_staff': 45,
                    'languages_supported': ['English', 'Tamil', 'Hindi', 'Telugu'],
                    'payment_methods': ['Cash', 'Card', 'UPI', 'Net Banking', 'Insurance'],
                    'insurance_accepted': ['Star Health', 'HDFC ERGO', 'New India Assurance', 'ICICI Lombard'],
                    'overall_rating': 4.7,
                    'total_reviews': 234,
                    'emergency_services': True,
                    'pharmacy_onsite': True,
                    'lab_services': True,
                    'parking_available': True,
                    'metro_nearby': 'Aminjikarai Metro Station - 0.5 km',
                    'is_verified': True,
                    'is_featured': True,
                    'specialties': ['Rhinoplasty And Nose Shaping', 'Breast Surgery', 'Face And Neck Lifts']
                },
                {
                    'name': 'Fortis Aesthetics & Reconstructive Surgery',
                    'name_hindi': 'फोर्टिस एस्थेटिक्स एंड रिकंस्ट्रक्टिव सर्जरी',
                    'address': 'B-22, Sector 62, Noida',
                    'area': 'Sector 62',
                    'city': 'Noida',
                    'state': 'Uttar Pradesh',
                    'pincode': '201301',
                    'phone_number': '+91-120-718-4444',
                    'whatsapp_number': '+91-98999-54321',
                    'email': 'aesthetics@fortishealthcare.com',
                    'website_url': 'https://fortisaesthetics.com',
                    'gstin': '09AABCF1234F1Z5',
                    'medical_license': 'UP/MED/2015/67890',
                    'established_year': 2015,
                    'total_staff': 60,
                    'languages_supported': ['English', 'Hindi', 'Punjabi', 'Urdu'],
                    'payment_methods': ['Cash', 'Card', 'UPI', 'EMI', 'Insurance'],
                    'insurance_accepted': ['Max Bupa', 'Bajaj Allianz', 'Oriental Insurance', 'United India'],
                    'overall_rating': 4.5,
                    'total_reviews': 189,
                    'emergency_services': True,
                    'ambulance_service': True,
                    'pharmacy_onsite': True,
                    'lab_services': True,
                    'parking_available': True,
                    'metro_nearby': 'Sector 62 Metro Station - 1.2 km',
                    'is_verified': True,
                    'is_featured': True,
                    'specialties': ['Body Contouring', 'Facial Rejuvenation', 'Hair Restoration']
                },
                {
                    'name': 'Lilavati Cosmetic & Plastic Surgery Institute',
                    'name_hindi': 'लीलावती कॉस्मेटिक एंड प्लास्टिक सर्जरी इंस्टीट्यूट',
                    'address': 'A-791, Bandra Reclamation, Bandra West',
                    'area': 'Bandra West',
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'pincode': '400050',
                    'phone_number': '+91-22-2675-1000',
                    'whatsapp_number': '+91-98200-11111',
                    'email': 'cosmetic@lilavatihospital.com',
                    'website_url': 'https://lilavaticosmetic.com',
                    'gstin': '27AABCL1234F1Z5',
                    'medical_license': 'MH/MED/2008/11111',
                    'established_year': 2008,
                    'total_staff': 80,
                    'languages_supported': ['English', 'Hindi', 'Marathi', 'Gujarati'],
                    'payment_methods': ['Cash', 'Card', 'UPI', 'Cheque', 'Insurance'],
                    'insurance_accepted': ['Religare', 'Care Health', 'Aditya Birla', 'Tata AIG'],
                    'overall_rating': 4.8,
                    'total_reviews': 345,
                    'emergency_services': True,
                    'ambulance_service': True,
                    'pharmacy_onsite': True,
                    'lab_services': True,
                    'parking_available': True,
                    'metro_nearby': 'Bandra Metro Station - 2.0 km',
                    'is_verified': True,
                    'is_featured': True,
                    'specialties': ['Breast Surgery', 'Abdominoplasty', 'Reconstructive Surgeries']
                },
                {
                    'name': 'Manipal Aesthetic Surgery Center',
                    'name_hindi': 'मणिपाल एस्थेटिक सर्जरी सेंटर',
                    'address': '98, Rustom Bagh, Airport Road',
                    'area': 'Airport Road',
                    'city': 'Bangalore',
                    'state': 'Karnataka',
                    'pincode': '560017',
                    'phone_number': '+91-80-2502-4444',
                    'whatsapp_number': '+91-99000-22222',
                    'email': 'aesthetics@manipalhospitals.com',
                    'website_url': 'https://manipalaesthetics.com',
                    'gstin': '29AABCM1234F1Z5',
                    'medical_license': 'KA/MED/2012/33333',
                    'established_year': 2012,
                    'total_staff': 55,
                    'languages_supported': ['English', 'Kannada', 'Tamil', 'Telugu', 'Hindi'],
                    'payment_methods': ['Cash', 'Card', 'UPI', 'Net Banking', 'Insurance'],
                    'insurance_accepted': ['Bharti AXA', 'Cholamandalam MS', 'Future Generali', 'Liberty General'],
                    'overall_rating': 4.6,
                    'total_reviews': 167,
                    'emergency_services': False,
                    'pharmacy_onsite': True,
                    'lab_services': True,
                    'parking_available': True,
                    'metro_nearby': 'Hebbal Metro Station - 3.5 km',
                    'is_verified': True,
                    'is_featured': False,
                    'specialties': ['Skin Rejuvenation And Resurfacing', 'Lip Enhancement', 'Cheek, Chin And Jawline Enhancement']
                },
                {
                    'name': 'Max Super Speciality Cosmetic Center',
                    'name_hindi': 'मैक्स सुपर स्पेशियलिटी कॉस्मेटिक सेंटर',
                    'address': '1, Press Enclave Road, Saket',
                    'area': 'Saket',
                    'city': 'New Delhi',
                    'state': 'Delhi',
                    'pincode': '110017',
                    'phone_number': '+91-11-2651-5050',
                    'whatsapp_number': '+91-98101-33333',
                    'email': 'cosmetic@maxhealthcare.com',
                    'website_url': 'https://maxcosmetic.com',
                    'gstin': '07AABCM1234F1Z5',
                    'medical_license': 'DL/MED/2014/44444',
                    'established_year': 2014,
                    'total_staff': 70,
                    'languages_supported': ['English', 'Hindi', 'Punjabi', 'Bengali'],
                    'payment_methods': ['Cash', 'Card', 'UPI', 'EMI', 'Insurance'],
                    'insurance_accepted': ['National Insurance', 'Royal Sundaram', 'Shriram General', 'SBI General'],
                    'overall_rating': 4.4,
                    'total_reviews': 278,
                    'emergency_services': True,
                    'ambulance_service': True,
                    'pharmacy_onsite': True,
                    'lab_services': True,
                    'parking_available': True,
                    'metro_nearby': 'Malviya Nagar Metro Station - 1.0 km',
                    'is_verified': True,
                    'is_featured': False,
                    'specialties': ['Eyelid Surgery', 'Hair Restoration', 'Body Contouring']
                }
            ]
            
            # Create clinic records
            created_clinics = []
            for clinic_info in clinic_data:
                try:
                    # Create operating hours JSON
                    operating_hours = {
                        'monday': {'open': '09:00', 'close': '18:00'},
                        'tuesday': {'open': '09:00', 'close': '18:00'},
                        'wednesday': {'open': '09:00', 'close': '18:00'},
                        'thursday': {'open': '09:00', 'close': '18:00'},
                        'friday': {'open': '09:00', 'close': '18:00'},
                        'saturday': {'open': '09:00', 'close': '16:00'},
                        'sunday': {'closed': True}
                    }
                    
                    # Extract specialties list
                    specialty_names = clinic_info.pop('specialties', [])
                    
                    # Create clinic
                    clinic = Clinic(
                        **clinic_info,
                        operating_hours=operating_hours,
                        slug=clinic_info['name'].lower().replace(' ', '-').replace('&', 'and'),
                        meta_description=f"Leading {clinic_info['name']} in {clinic_info['city']} offering world-class cosmetic and plastic surgery procedures.",
                        keywords=[clinic_info['city'], 'cosmetic surgery', 'plastic surgery', 'aesthetic procedures'],
                        price_rating=4.2,
                        service_rating=4.5,
                        facility_rating=4.4,
                        doctor_rating=4.6,
                        verification_date=datetime.utcnow()
                    )
                    
                    db.session.add(clinic)
                    db.session.flush()  # Get the clinic ID
                    
                    # Add clinic specialties
                    for specialty_name in specialty_names:
                        category = db.session.query(Category).filter(Category.name.ilike(f'%{specialty_name}%')).first()
                        if category:
                            clinic_specialty = ClinicSpecialty(
                                clinic_id=clinic.id,
                                category_id=category.id,
                                is_primary_specialty=specialty_names.index(specialty_name) == 0,
                                experience_years=8 + (len(specialty_names) - specialty_names.index(specialty_name)),
                                cases_completed=150 + (specialty_names.index(specialty_name) * 50),
                                success_rate=95.5 + (specialty_names.index(specialty_name) * 0.5)
                            )
                            db.session.add(clinic_specialty)
                    
                    created_clinics.append(clinic)
                    logger.info(f"Created clinic: {clinic.name} in {clinic.city}")
                    
                except Exception as e:
                    logger.error(f"Error creating clinic {clinic_info.get('name', 'Unknown')}: {e}")
                    db.session.rollback()
                    continue
            
            # Commit all clinic creations
            db.session.commit()
            logger.info(f"Successfully created {len(created_clinics)} clinics")
            
            # Add sample reviews for clinics
            add_sample_reviews(created_clinics)
            
            # Add sample consultation inquiries
            add_sample_consultations(created_clinics)
            
            logger.info("Sample clinic data creation completed successfully!")
            
    except Exception as e:
        logger.error(f"Error in add_sample_clinics: {e}")
        db.session.rollback()

def add_sample_reviews(clinics):
    """Add sample reviews for the created clinics."""
    try:
        # Get some users for reviews
        users = db.session.query(User).limit(20).all()
        if not users:
            logger.warning("No users found for creating sample reviews")
            return
        
        sample_reviews = [
            {
                'title': 'Excellent Experience',
                'content': 'The staff was very professional and the results exceeded my expectations. The facility is world-class and the doctors are highly skilled.',
                'overall_rating': 5,
                'facility_rating': 5,
                'staff_rating': 5,
                'doctor_rating': 5,
                'would_recommend': True
            },
            {
                'title': 'Great Results',
                'content': 'I am very happy with my procedure. The consultation was thorough and the aftercare was excellent. Highly recommend this clinic.',
                'overall_rating': 4,
                'facility_rating': 4,
                'staff_rating': 5,
                'doctor_rating': 4,
                'would_recommend': True
            },
            {
                'title': 'Professional Service',
                'content': 'Clean facilities, experienced doctors, and good patient care. The pricing is transparent and reasonable for the quality of service.',
                'overall_rating': 4,
                'facility_rating': 4,
                'staff_rating': 4,
                'doctor_rating': 4,
                'would_recommend': True
            }
        ]
        
        # Add reviews for each clinic
        for clinic in clinics[:3]:  # Add reviews for first 3 clinics
            for i, review_data in enumerate(sample_reviews):
                if i < len(users):
                    review = ClinicReview(
                        clinic_id=clinic.id,
                        user_id=users[i].id,
                        **review_data,
                        treatment_date=datetime.utcnow() - timedelta(days=30 + i*10),
                        is_verified_patient=True,
                        verification_method='phone_verification'
                    )
                    db.session.add(review)
        
        db.session.commit()
        logger.info("Sample clinic reviews added successfully")
        
    except Exception as e:
        logger.error(f"Error adding sample reviews: {e}")
        db.session.rollback()

def add_sample_consultations(clinics):
    """Add sample consultation inquiries."""
    try:
        consultation_data = [
            {
                'patient_name': 'Priya Sharma',
                'patient_phone': '+91-98765-43210',
                'patient_email': 'priya.sharma@email.com',
                'procedure_interest': 'Rhinoplasty',
                'message': 'I am interested in nose reshaping procedure. Please provide more details about the process and cost.',
                'status': 'pending',
                'source': 'website_contact_form'
            },
            {
                'patient_name': 'Rajesh Kumar',
                'patient_phone': '+91-98765-43211',
                'patient_email': 'rajesh.kumar@email.com',
                'procedure_interest': 'Hair Transplant',
                'message': 'I would like to know more about hair restoration procedures and book a consultation.',
                'status': 'contacted',
                'source': 'phone_inquiry'
            }
        ]
        
        # Add consultations for each clinic
        for clinic in clinics:
            for consult_data in consultation_data:
                consultation = ClinicConsultation(
                    clinic_id=clinic.id,
                    **consult_data,
                    preferred_date=datetime.utcnow() + timedelta(days=7)
                )
                db.session.add(consultation)
        
        db.session.commit()
        logger.info("Sample consultation inquiries added successfully")
        
    except Exception as e:
        logger.error(f"Error adding sample consultations: {e}")
        db.session.rollback()

if __name__ == '__main__':
    add_sample_clinics()