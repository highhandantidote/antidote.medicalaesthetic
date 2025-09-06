"""
Enhanced Key Highlights Routes
Handles the new package creation with enhanced key highlights structure.
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
import json
import logging
from models import db
from sqlalchemy import text

enhanced_highlights_bp = Blueprint('enhanced_highlights', __name__)
logger = logging.getLogger(__name__)

@enhanced_highlights_bp.route('/clinic/packages/add-enhanced', methods=['GET', 'POST'])
@login_required
def add_package_with_enhanced_highlights():
    """Add new package with enhanced key highlights structure."""
    try:
        # Get clinic for current user
        clinic_result = db.session.execute(text("SELECT * FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            flash('Clinic profile not found', 'error')
            return redirect(url_for('web.index'))
        
        clinic = dict(clinic_result._mapping)
    except Exception as e:
        logger.error(f"Error getting clinic for user {current_user.id}: {e}")
        flash('Error accessing clinic profile', 'error')
        return redirect(url_for('web.index'))
    
    if request.method == 'GET':
        return render_template('clinic/add_package_enhanced.html', clinic=clinic)
    
    try:
        # Basic package information
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validate required fields
        if not title or not category or not description:
            return jsonify({
                'success': False,
                'message': 'Title, category, and description are required'
            }), 400
        
        # Pricing information
        try:
            price_actual = float(request.form.get('price_actual', 0))
            if price_actual <= 0:
                return jsonify({
                    'success': False,
                    'message': 'Actual price must be greater than 0'
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid price format'
            }), 400
        
        price_discounted = None
        if request.form.get('price_discounted'):
            try:
                price_discounted = float(request.form.get('price_discounted'))
            except ValueError:
                pass
        
        # Process enhanced key highlights
        key_highlights = []
        try:
            highlights_json = request.form.get('key_highlights', '[]')
            if highlights_json:
                parsed_highlights = json.loads(highlights_json)
                if isinstance(parsed_highlights, list):
                    for highlight in parsed_highlights:
                        if isinstance(highlight, dict) and highlight.get('title') and highlight.get('value'):
                            key_highlights.append({
                                'title': highlight.get('title', '').strip(),
                                'value': highlight.get('value', '').strip(),
                                'explanation': highlight.get('explanation', '').strip()
                            })
        except json.JSONDecodeError:
            logger.error("Invalid JSON format for key highlights")
        
        # Other fields
        about_procedure = request.form.get('about_procedure', '').strip()
        downtime = request.form.get('downtime', '').strip()
        duration = request.form.get('duration', '').strip()
        anesthetic_type = request.form.get('anesthetic_type', '').strip()
        aftercare_kit = request.form.get('aftercare_kit', '').strip()
        
        # Generate slug
        slug = title.lower().replace(' ', '-').replace('&', 'and')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # Create package
        package_sql = """
            INSERT INTO packages (
                clinic_id, title, slug, description, price_actual, price_discounted,
                category, about_procedure, key_highlights, downtime, duration,
                anesthetic_type, aftercare_kit, is_active, created_at
            ) VALUES (
                :clinic_id, :title, :slug, :description, :price_actual, :price_discounted,
                :category, :about_procedure, :key_highlights, :downtime, :duration,
                :anesthetic_type, :aftercare_kit, :is_active, :created_at
            ) RETURNING id
        """
        
        from datetime import datetime
        create_result = db.session.execute(text(package_sql), {
            'clinic_id': clinic['id'],
            'title': title,
            'slug': slug,
            'description': description,
            'price_actual': price_actual,
            'price_discounted': price_discounted,
            'category': category,
            'about_procedure': about_procedure,
            'key_highlights': json.dumps(key_highlights) if key_highlights else None,
            'downtime': downtime,
            'duration': duration,
            'anesthetic_type': anesthetic_type,
            'aftercare_kit': aftercare_kit,
            'is_active': True,
            'created_at': datetime.utcnow()
        })
        
        result_row = create_result.fetchone()
        if result_row:
            package_id = result_row[0]
            db.session.commit()
            
            logger.info(f"Package {package_id} created successfully with enhanced highlights")
            
            return jsonify({
                'success': True,
                'message': 'Package created successfully with enhanced key highlights!',
                'package_id': package_id
            })
        else:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to create package'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating package with enhanced highlights: {e}")
        return jsonify({
            'success': False,
            'message': f'Error creating package: {str(e)}'
        }), 500