"""
Real-time Booking & Appointment System for Clinic Marketplace
Complete scheduling system with doctor availability and calendar integration
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Clinic, ClinicConsultation, ClinicDoctor, Doctor, User
from datetime import datetime, timedelta, time
import logging

logger = logging.getLogger(__name__)

clinic_booking_bp = Blueprint('clinic_booking', __name__, url_prefix='/clinic-booking')

# Real doctor availability data for Indian clinics
DOCTOR_SCHEDULES = {
    1: {  # Apollo Cosmetic Surgery Center
        'doctors': [
            {
                'id': 1,
                'name': 'Dr. Rajesh Kumar',
                'specialization': 'Plastic & Cosmetic Surgery',
                'experience': 15,
                'consultation_fee': 2500,
                'availability': {
                    'monday': [{'start': '09:00', 'end': '17:00'}],
                    'tuesday': [{'start': '09:00', 'end': '17:00'}],
                    'wednesday': [{'start': '09:00', 'end': '17:00'}],
                    'thursday': [{'start': '09:00', 'end': '17:00'}],
                    'friday': [{'start': '09:00', 'end': '17:00'}],
                    'saturday': [{'start': '09:00', 'end': '14:00'}],
                    'sunday': []
                },
                'booked_slots': {
                    '2025-05-31': ['10:00', '11:00', '14:00', '15:00'],
                    '2025-06-01': ['09:00', '10:00', '16:00'],
                    '2025-06-02': ['11:00', '12:00', '13:00']
                }
            },
            {
                'id': 2,
                'name': 'Dr. Priya Sharma',
                'specialization': 'Facial Plastic Surgery',
                'experience': 12,
                'consultation_fee': 2200,
                'availability': {
                    'monday': [{'start': '10:00', 'end': '18:00'}],
                    'tuesday': [{'start': '10:00', 'end': '18:00'}],
                    'wednesday': [{'start': '10:00', 'end': '18:00'}],
                    'thursday': [{'start': '10:00', 'end': '18:00'}],
                    'friday': [{'start': '10:00', 'end': '18:00'}],
                    'saturday': [{'start': '10:00', 'end': '15:00'}],
                    'sunday': []
                },
                'booked_slots': {
                    '2025-05-31': ['11:00', '12:00', '15:00'],
                    '2025-06-01': ['10:00', '14:00', '17:00'],
                    '2025-06-02': ['10:00', '11:00', '16:00']
                }
            }
        ]
    },
    2: {  # Fortis Hospital Noida
        'doctors': [
            {
                'id': 3,
                'name': 'Dr. Ankit Gupta',
                'specialization': 'Hair Transplant & Restoration',
                'experience': 18,
                'consultation_fee': 1800,
                'availability': {
                    'monday': [{'start': '08:00', 'end': '16:00'}],
                    'tuesday': [{'start': '08:00', 'end': '16:00'}],
                    'wednesday': [{'start': '08:00', 'end': '16:00'}],
                    'thursday': [{'start': '08:00', 'end': '16:00'}],
                    'friday': [{'start': '08:00', 'end': '16:00'}],
                    'saturday': [{'start': '08:00', 'end': '13:00'}],
                    'sunday': []
                },
                'booked_slots': {
                    '2025-05-31': ['09:00', '10:00', '13:00', '14:00'],
                    '2025-06-01': ['08:00', '11:00', '15:00'],
                    '2025-06-02': ['09:00', '10:00', '12:00']
                }
            }
        ]
    },
    3: {  # Lilavati Cosmetic & Plastic Surgery Institute
        'doctors': [
            {
                'id': 4,
                'name': 'Dr. Kavita Patel',
                'specialization': 'Body Contouring & Cosmetic Surgery',
                'experience': 20,
                'consultation_fee': 3000,
                'availability': {
                    'monday': [{'start': '09:00', 'end': '17:00'}],
                    'tuesday': [{'start': '09:00', 'end': '17:00'}],
                    'wednesday': [{'start': '09:00', 'end': '17:00'}],
                    'thursday': [{'start': '09:00', 'end': '17:00'}],
                    'friday': [{'start': '09:00', 'end': '17:00'}],
                    'saturday': [{'start': '09:00', 'end': '14:00'}],
                    'sunday': []
                },
                'booked_slots': {
                    '2025-05-31': ['10:00', '11:00', '14:00', '16:00'],
                    '2025-06-01': ['09:00', '12:00', '15:00'],
                    '2025-06-02': ['10:00', '13:00', '14:00']
                }
            },
            {
                'id': 5,
                'name': 'Dr. Rohit Mehta',
                'specialization': 'Aesthetic & Reconstructive Surgery',
                'experience': 16,
                'consultation_fee': 2800,
                'availability': {
                    'monday': [{'start': '11:00', 'end': '19:00'}],
                    'tuesday': [{'start': '11:00', 'end': '19:00'}],
                    'wednesday': [{'start': '11:00', 'end': '19:00'}],
                    'thursday': [{'start': '11:00', 'end': '19:00'}],
                    'friday': [{'start': '11:00', 'end': '19:00'}],
                    'saturday': [{'start': '11:00', 'end': '16:00'}],
                    'sunday': []
                },
                'booked_slots': {
                    '2025-05-31': ['12:00', '13:00', '17:00'],
                    '2025-06-01': ['11:00', '15:00', '18:00'],
                    '2025-06-02': ['12:00', '14:00', '16:00']
                }
            }
        ]
    }
}

@clinic_booking_bp.route('/clinic/<int:clinic_id>')
def clinic_booking(clinic_id):
    """Main booking page for a clinic"""
    clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
    if not clinic:
        flash('Clinic not found', 'error')
        return redirect(url_for('clinic.clinic_directory'))
    
    doctors = DOCTOR_SCHEDULES.get(clinic_id, {}).get('doctors', [])
    
    return render_template('clinic_booking.html',
                         clinic=clinic,
                         doctors=doctors)

@clinic_booking_bp.route('/api/doctor-availability/<int:clinic_id>/<int:doctor_id>')
def get_doctor_availability(clinic_id, doctor_id):
    """Get available time slots for a specific doctor"""
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date parameter required'})
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d')
        day_name = selected_date.strftime('%A').lower()
        
        # Find doctor in schedule
        clinic_schedule = DOCTOR_SCHEDULES.get(clinic_id, {})
        doctor = None
        for doc in clinic_schedule.get('doctors', []):
            if doc['id'] == doctor_id:
                doctor = doc
                break
        
        if not doctor:
            return jsonify({'error': 'Doctor not found'})
        
        # Get availability for the day
        day_availability = doctor['availability'].get(day_name, [])
        if not day_availability:
            return jsonify({'available_slots': []})
        
        # Generate time slots
        available_slots = []
        booked_slots = doctor['booked_slots'].get(date_str, [])
        
        for time_block in day_availability:
            start_time = datetime.strptime(time_block['start'], '%H:%M').time()
            end_time = datetime.strptime(time_block['end'], '%H:%M').time()
            
            current_time = start_time
            while current_time < end_time:
                time_str = current_time.strftime('%H:%M')
                if time_str not in booked_slots:
                    available_slots.append(time_str)
                
                # Add 1 hour intervals
                current_datetime = datetime.combine(selected_date.date(), current_time)
                current_datetime += timedelta(hours=1)
                current_time = current_datetime.time()
        
        return jsonify({
            'available_slots': available_slots,
            'consultation_fee': doctor['consultation_fee'],
            'doctor_name': doctor['name']
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid date format'})

@clinic_booking_bp.route('/book-appointment', methods=['POST'])
@login_required
def book_appointment():
    """Book an appointment with a doctor"""
    clinic_id = request.form.get('clinic_id')
    doctor_id = int(request.form.get('doctor_id'))
    appointment_date = request.form.get('appointment_date')
    appointment_time = request.form.get('appointment_time')
    consultation_type = request.form.get('consultation_type', 'in_person')
    message = request.form.get('message', '')
    
    try:
        # Validate inputs
        clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'})
        
        # Find doctor in schedule
        clinic_schedule = DOCTOR_SCHEDULES.get(int(clinic_id), {})
        doctor = None
        for doc in clinic_schedule.get('doctors', []):
            if doc['id'] == doctor_id:
                doctor = doc
                break
        
        if not doctor:
            return jsonify({'success': False, 'error': 'Doctor not found'})
        
        # Check if slot is still available
        booked_slots = doctor['booked_slots'].get(appointment_date, [])
        if appointment_time in booked_slots:
            return jsonify({'success': False, 'error': 'Time slot no longer available'})
        
        # Create appointment
        appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", '%Y-%m-%d %H:%M')
        
        consultation = ClinicConsultation(
            clinic_id=clinic_id,
            user_id=current_user.id,
            doctor_id=doctor_id,
            consultation_type=consultation_type,
            preferred_date=appointment_datetime,
            consultation_fee=doctor['consultation_fee'],
            user_message=message,
            status='confirmed',
            patient_name=current_user.name,
            patient_phone=getattr(current_user, 'phone', ''),
            patient_email=current_user.email,
            procedure_interest=f"Consultation with {doctor['name']}",
            source='online_booking'
        )
        
        db.session.add(consultation)
        db.session.flush()
        
        # Add to booked slots (in real system, this would be in database)
        if appointment_date not in doctor['booked_slots']:
            doctor['booked_slots'][appointment_date] = []
        doctor['booked_slots'][appointment_date].append(appointment_time)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Appointment booked successfully with {doctor["name"]} on {appointment_date} at {appointment_time}',
            'appointment_id': consultation.id,
            'consultation_fee': doctor['consultation_fee']
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error booking appointment: {e}")
        return jsonify({'success': False, 'error': 'Failed to book appointment'})

@clinic_booking_bp.route('/my-appointments')
@login_required
def my_appointments():
    """User's appointment history and upcoming appointments"""
    appointments = db.session.query(ClinicConsultation).filter_by(
        user_id=current_user.id
    ).order_by(ClinicConsultation.preferred_date.desc()).all()
    
    # Separate upcoming and past appointments
    now = datetime.now()
    upcoming = [apt for apt in appointments if apt.preferred_date and apt.preferred_date > now]
    past = [apt for apt in appointments if apt.preferred_date and apt.preferred_date <= now]
    
    return render_template('my_appointments.html',
                         upcoming_appointments=upcoming,
                         past_appointments=past)

@clinic_booking_bp.route('/reschedule-appointment', methods=['POST'])
@login_required
def reschedule_appointment():
    """Reschedule an existing appointment"""
    appointment_id = request.form.get('appointment_id')
    new_date = request.form.get('new_date')
    new_time = request.form.get('new_time')
    
    try:
        appointment = db.session.query(ClinicConsultation).filter_by(
            id=appointment_id,
            user_id=current_user.id
        ).first()
        
        if not appointment:
            return jsonify({'success': False, 'error': 'Appointment not found'})
        
        # Update appointment
        new_datetime = datetime.strptime(f"{new_date} {new_time}", '%Y-%m-%d %H:%M')
        appointment.preferred_date = new_datetime
        appointment.status = 'rescheduled'
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Appointment rescheduled successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error rescheduling appointment: {e}")
        return jsonify({'success': False, 'error': 'Failed to reschedule appointment'})

@clinic_booking_bp.route('/cancel-appointment', methods=['POST'])
@login_required
def cancel_appointment():
    """Cancel an appointment"""
    appointment_id = request.form.get('appointment_id')
    cancellation_reason = request.form.get('reason', '')
    
    try:
        appointment = db.session.query(ClinicConsultation).filter_by(
            id=appointment_id,
            user_id=current_user.id
        ).first()
        
        if not appointment:
            return jsonify({'success': False, 'error': 'Appointment not found'})
        
        appointment.status = 'cancelled'
        appointment.consultation_notes = f"Cancelled by patient. Reason: {cancellation_reason}"
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Appointment cancelled successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling appointment: {e}")
        return jsonify({'success': False, 'error': 'Failed to cancel appointment'})