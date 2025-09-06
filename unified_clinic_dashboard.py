"""
Unified Clinic Dashboard with Complete Profile Management
Consolidates all clinic management features into a single comprehensive dashboard
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from sqlalchemy import desc, and_, or_, text, func
from models import db, Clinic, Lead, User, Procedure, Category, Doctor
from werkzeug.utils import secure_filename
from google_places_service import google_places_service
from datetime import datetime, timedelta
import logging
import json
import os

# Create unified clinic dashboard blueprint
unified_clinic_bp = Blueprint('unified_clinic', __name__, url_prefix='/clinic')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File upload configuration
UPLOAD_FOLDER = 'static/uploads/clinics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, prefix='clinic'):
    """Save uploaded file and return the URL"""
    if file and allowed_file(file.filename):
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Generate secure filename with timestamp
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{prefix}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file
        file.save(filepath)
        
        # Return URL path
        return f"/static/uploads/clinics/{filename}"
    return None

# Helper functions
def get_clinic_for_user(user_id):
    """Get clinic owned by the current user"""
    try:
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics 
            WHERE owner_user_id = :user_id 
            LIMIT 1
        """), {'user_id': user_id}).fetchone()
        
        return dict(clinic_result._mapping) if clinic_result else None
    except Exception as e:
        logger.error(f"Error getting clinic for user {user_id}: {e}")
        return None

def get_dashboard_metrics(clinic_id):
    """Get comprehensive dashboard metrics"""
    try:
        # Total leads
        total_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads WHERE clinic_id = :clinic_id
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        # Pending leads
        pending_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE clinic_id = :clinic_id AND status = 'new'
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        # Monthly leads
        monthly_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE clinic_id = :clinic_id 
            AND created_at >= date_trunc('month', CURRENT_DATE)
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        # Credit balance
        credit_balance = db.session.execute(text("""
            SELECT COALESCE(credit_balance, 0) FROM clinics WHERE id = :clinic_id
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        # Package count
        package_count = db.session.execute(text("""
            SELECT COUNT(*) FROM packages WHERE clinic_id = :clinic_id AND is_active = true
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        # Doctor count
        doctor_count = db.session.execute(text("""
            SELECT COUNT(*) FROM doctors WHERE clinic_id = :clinic_id
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        return {
            'total_leads': total_leads,
            'pending_leads': pending_leads,
            'monthly_leads': monthly_leads,
            'credit_balance': credit_balance,
            'package_count': package_count,
            'doctor_count': doctor_count
        }
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return {
            'total_leads': 0,
            'pending_leads': 0,
            'monthly_leads': 0,
            'credit_balance': 0,
            'package_count': 0,
            'doctor_count': 0
        }

# ============================================================================
# MAIN DASHBOARD ROUTE
# ============================================================================

@unified_clinic_bp.route('/dashboard')
@login_required
def dashboard():
    """Unified clinic dashboard with all management features"""
    try:
        # Debug logging
        logger.info(f"Clinic dashboard accessed by user: {current_user.email}, role: {current_user.role}")
        
        # Check if user has clinic_owner role
        if current_user.role != 'clinic_owner':
            logger.warning(f"Access denied - user role is {current_user.role}, not clinic_owner")
            flash('You do not have permission to access this clinic dashboard.', 'warning')
            return redirect(url_for('web.index'))
        
        clinic = get_clinic_for_user(current_user.id)
        logger.info(f"Clinic found for user {current_user.id}: {clinic is not None}")
        
        if not clinic:
            logger.error(f"No clinic profile found for user {current_user.id}")
            flash('No clinic profile found. Please contact support to set up your clinic profile.', 'warning')
            return redirect(url_for('web.index'))
        
        # Get dashboard metrics
        metrics = get_dashboard_metrics(clinic['id'])
        
        # Get recent leads
        recent_leads_result = db.session.execute(text("""
            SELECT l.*, p.title as procedure_name, p.price_actual as min_cost, p.price_discounted as max_cost
            FROM leads l
            LEFT JOIN packages p ON l.package_id = p.id
            WHERE l.clinic_id = :clinic_id
            ORDER BY l.created_at DESC
            LIMIT 5
        """), {'clinic_id': clinic['id']}).fetchall()
        
        recent_leads = [dict(row._mapping) for row in recent_leads_result]
        
        # Get clinic packages
        packages_result = db.session.execute(text("""
            SELECT * FROM packages 
            WHERE clinic_id = :clinic_id AND is_active = true
            ORDER BY created_at DESC
            LIMIT 10
        """), {'clinic_id': clinic['id']}).fetchall()
        
        packages = [dict(row._mapping) for row in packages_result]
        
        # Get clinic doctors using the same logic as profile page
        doctors_result = db.session.execute(text("""
            SELECT d.*, cd.role, cd.is_primary 
            FROM doctors d
            JOIN clinic_doctors cd ON d.id = cd.doctor_id
            WHERE cd.clinic_id = :clinic_id AND cd.is_active = true
            ORDER BY cd.is_primary DESC, d.name
            LIMIT 10
        """), {'clinic_id': clinic['id']}).fetchall()
        
        doctors = [dict(row._mapping) for row in doctors_result]
        
        # Get all categories for specialty selection
        categories_result = db.session.execute(text("""
            SELECT id, name FROM categories ORDER BY name
        """)).fetchall()
        
        categories = [dict(row._mapping) for row in categories_result]
        
        # Get all procedures for popular procedures selection
        procedures_result = db.session.execute(text("""
            SELECT id, procedure_name, min_cost, max_cost FROM procedures 
            ORDER BY procedure_name LIMIT 100
        """)).fetchall()
        
        procedures = [dict(row._mapping) for row in procedures_result]
        
        return render_template('clinic/unified_dashboard.html',
                             clinic=clinic,
                             metrics=metrics,
                             recent_leads=recent_leads,
                             packages=packages,
                             doctors=doctors,
                             categories=categories,
                             procedures=procedures)
                             
    except Exception as e:
        logger.error(f"Error loading unified clinic dashboard: {e}")
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('web.index'))

# ============================================================================
# PROFILE MANAGEMENT ROUTES
# ============================================================================

@unified_clinic_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update clinic basic profile information"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        # Get form data
        name = request.form.get('name', '') or ''
        address = request.form.get('address', '') or ''
        city = request.form.get('city', '') or ''
        state = request.form.get('state', '') or ''
        working_hours = request.form.get('working_hours', '') or ''
        contact_number = request.form.get('contact_number', '') or ''
        whatsapp_number = request.form.get('whatsapp_number', '') or ''
        description = request.form.get('description', '') or ''
        
        # Update clinic profile
        db.session.execute(text("""
            UPDATE clinics SET 
                name = :name,
                address = :address,
                city = :city,
                state = :state,
                working_hours = :working_hours,
                contact_number = :contact_number,
                whatsapp_number = :whatsapp_number,
                description = :description,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :clinic_id
        """), {
            'name': name,
            'address': address,
            'city': city,
            'state': state,
            'working_hours': working_hours,
            'contact_number': contact_number,
            'whatsapp_number': whatsapp_number,
            'description': description,
            'clinic_id': clinic['id']
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating profile'})

# Removed duplicate function definitions - proper routes are defined later in this file

@unified_clinic_bp.route('/cta/update', methods=['POST'])
@login_required
def update_cta():
    """Update clinic CTA contact information"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        cta_phone = request.form.get('cta_phone_number', '').strip()
        cta_whatsapp = request.form.get('cta_whatsapp_number', '').strip()
        
        db.session.execute(text("""
            UPDATE clinics SET 
                cta_phone_number = :cta_phone,
                cta_whatsapp_number = :cta_whatsapp,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :clinic_id
        """), {
            'cta_phone': cta_phone,
            'cta_whatsapp': cta_whatsapp,
            'clinic_id': clinic['id']
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Contact settings updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating CTA settings: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating contact settings'})

# ============================================================================
# PACKAGE MANAGEMENT ROUTES  
# ============================================================================

@unified_clinic_bp.route('/packages')
@login_required
def packages():
    """Package management page"""
    return redirect(url_for('unified_clinic.dashboard') + '#packages')

@unified_clinic_bp.route('/packages/add', methods=['GET', 'POST'])
@login_required
def add_package():
    """Add new treatment package"""
    if request.method == 'POST':
        try:
            clinic = get_clinic_for_user(current_user.id)
            if not clinic:
                flash('Clinic not found', 'error')
                return redirect(url_for('unified_clinic.dashboard'))
            
            # Get comprehensive form data
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            
            # Validate required fields
            if not title:
                flash('Package title is required', 'error')
                return redirect(url_for('unified_clinic.add_package'))
            
            if not description:
                flash('Package description is required', 'error')
                return redirect(url_for('unified_clinic.add_package'))
            
            # Handle pricing with proper validation
            try:
                price_actual_str = request.form.get('price_actual', '0').strip()
                price_actual = float(price_actual_str) if price_actual_str else 0.0
                if price_actual <= 0:
                    flash('Regular price must be greater than 0', 'error')
                    return redirect(url_for('unified_clinic.add_package'))
            except (ValueError, TypeError):
                flash('Invalid regular price format', 'error')
                return redirect(url_for('unified_clinic.add_package'))
            
            try:
                price_discounted_str = request.form.get('price_discounted', '').strip()
                price_discounted = float(price_discounted_str) if price_discounted_str else None
            except (ValueError, TypeError):
                price_discounted = None
            
            duration = request.form.get('duration', '').strip()
            
            # Get additional fields
            key_highlights = request.form.get('key_highlights', '').strip()
            procedure_breakdown = request.form.get('procedure_breakdown', '').strip()
            includes = request.form.get('includes', '').strip()
            excludes = request.form.get('excludes', '').strip()
            pre_procedure_care = request.form.get('pre_procedure_care', '').strip()
            post_procedure_care = request.form.get('post_procedure_care', '').strip()
            recovery_timeline = request.form.get('recovery_timeline', '').strip()
            risks_complications = request.form.get('risks_complications', '').strip()
            expected_results = request.form.get('expected_results', '').strip()
            maintenance_schedule = request.form.get('maintenance_schedule', '').strip()
            
            # Process results gallery data
            results_gallery = []
            result_titles = request.form.getlist('result_title[]')
            result_doctor_ids = request.form.getlist('result_doctor_id[]')
            result_descriptions = request.form.getlist('result_description[]')
            result_before_images = request.files.getlist('result_before_image[]')
            result_after_images = request.files.getlist('result_after_image[]')
            
            # Process each result set
            for i in range(len(result_titles)):
                if result_titles[i].strip():  # Only process if title is provided
                    before_image_url = None
                    after_image_url = None
                    
                    # Handle before image upload
                    if i < len(result_before_images) and result_before_images[i].filename:
                        before_image_url = save_uploaded_file(result_before_images[i], 'gallery')
                    
                    # Handle after image upload
                    if i < len(result_after_images) and result_after_images[i].filename:
                        after_image_url = save_uploaded_file(result_after_images[i], 'gallery')
                    
                    results_gallery.append({
                        'title': result_titles[i].strip(),
                        'doctor_id': int(result_doctor_ids[i]) if i < len(result_doctor_ids) and result_doctor_ids[i] else None,
                        'description': result_descriptions[i].strip() if i < len(result_descriptions) else '',
                        'before_image': before_image_url,
                        'after_image': after_image_url
                    })
            
            # Generate slug from title
            import re
            slug = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
            slug = re.sub(r'\s+', '-', slug.strip())
            
            # Convert text fields to proper JSON or NULL if empty
            if key_highlights:
                try:
                    if key_highlights.startswith('[') or key_highlights.startswith('{'):
                        import ast
                        parsed = ast.literal_eval(key_highlights)
                        key_highlights = json.dumps(parsed)
                except:
                    pass
            else:
                key_highlights = None
            
            if procedure_breakdown:
                try:
                    if procedure_breakdown.startswith('[') or procedure_breakdown.startswith('{'):
                        import ast
                        parsed = ast.literal_eval(procedure_breakdown)
                        procedure_breakdown = json.dumps(parsed)
                except:
                    pass
            else:
                procedure_breakdown = None
            
            # Insert package with only existing columns
            db.session.execute(text("""
                INSERT INTO packages (
                    clinic_id, title, slug, description, 
                    price_actual, price_discounted, duration,
                    key_highlights, procedure_breakdown,
                    is_active, created_at
                ) VALUES (
                    :clinic_id, :title, :slug, :description,
                    :price_actual, :price_discounted, :duration,
                    :key_highlights, :procedure_breakdown,
                    true, CURRENT_TIMESTAMP
                )
            """), {
                'clinic_id': clinic['id'],
                'title': title,
                'slug': slug,
                'description': description,
                'price_actual': price_actual,
                'price_discounted': price_discounted,
                'duration': duration,
                'key_highlights': key_highlights,
                'procedure_breakdown': procedure_breakdown
            })
            
            # Get the package ID to save gallery images
            package_result = db.session.execute(text("""
                SELECT id FROM packages 
                WHERE clinic_id = :clinic_id AND title = :title AND slug = :slug
                ORDER BY created_at DESC LIMIT 1
            """), {
                'clinic_id': clinic['id'],
                'title': title,
                'slug': slug
            }).fetchone()
            
            if package_result and results_gallery:
                package_id = package_result[0]
                
                # Save gallery images to the package_doctor_gallery table
                for result in results_gallery:
                    db.session.execute(text("""
                        INSERT INTO package_doctor_gallery (
                            package_id, doctor_id, title, description, 
                            before_image_url, after_image_url
                        ) VALUES (
                            :package_id, :doctor_id, :title, :description,
                            :before_image_url, :after_image_url
                        )
                    """), {
                        'package_id': package_id,
                        'doctor_id': result['doctor_id'],
                        'title': result['title'],
                        'description': result['description'],
                        'before_image_url': result['before_image'],
                        'after_image_url': result['after_image']
                    })
            
            db.session.commit()
            
            flash('Package created successfully!', 'success')
            return redirect(url_for('unified_clinic.dashboard') + '#packages')
            
        except Exception as e:
            logger.error(f"Error adding package: {e}")
            db.session.rollback()
            flash('Error creating package. Please try again.', 'error')
            return redirect(url_for('unified_clinic.add_package'))
    
    # GET request - show the comprehensive package creation form
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            flash('Clinic not found', 'error')
            return redirect(url_for('web.index'))
        
        # Get categories for the form
        categories = db.session.execute(text("""
            SELECT id, name FROM categories ORDER BY name
        """)).fetchall()
        
        # Get procedures for the form
        procedures = db.session.execute(text("""
            SELECT id, procedure_name FROM procedures ORDER BY procedure_name LIMIT 100
        """)).fetchall()
        
        # Get clinic doctors for gallery dropdown
        clinic_doctors_result = db.session.execute(text("""
            SELECT d.id, d.name, d.specialty 
            FROM doctors d
            JOIN clinic_doctors cd ON d.id = cd.doctor_id
            WHERE cd.clinic_id = :clinic_id AND cd.is_active = true
            ORDER BY d.name ASC
        """), {'clinic_id': clinic['id']}).fetchall()
        
        clinic_doctors = [dict(row._mapping) for row in clinic_doctors_result]
        
        return render_template('clinic/add_package.html', 
                             clinic=clinic,
                             categories=[dict(row._mapping) for row in categories],
                             procedures=[dict(row._mapping) for row in procedures],
                             clinic_doctors=clinic_doctors)
        
    except Exception as e:
        logger.error(f"Error loading add package form: {e}")
        flash('Error loading form. Please try again.', 'error')
        return redirect(url_for('unified_clinic.dashboard'))

@unified_clinic_bp.route('/packages/edit/<int:package_id>', methods=['GET', 'POST'])
@login_required
def edit_package(package_id):
    """Edit existing treatment package"""
    if request.method == 'POST':
        try:
            clinic = get_clinic_for_user(current_user.id)
            if not clinic:
                flash('Clinic not found', 'error')
                return redirect(url_for('unified_clinic.dashboard'))
            
            # Verify package belongs to clinic
            package_check = db.session.execute(text("""
                SELECT id FROM packages WHERE id = :package_id AND clinic_id = :clinic_id
            """), {'package_id': package_id, 'clinic_id': clinic['id']}).fetchone()
            
            if not package_check:
                flash('Package not found or access denied', 'error')
                return redirect(url_for('unified_clinic.dashboard'))
            
            # Get comprehensive form data
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            price_actual = request.form.get('price_actual', type=float)
            price_discounted = request.form.get('price_discounted', type=float)
            duration = request.form.get('duration', '').strip()
            
            # Get additional fields
            key_highlights = request.form.get('key_highlights', '').strip()
            procedure_breakdown = request.form.get('procedure_breakdown', '').strip()
            includes = request.form.get('includes', '').strip()
            excludes = request.form.get('excludes', '').strip()
            pre_procedure_care = request.form.get('pre_procedure_care', '').strip()
            post_procedure_care = request.form.get('post_procedure_care', '').strip()
            recovery_timeline = request.form.get('recovery_timeline', '').strip()
            risks_complications = request.form.get('risks_complications', '').strip()
            expected_results = request.form.get('expected_results', '').strip()
            maintenance_schedule = request.form.get('maintenance_schedule', '').strip()
            
            # Handle Results Gallery - Process before/after images with doctor linking
            results_gallery = []
            
            # Get all result sets from the form arrays
            result_titles = request.form.getlist('result_title[]')
            result_doctor_ids = request.form.getlist('result_doctor_id[]')
            result_descriptions = request.form.getlist('result_description[]')
            result_before_images = request.files.getlist('result_before_image[]')
            result_after_images = request.files.getlist('result_after_image[]')
            
            # Process each result set
            for i in range(len(result_titles)):
                if result_titles[i].strip() and i < len(result_doctor_ids) and result_doctor_ids[i]:
                    result_data = {
                        'title': result_titles[i].strip(),
                        'doctor_id': int(result_doctor_ids[i]),
                        'description': result_descriptions[i].strip() if i < len(result_descriptions) else '',
                        'before_image': None,
                        'after_image': None
                    }
                    
                    # Handle image uploads (placeholder for now - actual file handling would go here)
                    if i < len(result_before_images) and result_before_images[i].filename:
                        result_data['before_image'] = f"package_results/before_{result_titles[i].replace(' ', '_').lower()}_{i}.jpg"
                    
                    if i < len(result_after_images) and result_after_images[i].filename:
                        result_data['after_image'] = f"package_results/after_{result_titles[i].replace(' ', '_').lower()}_{i}.jpg"
                    
                    results_gallery.append(result_data)
                

            
            # Convert results gallery to JSON
            results_gallery_json = json.dumps(results_gallery) if results_gallery else None
            
            # Fix JSON fields - handle empty strings and convert to proper JSON
            if key_highlights and key_highlights.strip():
                try:
                    # If it looks like a Python list/dict with single quotes, convert to JSON
                    if key_highlights.startswith('[') or key_highlights.startswith('{'):
                        import ast
                        parsed = ast.literal_eval(key_highlights)
                        key_highlights = json.dumps(parsed)
                    else:
                        # Convert simple text to JSON array
                        key_highlights = json.dumps([key_highlights])
                except:
                    # If conversion fails, wrap in JSON array
                    key_highlights = json.dumps([key_highlights])
            else:
                # Set empty string to None for JSON fields
                key_highlights = None
            
            if procedure_breakdown and procedure_breakdown.strip():
                try:
                    # If it looks like a Python list/dict with single quotes, convert to JSON
                    if procedure_breakdown.startswith('[') or procedure_breakdown.startswith('{'):
                        import ast
                        parsed = ast.literal_eval(procedure_breakdown)
                        procedure_breakdown = json.dumps(parsed)
                    else:
                        # Convert simple text to JSON object
                        procedure_breakdown = json.dumps({"description": procedure_breakdown})
                except:
                    # If conversion fails, wrap in JSON object
                    procedure_breakdown = json.dumps({"description": procedure_breakdown})
            else:
                # Set empty string to None for JSON fields
                procedure_breakdown = None
            
            # Generate slug from title
            import re
            slug = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
            slug = re.sub(r'\s+', '-', slug.strip())
            
            # Update package with results gallery
            db.session.execute(text("""
                UPDATE packages SET 
                    title = :title, 
                    slug = :slug, 
                    description = :description,
                    price_actual = :price_actual, 
                    price_discounted = :price_discounted, 
                    duration = :duration, 
                    key_highlights = :key_highlights,
                    procedure_breakdown = :procedure_breakdown,
                    results_gallery = :results_gallery,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :package_id AND clinic_id = :clinic_id
            """), {
                'package_id': package_id,
                'clinic_id': clinic['id'],
                'title': title,
                'slug': slug,
                'description': description,
                'price_actual': price_actual,
                'price_discounted': price_discounted,
                'duration': duration,
                'key_highlights': key_highlights,
                'procedure_breakdown': procedure_breakdown,
                'results_gallery': results_gallery_json
            })
            
            db.session.commit()
            
            flash('Package updated successfully!', 'success')
            return redirect(url_for('unified_clinic.dashboard') + '#packages')
            
        except Exception as e:
            logger.error(f"Error updating package: {e}")
            db.session.rollback()
            flash(f'Error updating package: {str(e)}', 'error')
            return redirect(url_for('unified_clinic.edit_package', package_id=package_id))
    
    # GET request - show the package edit form
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            flash('Clinic not found', 'error')
            return redirect(url_for('web.index'))
        
        # Get package data
        package_data = db.session.execute(text("""
            SELECT * FROM packages 
            WHERE id = :package_id AND clinic_id = :clinic_id
        """), {'package_id': package_id, 'clinic_id': clinic['id']}).fetchone()
        
        if not package_data:
            flash('Package not found or access denied', 'error')
            return redirect(url_for('unified_clinic.dashboard'))
        
        package = dict(package_data._mapping)
        
        # Parse JSON fields if they exist
        if package.get('results_gallery'):
            try:
                import json
                package['results_gallery'] = json.loads(package['results_gallery'])
            except:
                package['results_gallery'] = []
        else:
            package['results_gallery'] = []
        
        # Get categories for the form
        categories = db.session.execute(text("""
            SELECT id, name FROM categories ORDER BY name
        """)).fetchall()
        
        # Get procedures for the form
        procedures = db.session.execute(text("""
            SELECT id, procedure_name FROM procedures ORDER BY procedure_name LIMIT 100
        """)).fetchall()
        
        # Get clinic doctors for the form
        clinic_doctors = db.session.execute(text("""
            SELECT d.id, d.name, d.specialty
            FROM doctors d
            JOIN clinic_doctors cd ON d.id = cd.doctor_id
            WHERE cd.clinic_id = :clinic_id AND cd.is_active = true
            ORDER BY d.name ASC
        """), {'clinic_id': clinic['id']}).fetchall()
        
        # Debug logging
        clinic_doctors_list = [dict(row._mapping) for row in clinic_doctors]
        logger.info(f"Clinic doctors for package edit: {clinic_doctors_list}")
        logger.info(f"Package results gallery: {package.get('results_gallery')}")
        
        return render_template('clinic/edit_package.html', 
                             clinic=clinic,
                             package=package,
                             categories=[dict(row._mapping) for row in categories],
                             procedures=[dict(row._mapping) for row in procedures],
                             clinic_doctors=clinic_doctors_list)
        
    except Exception as e:
        logger.error(f"Error loading edit package form: {e}")
        flash('Error loading form. Please try again.', 'error')
        return redirect(url_for('unified_clinic.dashboard'))

@unified_clinic_bp.route('/packages/preview/<int:package_id>')
@login_required
def preview_package(package_id):
    """Preview a package as it would appear to customers"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            flash('Clinic not found', 'error')
            return redirect(url_for('unified_clinic.dashboard'))
        
        # Get package data with clinic information
        package_data = db.session.execute(text("""
            SELECT p.*, c.name as clinic_name, c.city as clinic_city, c.state as clinic_state,
                   c.address as clinic_address, c.phone_number as clinic_phone,
                   c.email as clinic_email, c.website as clinic_website
            FROM packages p
            JOIN clinics c ON p.clinic_id = c.id
            WHERE p.id = :package_id AND p.clinic_id = :clinic_id
        """), {'package_id': package_id, 'clinic_id': clinic['id']}).fetchone()
        
        if not package_data:
            flash('Package not found or access denied', 'error')
            return redirect(url_for('unified_clinic.dashboard'))
        
        package = dict(package_data._mapping)
        
        # Parse JSON fields if they exist
        if package.get('key_highlights'):
            try:
                package['key_highlights'] = json.loads(package['key_highlights'])
            except:
                pass
        
        if package.get('procedure_breakdown'):
            try:
                package['procedure_breakdown'] = json.loads(package['procedure_breakdown'])
            except:
                pass
        
        if package.get('results_gallery'):
            try:
                package['results_gallery'] = json.loads(package['results_gallery'])
            except:
                pass
        
        # Calculate discount percentage if applicable
        if package.get('price_actual') and package.get('price_discounted'):
            if package['price_discounted'] < package['price_actual']:
                discount = ((package['price_actual'] - package['price_discounted']) / package['price_actual']) * 100
                package['discount_percentage'] = round(discount)
        
        return render_template('packages/detail.html', package=package)
        
    except Exception as e:
        logger.error(f"Error loading package preview: {e}")
        flash('Error loading package preview. Please try again.', 'error')
        return redirect(url_for('unified_clinic.dashboard'))

@unified_clinic_bp.route('/api/procedures/search')
@login_required
def search_procedures_api():
    """API endpoint to search procedures for auto-population"""
    try:
        # Get procedures with detailed information for auto-population
        procedures_data = db.session.execute(text("""
            SELECT 
                p.id,
                p.procedure_name,
                p.short_description,
                p.overview,
                p.procedure_details,
                p.ideal_candidates,
                p.recovery_process,
                p.recovery_time,
                p.procedure_duration,
                p.results_duration,
                p.risks,
                p.benefits,
                p.min_cost,
                p.max_cost,
                c.name as category_name,
                bp.name as body_part_name
            FROM procedures p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN body_parts bp ON c.body_part_id = bp.id
            ORDER BY p.procedure_name
            LIMIT 100
        """)).fetchall()
        
        procedures = [dict(row._mapping) for row in procedures_data]
        
        return jsonify({
            'success': True,
            'procedures': procedures
        })
        
    except Exception as e:
        logger.error(f"Error searching procedures: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load procedures'
        }), 500

@unified_clinic_bp.route('/api/doctors')
@login_required
def get_clinic_doctors_api():
    """API endpoint to get doctors assigned to the current clinic for dropdowns"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'}), 404
        
        # Get clinic doctors for dropdown
        clinic_doctors_result = db.session.execute(text("""
            SELECT d.id, d.name, d.specialty, d.qualification, d.experience,
                   d.profile_image, d.image_url, cd.role, cd.is_primary
            FROM doctors d
            JOIN clinic_doctors cd ON d.id = cd.doctor_id
            WHERE cd.clinic_id = :clinic_id AND cd.is_active = true
            ORDER BY d.name ASC
        """), {'clinic_id': clinic['id']}).fetchall()
        
        doctors = []
        for row in clinic_doctors_result:
            doctors.append({
                'id': row[0],
                'name': row[1],
                'specialty': row[2],
                'qualification': row[3],
                'experience': row[4],
                'profile_image': row[5] or row[6],  # Use profile_image or image_url
                'role': row[7],
                'is_primary': row[8]
            })
        
        return jsonify({
            'success': True,
            'doctors': doctors
        })
        
    except Exception as e:
        logger.error(f"Error getting clinic doctors: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load clinic doctors'
        }), 500

# ============================================================================
# DOCTOR MANAGEMENT ROUTES
# ============================================================================

@unified_clinic_bp.route('/doctors')
@login_required
def doctors():
    """Doctor management page"""
    return redirect(url_for('unified_clinic.dashboard') + '#doctors')

@unified_clinic_bp.route('/doctors/add', methods=['POST'])
@login_required
def add_doctor():
    """Add new doctor to clinic with comprehensive parameters"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        # Get basic form data
        name = request.form.get('name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        email = request.form.get('email', '').strip()
        qualification = request.form.get('qualification', '').strip()
        specialty = request.form.get('specialty', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        experience = request.form.get('experience', type=int) or 0
        consultation_fee = request.form.get('consultation_fee', type=int) or 1500
        medical_license_number = request.form.get('medical_license_number', '').strip()
        practice_location = request.form.get('practice_location', '').strip()
        bio = request.form.get('bio', '').strip()
        role = request.form.get('role', 'doctor').strip()
        is_primary = request.form.get('is_primary') == 'true'
        
        # Use clinic location if city/state not provided
        if not city:
            city = clinic.get('city', 'Unknown')
        if not state:
            state = clinic.get('state', '')
        
        # Validate required fields
        if not name or not phone_number or not qualification or not specialty:
            return jsonify({'success': False, 'message': 'Please fill all required fields (Name, Phone, Qualification, Specialization)'})
        
        # Check if phone number already exists
        existing_phone = db.session.execute(text("""
            SELECT id FROM users WHERE phone_number = :phone_number
        """), {'phone_number': phone_number}).fetchone()
        
        if existing_phone:
            return jsonify({'success': False, 'message': 'Phone number already exists. Please use a different phone number.'})
        
        # Handle profile image upload
        profile_image_url = None
        profile_image_url_input = request.form.get('profile_image_url', '').strip()
        
        if 'profile_image' in request.files and request.files['profile_image'].filename:
            # Handle file upload
            file = request.files['profile_image']
            if file and file.filename:
                import os
                from werkzeug.utils import secure_filename
                
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join('static', 'uploads', 'doctors')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generate unique filename
                from datetime import datetime
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(upload_dir, filename)
                
                # Save file
                file.save(filepath)
                profile_image_url = f"/static/uploads/doctors/{filename}"
        elif profile_image_url_input:
            # Use provided URL
            profile_image_url = profile_image_url_input
        
        # Process education and certifications JSON
        import json
        education_json = request.form.get('education_json', '[]')
        certifications_json = request.form.get('certifications_json', '[]')
        
        try:
            education = json.loads(education_json) if education_json else []
            certifications = json.loads(certifications_json) if certifications_json else []
        except json.JSONDecodeError:
            education = []
            certifications = []
        
        # Create a user account for the doctor
        # Use provided email or generate one if not provided
        if not email:
            doctor_email = f"{name.lower().replace(' ', '.')}.{clinic['id']}@clinic-doctors.com"
        else:
            doctor_email = email
            
        doctor_username = f"{name.lower().replace(' ', '_')}_doc_{clinic['id']}"
        
        # Check if email already exists (if provided)
        if email:
            existing_email = db.session.execute(text("""
                SELECT id FROM users WHERE email = :email
            """), {'email': email}).fetchone()
            
            if existing_email:
                return jsonify({'success': False, 'message': 'Email address already exists. Please use a different email.'})
        
        # Insert user record for doctor with required fields
        user_result = db.session.execute(text("""
            INSERT INTO users (
                name, phone_number, username, email, role, is_verified, created_at
            ) VALUES (
                :name, :phone_number, :username, :email, 'doctor', true, CURRENT_TIMESTAMP
            ) RETURNING id
        """), {
            'name': name,
            'phone_number': phone_number,  # Use actual phone number from form
            'username': doctor_username,
            'email': doctor_email
        }).fetchone()
        
        user_id = user_result[0] if user_result else None
        
        # Insert comprehensive doctor record
        doctor_result = db.session.execute(text("""
            INSERT INTO doctors (
                user_id, name, qualification, specialty, experience,
                consultation_fee, medical_license_number, practice_location,
                bio, education, certifications, clinic_id, city, state,
                profile_image, image_url, verification_status, is_verified, created_at
            ) VALUES (
                :user_id, :name, :qualification, :specialty, :experience,
                :consultation_fee, :medical_license_number, :practice_location,
                :bio, :education, :certifications, :clinic_id, :city, :state,
                :profile_image, :image_url, 'pending', false, CURRENT_TIMESTAMP
            ) RETURNING id
        """), {
            'user_id': user_id,
            'name': name,
            'qualification': qualification,
            'specialty': specialty,
            'experience': experience,
            'consultation_fee': consultation_fee,
            'medical_license_number': medical_license_number,
            'practice_location': practice_location or clinic.get('address', ''),
            'bio': bio,
            'education': json.dumps(education),
            'certifications': json.dumps(certifications),
            'clinic_id': clinic['id'],
            'city': city,  # Use actual city from form
            'state': state or clinic.get('state', ''),  # Use form state or clinic state as fallback
            'profile_image': profile_image_url,  # Add profile image URL
            'image_url': profile_image_url  # Also populate image_url field for compatibility
        }).fetchone()
        
        doctor_id = doctor_result[0] if doctor_result else None
        
        if not doctor_id:
            return jsonify({'success': False, 'message': 'Error creating doctor record'})
        
        # Create relationship in clinic_doctors table
        db.session.execute(text("""
            INSERT INTO clinic_doctors (
                clinic_id, doctor_id, role, is_primary, is_active, created_at
            ) VALUES (
                :clinic_id, :doctor_id, :role, :is_primary, true, CURRENT_TIMESTAMP
            )
        """), {
            'clinic_id': clinic['id'],
            'doctor_id': doctor_id,
            'role': role,
            'is_primary': is_primary
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Doctor added successfully. Pending admin verification before appearing in search results.'
        })
        
    except Exception as e:
        logger.error(f"Error adding doctor: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error adding doctor'})

@unified_clinic_bp.route('/doctors/search', methods=['GET'])
@login_required
def search_doctors():
    """Search for existing doctors to add to clinic"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        query = request.args.get('q', '').strip()
        
        # Build search query - exclude doctors already in this clinic
        sql_query = """
            SELECT DISTINCT d.id, d.name, d.specialty, d.qualification, d.experience, 
                   d.city, d.state, d.profile_image, d.image_url, u.phone_number
            FROM doctors d
            LEFT JOIN users u ON d.user_id = u.id
            LEFT JOIN clinic_doctors cd ON d.id = cd.doctor_id AND cd.clinic_id = :clinic_id
            WHERE cd.id IS NULL AND d.is_verified = true
        """
        
        params = {'clinic_id': clinic['id']}
        
        if query:
            sql_query += """
                AND (
                    LOWER(d.name) LIKE LOWER(:query) OR 
                    LOWER(d.specialty) LIKE LOWER(:query) OR 
                    LOWER(d.qualification) LIKE LOWER(:query) OR
                    LOWER(d.city) LIKE LOWER(:query) OR
                    u.phone_number LIKE :query
                )
            """
            params['query'] = f'%{query}%'
        
        sql_query += " ORDER BY d.name LIMIT 20"
        
        doctors_result = db.session.execute(text(sql_query), params).fetchall()
        
        doctors = []
        for row in doctors_result:
            doctors.append({
                'id': row[0],
                'name': row[1],
                'specialty': row[2],
                'qualification': row[3],
                'experience': row[4],
                'city': row[5],
                'state': row[6],
                'profile_image': row[7] or row[8],  # Use profile_image or image_url
                'phone_number': row[9]
            })
        
        return jsonify({'success': True, 'doctors': doctors})
        
    except Exception as e:
        logger.error(f"Error searching doctors: {e}")
        return jsonify({'success': False, 'message': 'Error searching doctors'})

@unified_clinic_bp.route('/doctors/add-existing', methods=['POST'])
@login_required
def add_existing_doctor():
    """Add an existing doctor to the clinic"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        doctor_id = request.form.get('doctor_id', type=int)
        role = request.form.get('role', 'doctor').strip()
        
        if not doctor_id:
            return jsonify({'success': False, 'message': 'Doctor ID is required'})
        
        # Verify doctor exists (allow both verified and unverified doctors)
        doctor_result = db.session.execute(text("""
            SELECT id, name FROM doctors WHERE id = :doctor_id
        """), {'doctor_id': doctor_id}).fetchone()
        
        if not doctor_result:
            return jsonify({'success': False, 'message': 'Doctor not found'})
        
        # Check if doctor is already added to this clinic
        existing_relation = db.session.execute(text("""
            SELECT id FROM clinic_doctors WHERE clinic_id = :clinic_id AND doctor_id = :doctor_id
        """), {
            'clinic_id': clinic['id'],
            'doctor_id': doctor_id
        }).fetchone()
        
        if existing_relation:
            return jsonify({'success': False, 'message': 'Doctor is already added to your clinic'})
        
        # Add doctor to clinic
        db.session.execute(text("""
            INSERT INTO clinic_doctors (
                clinic_id, doctor_id, role, is_primary, is_active, created_at
            ) VALUES (
                :clinic_id, :doctor_id, :role, false, true, CURRENT_TIMESTAMP
            )
        """), {
            'clinic_id': clinic['id'],
            'doctor_id': doctor_id,
            'role': role
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Dr. {doctor_result[1]} has been added to your clinic successfully'
        })
        
    except Exception as e:
        logger.error(f"Error adding existing doctor: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error adding doctor to clinic'})

@unified_clinic_bp.route('/doctors/edit/<int:doctor_id>', methods=['POST'])
@login_required
def edit_doctor(doctor_id):
    """Edit doctor information in clinic"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        # Verify doctor belongs to this clinic
        clinic_doctor_result = db.session.execute(text("""
            SELECT cd.id, d.id as doctor_id 
            FROM clinic_doctors cd
            JOIN doctors d ON cd.doctor_id = d.id
            WHERE cd.clinic_id = :clinic_id AND d.id = :doctor_id
        """), {
            'clinic_id': clinic['id'],
            'doctor_id': doctor_id
        }).fetchone()
        
        if not clinic_doctor_result:
            return jsonify({'success': False, 'message': 'Doctor not found in your clinic'})
        
        # Get form data - matching the create form structure
        name = request.form.get('name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        email = request.form.get('email', '').strip()
        qualification = request.form.get('qualification', '').strip()
        specialty = request.form.get('specialty', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        experience = request.form.get('experience', type=int) or 0
        consultation_fee = request.form.get('consultation_fee', type=int) or 1500
        medical_license_number = request.form.get('medical_license_number', '').strip()
        practice_location = request.form.get('practice_location', '').strip()
        bio = request.form.get('bio', '').strip()
        role = request.form.get('role', 'doctor').strip()
        is_primary = request.form.get('is_primary') == 'on'
        
        # Handle education data
        education_degrees = request.form.getlist('education_degree[]')
        education_institutions = request.form.getlist('education_institution[]')
        education_years = request.form.getlist('education_year[]')
        
        education = []
        for i in range(len(education_degrees)):
            if education_degrees[i].strip():
                education.append({
                    'degree': education_degrees[i].strip(),
                    'institution': education_institutions[i].strip() if i < len(education_institutions) else '',
                    'year': education_years[i] if i < len(education_years) and education_years[i] else ''
                })
        
        # Handle certifications data
        certification_names = request.form.getlist('certification_name[]')
        certification_organizations = request.form.getlist('certification_organization[]')
        certification_years = request.form.getlist('certification_year[]')
        
        certifications = []
        for i in range(len(certification_names)):
            if certification_names[i].strip():
                certifications.append({
                    'name': certification_names[i].strip(),
                    'organization': certification_organizations[i].strip() if i < len(certification_organizations) else '',
                    'year': certification_years[i] if i < len(certification_years) and certification_years[i] else ''
                })
        
        # Handle profile image
        profile_image_url = None
        if 'profile_image' in request.files and request.files['profile_image'].filename:
            profile_image_url = save_uploaded_file(request.files['profile_image'], 'doctor')
        else:
            image_url = request.form.get('profile_image_url')
            if image_url and image_url.strip():
                profile_image_url = image_url.strip()
        
        # Validate required fields
        if not name or not specialty:
            return jsonify({'success': False, 'message': 'Name and specialty are required'})
        
        # Update doctor information with all fields
        update_data = {
            'name': name,
            'phone_number': phone_number,
            'email': email,
            'specialty': specialty,
            'qualification': qualification,
            'city': city,
            'state': state,
            'experience': experience,
            'consultation_fee': consultation_fee,
            'medical_license_number': medical_license_number,
            'practice_location': practice_location,
            'bio': bio,
            'education': json.dumps(education) if education else None,
            'certifications': json.dumps(certifications) if certifications else None,
            'doctor_id': doctor_id
        }
        
        # Add profile image to update if provided
        if profile_image_url:
            update_data['profile_image'] = profile_image_url
            
        # Build update query dynamically
        update_fields = []
        query_params = {}
        
        for field, value in update_data.items():
            if field != 'doctor_id' and value is not None:
                if field == 'phone_number':
                    # Skip phone_number as it doesn't exist in the database
                    continue
                elif field == 'email':
                    # Skip email as it doesn't exist in the database
                    continue
                elif field == 'medical_license_number':
                    # Handle empty medical license number to avoid unique constraint violation
                    if value.strip():
                        update_fields.append("medical_license_number = :medical_license_number")
                        query_params[field] = value
                    else:
                        # Set to NULL for empty values to avoid unique constraint issues
                        update_fields.append("medical_license_number = NULL")
                elif field == 'profile_image':
                    update_fields.append("profile_image = :profile_image")
                    update_fields.append("image_url = :profile_image")  # Also update image_url for compatibility
                    query_params[field] = value
                else:
                    update_fields.append(f"{field} = :{field}")
                    query_params[field] = value
        
        query_params['doctor_id'] = doctor_id
        
        if update_fields:
            db.session.execute(text(f"""
                UPDATE doctors SET 
                    {', '.join(update_fields)}
                WHERE id = :doctor_id
            """), query_params)
        
        # Update clinic-doctor relationship
        db.session.execute(text("""
            UPDATE clinic_doctors SET 
                role = :role,
                is_primary = :is_primary
            WHERE clinic_id = :clinic_id AND doctor_id = :doctor_id
        """), {
            'role': role,
            'is_primary': is_primary,
            'clinic_id': clinic['id'],
            'doctor_id': doctor_id
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Doctor updated successfully'})
        
    except Exception as e:
        logger.error(f"Error editing doctor: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating doctor'})

@unified_clinic_bp.route('/doctors/get/<int:doctor_id>', methods=['GET'])
@login_required
def get_doctor_details(doctor_id):
    """Get doctor details for editing"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        # Get doctor details
        doctor_result = db.session.execute(text("""
            SELECT d.*, cd.role, cd.is_primary 
            FROM doctors d
            JOIN clinic_doctors cd ON d.id = cd.doctor_id
            WHERE cd.clinic_id = :clinic_id AND d.id = :doctor_id
        """), {
            'clinic_id': clinic['id'],
            'doctor_id': doctor_id
        }).fetchone()
        
        if not doctor_result:
            return jsonify({'success': False, 'message': 'Doctor not found in your clinic'})
        
        doctor_data = dict(doctor_result._mapping)
        
        return jsonify({'success': True, 'doctor': doctor_data})
        
    except Exception as e:
        logger.error(f"Error getting doctor details: {e}")
        return jsonify({'success': False, 'message': 'Error fetching doctor details'})

@unified_clinic_bp.route('/doctors/remove/<int:doctor_id>', methods=['POST'])
@login_required
def remove_doctor(doctor_id):
    """Remove doctor from clinic"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        # Remove doctor from clinic (soft delete by setting is_active = false)
        db.session.execute(text("""
            UPDATE clinic_doctors 
            SET is_active = false
            WHERE clinic_id = :clinic_id AND doctor_id = :doctor_id
        """), {
            'clinic_id': clinic['id'],
            'doctor_id': doctor_id
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Doctor removed from clinic successfully'})
        
    except Exception as e:
        logger.error(f"Error removing doctor: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error removing doctor'})

# ============================================================================
# IMAGE UPLOAD ROUTES
# ============================================================================

@unified_clinic_bp.route('/upload/profile-image', methods=['POST'])
@login_required
def upload_profile_image():
    """Upload clinic profile image via file or URL"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        image_url = None
        profile_image_url_input = request.form.get('profile_image_url', '').strip()
        
        # Handle file upload
        if 'profile_image' in request.files and request.files['profile_image'].filename:
            file = request.files['profile_image']
            if file and file.filename:
                # Save the file
                image_url = save_uploaded_file(file, 'profile')
                if not image_url:
                    return jsonify({'success': False, 'message': 'Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP files.'})
        
        # Handle URL input
        elif profile_image_url_input:
            image_url = profile_image_url_input
        
        else:
            return jsonify({'success': False, 'message': 'Please select a file or provide an image URL'})
        
        # Update clinic profile
        db.session.execute(text("""
            UPDATE clinics 
            SET profile_image = :image_url, updated_at = CURRENT_TIMESTAMP
            WHERE id = :clinic_id
        """), {
            'image_url': image_url,
            'clinic_id': clinic['id']
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Profile image updated successfully',
            'image_url': image_url
        })
        
    except Exception as e:
        logger.error(f"Error uploading profile image: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error uploading image'})

@unified_clinic_bp.route('/upload/banner-image', methods=['POST'])
@login_required
def upload_banner_image():
    """Upload clinic promotional banner"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        if 'banner_image' not in request.files:
            return jsonify({'success': False, 'message': 'No file selected'})
        
        file = request.files['banner_image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        # Save the file
        image_url = save_uploaded_file(file, 'banner')
        if not image_url:
            return jsonify({'success': False, 'message': 'Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP files.'})
        
        # Update clinic banner
        db.session.execute(text("""
            UPDATE clinics 
            SET promotional_banner_url = :image_url, updated_at = CURRENT_TIMESTAMP
            WHERE id = :clinic_id
        """), {
            'image_url': image_url,
            'clinic_id': clinic['id']
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Banner image uploaded successfully',
            'image_url': image_url
        })
        
    except Exception as e:
        logger.error(f"Error uploading banner image: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error uploading banner image'})

# ============================================================================
# PROFILE UPDATE ROUTES
# ============================================================================

@unified_clinic_bp.route('/update-profile', methods=['POST'])
@login_required
def update_clinic_profile():
    """Update clinic profile information"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        # Get form data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()
        working_hours = request.form.get('working_hours', '').strip()
        website = request.form.get('website', '').strip()
        
        # Update clinic profile
        db.session.execute(text("""
            UPDATE clinics 
            SET name = :name, description = :description, address = :address,
                city = :city, state = :state, pincode = :pincode,
                working_hours = :working_hours, website = :website,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :clinic_id
        """), {
            'name': name,
            'description': description,
            'address': address,
            'city': city,
            'state': state,
            'pincode': pincode,
            'working_hours': working_hours,
            'website': website,
            'clinic_id': clinic['id']
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating clinic profile: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating profile'})

@unified_clinic_bp.route('/update-contact', methods=['POST'])
@login_required
def update_contact_settings():
    """Update clinic contact settings"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        # Get form data
        contact_number = request.form.get('contact_number', '').strip()
        whatsapp_number = request.form.get('whatsapp_number', '').strip()
        email = request.form.get('email', '').strip()
        
        # Update contact settings
        db.session.execute(text("""
            UPDATE clinics 
            SET contact_number = :contact_number, whatsapp_number = :whatsapp_number, email = :email,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :clinic_id
        """), {
            'contact_number': contact_number,
            'whatsapp_number': whatsapp_number,
            'email': email,
            'clinic_id': clinic['id']
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Contact settings updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating contact settings: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating contact settings'})

# ============================================================================
# CLINIC ENHANCEMENT ROUTES
# ============================================================================

@unified_clinic_bp.route('/update-highlights', methods=['POST'])
@login_required
def update_highlights():
    """Update clinic highlights"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        highlights = request.form.get('highlights', '').strip()
        
        # Update clinic highlights
        db.session.execute(text("""
            UPDATE clinics 
            SET highlights = :highlights, updated_at = CURRENT_TIMESTAMP
            WHERE id = :clinic_id
        """), {
            'highlights': highlights,
            'clinic_id': clinic['id']
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Highlights updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating highlights: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating highlights'})

@unified_clinic_bp.route('/update-specialties', methods=['POST'])
@login_required
def update_specialties():
    """Update clinic specialties"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        selected_specialties = request.form.get('selected_specialties', '').strip()
        
        # Update clinic specialties
        db.session.execute(text("""
            UPDATE clinics 
            SET specialties = :specialties, updated_at = CURRENT_TIMESTAMP
            WHERE id = :clinic_id
        """), {
            'specialties': selected_specialties,
            'clinic_id': clinic['id']
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Specialties updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating specialties: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating specialties'})

@unified_clinic_bp.route('/update-popular-procedures', methods=['POST'])
@login_required
def update_popular_procedures():
    """Update clinic popular procedures"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        selected_procedures = request.form.get('selected_procedures', '').strip()
        
        # Update clinic popular procedures
        db.session.execute(text("""
            UPDATE clinics 
            SET popular_procedures = :popular_procedures, updated_at = CURRENT_TIMESTAMP
            WHERE id = :clinic_id
        """), {
            'popular_procedures': selected_procedures,
            'clinic_id': clinic['id']
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Popular procedures updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating popular procedures: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating popular procedures'})

# ============================================================================
# API ENDPOINTS
# ============================================================================

@unified_clinic_bp.route('/api/categories', methods=['GET'])
@login_required
def api_get_categories():
    """API endpoint to get all categories for autocomplete"""
    try:
        categories = db.session.execute(text("""
            SELECT DISTINCT name FROM categories 
            ORDER BY name ASC
        """)).fetchall()
        
        category_list = [{'name': row[0]} for row in categories]
        
        return jsonify({
            'success': True,
            'categories': category_list
        })
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return jsonify({
            'success': False,
            'categories': [],
            'error': str(e)
        })

@unified_clinic_bp.route('/api/procedures/search', methods=['GET'])
@login_required
def api_search_procedures():
    """API endpoint to search procedures for autocomplete"""
    try:
        procedures = db.session.execute(text("""
            SELECT DISTINCT p.id, p.procedure_name, c.name as category_name, 
                   p.min_cost, p.max_cost
            FROM procedures p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.procedure_name ASC
            LIMIT 100
        """)).fetchall()
        
        procedure_list = []
        for row in procedures:
            procedure_list.append({
                'id': row[0],
                'procedure_name': row[1],
                'category_name': row[2],
                'min_cost': row[3],
                'max_cost': row[4]
            })
        
        return jsonify({
            'success': True,
            'procedures': procedure_list
        })
        
    except Exception as e:
        logger.error(f"Error fetching procedures: {e}")
        return jsonify({
            'success': False,
            'procedures': [],
            'error': str(e)
        })

@unified_clinic_bp.route('/api/extract-location', methods=['POST'])
@login_required
def api_extract_location():
    """API endpoint to extract location from Google My Business URL"""
    try:
        data = request.get_json()
        google_business_url = data.get('google_business_url', '').strip()
        
        if not google_business_url:
            return jsonify({
                'success': False,
                'error': 'Google My Business URL is required'
            })
        
        # Extract location using Google Places service
        result = google_places_service.extract_location_from_url(google_business_url)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error extracting location from Google URL: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to extract location. Please check your URL and try again.'
        })

def register_unified_clinic_routes(app):
    """Register unified clinic dashboard routes"""
    app.register_blueprint(unified_clinic_bp)
    logger.info("Unified clinic dashboard routes registered successfully")