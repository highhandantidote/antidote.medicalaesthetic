"""
Admin routes for managing clinic applications and approvals.
Handles the workflow from Google Form submissions to clinic dashboard access.
"""

import logging
import csv
import io
import secrets
import string
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import text
from app import db
from models import ClinicApplication, Clinic, User
from email_notification_system import send_clinic_approval_email, send_clinic_rejection_email

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
admin_clinic_bp = Blueprint('admin_clinic', __name__, url_prefix='/admin')

def require_admin(f):
    """Decorator to require admin access."""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not hasattr(current_user, 'role') or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def generate_random_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def create_slug(name):
    """Create a URL-friendly slug from clinic name."""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    slug = slug.strip('-')
    
    # Ensure uniqueness
    base_slug = slug
    counter = 1
    while Clinic.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug

@admin_clinic_bp.route('/clinic-applications')
@login_required
@require_admin
def clinic_applications():
    """View all clinic applications."""
    try:
        applications = ClinicApplication.query.order_by(ClinicApplication.created_at.desc()).all()
        return render_template('admin/clinic_applications.html', applications=applications)
    except Exception as e:
        logger.error(f"Error loading clinic applications: {e}")
        flash('Error loading applications.', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_clinic_bp.route('/clinic-applications/add', methods=['POST'])
@login_required
@require_admin
def add_clinic_application():
    """Add a new clinic application manually."""
    try:
        # Get form data
        data = {
            'clinic_name': request.form.get('clinic_name', '').strip(),
            'contact_person': request.form.get('contact_person', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'address': request.form.get('address', '').strip(),
            'city': request.form.get('city', '').strip(),
            'state': request.form.get('state', '').strip(),
            'pincode': request.form.get('pincode', '').strip(),
            'website': request.form.get('website', '').strip(),
            'specialties': request.form.get('specialties', '').strip(),
            'description': request.form.get('description', '').strip(),
            'notes': request.form.get('notes', '').strip()
        }
        
        # Validate required fields
        required_fields = ['clinic_name', 'contact_person', 'email', 'phone', 'address', 'city', 'state']
        for field in required_fields:
            if not data[field]:
                flash(f'Please fill the {field.replace("_", " ").title()} field.', 'error')
                return redirect(url_for('admin_clinic.clinic_applications'))
        
        # Check for duplicate email
        existing = ClinicApplication.query.filter_by(email=data['email']).first()
        if existing:
            flash('An application with this email already exists.', 'error')
            return redirect(url_for('admin_clinic.clinic_applications'))
        
        # Create application
        application = ClinicApplication(**data)
        db.session.add(application)
        db.session.commit()
        
        flash('Application added successfully.', 'success')
        return redirect(url_for('admin_clinic.clinic_applications'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding application: {e}")
        flash('Error adding application.', 'error')
        return redirect(url_for('admin_clinic.clinic_applications'))

@admin_clinic_bp.route('/clinic-applications/bulk-import', methods=['POST'])
@login_required
@require_admin
def bulk_import_applications():
    """Bulk import applications from CSV."""
    try:
        if 'csv_file' not in request.files:
            flash('No file uploaded.', 'error')
            return redirect(url_for('admin_clinic.clinic_applications'))
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('admin_clinic.clinic_applications'))
        
        if not file.filename.lower().endswith('.csv'):
            flash('Please upload a CSV file.', 'error')
            return redirect(url_for('admin_clinic.clinic_applications'))
        
        # Read CSV content
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Map CSV columns to application fields
                data = {
                    'clinic_name': row.get('clinic_name', '').strip(),
                    'contact_person': row.get('contact_person', '').strip(),
                    'email': row.get('email', '').strip(),
                    'phone': row.get('phone', '').strip(),
                    'address': row.get('address', '').strip(),
                    'city': row.get('city', '').strip(),
                    'state': row.get('state', '').strip(),
                    'pincode': row.get('pincode', '').strip(),
                    'website': row.get('website', '').strip(),
                    'specialties': row.get('specialties', '').strip(),
                    'description': row.get('description', '').strip()
                }
                
                # Validate required fields
                required_fields = ['clinic_name', 'contact_person', 'email', 'phone', 'address', 'city', 'state']
                missing_fields = [field for field in required_fields if not data[field]]
                
                if missing_fields:
                    errors.append(f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}")
                    continue
                
                # Check for duplicate email
                existing = ClinicApplication.query.filter_by(email=data['email']).first()
                if existing:
                    errors.append(f"Row {row_num}: Email {data['email']} already exists")
                    continue
                
                # Create application
                application = ClinicApplication(**data)
                db.session.add(application)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue
        
        db.session.commit()
        
        if imported_count > 0:
            flash(f'Successfully imported {imported_count} applications.', 'success')
        
        if errors:
            flash(f'Errors encountered: {"; ".join(errors[:5])}', 'warning')
        
        return redirect(url_for('admin_clinic.clinic_applications'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing CSV: {e}")
        flash('Error processing CSV file.', 'error')
        return redirect(url_for('admin_clinic.clinic_applications'))

@admin_clinic_bp.route('/clinic-applications/<int:app_id>/approve', methods=['POST'])
@login_required
@require_admin
def approve_application(app_id):
    """Approve a clinic application and create clinic + user account."""
    try:
        application = ClinicApplication.query.get_or_404(app_id)
        
        if application.status != 'pending':
            return jsonify({'success': False, 'message': 'Application already processed'})
        
        # Generate password for clinic user
        password = generate_random_password()
        
        # Create user account for clinic
        user_data = {
            'username': application.email,
            'email': application.email,
            'password_hash': generate_password_hash(password),
            'role': 'clinic',
            'is_verified': True,
            'created_at': datetime.utcnow()
        }
        
        # Use raw SQL to create user to avoid model conflicts
        user_sql = """
            INSERT INTO users (username, email, password_hash, role, is_verified, created_at)
            VALUES (:username, :email, :password_hash, :role, :is_verified, :created_at)
            RETURNING id
        """
        
        user_result = db.session.execute(text(user_sql), user_data).fetchone()
        user_id = user_result[0]
        
        # Create clinic profile
        clinic_slug = create_slug(application.clinic_name)
        specialties_list = [s.strip() for s in application.specialties.split(',') if s.strip()] if application.specialties else []
        
        clinic_data = {
            'owner_user_id': user_id,
            'name': application.clinic_name,
            'slug': clinic_slug,
            'address': application.address,
            'city': application.city,
            'state': application.state,
            'pincode': application.pincode,
            'contact_number': application.phone,
            'email': application.email,
            'website': application.website,
            'description': application.description,
            'specialties': specialties_list,
            'is_approved': True,
            'verification_status': 'approved',
            'verification_date': datetime.utcnow(),
            'credit_balance': 100,  # Starting credit balance
            'created_at': datetime.utcnow()
        }
        
        # Use raw SQL for clinic creation
        clinic_sql = """
            INSERT INTO clinics (
                owner_user_id, name, slug, address, city, state, pincode, 
                contact_number, email, website, description, specialties,
                is_approved, verification_status, verification_date, 
                credit_balance, created_at
            ) VALUES (
                :owner_user_id, :name, :slug, :address, :city, :state, :pincode,
                :contact_number, :email, :website, :description, :specialties,
                :is_approved, :verification_status, :verification_date,
                :credit_balance, :created_at
            ) RETURNING id
        """
        
        clinic_result = db.session.execute(text(clinic_sql), clinic_data).fetchone()
        clinic_id = clinic_result[0]
        
        # Update application status
        application.status = 'approved'
        application.processed_by_user_id = current_user.id
        application.processed_at = datetime.utcnow()
        application.created_clinic_id = clinic_id
        
        db.session.commit()
        
        # Send approval email with credentials
        try:
            send_clinic_approval_email(
                email=application.email,
                clinic_name=application.clinic_name,
                contact_person=application.contact_person,
                login_email=application.email,
                password=password,
                dashboard_url=url_for('clinic.clinic_dashboard', _external=True)
            )
        except Exception as e:
            logger.error(f"Error sending approval email: {e}")
            # Don't fail the approval if email fails
        
        return jsonify({
            'success': True, 
            'message': f'Application approved. Clinic account created with email: {application.email}'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error approving application: {e}")
        return jsonify({'success': False, 'message': str(e)})

@admin_clinic_bp.route('/clinic-applications/<int:app_id>/reject', methods=['POST'])
@login_required
@require_admin
def reject_application(app_id):
    """Reject a clinic application."""
    try:
        application = ClinicApplication.query.get_or_404(app_id)
        
        if application.status != 'pending':
            return jsonify({'success': False, 'message': 'Application already processed'})
        
        data = request.get_json()
        rejection_reason = data.get('reason', 'No reason provided')
        
        # Update application status
        application.status = 'rejected'
        application.rejection_reason = rejection_reason
        application.processed_by_user_id = current_user.id
        application.processed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send rejection email
        try:
            send_clinic_rejection_email(
                email=application.email,
                clinic_name=application.clinic_name,
                contact_person=application.contact_person,
                reason=rejection_reason
            )
        except Exception as e:
            logger.error(f"Error sending rejection email: {e}")
        
        return jsonify({'success': True, 'message': 'Application rejected'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error rejecting application: {e}")
        return jsonify({'success': False, 'message': str(e)})

@admin_clinic_bp.route('/clinic-applications/<int:app_id>')
@login_required
@require_admin
def view_application(app_id):
    """View detailed clinic application."""
    try:
        application = ClinicApplication.query.get_or_404(app_id)
        return render_template('admin/clinic_application_detail.html', application=application)
    except Exception as e:
        logger.error(f"Error viewing application: {e}")
        flash('Error loading application details.', 'error')
        return redirect(url_for('admin_clinic.clinic_applications'))

def register_admin_clinic_routes(app):
    """Register admin clinic routes with the main app."""
    app.register_blueprint(admin_clinic_bp)
    logger.info("Admin clinic routes registered successfully")