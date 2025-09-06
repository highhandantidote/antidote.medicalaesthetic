"""
Comprehensive Clinic Profile Management Routes
Implementation of the complete clinic profile and dashboard system
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from sqlalchemy import desc, and_, or_, text, func
from models import db, Clinic, User, Procedure, Category, Doctor
from werkzeug.utils import secure_filename
from datetime import datetime
import logging
import json
import os

# Create blueprint for comprehensive clinic management
comprehensive_clinic_bp = Blueprint('comprehensive_clinic', __name__, url_prefix='/clinic')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function to check clinic ownership
def is_clinic_owner(clinic_id):
    """Check if current user owns the clinic"""
    if not current_user.is_authenticated:
        return False
    
    try:
        clinic = db.session.execute(text("""
            SELECT owner_user_id FROM clinics WHERE id = :clinic_id
        """), {"clinic_id": clinic_id}).fetchone()
        
        return clinic and clinic[0] == current_user.id
    except Exception as e:
        logger.error(f"Error checking clinic ownership: {e}")
        return False

# File upload helper
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder):
    """Save uploaded file and return the file path"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to prevent conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + filename
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join('static', 'uploads', folder)
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Return the web-accessible path
        return f"/static/uploads/{folder}/{filename}"
    return None

# ============================================================================
# PUBLIC CLINIC PROFILE ROUTES
# ============================================================================



# ============================================================================
# CLINIC DASHBOARD ROUTES
# ============================================================================

@comprehensive_clinic_bp.route('/dashboard')
@login_required
def dashboard():
    """Main clinic dashboard"""
    try:
        # Get user's clinic
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            flash('No clinic found for your account. Please contact support.', 'error')
            return redirect(url_for('web.index'))
        
        clinic = dict(clinic_result._mapping)
        
        # Get dashboard metrics
        metrics = {
            'total_packages': 0,
            'total_leads': 0,
            'total_doctors': 0,
            'profile_completion': 0
        }
        
        # Get package count
        package_count = db.session.execute(text("""
            SELECT COUNT(*) FROM clinic_packages WHERE clinic_id = :clinic_id AND is_active = true
        """), {"clinic_id": clinic['id']}).scalar()
        metrics['total_packages'] = package_count or 0
        
        # Get lead count
        lead_count = db.session.execute(text("""
            SELECT COUNT(*) FROM clinic_consultations WHERE clinic_id = :clinic_id
        """), {"clinic_id": clinic['id']}).scalar()
        metrics['total_leads'] = lead_count or 0
        
        # Get doctor count
        doctor_count = db.session.execute(text("""
            SELECT COUNT(*) FROM clinic_doctors WHERE clinic_id = :clinic_id AND is_active = true
        """), {"clinic_id": clinic['id']}).scalar()
        metrics['total_doctors'] = doctor_count or 0
        
        # Calculate profile completion
        completion_fields = ['name', 'address', 'city', 'working_hours', 'description']
        completed_fields = sum(1 for field in completion_fields if clinic.get(field))
        metrics['profile_completion'] = int((completed_fields / len(completion_fields)) * 100)
        
        return render_template('clinic/dashboard.html', clinic=clinic, metrics=metrics)
        
    except Exception as e:
        logger.error(f"Error loading clinic dashboard: {e}")
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('web.index'))

@comprehensive_clinic_bp.route('/dashboard/profile')
@login_required
def dashboard_profile():
    """Profile management dashboard"""
    try:
        # Get user's clinic
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            flash('No clinic found for your account.', 'error')
            return redirect(url_for('web.index'))
        
        clinic = dict(clinic_result._mapping)
        
        # Parse JSON fields for display
        if clinic.get('clinic_highlights'):
            try:
                clinic['clinic_highlights'] = json.loads(clinic['clinic_highlights'])
            except:
                clinic['clinic_highlights'] = []
        
        if clinic.get('popular_procedures'):
            try:
                clinic['popular_procedures'] = json.loads(clinic['popular_procedures'])
            except:
                clinic['popular_procedures'] = []
        
        # Get all procedures for selection
        all_procedures_result = db.session.execute(text("""
            SELECT id, procedure_name FROM procedures ORDER BY procedure_name
        """)).fetchall()
        
        all_procedures = [dict(row._mapping) for row in all_procedures_result]
        
        # Get all categories for specialties
        categories_result = db.session.execute(text("""
            SELECT id, name FROM categories ORDER BY name
        """)).fetchall()
        
        categories = [dict(row._mapping) for row in categories_result]
        
        return render_template('clinic/dashboard/profile_management.html',
                             clinic=clinic,
                             all_procedures=all_procedures,
                             categories=categories)
                             
    except Exception as e:
        logger.error(f"Error loading profile management: {e}")
        flash('Error loading profile management. Please try again.', 'error')
        return redirect(url_for('comprehensive_clinic.dashboard'))

# ============================================================================
# PROFILE UPDATE ROUTES
# ============================================================================

@comprehensive_clinic_bp.route('/dashboard/update-basic-info', methods=['POST'])
@login_required
def update_basic_info():
    """Update clinic basic information"""
    try:
        # Get user's clinic
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        
        # Handle file upload
        profile_image_url = None
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename:
                profile_image_url = save_uploaded_file(file, 'clinic_profiles')
        
        # Update basic information
        update_query = """
            UPDATE clinics SET
                name = :name,
                address = :address,
                city = :city,
                state = :state,
                working_hours = :working_hours,
                description = :description,
                updated_at = :updated_at
        """
        
        params = {
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'working_hours': request.form.get('working_hours'),
            'description': request.form.get('description'),
            'updated_at': datetime.utcnow()
        }
        
        if profile_image_url:
            update_query += ", profile_image = :profile_image"
            params['profile_image'] = profile_image_url
        
        update_query += " WHERE id = :clinic_id"
        params['clinic_id'] = clinic_id
        
        db.session.execute(text(update_query), params)
        db.session.commit()
        
        return jsonify({'success': True, 'reload': bool(profile_image_url)})
        
    except Exception as e:
        logger.error(f"Error updating basic info: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update basic information'})

@comprehensive_clinic_bp.route('/dashboard/update-banner', methods=['POST'])
@login_required
def update_banner():
    """Update promotional banner"""
    try:
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        
        if request.form.get('remove_banner'):
            # Remove banner
            db.session.execute(text("""
                UPDATE clinics SET promotional_banner_url = NULL WHERE id = :clinic_id
            """), {"clinic_id": clinic_id})
            db.session.commit()
            return jsonify({'success': True, 'reload': True})
        
        # Handle banner upload
        if 'banner_image' in request.files:
            file = request.files['banner_image']
            if file and file.filename:
                banner_url = save_uploaded_file(file, 'clinic_banners')
                
                if banner_url:
                    db.session.execute(text("""
                        UPDATE clinics SET promotional_banner_url = :banner_url WHERE id = :clinic_id
                    """), {"banner_url": banner_url, "clinic_id": clinic_id})
                    db.session.commit()
                    
                    return jsonify({'success': True, 'reload': True})
        
        return jsonify({'success': False, 'message': 'No valid banner image provided'})
        
    except Exception as e:
        logger.error(f"Error updating banner: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update banner'})

@comprehensive_clinic_bp.route('/dashboard/update-highlights', methods=['POST'])
@login_required
def update_highlights():
    """Update clinic highlights"""
    try:
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        highlights = json.loads(request.form.get('highlights', '[]'))
        
        db.session.execute(text("""
            UPDATE clinics SET clinic_highlights = :highlights WHERE id = :clinic_id
        """), {"highlights": json.dumps(highlights), "clinic_id": clinic_id})
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating highlights: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update highlights'})

@comprehensive_clinic_bp.route('/dashboard/update-popular-procedures', methods=['POST'])
@login_required
def update_popular_procedures():
    """Update popular procedures"""
    try:
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        procedures = json.loads(request.form.get('popular_procedures', '[]'))
        
        # Limit to 5 procedures
        if len(procedures) > 5:
            procedures = procedures[:5]
        
        db.session.execute(text("""
            UPDATE clinics SET popular_procedures = :procedures WHERE id = :clinic_id
        """), {"procedures": json.dumps(procedures), "clinic_id": clinic_id})
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating popular procedures: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update popular procedures'})

@comprehensive_clinic_bp.route('/dashboard/update-specialties', methods=['POST'])
@login_required
def update_specialties():
    """Update clinic specialties"""
    try:
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        specialties = json.loads(request.form.get('specialties', '[]'))
        specialties_str = ','.join(specialties)
        
        db.session.execute(text("""
            UPDATE clinics SET specialties = :specialties WHERE id = :clinic_id
        """), {"specialties": specialties_str, "clinic_id": clinic_id})
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating specialties: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update specialties'})

@comprehensive_clinic_bp.route('/dashboard/update-contact', methods=['POST'])
@login_required
def update_contact():
    """Update contact information"""
    try:
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        
        db.session.execute(text("""
            UPDATE clinics SET
                cta_whatsapp_number = :whatsapp,
                cta_phone_number = :phone,
                email = :email,
                website = :website
            WHERE id = :clinic_id
        """), {
            "whatsapp": request.form.get('cta_whatsapp_number'),
            "phone": request.form.get('cta_phone_number'),
            "email": request.form.get('email'),
            "website": request.form.get('website'),
            "clinic_id": clinic_id
        })
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating contact information: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update contact information'})

# ============================================================================
# DOCTOR MANAGEMENT ROUTES
# ============================================================================

@comprehensive_clinic_bp.route('/dashboard/doctors')
@login_required
def dashboard_doctors():
    """Doctor management dashboard"""
    try:
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            flash('No clinic found for your account.', 'error')
            return redirect(url_for('web.index'))
        
        clinic_id = clinic_result[0]
        
        # Get clinic doctors
        doctors_result = db.session.execute(text("""
            SELECT d.*, cd.role, cd.is_primary, cd.is_active, cd.id as clinic_doctor_id
            FROM doctors d
            JOIN clinic_doctors cd ON d.id = cd.doctor_id
            WHERE cd.clinic_id = :clinic_id
            ORDER BY cd.is_primary DESC, d.name
        """), {"clinic_id": clinic_id}).fetchall()
        
        doctors = [dict(row._mapping) for row in doctors_result]
        
        return render_template('clinic/dashboard/doctor_management.html',
                             doctors=doctors,
                             clinic_id=clinic_id)
                             
    except Exception as e:
        logger.error(f"Error loading doctor management: {e}")
        flash('Error loading doctor management. Please try again.', 'error')
        return redirect(url_for('comprehensive_clinic.dashboard'))

@comprehensive_clinic_bp.route('/dashboard/add-doctor', methods=['POST'])
@login_required
def add_doctor():
    """Add new doctor to clinic"""
    try:
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        
        # Create doctor with pending verification status
        doctor_data = {
            'name': request.form.get('name'),
            'qualification': request.form.get('qualification'),
            'specialization': request.form.get('specialization'),
            'experience_years': int(request.form.get('experience_years', 0)),
            'medical_license': request.form.get('medical_license'),
            'bio': request.form.get('bio'),
            'consultation_fee': int(request.form.get('consultation_fee', 0)),
            'verification_status': 'pending_verification',
            'created_at': datetime.utcnow()
        }
        
        # Insert doctor
        doctor_insert = db.session.execute(text("""
            INSERT INTO doctors (name, qualification, specialization, experience_years, 
                               medical_license, bio, consultation_fee, verification_status, created_at)
            VALUES (:name, :qualification, :specialization, :experience_years,
                    :medical_license, :bio, :consultation_fee, :verification_status, :created_at)
            RETURNING id
        """), doctor_data)
        
        try:
            doctor_result = doctor_insert.fetchone()
            if not doctor_result:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Failed to create doctor profile'})
            
            doctor_id = doctor_result[0]
        except Exception as e:
            logger.error(f"Error inserting doctor: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Database error creating doctor profile'})
        
        # Associate doctor with clinic
        db.session.execute(text("""
            INSERT INTO clinic_doctors (clinic_id, doctor_id, role, is_active, is_primary)
            VALUES (:clinic_id, :doctor_id, :role, true, :is_primary)
        """), {
            "clinic_id": clinic_id,
            "doctor_id": doctor_id,
            "role": request.form.get('role', 'doctor'),
            "is_primary": request.form.get('is_primary') == 'true'
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Doctor added successfully. Pending admin verification.'})
        
    except Exception as e:
        logger.error(f"Error adding doctor: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to add doctor'})

# API route for consultation booking
@comprehensive_clinic_bp.route('/api/consultation/book', methods=['POST'])
def book_consultation():
    """Book consultation for clinic"""
    try:
        consultation_data = {
            'clinic_id': request.form.get('clinic_id'),
            'patient_name': request.form.get('patient_name'),
            'patient_phone': request.form.get('patient_phone'),
            'patient_email': request.form.get('patient_email'),
            'procedure_interest': request.form.get('procedure_interest'),
            'message': request.form.get('message'),
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        db.session.execute(text("""
            INSERT INTO clinic_consultations 
            (clinic_id, patient_name, patient_phone, patient_email, procedure_interest, message, status, created_at)
            VALUES (:clinic_id, :patient_name, :patient_phone, :patient_email, :procedure_interest, :message, :status, :created_at)
        """), consultation_data)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Consultation booked successfully'})
        
    except Exception as e:
        logger.error(f"Error booking consultation: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to book consultation'})