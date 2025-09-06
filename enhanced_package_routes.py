"""
Enhanced package routes for comprehensive package management.
Handles the new package creation form with all enhanced fields.
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
import logging
import requests
from datetime import datetime
from models import db, Package, Clinic
from sqlalchemy import text
from enhanced_highlights_handler import process_key_highlights
from intelligent_procedure_generator import procedure_generator
from auto_categorization import auto_categorize_package

enhanced_package_bp = Blueprint('enhanced_package', __name__)
logger = logging.getLogger(__name__)

# Import CSRF from app to use exemptions
try:
    from app import csrf
except ImportError:
    csrf = None

# Configure file upload settings
UPLOAD_FOLDER = 'static/uploads/packages'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_description_quality(description, title, category):
    """Validate that description is not generic template text and provides real value."""
    # Check for template phrases that indicate low-quality content
    template_phrases = [
        "Limited time offer: 20% discount",
        "premier destination for advanced aesthetic treatments",
        "Experience world-class medical aesthetics with personalized care",
        "Professional {title} at",
        "Limited time offer"
    ]
    
    description_lower = description.lower()
    
    # Check if description contains template phrases
    for phrase in template_phrases:
        if phrase.lower() in description_lower:
            return False, f"Description appears to use template text. Please provide a unique description specific to this {title} treatment."
    
    # Check if description is too short or generic
    if len(description.strip()) < 50:
        return False, "Description must be at least 50 characters and provide meaningful details about the treatment."
    
    # Check if description just repeats the title
    title_words = set(title.lower().split())
    description_words = set(description.lower().split())
    overlap = len(title_words.intersection(description_words))
    if overlap == len(title_words) and len(description_words) < 15:
        return False, "Description should provide more details beyond just the treatment name."
    
    return True, "Description is acceptable"

def generate_smart_description(title, category):
    """Generate a smart default description based on treatment title and category."""
    # Treatment-specific templates based on common aesthetic procedures
    treatment_templates = {
        'botox': 'Professional Botox treatment for reducing facial wrinkles and fine lines. Achieve smoother, more youthful skin with expert injection techniques.',
        'filler': 'Premium dermal filler treatment for facial enhancement and volume restoration. Natural-looking results with high-quality hyaluronic acid.',
        'laser': 'Advanced laser treatment using state-of-the-art technology for skin rejuvenation and targeted concerns.',
        'facial': 'Comprehensive facial treatment designed to improve skin health, texture, and radiance through professional techniques.',
        'peel': 'Professional chemical peel treatment for skin renewal, improving texture and reducing signs of aging.',
        'hair': 'Specialized hair treatment addressing hair loss and promoting healthy hair growth using proven methods.',
        'scar': 'Advanced scar treatment using proven techniques to reduce appearance and improve skin texture.',
        'pigmentation': 'Targeted treatment for pigmentation concerns, helping achieve more even skin tone and clarity.',
        'lift': 'Non-surgical lifting treatment providing facial rejuvenation and improved contours without downtime.',
        'glow': 'Rejuvenating treatment designed to enhance natural skin radiance and achieve a healthy, glowing complexion.'
    }
    
    title_lower = title.lower()
    
    # Find matching template based on keywords in title
    for keyword, template in treatment_templates.items():
        if keyword in title_lower:
            return template
    
    # Category-based fallbacks
    category_templates = {
        'aesthetic medicine': f'Professional {title} treatment using advanced aesthetic medicine techniques for optimal results.',
        'injectable treatments': f'Expert {title} using premium injectable products for natural-looking enhancement.',
        'laser treatments': f'Advanced {title} using cutting-edge laser technology for effective and safe results.',
        'facial treatments': f'Comprehensive {title} designed to improve skin health and appearance.',
        'hair restoration': f'Specialized {title} addressing hair concerns using proven restoration methods.',
        'anti-aging treatments': f'Professional {title} targeting signs of aging for more youthful appearance.',
        'skin rejuvenation': f'Rejuvenating {title} improving skin texture, tone, and overall quality.'
    }
    
    category_lower = category.lower()
    for cat_key, template in category_templates.items():
        if cat_key in category_lower:
            return template
    
    # Generic fallback
    return f'Professional {title} treatment providing effective results using advanced techniques and personalized care.'

def save_uploaded_file(file, subfolder=''):
    """Save uploaded file and return the file path."""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Create upload directory if it doesn't exist
        upload_path = os.path.join(UPLOAD_FOLDER, subfolder)
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, filename)
        try:
            file.save(file_path)
            return f"/static/uploads/packages/{subfolder}/{filename}" if subfolder else f"/static/uploads/packages/{filename}"
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return None
    return None

@enhanced_package_bp.route('/clinic/packages/add', methods=['GET', 'POST'])
@login_required
def add_package_enhanced():
    """Add new package with enhanced fields."""
    try:
        # Get clinic for current user using raw SQL to avoid model issues
        clinic_result = db.session.execute(text("SELECT * FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            flash('Clinic profile not found', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic = dict(clinic_result._mapping)
    except Exception as e:
        logger.error(f"Error getting clinic for user {current_user.id}: {e}")
        flash('Error accessing clinic profile', 'error')
        return redirect(url_for('clinic.clinic_dashboard'))
    
    if request.method == 'GET':
        return render_template('clinic/add_package_enhanced.html', clinic=clinic)
    
    try:
        # Basic package information
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        actual_treatment_name = request.form.get('actual_treatment_name', '').strip()
        clinic_address = request.form.get('clinic_address', '').strip()
        
        # Validate required fields
        if not title:
            return jsonify({
                'success': False,
                'message': 'Package name is required'
            }), 400
            
        if not category:
            return jsonify({
                'success': False,
                'message': 'Category is required'
            }), 400
            
        if not description:
            return jsonify({
                'success': False,
                'message': 'Package description is required'
            }), 400
        
        # Validate description quality to prevent template descriptions
        is_valid, validation_message = validate_description_quality(description, title, category)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': validation_message
            }), 400
        
        # Pricing information
        price_actual_str = request.form.get('price_actual', '0')
        try:
            price_actual = float(price_actual_str) if price_actual_str else 0
            if price_actual <= 0:
                return jsonify({
                    'success': False,
                    'message': 'Actual price must be greater than 0'
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid actual price format'
            }), 400
        
        price_discounted_str = request.form.get('price_discounted')
        try:
            price_discounted = float(price_discounted_str) if price_discounted_str and price_discounted_str.strip() else None
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid discounted price format'
            }), 400
        
        discount_percentage_str = request.form.get('discount_percentage')
        try:
            discount_percentage = int(discount_percentage_str) if discount_percentage_str and discount_percentage_str.strip() else None
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid discount percentage format'
            }), 400
        
        vat_amount_str = request.form.get('vat_amount')
        try:
            vat_amount = float(vat_amount_str) if vat_amount_str and vat_amount_str.strip() else None
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid VAT amount format'
            }), 400
        anesthetic_type = request.form.get('anesthetic_type', '').strip()
        aftercare_kit = request.form.get('aftercare_kit', '').strip()
        
        # Procedure information
        about_procedure = request.form.get('about_procedure', '').strip()
        recommended_for = request.form.get('recommended_for', '').strip()
        downtime = request.form.get('downtime', '').strip()
        duration = request.form.get('duration', '').strip()
        downtime_description = request.form.get('downtime_description', '').strip()
        precautions = request.form.get('precautions', '').strip()
        
        # Contact information
        whatsapp_number = request.form.get('whatsapp_number', '').strip()
        custom_phone_number = request.form.get('custom_phone_number', '').strip()
        chat_message_template = request.form.get('chat_message_template', '').strip()
        call_message_template = request.form.get('call_message_template', '').strip()
        
        # Location information
        clinic_latitude_str = request.form.get('clinic_latitude')
        clinic_latitude = float(clinic_latitude_str) if clinic_latitude_str and clinic_latitude_str.strip() else None
        
        clinic_longitude_str = request.form.get('clinic_longitude')
        clinic_longitude = float(clinic_longitude_str) if clinic_longitude_str and clinic_longitude_str.strip() else None
        
        # Parse JSON fields with error handling
        try:
            key_highlights = json.loads(request.form.get('key_highlights', '{}'))
        except json.JSONDecodeError:
            key_highlights = {}
            
        try:
            procedure_breakdown = json.loads(request.form.get('procedure_breakdown', '[]'))
        except json.JSONDecodeError:
            procedure_breakdown = []
        
        # Auto-generate procedure breakdown if not provided (for new packages)
        if not procedure_breakdown or len(procedure_breakdown) == 0:
            logger.info(f"Auto-generating procedure breakdown for new package: {title}")
            procedure_breakdown = procedure_generator.generate_procedure_breakdown(
                title=title,
                category=category,
                actual_treatment_name=actual_treatment_name,
                package_price=price_actual
            )
            
        try:
            results_gallery_data = json.loads(request.form.get('results_gallery', '[]'))
        except json.JSONDecodeError:
            results_gallery_data = []
        
        # Handle file uploads for results gallery
        results_gallery = []
        for i, result_data in enumerate(results_gallery_data, 1):
            result_item = result_data.copy()
            
            # Handle before/after images and videos
            for media_type in ['before_image', 'after_image', 'before_video', 'after_video']:
                file_key = f"{media_type}_{i}"
                if file_key in request.files:
                    file = request.files[file_key]
                    if file.filename:
                        file_path = save_uploaded_file(file, 'results')
                        if file_path:
                            result_item[media_type] = file_path
            
            results_gallery.append(result_item)
        
        # Generate slug from title
        slug = title.lower().replace(' ', '-').replace('&', 'and')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # Create package using raw SQL to handle new fields
        package_sql = """
            INSERT INTO packages (
                clinic_id, title, slug, description, actual_treatment_name, price_actual, price_discounted, 
                discount_percentage, category, about_procedure, key_highlights, 
                procedure_breakdown, vat_amount, anesthetic_type, aftercare_kit,
                recommended_for, downtime, duration, downtime_description, precautions,
                results_gallery, whatsapp_number, custom_phone_number, 
                chat_message_template, call_message_template, clinic_latitude, 
                clinic_longitude, clinic_address, is_active, created_at
            ) VALUES (
                :clinic_id, :title, :slug, :description, :actual_treatment_name, :price_actual, :price_discounted,
                :discount_percentage, :category, :about_procedure, :key_highlights,
                :procedure_breakdown, :vat_amount, :anesthetic_type, :aftercare_kit,
                :recommended_for, :downtime, :duration, :downtime_description, :precautions,
                :results_gallery, :whatsapp_number, :custom_phone_number,
                :chat_message_template, :call_message_template, :clinic_latitude,
                :clinic_longitude, :clinic_address, :is_active, :created_at
            ) RETURNING id
        """
        
        # Auto-generate treatment name if not provided
        if not actual_treatment_name:
            actual_treatment_name = generate_smart_description(title, category).split('.')[0]
        
        create_result = db.session.execute(text(package_sql), {
            'clinic_id': clinic['id'],
            'title': title,
            'slug': slug,
            'description': description,
            'actual_treatment_name': actual_treatment_name,
            'price_actual': price_actual,
            'price_discounted': price_discounted,
            'discount_percentage': discount_percentage,
            'category': category,
            'about_procedure': about_procedure,
            'key_highlights': json.dumps(key_highlights) if key_highlights else None,
            'procedure_breakdown': json.dumps(procedure_breakdown) if procedure_breakdown else None,
            'vat_amount': vat_amount,
            'anesthetic_type': anesthetic_type,
            'aftercare_kit': aftercare_kit,
            'recommended_for': recommended_for,
            'downtime': downtime,
            'duration': duration,
            'downtime_description': downtime_description,
            'precautions': precautions,
            'results_gallery': json.dumps(results_gallery) if results_gallery else None,
            'whatsapp_number': whatsapp_number,
            'custom_phone_number': custom_phone_number,
            'chat_message_template': chat_message_template,
            'call_message_template': call_message_template,
            'clinic_latitude': clinic_latitude,
            'clinic_longitude': clinic_longitude,
            'clinic_address': clinic_address,
            'is_active': True,
            'created_at': datetime.utcnow()
        })
        
        result_row = create_result.fetchone()
        if result_row:
            package_id = result_row[0]
            db.session.commit()
            
            # Auto-categorize the package
            try:
                from auto_categorization import auto_categorize_and_assign_package
                auto_categorize_and_assign_package(package_id, title, description)
                logger.info(f"Package {package_id} auto-categorized successfully")
            except Exception as e:
                logger.warning(f"Auto-categorization failed for package {package_id}: {e}")
            
            logger.info(f"Package {package_id} created successfully by clinic {clinic['id']}")
            
            return jsonify({
                'success': True,
                'message': 'Package created successfully!',
                'package_id': package_id
            })
        else:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to create package in database'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating package: {e}")
        return jsonify({
            'success': False,
            'message': f'Error creating package: {str(e)}'
        }), 500

@enhanced_package_bp.route('/clinic/packages/<int:package_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_package_enhanced(package_id):
    """Edit package with enhanced fields."""
    try:
        # Get clinic for current user
        clinic_result = db.session.execute(text("SELECT * FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            flash('Clinic profile not found', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic = dict(clinic_result._mapping)
        
        # Get package details that belongs to this clinic
        package_result = db.session.execute(text("""
            SELECT * FROM packages 
            WHERE id = :package_id AND clinic_id = :clinic_id
        """), {'package_id': package_id, 'clinic_id': clinic['id']}).fetchone()
        
        if not package_result:
            flash('Package not found or access denied', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        package = dict(package_result._mapping)
        
        if request.method == 'GET':
            return render_template('clinic/edit_package_enhanced.html', clinic=clinic, package=package)
        
        # Handle POST request (update package)
        # Basic package information
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        actual_treatment_name = request.form.get('actual_treatment_name', '').strip()
        clinic_address = request.form.get('clinic_address', '').strip()
        
        # Validate required fields
        if not title:
            return jsonify({
                'success': False,
                'message': 'Package name is required'
            }), 400
            
        if not category:
            return jsonify({
                'success': False,
                'message': 'Category is required'
            }), 400
            
        if not description:
            return jsonify({
                'success': False,
                'message': 'Package description is required'
            }), 400
        
        # Validate description quality to prevent template descriptions
        is_valid, validation_message = validate_description_quality(description, title, category)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': validation_message
            }), 400
        
        # Pricing information with validation
        price_actual_str = request.form.get('price_actual', '0')
        try:
            price_actual = float(price_actual_str) if price_actual_str else 0
            if price_actual <= 0:
                return jsonify({
                    'success': False,
                    'message': 'Actual price must be greater than 0'
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid actual price format'
            }), 400
        
        price_discounted_str = request.form.get('price_discounted')
        try:
            price_discounted = float(price_discounted_str) if price_discounted_str and price_discounted_str.strip() else None
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid discounted price format'
            }), 400
        
        discount_percentage_str = request.form.get('discount_percentage')
        try:
            discount_percentage = int(discount_percentage_str) if discount_percentage_str and discount_percentage_str.strip() else None
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid discount percentage format'
            }), 400
        
        vat_amount_str = request.form.get('vat_amount')
        try:
            vat_amount = float(vat_amount_str) if vat_amount_str and vat_amount_str.strip() else None
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid VAT amount format'
            }), 400
        
        anesthetic_type = request.form.get('anesthetic_type', '').strip()
        aftercare_kit = request.form.get('aftercare_kit', '').strip()
        
        # Procedure information
        about_procedure = request.form.get('about_procedure', '').strip()
        recommended_for = request.form.get('recommended_for', '').strip()
        downtime = request.form.get('downtime', '').strip()
        duration = request.form.get('duration', '').strip()
        downtime_description = request.form.get('downtime_description', '').strip()
        precautions = request.form.get('precautions', '').strip()
        
        # Contact information
        whatsapp_number = request.form.get('whatsapp_number', '').strip()
        custom_phone_number = request.form.get('custom_phone_number', '').strip()
        chat_message_template = request.form.get('chat_message_template', '').strip()
        call_message_template = request.form.get('call_message_template', '').strip()
        
        # Location information
        clinic_latitude_str = request.form.get('clinic_latitude')
        clinic_latitude = float(clinic_latitude_str) if clinic_latitude_str and clinic_latitude_str.strip() else None
        
        clinic_longitude_str = request.form.get('clinic_longitude')
        clinic_longitude = float(clinic_longitude_str) if clinic_longitude_str and clinic_longitude_str.strip() else None
        
        # Parse JSON fields with error handling
        try:
            key_highlights = json.loads(request.form.get('key_highlights', '{}'))
        except json.JSONDecodeError:
            key_highlights = {}
            
        try:
            procedure_breakdown = json.loads(request.form.get('procedure_breakdown', '[]'))
        except json.JSONDecodeError:
            procedure_breakdown = []
        
        # Auto-generate procedure breakdown if not provided (for existing packages being edited)
        if not procedure_breakdown or len(procedure_breakdown) == 0:
            logger.info(f"Auto-generating procedure breakdown for existing package: {title}")
            procedure_breakdown = procedure_generator.generate_procedure_breakdown(
                title=title,
                category=category,
                actual_treatment_name=actual_treatment_name,
                package_price=price_actual
            )
            
        try:
            results_gallery_data = json.loads(request.form.get('results_gallery', '[]'))
        except json.JSONDecodeError:
            results_gallery_data = []
        
        # Handle file uploads for results gallery (similar to creation)
        results_gallery = []
        for i, result_data in enumerate(results_gallery_data, 1):
            result_item = result_data.copy()
            
            # Handle before/after images and videos
            for media_type in ['before_image', 'after_image', 'before_video', 'after_video']:
                file_key = f"{media_type}_{i}"
                if file_key in request.files:
                    file = request.files[file_key]
                    if file.filename:
                        file_path = save_uploaded_file(file, 'results')
                        if file_path:
                            result_item[media_type] = file_path
            
            results_gallery.append(result_item)
        
        # Generate slug from title
        slug = title.lower().replace(' ', '-').replace('&', 'and')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # Auto-generate treatment name if not provided
        if not actual_treatment_name:
            actual_treatment_name = generate_smart_description(title, category).split('.')[0]
        
        # Update package using raw SQL
        update_sql = """
            UPDATE packages SET
                title = :title,
                slug = :slug,
                description = :description,
                actual_treatment_name = :actual_treatment_name,
                price_actual = :price_actual,
                price_discounted = :price_discounted,
                discount_percentage = :discount_percentage,
                category = :category,
                about_procedure = :about_procedure,
                key_highlights = :key_highlights,
                procedure_breakdown = :procedure_breakdown,
                vat_amount = :vat_amount,
                anesthetic_type = :anesthetic_type,
                aftercare_kit = :aftercare_kit,
                recommended_for = :recommended_for,
                downtime = :downtime,
                duration = :duration,
                downtime_description = :downtime_description,
                precautions = :precautions,
                results_gallery = :results_gallery,
                whatsapp_number = :whatsapp_number,
                custom_phone_number = :custom_phone_number,
                chat_message_template = :chat_message_template,
                call_message_template = :call_message_template,
                clinic_latitude = :clinic_latitude,
                clinic_longitude = :clinic_longitude,
                clinic_address = :clinic_address,
                updated_at = :updated_at
            WHERE id = :package_id AND clinic_id = :clinic_id
        """
        
        db.session.execute(text(update_sql), {
            'title': title,
            'slug': slug,
            'description': description,
            'actual_treatment_name': actual_treatment_name,
            'price_actual': price_actual,
            'price_discounted': price_discounted,
            'discount_percentage': discount_percentage,
            'category': category,
            'about_procedure': about_procedure,
            'key_highlights': json.dumps(key_highlights) if key_highlights else None,
            'procedure_breakdown': json.dumps(procedure_breakdown) if procedure_breakdown else None,
            'vat_amount': vat_amount,
            'anesthetic_type': anesthetic_type,
            'aftercare_kit': aftercare_kit,
            'recommended_for': recommended_for,
            'downtime': downtime,
            'duration': duration,
            'downtime_description': downtime_description,
            'precautions': precautions,
            'results_gallery': json.dumps(results_gallery) if results_gallery else None,
            'whatsapp_number': whatsapp_number,
            'custom_phone_number': custom_phone_number,
            'chat_message_template': chat_message_template,
            'call_message_template': call_message_template,
            'clinic_latitude': clinic_latitude,
            'clinic_longitude': clinic_longitude,
            'clinic_address': clinic_address,
            'updated_at': datetime.utcnow(),
            'package_id': package_id,
            'clinic_id': clinic['id']
        })
        
        db.session.commit()
        
        logger.info(f"Package {package_id} updated successfully by clinic {clinic['id']}")
        
        return jsonify({
            'success': True,
            'message': 'Package updated successfully!',
            'package_id': package_id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating package {package_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Error updating package: {str(e)}'
        }), 500

@enhanced_package_bp.route('/packages/')
def package_directory():
    """Enhanced package directory with filtering and search."""
    try:
        # Get filter parameters
        category = request.args.get('category', '')
        category_id = request.args.get('category_id', '')  # New hierarchical category filtering
        location = request.args.get('location', '')
        price_range = request.args.get('price_range', '')
        min_price = request.args.get('min_price', '')
        max_price = request.args.get('max_price', '')
        search = request.args.get('search', '')
        sort = request.args.get('sort', 'mixed')
        
        # Base query
        package_sql = """
            SELECT p.*, c.name as clinic_name, c.city as clinic_city, c.contact_number as clinic_contact,
                   c.overall_rating as clinic_rating, c.total_reviews as clinic_reviews
            FROM packages p
            JOIN clinics c ON p.clinic_id = c.id
            WHERE p.is_active = true
        """
        
        params = {}
        
        # Add filters
        if category_id:
            # Filter by new hierarchical categories (including child categories)
            package_sql += """ AND p.id IN (
                SELECT DISTINCT ec.entity_id 
                FROM entity_categories ec 
                JOIN category_hierarchy ch ON ec.category_id = ch.id
                WHERE ec.entity_type = 'package' 
                  AND (ch.id = :category_id OR ch.parent_id = :category_id 
                       OR ch.parent_id IN (SELECT id FROM category_hierarchy WHERE parent_id = :category_id))
            )"""
            params['category_id'] = category_id
        elif category:
            # Fallback to old category filtering
            package_sql += " AND p.category ILIKE :category"
            params['category'] = f'%{category}%'
            
        if location:
            package_sql += " AND (c.city ILIKE :location OR c.state ILIKE :location)"
            params['location'] = f'%{location}%'
            
        if search:
            package_sql += " AND (p.title ILIKE :search OR p.description ILIKE :search OR c.name ILIKE :search OR p.id IN (SELECT pc.package_id FROM package_categories pc WHERE pc.category_name ILIKE :search))"
            params['search'] = f'%{search}%'
            
        # Handle custom price range
        if min_price and max_price:
            try:
                min_price_val = float(min_price)
                max_price_val = float(max_price)
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN :min_price AND :max_price"
                params['min_price'] = min_price_val
                params['max_price'] = max_price_val
            except ValueError:
                pass
        elif min_price:
            try:
                min_price_val = float(min_price)
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) >= :min_price"
                params['min_price'] = min_price_val
            except ValueError:
                pass
        elif max_price:
            try:
                max_price_val = float(max_price)
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) <= :max_price"
                params['max_price'] = max_price_val
            except ValueError:
                pass
        elif price_range:
            # Handle preset price ranges
            if price_range == '0-50000':
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) < 50000"
            elif price_range == '50000-100000':
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN 50000 AND 100000"
            elif price_range == '100000-200000':
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN 100000 AND 200000"
            elif price_range == '200000+':
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) > 200000"
        
        # Add sorting - mixed by default for variety
        if sort == 'price_low':
            package_sql += " ORDER BY COALESCE(p.price_discounted, p.price_actual) ASC"
        elif sort == 'price_high':
            package_sql += " ORDER BY COALESCE(p.price_discounted, p.price_actual) DESC"
        elif sort == 'rating':
            package_sql += " ORDER BY c.overall_rating DESC NULLS LAST"
        elif sort == 'popularity':
            package_sql += " ORDER BY c.total_reviews DESC NULLS LAST"
        elif sort == 'newest':
            package_sql += " ORDER BY p.created_at DESC"
        else:  # mixed (default) - randomized to show variety of clinics
            package_sql += " ORDER BY RANDOM()"
        
        # Get total count for pagination (before adding LIMIT)
        # Create a cleaner count query by building it separately to avoid string replacement issues
        count_sql = """
            SELECT COUNT(DISTINCT p.id)
            FROM packages p
            JOIN clinics c ON p.clinic_id = c.id
            WHERE p.is_active = true
        """
        
        # Add the same filters to count query
        if category_id:
            # Filter by new hierarchical categories (including child categories)
            count_sql += """ AND p.id IN (
                SELECT DISTINCT ec.entity_id 
                FROM entity_categories ec 
                JOIN category_hierarchy ch ON ec.category_id = ch.id
                WHERE ec.entity_type = 'package' 
                  AND (ch.id = :category_id OR ch.parent_id = :category_id 
                       OR ch.parent_id IN (SELECT id FROM category_hierarchy WHERE parent_id = :category_id))
            )"""
        elif category:
            count_sql += " AND p.category ILIKE :category"
            
        if location:
            count_sql += " AND (c.city ILIKE :location OR c.state ILIKE :location)"
            
        if search:
            count_sql += " AND (p.title ILIKE :search OR p.description ILIKE :search OR c.name ILIKE :search OR p.id IN (SELECT pc.package_id FROM package_categories pc WHERE pc.category_name ILIKE :search))"
            
        # Handle custom price range for count query
        if min_price and max_price:
            try:
                min_price_val = float(min_price)
                max_price_val = float(max_price)
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN :min_price AND :max_price"
            except ValueError:
                pass
        elif min_price:
            try:
                min_price_val = float(min_price)
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) >= :min_price"
            except ValueError:
                pass
        elif max_price:
            try:
                max_price_val = float(max_price)
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) <= :max_price"
            except ValueError:
                pass
        elif price_range:
            # Handle preset price ranges for count query
            if price_range == '0-50000':
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) < 50000"
            elif price_range == '50000-100000':
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN 50000 AND 100000"
            elif price_range == '100000-200000':
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN 100000 AND 200000"
            elif price_range == '200000+':
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) > 200000"
        
        total_count = db.session.execute(text(count_sql), params).scalar()
        logger.info(f"Package directory total_count: {total_count}")
        
        # Add pagination limit for "Show More" functionality
        limit = 20  # Show 20 packages initially
        package_sql += " LIMIT :limit"
        params['limit'] = limit
        
        packages_result = db.session.execute(text(package_sql), params).fetchall()
        packages = []
        
        for row in packages_result:
            package = dict(row._mapping)
            
            # Parse JSON fields safely for directory display
            if package.get('results_gallery'):
                try:
                    if isinstance(package['results_gallery'], str):
                        package['results_gallery'] = json.loads(package['results_gallery'])
                    elif isinstance(package['results_gallery'], list):
                        # Already a list, keep as is
                        pass
                    else:
                        package['results_gallery'] = []
                except Exception as e:
                    logger.error(f"Error parsing results_gallery for package {package['id']}: {e}")
                    package['results_gallery'] = []
            else:
                package['results_gallery'] = []
            
            # Validate image paths in results_gallery and check if they exist
            valid_results = []
            if package['results_gallery']:
                import os
                for result in package['results_gallery']:
                    before_path = result.get('before_image', '')
                    after_path = result.get('after_image', '')
                    
                    # Check if image paths exist and are valid (not relative paths without /static/)
                    before_exists = before_path and (before_path.startswith('/static/') and os.path.exists(f".{before_path}"))
                    after_exists = after_path and (after_path.startswith('/static/') and os.path.exists(f".{after_path}"))
                    
                    if before_exists and after_exists:
                        valid_results.append(result)
                
                package['results_gallery'] = valid_results
            
            # If no valid results_gallery data, check package_doctor_gallery table
            if not package['results_gallery']:
                gallery_sql = """
                    SELECT pdg.title as procedure_name, pdg.before_image_url as before_image, 
                           pdg.after_image_url as after_image, pdg.description
                    FROM package_doctor_gallery pdg
                    WHERE pdg.package_id = :package_id
                    ORDER BY pdg.created_at DESC
                    LIMIT 5
                """
                gallery_result = db.session.execute(text(gallery_sql), {'package_id': package['id']}).fetchall()
                if gallery_result:
                    package['results_gallery'] = [dict(row._mapping) for row in gallery_result]
                
            packages.append(package)
        
        # Get unique categories and locations for filters (using new many-to-many structure)
        categories_sql = "SELECT DISTINCT category_name FROM package_categories ORDER BY category_name"
        categories_result = db.session.execute(text(categories_sql)).fetchall()
        categories = [row[0] for row in categories_result]
        
        locations_sql = "SELECT DISTINCT city FROM clinics ORDER BY city"
        locations_result = db.session.execute(text(locations_sql)).fetchall()
        locations = [row[0] for row in locations_result]
        
        # Create filter_params object for template
        filter_params = {
            'category': category,
            'location': location,
            'price_range': price_range,
            'min_price': min_price,
            'max_price': max_price,
            'search': search,
            'sort': sort
        }
        
        # Add pagination variables that template expects
        return render_template('packages/directory.html', 
                             packages=packages,
                             categories=categories,
                             locations=locations,
                             filter_params=filter_params,
                             selected_category=category,
                             selected_location=location,
                             selected_price_range=price_range,
                             search_query=search,
                             # Pagination variables for "Show More" functionality
                             total_count=total_count,
                             showing_count=len(packages),
                             has_more=total_count > limit,
                             page=1,
                             total_pages=1,
                             has_prev=False,
                             has_next=False)
                             
    except Exception as e:
        logger.error(f"Error loading package directory: {e}")
        flash('Error loading packages. Please try again.', 'error')
        filter_params = {'category': '', 'location': '', 'price_range': '', 'search': ''}
        return render_template('packages/directory.html', packages=[], categories=[], locations=[], filter_params=filter_params)

@enhanced_package_bp.route('/api/packages/load-more')
def api_packages_load_more():
    """API endpoint for loading more packages (Show More functionality)."""
    try:
        # Get pagination parameters
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Get filter parameters (same as main packages route)
        category = request.args.get('category', '')
        location = request.args.get('location', '')
        price_range = request.args.get('price_range', '')
        min_price = request.args.get('min_price', '')
        max_price = request.args.get('max_price', '')
        search = request.args.get('search', '')
        sort = request.args.get('sort', 'mixed')
        
        # Base query (same as main route)
        package_sql = """
            SELECT p.*, c.name as clinic_name, c.city as clinic_city, c.contact_number as clinic_contact,
                   c.overall_rating as clinic_rating, c.total_reviews as clinic_reviews
            FROM packages p
            JOIN clinics c ON p.clinic_id = c.id
            WHERE p.is_active = true
        """
        
        params = {}
        
        # Add filters (same logic as main route) - using new many-to-many category structure
        if category:
            package_sql += " AND p.id IN (SELECT pc.package_id FROM package_categories pc WHERE pc.category_name ILIKE :category)"
            params['category'] = f'%{category}%'
            
        if location:
            package_sql += " AND (c.city ILIKE :location OR c.state ILIKE :location)"
            params['location'] = f'%{location}%'
            
        if search:
            package_sql += " AND (p.title ILIKE :search OR p.description ILIKE :search OR c.name ILIKE :search OR p.id IN (SELECT pc.package_id FROM package_categories pc WHERE pc.category_name ILIKE :search))"
            params['search'] = f'%{search}%'
            
        # Handle price filtering
        if min_price and max_price:
            try:
                min_price_val = float(min_price)
                max_price_val = float(max_price)
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN :min_price AND :max_price"
                params['min_price'] = min_price_val
                params['max_price'] = max_price_val
            except ValueError:
                pass
        elif min_price:
            try:
                min_price_val = float(min_price)
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) >= :min_price"
                params['min_price'] = min_price_val
            except ValueError:
                pass
        elif max_price:
            try:
                max_price_val = float(max_price)
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) <= :max_price"
                params['max_price'] = max_price_val
            except ValueError:
                pass
        elif price_range:
            # Handle preset price ranges
            if price_range == '0-50000':
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) < 50000"
            elif price_range == '50000-100000':
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN 50000 AND 100000"
            elif price_range == '100000-200000':
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN 100000 AND 200000"
            elif price_range == '200000+':
                package_sql += " AND COALESCE(p.price_discounted, p.price_actual) > 200000"
        
        # Add sorting - mixed by default for variety
        if sort == 'price_low':
            package_sql += " ORDER BY COALESCE(p.price_discounted, p.price_actual) ASC"
        elif sort == 'price_high':
            package_sql += " ORDER BY COALESCE(p.price_discounted, p.price_actual) DESC"
        elif sort == 'rating':
            package_sql += " ORDER BY c.overall_rating DESC NULLS LAST"
        elif sort == 'popularity':
            package_sql += " ORDER BY c.total_reviews DESC NULLS LAST"
        elif sort == 'newest':
            package_sql += " ORDER BY p.created_at DESC"
        else:  # mixed (default) - randomized to show variety of clinics
            package_sql += " ORDER BY RANDOM()"
        
        # Get total count - build separate count query to avoid string replacement issues
        count_sql = """
            SELECT COUNT(DISTINCT p.id)
            FROM packages p
            JOIN clinics c ON p.clinic_id = c.id
            WHERE p.is_active = true
        """
        
        # Add the same filters to count query as main query
        if category:
            count_sql += " AND p.id IN (SELECT pc.package_id FROM package_categories pc WHERE pc.category_name ILIKE :category)"
            
        if location:
            count_sql += " AND (c.city ILIKE :location OR c.state ILIKE :location)"
            
        if search:
            count_sql += " AND (p.title ILIKE :search OR p.description ILIKE :search OR c.name ILIKE :search OR p.id IN (SELECT pc.package_id FROM package_categories pc WHERE pc.category_name ILIKE :search))"
            
        # Handle price filtering for count query
        if min_price and max_price:
            try:
                min_price_val = float(min_price)
                max_price_val = float(max_price)
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN :min_price AND :max_price"
            except ValueError:
                pass
        elif min_price:
            try:
                min_price_val = float(min_price)
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) >= :min_price"
            except ValueError:
                pass
        elif max_price:
            try:
                max_price_val = float(max_price)
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) <= :max_price"
            except ValueError:
                pass
        elif price_range:
            # Handle preset price ranges for count query
            if price_range == '0-50000':
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) < 50000"
            elif price_range == '50000-100000':
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN 50000 AND 100000"
            elif price_range == '100000-200000':
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) BETWEEN 100000 AND 200000"
            elif price_range == '200000+':
                count_sql += " AND COALESCE(p.price_discounted, p.price_actual) > 200000"
        
        total_count = db.session.execute(text(count_sql), params).scalar()
        
        # Add pagination
        package_sql += " LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset
        
        packages_result = db.session.execute(text(package_sql), params).fetchall()
        packages = [dict(row._mapping) for row in packages_result]
        
        return jsonify({
            'success': True,
            'packages': packages,
            'total_count': total_count,
            'showing_count': len(packages),
            'has_more': (offset + len(packages)) < total_count
        })
        
    except Exception as e:
        logger.error(f"Error loading more packages: {e}")
        return jsonify({
            'success': False,
            'message': f'Error loading more packages: {str(e)}'
        }), 500

@enhanced_package_bp.route('/packages/<slug>')
def package_detail(slug):
    """Enhanced package detail page with SEO-friendly URLs using slugs."""
    try:
        # Get package with enhanced fields using raw SQL
        package_sql = """
            SELECT p.*, c.name as clinic_name, c.city as clinic_city, c.contact_number as clinic_contact,
                   c.overall_rating as clinic_rating, c.total_reviews as clinic_reviews,
                   c.whatsapp_number as clinic_whatsapp, c.address as clinic_address, c.slug as clinic_slug
            FROM packages p
            JOIN clinics c ON p.clinic_id = c.id
            WHERE p.slug = :slug AND p.is_active = true
        """
        
        package_result = db.session.execute(text(package_sql), {'slug': slug}).fetchone()
        
        if not package_result:
            flash('Package not found', 'error')
            return redirect(url_for('enhanced_package.package_directory'))
        
        # Convert to dictionary and parse JSON fields
        package = dict(package_result._mapping)
        
        # Parse JSON fields safely - handle both string and already-parsed data
        if package.get('key_highlights'):
            if isinstance(package['key_highlights'], str):
                try:
                    package['key_highlights'] = json.loads(package['key_highlights'])
                    logger.info(f"Parsed key_highlights from string for package {package['id']}: {package['key_highlights']}")
                except Exception as e:
                    logger.error(f"Error parsing key_highlights string for package {package['id']}: {e}")
                    package['key_highlights'] = {}
            elif isinstance(package['key_highlights'], dict):
                logger.info(f"Key_highlights already parsed for package {package['id']}: {package['key_highlights']}")
            else:
                logger.info(f"Key_highlights is neither string nor dict for package {package['id']}")
                package['key_highlights'] = {}
        else:
            logger.info(f"No key_highlights found for package {package['id']}")
            package['key_highlights'] = {}
        
        if package.get('procedure_breakdown'):
            if isinstance(package['procedure_breakdown'], str):
                try:
                    package['procedure_breakdown'] = json.loads(package['procedure_breakdown'])
                    logger.info(f"Parsed procedure_breakdown from string for package {package['id']}: {package['procedure_breakdown']}")
                except Exception as e:
                    logger.error(f"Error parsing procedure_breakdown string for package {package['id']}: {e}")
                    package['procedure_breakdown'] = []
            elif isinstance(package['procedure_breakdown'], list):
                logger.info(f"Procedure_breakdown already parsed for package {package['id']}: {package['procedure_breakdown']}")
            else:
                logger.info(f"Procedure_breakdown is neither string nor list for package {package['id']}")
                package['procedure_breakdown'] = []
        else:
            logger.info(f"No procedure_breakdown found for package {package['id']}")
            package['procedure_breakdown'] = []
                
        if package.get('results_gallery'):
            try:
                if isinstance(package['results_gallery'], str):
                    package['results_gallery'] = json.loads(package['results_gallery'])
                elif isinstance(package['results_gallery'], list):
                    # Already a list, keep as is
                    pass
                else:
                    package['results_gallery'] = []
            except Exception as e:
                logger.error(f"Error parsing results_gallery for package {package['id']}: {e}")
                package['results_gallery'] = []
        else:
            package['results_gallery'] = []
        
        # Update view count
        db.session.execute(text("UPDATE packages SET view_count = COALESCE(view_count, 0) + 1 WHERE id = :id"), {'id': package['id']})
        db.session.commit()
        
        # Get clinic data for ratings and reviews
        clinic_sql = """
            SELECT id, name, address, city, state, contact_number, whatsapp_number,
                   google_rating, google_review_count, last_review_sync
            FROM clinics 
            WHERE id = :clinic_id
        """
        clinic_result = db.session.execute(text(clinic_sql), {'clinic_id': package['clinic_id']}).fetchone()
        clinic_data = dict(clinic_result._mapping) if clinic_result else None
        
        # Get Google reviews for the clinic
        google_reviews = []
        if clinic_data:
            reviews_sql = """
                SELECT author_name, rating, text, profile_photo_url, relative_time_description
                FROM google_reviews 
                WHERE clinic_id = :clinic_id 
                ORDER BY rating DESC, created_at DESC
                LIMIT 10
            """
            reviews_result = db.session.execute(text(reviews_sql), {'clinic_id': package['clinic_id']}).fetchall()
            google_reviews = [dict(row._mapping) for row in reviews_result]
        
        # Get package gallery data from package_doctor_gallery table
        gallery_sql = """
            SELECT pdg.*, d.name as doctor_name, d.specialty as doctor_specialty
            FROM package_doctor_gallery pdg
            LEFT JOIN doctors d ON pdg.doctor_id = d.id
            WHERE pdg.package_id = :package_id
            ORDER BY pdg.created_at DESC
        """
        gallery_result = db.session.execute(text(gallery_sql), {'package_id': package['id']}).fetchall()
        package_gallery = [dict(row._mapping) for row in gallery_result]
        
        # Get related packages from same clinic
        related_sql = """
            SELECT p.*, c.name as clinic_name 
            FROM packages p 
            JOIN clinics c ON p.clinic_id = c.id
            WHERE p.clinic_id = :clinic_id AND p.id != :package_id AND p.is_active = true
            LIMIT 4
        """
        related_result = db.session.execute(text(related_sql), {'clinic_id': package['clinic_id'], 'package_id': package['id']}).fetchall()
        related_packages = [dict(row._mapping) for row in related_result]
        
        return render_template('packages/detail.html', 
                             package=package, 
                             related_packages=related_packages,
                             clinic_data=clinic_data,
                             google_reviews=google_reviews,
                             package_gallery=package_gallery)
        
    except Exception as e:
        logger.error(f"Error loading package {slug}: {e}")
        flash('Error loading package details. Please try again.', 'error')
        return redirect(url_for('enhanced_package.package_directory'))



# Backward compatibility route for old ID-based URLs
@enhanced_package_bp.route('/packages/<int:package_id>')
def package_detail_legacy_redirect(package_id):
    """Redirect old ID-based URLs to new slug-based URLs for SEO and backward compatibility."""
    try:
        # Get package slug by ID
        package = db.session.execute(
            text("SELECT slug FROM packages WHERE id = :package_id AND is_active = true"),
            {'package_id': package_id}
        ).fetchone()
        
        if package:
            # Redirect to new slug-based URL with 301 permanent redirect for SEO
            return redirect(url_for('enhanced_package.package_detail', slug=package.slug), code=301)
        else:
            flash('Package not found', 'error')
            return redirect(url_for('enhanced_package.package_directory'))
    except Exception as e:
        logger.error(f"Error redirecting legacy package URL: {e}")
        return redirect(url_for('enhanced_package.package_directory'))

@enhanced_package_bp.route('/packages/contact/<int:package_id>', methods=['POST'])
def contact_package_enhanced(package_id):
    """Handle enhanced package contact with custom messaging."""
    try:
        data = request.get_json()
        action_type = data.get('action_type', 'chat')
        
        # Get package contact details
        package_sql = """
            SELECT p.whatsapp_number, p.custom_phone_number, p.chat_message_template, 
                   p.call_message_template, c.contact_number, c.whatsapp_number as clinic_whatsapp
            FROM packages p
            JOIN clinics c ON p.clinic_id = c.id
            WHERE p.id = :package_id
        """
        
        contact_result = db.session.execute(text(package_sql), {'package_id': package_id}).fetchone()
        
        if not contact_result:
            return jsonify({'success': False, 'message': 'Package not found'}), 404
        
        package_contact = dict(contact_result._mapping)
        
        # Determine contact numbers
        whatsapp_number = package_contact.get('whatsapp_number') or package_contact.get('clinic_whatsapp')
        phone_number = package_contact.get('custom_phone_number') or package_contact.get('contact_number')
        
        return jsonify({
            'success': True,
            'whatsapp_number': whatsapp_number,
            'phone_number': phone_number,
            'chat_template': package_contact.get('chat_message_template'),
            'call_template': package_contact.get('call_message_template')
        })
        
    except Exception as e:
        logger.error(f"Error handling package contact: {e}")
        return jsonify({'success': False, 'message': 'Error processing contact request'}), 500

# Geocode endpoint moved to app.py with proper CSRF exemption

@enhanced_package_bp.route('/api/categories/search', methods=['GET'])
def search_categories():
    """Search categories with autocomplete functionality."""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            # Return all categories if no query
            categories_sql = """
                SELECT pc.category_name, COUNT(DISTINCT p.id) as package_count 
                FROM package_categories pc
                JOIN packages p ON pc.package_id = p.id
                WHERE p.is_active = true
                GROUP BY pc.category_name 
                ORDER BY package_count DESC, pc.category_name ASC
            """
            categories_result = db.session.execute(text(categories_sql)).fetchall()
        else:
            # Search categories matching the query
            categories_sql = """
                SELECT pc.category_name, COUNT(DISTINCT p.id) as package_count 
                FROM package_categories pc
                JOIN packages p ON pc.package_id = p.id
                WHERE p.is_active = true
                AND pc.category_name ILIKE :query
                GROUP BY pc.category_name 
                ORDER BY package_count DESC, pc.category_name ASC
            """
            categories_result = db.session.execute(text(categories_sql), {'query': f'%{query}%'}).fetchall()
        
        categories = [
            {
                'name': row[0],
                'count': row[1]
            }
            for row in categories_result
        ]
        
        return jsonify({
            'success': True,
            'categories': categories
        })
        
    except Exception as e:
        logger.error(f"Error searching categories: {e}")
        return jsonify({
            'success': False,
            'error': 'Error searching categories'
        }), 500

@enhanced_package_bp.route('/api/locations/search', methods=['GET'])
def search_locations():
    """Search locations with autocomplete functionality."""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            # Return all locations if no query
            locations_sql = """
                SELECT c.city, c.state, COUNT(p.id) as package_count 
                FROM clinics c 
                LEFT JOIN packages p ON c.id = p.clinic_id AND p.is_active = true
                WHERE c.city IS NOT NULL 
                GROUP BY c.city, c.state 
                ORDER BY package_count DESC, c.city ASC
            """
            locations_result = db.session.execute(text(locations_sql)).fetchall()
        else:
            # Search locations matching the query
            locations_sql = """
                SELECT c.city, c.state, COUNT(p.id) as package_count 
                FROM clinics c 
                LEFT JOIN packages p ON c.id = p.clinic_id AND p.is_active = true
                WHERE c.city IS NOT NULL 
                AND (c.city ILIKE :query OR c.state ILIKE :query)
                GROUP BY c.city, c.state 
                ORDER BY package_count DESC, c.city ASC
            """
            locations_result = db.session.execute(text(locations_sql), {'query': f'%{query}%'}).fetchall()
        
        locations = [
            {
                'city': row[0],
                'state': row[1],
                'count': row[2],
                'display_name': f"{row[0]}, {row[1]}" if row[1] else row[0]
            }
            for row in locations_result
        ]
        
        return jsonify({
            'success': True,
            'locations': locations
        })
        
    except Exception as e:
        logger.error(f"Error searching locations: {e}")
        return jsonify({
            'success': False,
            'error': 'Error searching locations'
        }), 500

@enhanced_package_bp.route('/api/packages/filters', methods=['GET'])
def get_filter_data():
    """Get filter data with real-time updates."""
    try:
        # Get price range statistics
        price_stats_sql = """
            SELECT 
                MIN(COALESCE(price_discounted, price_actual)) as min_price,
                MAX(COALESCE(price_discounted, price_actual)) as max_price,
                AVG(COALESCE(price_discounted, price_actual)) as avg_price,
                COUNT(*) as total_packages
            FROM packages 
            WHERE is_active = true
        """
        price_stats = db.session.execute(text(price_stats_sql)).fetchone()
        
        # Get price distribution for histogram
        price_ranges = [
            {'min': 0, 'max': 25000, 'label': 'Under ₹25K'},
            {'min': 25000, 'max': 50000, 'label': '₹25K - ₹50K'},
            {'min': 50000, 'max': 100000, 'label': '₹50K - ₹1L'},
            {'min': 100000, 'max': 200000, 'label': '₹1L - ₹2L'},
            {'min': 200000, 'max': 500000, 'label': '₹2L - ₹5L'},
            {'min': 500000, 'max': 10000000, 'label': 'Above ₹5L'}
        ]
        
        distribution = []
        for range_data in price_ranges:
            count_sql = """
                SELECT COUNT(*) 
                FROM packages 
                WHERE is_active = true 
                AND COALESCE(price_discounted, price_actual) >= :min_price
                AND COALESCE(price_discounted, price_actual) < :max_price
            """
            count_result = db.session.execute(text(count_sql), {
                'min_price': range_data['min'],
                'max_price': range_data['max']
            }).fetchone()
            
            distribution.append({
                'range': range_data['label'],
                'count': count_result[0] if count_result else 0,
                'min': range_data['min'],
                'max': range_data['max']
            })
        
        return jsonify({
            'success': True,
            'price_stats': {
                'min_price': float(price_stats[0]) if price_stats[0] else 0,
                'max_price': float(price_stats[1]) if price_stats[1] else 1000000,
                'avg_price': float(price_stats[2]) if price_stats[2] else 50000,
                'total_packages': price_stats[3] if price_stats[3] else 0
            },
            'price_distribution': distribution
        })
        
    except Exception as e:
        logger.error(f"Error getting filter data: {e}")
        return jsonify({
            'success': False,
            'error': 'Error loading filter data'
        }), 500

@enhanced_package_bp.route('/api/geolocation', methods=['GET'])
def get_user_location():
    """Get user's approximate location based on IP."""
    try:
        # Get user's IP address
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        else:
            ip = request.remote_addr
        
        # Skip local IPs
        if ip in ['127.0.0.1', 'localhost'] or ip.startswith('192.168.') or ip.startswith('10.'):
            return jsonify({
                'success': False,
                'error': 'Local IP detected, cannot determine location'
            }), 400
        
        # Use a free IP geolocation service
        try:
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return jsonify({
                        'success': True,
                        'city': data.get('city'),
                        'region': data.get('regionName'),
                        'country': data.get('country'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon')
                    })
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': 'Unable to determine location'
        }), 400
        
    except Exception as e:
        logger.error(f"Error getting user location: {e}")
        return jsonify({
            'success': False,
            'error': 'Error determining location'
        }), 500