"""
Enhanced Booking Features
Multiple appointment types, group booking, waitlist management, and advanced scheduling
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Clinic, ClinicConsultation, Doctor, User
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

enhanced_booking_bp = Blueprint('enhanced_booking', __name__, url_prefix='/enhanced-booking')

# Appointment types with detailed configurations
APPOINTMENT_TYPES = {
    'consultation': {
        'name': 'Initial Consultation',
        'duration': 30,
        'price_range': (1500, 3000),
        'description': 'Comprehensive evaluation and treatment planning',
        'preparation_required': False,
        'cancellation_policy': '24 hours advance notice required'
    },
    'procedure': {
        'name': 'Procedure/Surgery',
        'duration': 180,
        'price_range': (50000, 500000),
        'description': 'Main surgical or non-surgical procedure',
        'preparation_required': True,
        'cancellation_policy': '72 hours advance notice required'
    },
    'follow_up': {
        'name': 'Follow-up Visit',
        'duration': 20,
        'price_range': (500, 1500),
        'description': 'Post-procedure check-up and progress assessment',
        'preparation_required': False,
        'cancellation_policy': '12 hours advance notice required'
    },
    'pre_op': {
        'name': 'Pre-operative Assessment',
        'duration': 45,
        'price_range': (2000, 4000),
        'description': 'Medical clearance and pre-surgery preparation',
        'preparation_required': True,
        'cancellation_policy': '48 hours advance notice required'
    },
    'post_op': {
        'name': 'Post-operative Care',
        'duration': 30,
        'price_range': (1000, 2500),
        'description': 'Wound care, dressing change, and recovery monitoring',
        'preparation_required': False,
        'cancellation_policy': '6 hours advance notice required'
    },
    'virtual_consultation': {
        'name': 'Virtual Consultation',
        'duration': 25,
        'price_range': (1000, 2000),
        'description': 'Online video consultation from home',
        'preparation_required': False,
        'cancellation_policy': '2 hours advance notice required'
    }
}

# Group booking packages
GROUP_BOOKING_PACKAGES = {
    'friends_package': {
        'name': 'Friends Together Package',
        'min_people': 2,
        'max_people': 4,
        'discount_percentage': 15,
        'applicable_procedures': ['Botox', 'Dermal Fillers', 'Chemical Peel', 'Microneedling'],
        'benefits': [
            '15% discount for all participants',
            'Synchronized appointment scheduling',
            'Group recovery support',
            'Shared aftercare guidance'
        ]
    },
    'couple_package': {
        'name': 'Couple Transformation Package',
        'min_people': 2,
        'max_people': 2,
        'discount_percentage': 12,
        'applicable_procedures': ['Hair Transplant', 'Laser Hair Removal', 'Skin Treatments'],
        'benefits': [
            '12% discount for both partners',
            'Coordinated treatment plans',
            'Joint follow-up sessions',
            'Couples consultation included'
        ]
    },
    'family_package': {
        'name': 'Family Wellness Package',
        'min_people': 3,
        'max_people': 6,
        'discount_percentage': 20,
        'applicable_procedures': ['Dental Treatments', 'Skin Care', 'General Wellness'],
        'benefits': [
            '20% discount for family members',
            'Family health assessment',
            'Coordinated appointments',
            'Family aftercare support'
        ]
    }
}

# Waitlist management system
WAITLIST_PRIORITIES = {
    'urgent': {'priority_score': 10, 'notification_advance': 24},  # 24 hours advance notice
    'high': {'priority_score': 7, 'notification_advance': 48},    # 48 hours advance notice
    'normal': {'priority_score': 5, 'notification_advance': 72},  # 72 hours advance notice
    'flexible': {'priority_score': 3, 'notification_advance': 168} # 1 week advance notice
}

@enhanced_booking_bp.route('/')
def enhanced_booking_home():
    """Enhanced booking system homepage"""
    return render_template('enhanced_booking_home.html',
                         appointment_types=APPOINTMENT_TYPES,
                         group_packages=GROUP_BOOKING_PACKAGES)

@enhanced_booking_bp.route('/book-appointment/<int:clinic_id>')
@login_required
def book_enhanced_appointment(clinic_id):
    """Enhanced appointment booking with multiple types"""
    clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
    if not clinic:
        flash('Clinic not found', 'error')
        return redirect(url_for('clinic.clinic_directory'))
    
    appointment_type = request.args.get('type', 'consultation')
    doctor_id = request.args.get('doctor_id', type=int)
    
    if appointment_type not in APPOINTMENT_TYPES:
        appointment_type = 'consultation'
    
    appointment_info = APPOINTMENT_TYPES[appointment_type]
    
    return render_template('book_enhanced_appointment.html',
                         clinic=clinic,
                         appointment_type=appointment_type,
                         appointment_info=appointment_info,
                         doctor_id=doctor_id)

@enhanced_booking_bp.route('/group-booking/<int:clinic_id>')
@login_required
def group_booking_form(clinic_id):
    """Group booking form"""
    clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
    if not clinic:
        flash('Clinic not found', 'error')
        return redirect(url_for('clinic.clinic_directory'))
    
    package_type = request.args.get('package', 'friends_package')
    
    if package_type not in GROUP_BOOKING_PACKAGES:
        package_type = 'friends_package'
    
    package_info = GROUP_BOOKING_PACKAGES[package_type]
    
    return render_template('group_booking_form.html',
                         clinic=clinic,
                         package_type=package_type,
                         package_info=package_info)

@enhanced_booking_bp.route('/submit-group-booking', methods=['POST'])
@login_required
def submit_group_booking():
    """Submit group booking request"""
    clinic_id = request.form.get('clinic_id')
    package_type = request.form.get('package_type')
    procedure = request.form.get('procedure')
    preferred_date = request.form.get('preferred_date')
    
    # Get participant details
    participants = []
    participant_count = int(request.form.get('participant_count', 1))
    
    for i in range(1, participant_count + 1):
        name = request.form.get(f'participant_{i}_name')
        email = request.form.get(f'participant_{i}_email')
        phone = request.form.get(f'participant_{i}_phone')
        
        if name and email:
            participants.append({
                'name': name,
                'email': email,
                'phone': phone
            })
    
    try:
        clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
        package_info = GROUP_BOOKING_PACKAGES.get(package_type)
        
        if not clinic or not package_info:
            return jsonify({'success': False, 'error': 'Invalid clinic or package'})
        
        # Validate participant count
        if len(participants) < package_info['min_people'] or len(participants) > package_info['max_people']:
            return jsonify({
                'success': False, 
                'error': f"This package requires {package_info['min_people']}-{package_info['max_people']} participants"
            })
        
        # Create group booking consultation
        consultation = ClinicConsultation(
            clinic_id=clinic_id,
            user_id=current_user.id,
            consultation_type='group_booking',
            preferred_date=datetime.strptime(preferred_date, '%Y-%m-%d') if preferred_date else None,
            user_message=f"Group booking: {package_info['name']}\nProcedure: {procedure}\nParticipants: {len(participants)}",
            status='group_booking_requested',
            patient_name=current_user.name,
            patient_email=current_user.email,
            procedure_interest=procedure,
            source='group_booking',
            group_booking_details={
                'package_type': package_type,
                'participants': participants,
                'discount_percentage': package_info['discount_percentage']
            }
        )
        
        db.session.add(consultation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Group booking request submitted! You will receive a {package_info["discount_percentage"]}% discount.',
            'consultation_id': consultation.id,
            'discount_percentage': package_info['discount_percentage']
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting group booking: {e}")
        return jsonify({'success': False, 'error': 'Failed to submit group booking'})

@enhanced_booking_bp.route('/waitlist/<int:clinic_id>')
@login_required
def join_waitlist_form(clinic_id):
    """Join waitlist for appointments"""
    clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
    if not clinic:
        flash('Clinic not found', 'error')
        return redirect(url_for('clinic.clinic_directory'))
    
    return render_template('join_waitlist_form.html',
                         clinic=clinic,
                         waitlist_priorities=WAITLIST_PRIORITIES)

@enhanced_booking_bp.route('/submit-waitlist', methods=['POST'])
@login_required
def submit_waitlist_request():
    """Submit waitlist request"""
    clinic_id = request.form.get('clinic_id')
    procedure = request.form.get('procedure')
    preferred_dates = request.form.getlist('preferred_dates')
    priority_level = request.form.get('priority_level', 'normal')
    flexible_timing = request.form.get('flexible_timing') == 'on'
    
    try:
        clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'})
        
        priority_info = WAITLIST_PRIORITIES.get(priority_level, WAITLIST_PRIORITIES['normal'])
        
        # Create waitlist consultation
        consultation = ClinicConsultation(
            clinic_id=clinic_id,
            user_id=current_user.id,
            consultation_type='waitlist',
            user_message=f"Waitlist request for {procedure}\nPriority: {priority_level}\nFlexible timing: {flexible_timing}",
            status='waitlist_active',
            patient_name=current_user.name,
            patient_email=current_user.email,
            procedure_interest=procedure,
            source='waitlist',
            waitlist_details={
                'priority_level': priority_level,
                'priority_score': priority_info['priority_score'],
                'preferred_dates': preferred_dates,
                'flexible_timing': flexible_timing,
                'notification_advance_hours': priority_info['notification_advance']
            }
        )
        
        db.session.add(consultation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Added to waitlist with {priority_level} priority. You will be notified {priority_info["notification_advance"]} hours in advance.',
            'consultation_id': consultation.id,
            'estimated_wait_time': '2-4 weeks'  # Would calculate based on actual data
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting waitlist request: {e}")
        return jsonify({'success': False, 'error': 'Failed to join waitlist'})

@enhanced_booking_bp.route('/my-bookings')
@login_required
def my_enhanced_bookings():
    """User's all booking types and waitlist status"""
    # Get all user consultations
    consultations = db.session.query(ClinicConsultation).filter_by(
        user_id=current_user.id
    ).order_by(ClinicConsultation.created_at.desc()).all()
    
    # Categorize by type
    bookings = {
        'confirmed': [],
        'pending': [],
        'waitlist': [],
        'group_bookings': [],
        'completed': []
    }
    
    for consultation in consultations:
        if consultation.status == 'confirmed':
            bookings['confirmed'].append(consultation)
        elif consultation.status in ['pending', 'quote_requested', 'group_booking_requested']:
            bookings['pending'].append(consultation)
        elif consultation.status == 'waitlist_active':
            bookings['waitlist'].append(consultation)
        elif consultation.consultation_type == 'group_booking':
            bookings['group_bookings'].append(consultation)
        elif consultation.status in ['completed', 'cancelled']:
            bookings['completed'].append(consultation)
    
    return render_template('my_enhanced_bookings.html',
                         bookings=bookings,
                         appointment_types=APPOINTMENT_TYPES)

@enhanced_booking_bp.route('/modify-appointment/<int:consultation_id>')
@login_required
def modify_appointment_form(consultation_id):
    """Form to modify existing appointment"""
    consultation = db.session.query(ClinicConsultation).filter_by(
        id=consultation_id,
        user_id=current_user.id
    ).first()
    
    if not consultation:
        flash('Appointment not found', 'error')
        return redirect(url_for('enhanced_booking.my_enhanced_bookings'))
    
    return render_template('modify_appointment_form.html',
                         consultation=consultation,
                         appointment_types=APPOINTMENT_TYPES)

@enhanced_booking_bp.route('/submit-appointment-modification', methods=['POST'])
@login_required
def submit_appointment_modification():
    """Submit appointment modification request"""
    consultation_id = request.form.get('consultation_id')
    modification_type = request.form.get('modification_type')  # reschedule, change_type, add_services
    new_date = request.form.get('new_date')
    new_time = request.form.get('new_time')
    new_appointment_type = request.form.get('new_appointment_type')
    additional_services = request.form.getlist('additional_services')
    reason = request.form.get('reason')
    
    try:
        consultation = db.session.query(ClinicConsultation).filter_by(
            id=consultation_id,
            user_id=current_user.id
        ).first()
        
        if not consultation:
            return jsonify({'success': False, 'error': 'Appointment not found'})
        
        # Create modification request
        modification_details = {
            'modification_type': modification_type,
            'reason': reason,
            'original_date': consultation.preferred_date.isoformat() if consultation.preferred_date else None,
            'original_type': consultation.consultation_type
        }
        
        if modification_type == 'reschedule' and new_date and new_time:
            new_datetime = datetime.strptime(f"{new_date} {new_time}", '%Y-%m-%d %H:%M')
            modification_details['new_date'] = new_datetime.isoformat()
        
        if modification_type == 'change_type' and new_appointment_type:
            modification_details['new_appointment_type'] = new_appointment_type
        
        if modification_type == 'add_services' and additional_services:
            modification_details['additional_services'] = additional_services
        
        # Update consultation status
        consultation.status = 'modification_requested'
        consultation.user_message += f"\n\nModification request: {modification_type}\nReason: {reason}"
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Modification request submitted successfully. The clinic will respond within 24 hours.',
            'consultation_id': consultation.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting appointment modification: {e}")
        return jsonify({'success': False, 'error': 'Failed to submit modification request'})

@enhanced_booking_bp.route('/api/availability/<int:clinic_id>')
def get_enhanced_availability(clinic_id):
    """Get detailed availability for different appointment types"""
    appointment_type = request.args.get('type', 'consultation')
    date_range = request.args.get('date_range', '7')  # days
    
    # Generate availability data for the specified range
    availability = []
    
    for day_offset in range(int(date_range)):
        date = datetime.now() + timedelta(days=day_offset)
        date_str = date.strftime('%Y-%m-%d')
        
        # Skip weekends for some appointment types
        if date.weekday() >= 5 and appointment_type in ['procedure', 'pre_op']:
            continue
        
        day_availability = {
            'date': date_str,
            'day_name': date.strftime('%A'),
            'appointment_types': {}
        }
        
        # Generate slots based on appointment type
        for apt_type, info in APPOINTMENT_TYPES.items():
            slots = []
            duration = info['duration']
            
            # Generate slots from 9 AM to 6 PM
            start_hour = 9
            end_hour = 18
            
            current_time = start_hour * 60  # minutes from midnight
            end_time = end_hour * 60
            
            while current_time + duration <= end_time:
                hour = current_time // 60
                minute = current_time % 60
                time_str = f"{hour:02d}:{minute:02d}"
                
                # Randomly mark some slots as unavailable
                is_available = (hour + minute + day_offset) % 3 != 0
                
                slots.append({
                    'time': time_str,
                    'available': is_available,
                    'price': info['price_range'][0] if is_available else None
                })
                
                current_time += duration
            
            day_availability['appointment_types'][apt_type] = slots
        
        availability.append(day_availability)
    
    return jsonify({
        'clinic_id': clinic_id,
        'appointment_type': appointment_type,
        'availability': availability
    })

@enhanced_booking_bp.route('/api/waitlist-status/<int:consultation_id>')
@login_required
def get_waitlist_status(consultation_id):
    """Get current waitlist status"""
    consultation = db.session.query(ClinicConsultation).filter_by(
        id=consultation_id,
        user_id=current_user.id,
        consultation_type='waitlist'
    ).first()
    
    if not consultation:
        return jsonify({'error': 'Waitlist entry not found'})
    
    # Simulate waitlist position and estimated wait time
    position_in_queue = 7  # Would calculate from actual data
    estimated_wait_weeks = 3
    
    return jsonify({
        'consultation_id': consultation_id,
        'status': consultation.status,
        'position_in_queue': position_in_queue,
        'estimated_wait_weeks': estimated_wait_weeks,
        'priority_level': consultation.waitlist_details.get('priority_level', 'normal'),
        'created_date': consultation.created_at.isoformat(),
        'procedure': consultation.procedure_interest
    })