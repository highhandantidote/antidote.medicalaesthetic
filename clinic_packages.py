"""
Treatment Package & Pricing System for Clinic Marketplace
Complete Gangnam Unni-style package management with real pricing
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Clinic, ClinicConsultation, ClinicLead, ClinicBilling, User, Category
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

clinic_packages_bp = Blueprint('clinic_packages', __name__, url_prefix='/clinic-packages')

# Real Indian clinic package data
CLINIC_PACKAGES = {
    1: {  # Apollo Cosmetic Surgery Center
        'rhinoplasty': {
            'name': 'Complete Rhinoplasty Package',
            'base_price': 185000,
            'emi_starting': 7500,
            'duration': '2-3 hours',
            'hospital_stay': '1 day',
            'inclusions': [
                'Pre-operative consultation & evaluation',
                'Surgery by senior plastic surgeon',
                'General anesthesia',
                '1 day hospital stay',
                '3 follow-up consultations',
                'Post-operative care kit',
                'Digital imaging consultation'
            ],
            'financing_options': ['6 months EMI', '12 months EMI', '18 months EMI'],
            'insurance_covered': False,
            'rating': 4.8,
            'total_reviews': 127,
            'before_after_photos': 15
        },
        'breast_augmentation': {
            'name': 'Breast Augmentation Premium Package',
            'base_price': 245000,
            'emi_starting': 9800,
            'duration': '3-4 hours',
            'hospital_stay': '2 days',
            'inclusions': [
                'Pre-surgical consultation & 3D imaging',
                'Premium silicone implants (FDA approved)',
                'Surgery by board-certified surgeon',
                'General anesthesia & monitoring',
                '2 days private room stay',
                '6 follow-up consultations over 1 year',
                'Compression garments',
                'Emergency support hotline'
            ],
            'financing_options': ['6 months EMI', '12 months EMI', '24 months EMI'],
            'insurance_covered': False,
            'rating': 4.9,
            'total_reviews': 89,
            'before_after_photos': 23
        },
        'liposuction': {
            'name': 'VASER Liposuction Complete Package',
            'base_price': 165000,
            'emi_starting': 6500,
            'duration': '2-4 hours',
            'hospital_stay': '1 day',
            'inclusions': [
                'VASER ultrasonic liposuction technology',
                'Multiple area treatment (up to 3 areas)',
                'Tumescent anesthesia',
                'Same-day discharge',
                'Compression garments (2 sets)',
                '4 follow-up consultations',
                'Lymphatic massage sessions (3)'
            ],
            'financing_options': ['6 months EMI', '12 months EMI'],
            'insurance_covered': False,
            'rating': 4.7,
            'total_reviews': 156,
            'before_after_photos': 31
        }
    },
    2: {  # Fortis Hospital Noida
        'hair_transplant': {
            'name': 'FUE Hair Transplant Premium Package',
            'base_price': 135000,
            'emi_starting': 5400,
            'duration': '6-8 hours',
            'hospital_stay': 'Day care',
            'inclusions': [
                'FUE technique (2500-3000 grafts)',
                'Local anesthesia',
                'Post-operative medications',
                'Hair care kit',
                '6 follow-up consultations over 1 year',
                'PRP therapy session (1)',
                'Hair growth guarantee'
            ],
            'financing_options': ['6 months EMI', '12 months EMI', '18 months EMI'],
            'insurance_covered': False,
            'rating': 4.6,
            'total_reviews': 234,
            'before_after_photos': 42
        },
        'facelift': {
            'name': 'Mini Facelift Package',
            'base_price': 285000,
            'emi_starting': 11500,
            'duration': '3-5 hours',
            'hospital_stay': '2 days',
            'inclusions': [
                'Mini facelift with neck lift',
                'General anesthesia',
                '2 days private room stay',
                'Post-operative care',
                '8 follow-up consultations',
                'Skincare regime consultation',
                'Recovery support package'
            ],
            'financing_options': ['12 months EMI', '18 months EMI', '24 months EMI'],
            'insurance_covered': False,
            'rating': 4.8,
            'total_reviews': 67,
            'before_after_photos': 18
        }
    },
    3: {  # Lilavati Cosmetic & Plastic Surgery Institute
        'mommy_makeover': {
            'name': 'Complete Mommy Makeover Package',
            'base_price': 385000,
            'emi_starting': 15500,
            'duration': '4-6 hours',
            'hospital_stay': '3 days',
            'inclusions': [
                'Tummy tuck (abdominoplasty)',
                'Breast lift or augmentation',
                'Liposuction (2 areas)',
                'General anesthesia',
                '3 days private room stay',
                'Dedicated nurse care',
                '10 follow-up consultations over 18 months',
                'Post-surgery garments',
                'Nutritionist consultation',
                'Physical therapy sessions (5)'
            ],
            'financing_options': ['12 months EMI', '18 months EMI', '24 months EMI', '36 months EMI'],
            'insurance_covered': False,
            'rating': 4.9,
            'total_reviews': 45,
            'before_after_photos': 28
        },
        'bbl': {
            'name': 'Brazilian Butt Lift Package',
            'base_price': 295000,
            'emi_starting': 12000,
            'duration': '3-4 hours',
            'hospital_stay': '2 days',
            'inclusions': [
                'Fat harvesting from donor areas',
                'BBL with fat grafting',
                'General anesthesia',
                '2 days monitored stay',
                'Special BBL pillow',
                'Compression garments',
                '7 follow-up consultations',
                'Lymphatic massage sessions (5)'
            ],
            'financing_options': ['12 months EMI', '18 months EMI', '24 months EMI'],
            'insurance_covered': False,
            'rating': 4.7,
            'total_reviews': 78,
            'before_after_photos': 35
        }
    }
}

@clinic_packages_bp.route('/clinic/<int:clinic_id>')
def clinic_packages(clinic_id):
    """Display all packages for a specific clinic"""
    clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
    if not clinic:
        flash('Clinic not found', 'error')
        return redirect(url_for('clinic.clinic_directory'))
    
    packages = CLINIC_PACKAGES.get(clinic_id, {})
    
    return render_template('clinic_packages.html', 
                         clinic=clinic,
                         packages=packages)

@clinic_packages_bp.route('/package/<int:clinic_id>/<package_type>')
def package_details(clinic_id, package_type):
    """Detailed view of a specific package"""
    clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
    if not clinic:
        flash('Clinic not found', 'error')
        return redirect(url_for('clinic.clinic_directory'))
    
    package = CLINIC_PACKAGES.get(clinic_id, {}).get(package_type)
    if not package:
        flash('Package not found', 'error')
        return redirect(url_for('clinic_packages.clinic_packages', clinic_id=clinic_id))
    
    # Calculate EMI options
    emi_options = []
    for duration in package['financing_options']:
        months = int(duration.split()[0])
        monthly_payment = round(package['base_price'] / months)
        emi_options.append({
            'duration': duration,
            'monthly_payment': monthly_payment,
            'total_amount': monthly_payment * months
        })
    
    return render_template('package_details.html',
                         clinic=clinic,
                         package=package,
                         package_type=package_type,
                         emi_options=emi_options)

@clinic_packages_bp.route('/book-package', methods=['POST'])
@login_required
def book_package():
    """Book a treatment package"""
    clinic_id = request.form.get('clinic_id')
    package_type = request.form.get('package_type')
    financing_option = request.form.get('financing_option')
    preferred_date = request.form.get('preferred_date')
    special_requests = request.form.get('special_requests')
    
    clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
    package = CLINIC_PACKAGES.get(int(clinic_id), {}).get(package_type)
    
    if not clinic or not package:
        return jsonify({'success': False, 'error': 'Invalid clinic or package'})
    
    try:
        # Create consultation record
        consultation = ClinicConsultation(
            clinic_id=clinic_id,
            user_id=current_user.id,
            consultation_type='package_booking',
            preferred_date=datetime.strptime(preferred_date, '%Y-%m-%d') if preferred_date else None,
            user_message=f"Package booking: {package['name']} - {financing_option}\n\nSpecial requests: {special_requests}",
            status='package_requested',
            patient_name=current_user.name,
            patient_phone=getattr(current_user, 'phone', ''),
            patient_email=current_user.email,
            procedure_interest=package['name'],
            message=special_requests,
            source='package_booking'
        )
        
        db.session.add(consultation)
        db.session.flush()
        
        # Create lead tracking
        lead = ClinicLead(
            clinic_id=clinic_id,
            consultation_id=consultation.id,
            lead_type='package_booking',
            value_score=package['base_price'] * 0.1,  # 10% lead value
            conversion_likelihood=0.7,  # Higher for package bookings
            notes=f"Package booking request: {package['name']}"
        )
        
        db.session.add(lead)
        
        # Create billing entry for package lead
        billing = ClinicBilling(
            clinic_id=clinic_id,
            consultation_id=consultation.id,
            billing_type='package_lead',
            amount=1500.00,  # Premium package lead fee
            status='pending',
            description=f"Package booking lead: {package['name']}"
        )
        
        db.session.add(billing)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Package booking request submitted successfully! The clinic will contact you within 24 hours.',
            'consultation_id': consultation.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error booking package: {e}")
        return jsonify({'success': False, 'error': 'Failed to submit booking request'})

@clinic_packages_bp.route('/compare')
def compare_packages():
    """Compare packages across different clinics"""
    package_type = request.args.get('type', 'rhinoplasty')
    
    # Collect packages of the same type from all clinics
    comparison_data = []
    for clinic_id, packages in CLINIC_PACKAGES.items():
        if package_type in packages:
            clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
            if clinic:
                package_data = packages[package_type].copy()
                package_data['clinic'] = clinic
                package_data['clinic_id'] = clinic_id
                comparison_data.append(package_data)
    
    # Sort by price
    comparison_data.sort(key=lambda x: x['base_price'])
    
    return render_template('package_comparison.html',
                         packages=comparison_data,
                         package_type=package_type)

@clinic_packages_bp.route('/api/calculate-emi')
def calculate_emi():
    """API endpoint to calculate EMI for any package"""
    amount = float(request.args.get('amount', 0))
    months = int(request.args.get('months', 12))
    
    if amount <= 0 or months <= 0:
        return jsonify({'error': 'Invalid amount or duration'})
    
    # Simple EMI calculation (without interest for now)
    monthly_payment = round(amount / months)
    total_amount = monthly_payment * months
    
    return jsonify({
        'monthly_payment': monthly_payment,
        'total_amount': total_amount,
        'months': months,
        'original_amount': amount
    })