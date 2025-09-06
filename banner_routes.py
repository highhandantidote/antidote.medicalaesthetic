"""
Banner routes for the Antidote platform.

This module defines the routes for managing and displaying banners on the homepage.
Banners are placed in strategic positions and can contain multiple slides that rotate
in a carousel/slider.
"""

import os
import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

from app import db
from models import Banner, BannerSlide
from routes import admin_required

# Create the blueprints
banner_bp = Blueprint('banners', __name__)
banner_api_bp = Blueprint('banner_api', __name__, url_prefix='/api/banners')

# Constants for banner positions
BANNER_POSITIONS = [
    'between_hero_stats',
    'between_treatment_categories',
    'between_popular_procedures',
    'between_top_specialists',
    'between_community_posts',
    'before_footer'
]

@banner_bp.route('/admin/banners')
@login_required
@admin_required
def admin_banners():
    """
    Admin interface for managing banners.
    
    This page allows administrators to view, create, edit, and delete banners and slides.
    """
    banners = Banner.query.all()
    return render_template('admin_banners.html', 
                          banners=banners,
                          banner_positions=BANNER_POSITIONS)

@banner_bp.route('/admin/banners/create', methods=['POST'])
@login_required
@admin_required
def create_banner():
    """Create a new banner."""
    name = request.form.get('name')
    position = request.form.get('position')
    
    if not name or not position:
        flash('Name and position are required', 'danger')
        return redirect(url_for('banners.admin_banners'))
    
    banner = Banner(
        name=name,
        position=position,
        is_active=True
    )
    
    db.session.add(banner)
    db.session.commit()
    
    flash(f'Banner "{name}" created successfully', 'success')
    return redirect(url_for('banners.admin_banners'))

@banner_bp.route('/admin/banners/<int:banner_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_banner(banner_id):
    """Toggle a banner's active status."""
    banner = Banner.query.get_or_404(banner_id)
    banner.is_active = not banner.is_active
    
    db.session.commit()
    
    status = 'activated' if banner.is_active else 'deactivated'
    flash(f'Banner "{banner.name}" {status} successfully', 'success')
    
    return redirect(url_for('banners.admin_banners'))

@banner_bp.route('/admin/banners/<int:banner_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_banner(banner_id):
    """Delete a banner and all its slides."""
    banner = Banner.query.get_or_404(banner_id)
    name = banner.name
    
    db.session.delete(banner)
    db.session.commit()
    
    flash(f'Banner "{name}" deleted successfully', 'success')
    return redirect(url_for('banners.admin_banners'))

@banner_bp.route('/admin/banners/<int:banner_id>/slides/create', methods=['POST'])
@login_required
@admin_required
def create_slide(banner_id):
    """Create a new slide for a banner."""
    banner = Banner.query.get_or_404(banner_id)
    
    title = request.form.get('title')
    subtitle = request.form.get('subtitle')
    image_url = request.form.get('image_url')
    uploaded_image = request.files.get('uploaded_image')
    mobile_image_url = request.form.get('mobile_image_url')
    uploaded_mobile_image = request.files.get('uploaded_mobile_image')
    redirect_url = request.form.get('redirect_url')
    display_order = request.form.get('display_order', 0)
    
    # Debug logging
    current_app.logger.info(f"=== BANNER SLIDE CREATION DEBUG ===")
    current_app.logger.info(f"Form data: title={title}")
    current_app.logger.info(f"Form data: subtitle={subtitle}")
    current_app.logger.info(f"Form data: image_url={image_url}")
    current_app.logger.info(f"Form data: mobile_image_url={mobile_image_url}")
    current_app.logger.info(f"Form data: redirect_url={redirect_url}")
    current_app.logger.info(f"Form data: display_order={display_order}")
    current_app.logger.info(f"Files: uploaded_image={uploaded_image.filename if uploaded_image else 'None'}")
    current_app.logger.info(f"Files: uploaded_mobile_image={uploaded_mobile_image.filename if uploaded_mobile_image else 'None'}")
    current_app.logger.info(f"Request files keys: {list(request.files.keys())}")
    current_app.logger.info(f"Request form keys: {list(request.form.keys())}")
    current_app.logger.info(f"=== END DEBUG ===")
    
    # Check if we have either an image URL or an uploaded image
    if not title or (not image_url and not uploaded_image) or not redirect_url:
        flash('Title, image (URL or upload), and redirect URL are required', 'danger')
        return redirect(url_for('banners.admin_banners'))
    
    # Get the highest display order if not provided
    if not display_order:
        highest_order = db.session.query(db.func.max(BannerSlide.display_order))\
            .filter_by(banner_id=banner_id).scalar() or 0
        display_order = highest_order + 10
    
    # Check if we have an uploaded image
    if uploaded_image and uploaded_image.filename:
        try:
            # Create a safe filename
            filename = secure_filename(uploaded_image.filename)
            
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'banners')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Create a unique filename using timestamp and original filename
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            
            # Save the uploaded file
            file_path = os.path.join(upload_dir, unique_filename)
            uploaded_image.save(file_path)
            
            # Update the image URL to point to the saved file
            image_url = f"/static/uploads/banners/{unique_filename}"
            
        except Exception as e:
            flash(f'Error uploading image: {str(e)}', 'danger')
            return redirect(url_for('banners.admin_banners'))
    
    # Handle mobile image upload
    if uploaded_mobile_image and uploaded_mobile_image.filename:
        current_app.logger.info(f"Processing mobile image upload: {uploaded_mobile_image.filename}")
        try:
            # Create a safe filename
            filename = secure_filename(uploaded_mobile_image.filename)
            current_app.logger.info(f"Secure filename: {filename}")
            
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'banners')
            os.makedirs(upload_dir, exist_ok=True)
            current_app.logger.info(f"Upload directory: {upload_dir}")
            
            # Create a unique filename using timestamp and original filename
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_filename = f"{timestamp}_mobile_{filename}"
            current_app.logger.info(f"Unique filename: {unique_filename}")
            
            # Save the uploaded file
            file_path = os.path.join(upload_dir, unique_filename)
            uploaded_mobile_image.save(file_path)
            current_app.logger.info(f"File saved to: {file_path}")
            
            # Update the mobile image URL to point to the saved file
            mobile_image_url = f"/static/uploads/banners/{unique_filename}"
            current_app.logger.info(f"Mobile image URL set to: {mobile_image_url}")
            
        except Exception as e:
            current_app.logger.error(f'Error uploading mobile image: {str(e)}')
            flash(f'Error uploading mobile image: {str(e)}', 'danger')
            return redirect(url_for('banners.admin_banners'))
    else:
        current_app.logger.info("No mobile image uploaded or filename is empty")
    
    slide = BannerSlide(
        banner_id=banner_id,
        title=title,
        subtitle=subtitle,
        image_url=image_url,
        mobile_image_url=mobile_image_url,
        redirect_url=redirect_url,
        display_order=display_order,
        is_active=True
    )
    
    db.session.add(slide)
    db.session.commit()
    
    flash(f'Slide "{title}" created successfully', 'success')
    return redirect(url_for('banners.admin_banners'))

@banner_bp.route('/admin/slides/<int:slide_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_slide(slide_id):
    """Toggle a slide's active status."""
    slide = BannerSlide.query.get_or_404(slide_id)
    slide.is_active = not slide.is_active
    
    db.session.commit()
    
    status = 'activated' if slide.is_active else 'deactivated'
    flash(f'Slide "{slide.title}" {status} successfully', 'success')
    
    return redirect(url_for('banners.admin_banners'))

@banner_bp.route('/admin/slides/<int:slide_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_slide(slide_id):
    """Delete a slide."""
    slide = BannerSlide.query.get_or_404(slide_id)
    title = slide.title
    
    db.session.delete(slide)
    db.session.commit()
    
    flash(f'Slide "{title}" deleted successfully', 'success')
    return redirect(url_for('banners.admin_banners'))

@banner_bp.route('/admin/slides/<int:slide_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_slide(slide_id):
    """Edit a slide."""
    slide = BannerSlide.query.get_or_404(slide_id)
    
    if request.method == 'POST':
        slide.title = request.form.get('title')
        slide.subtitle = request.form.get('subtitle')
        image_url = request.form.get('image_url')
        uploaded_image = request.files.get('uploaded_image')
        mobile_image_url = request.form.get('mobile_image_url')
        uploaded_mobile_image = request.files.get('uploaded_mobile_image')
        slide.redirect_url = request.form.get('redirect_url')
        slide.display_order = request.form.get('display_order', slide.display_order)
        
        # Check if a new image was uploaded
        if uploaded_image and uploaded_image.filename:
            try:
                # Create a safe filename
                filename = secure_filename(uploaded_image.filename)
                
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'banners')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Create a unique filename using timestamp and original filename
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                
                # Save the uploaded file
                file_path = os.path.join(upload_dir, unique_filename)
                uploaded_image.save(file_path)
                
                # Update the image URL to point to the saved file
                slide.image_url = f"/static/uploads/banners/{unique_filename}"
                
            except Exception as e:
                flash(f'Error uploading image: {str(e)}', 'danger')
                return redirect(url_for('banners.edit_slide', slide_id=slide_id))
        elif image_url:  # If no upload but URL is provided
            slide.image_url = image_url
        # else: keep existing image URL if neither is provided
        
        # Handle mobile image removal
        if request.form.get('remove_mobile_image'):
            slide.mobile_image_url = None
        else:
            # Check if a new mobile image was uploaded
            if uploaded_mobile_image and uploaded_mobile_image.filename:
                try:
                    # Create a safe filename
                    filename = secure_filename(uploaded_mobile_image.filename)
                    
                    # Create uploads directory if it doesn't exist
                    upload_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'banners')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Create a unique filename using timestamp and original filename
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    unique_filename = f"{timestamp}_mobile_{filename}"
                    
                    # Save the uploaded file
                    file_path = os.path.join(upload_dir, unique_filename)
                    uploaded_mobile_image.save(file_path)
                    
                    # Update the mobile image URL to point to the saved file
                    slide.mobile_image_url = f"/static/uploads/banners/{unique_filename}"
                    
                except Exception as e:
                    flash(f'Error uploading mobile image: {str(e)}', 'danger')
                    return redirect(url_for('banners.edit_slide', slide_id=slide_id))
            elif mobile_image_url:  # If no upload but URL is provided
                slide.mobile_image_url = mobile_image_url
            # else: keep existing mobile image URL if neither is provided
        
        db.session.commit()
        
        flash(f'Slide "{slide.title}" updated successfully', 'success')
        return redirect(url_for('banners.admin_banners'))
    
    return render_template('admin_edit_slide.html', slide=slide)

# API endpoints for banners
@banner_api_bp.route('/active-positions', methods=['GET'])
def get_active_banner_positions():
    """
    Get all banner positions that have active banners with slides.
    Uses caching for instant response.
    
    Returns:
        JSON with list of positions that have content.
    """
    from banner_cache import banner_cache
    
    try:
        positions = banner_cache.get_active_positions()
        
        return jsonify({
            'success': True,
            'positions': positions
        })
    except Exception as e:
        current_app.logger.error(f"Error getting active positions: {e}")
        return jsonify({
            'success': False,
            'positions': []
        })

@banner_api_bp.route('/<position>', methods=['GET'])
def get_banner_by_position(position):
    """
    Get a banner by its position with optimized caching for instant loading.
    
    Returns:
        JSON with the banner and its active slides, optimized for WebP.
    """
    from banner_cache import banner_cache
    
    # Use cached data for hero banner for instant loading
    if position == 'hero_banner':
        try:
            banner_data = banner_cache.get_hero_banner_data()
            if not banner_data:
                return jsonify({'success': False, 'message': 'No active hero banner found'}), 404
            
            response = jsonify({
                'success': True,
                'banner': banner_data
            })
            
            # Add cache headers for images but not API data
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            return response
            
        except Exception as e:
            current_app.logger.error(f"Error getting cached hero banner: {e}")
            # Fall back to database query
    
    # Original database query for non-hero banners or fallback
    banner = Banner.query.filter_by(position=position, is_active=True).first()
    
    if not banner:
        return jsonify({'success': False, 'message': f'No active banner found for position: {position}'}), 404
    
    # Check if banner has any active slides
    active_slides = [slide for slide in banner.slides if slide.is_active]
    if not active_slides:
        return jsonify({'success': False, 'message': f'No active slides found for banner at position: {position}'}), 404
    
    # For hero banner, use optimized WebP if available, otherwise use original URLs
    if position == 'hero_banner':
        for slide in active_slides:
            # Use actual image URLs from database, not hardcoded paths
            # Only optimize for WebP if the files exist
            if slide.image_url and slide.image_url.endswith('.png'):
                webp_url = slide.image_url.replace('.png', '.webp')
                webp_path = os.path.join(os.getcwd(), 'static', webp_url.lstrip('/static/'))
                if os.path.exists(webp_path):
                    slide.image_url = webp_url
            
            if slide.mobile_image_url and slide.mobile_image_url.endswith('.png'):
                webp_url = slide.mobile_image_url.replace('.png', '.webp')
                webp_path = os.path.join(os.getcwd(), 'static', webp_url.lstrip('/static/'))
                if os.path.exists(webp_path):
                    slide.mobile_image_url = webp_url
    
    # Optimize images for WebP delivery
    def optimize_image_url(image_url):
        """Convert image URL to WebP if available"""
        if image_url and image_url.endswith('.png'):
            webp_url = image_url.replace('.png', '.webp')
            # Check if WebP version exists
            import os
            webp_path = os.path.join(os.getcwd(), 'static', webp_url.lstrip('/static/'))
            if os.path.exists(webp_path):
                return webp_url
        return image_url
    
    # Increment impression count for each active slide
    for slide in active_slides:
        if slide.impression_count is not None:
            slide.impression_count += 1
        else:
            # Initialize impression_count if it's None
            slide.impression_count = 1
        
        # Optimize image URLs for WebP (only for non-hero banners)
        if position != 'hero_banner':
            slide.image_url = optimize_image_url(slide.image_url)
            if slide.mobile_image_url:
                slide.mobile_image_url = optimize_image_url(slide.mobile_image_url)
    
    db.session.commit()
    
    response = jsonify({
        'success': True,
        'banner': banner.to_dict()
    })
    
    # Add cache-busting headers to prevent browser caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@banner_api_bp.route('/impression', methods=['POST'])
def record_banner_impression():
    """Record a banner impression."""
    try:
        data = request.get_json()
        if not data or 'slide_id' not in data:
            return jsonify({'success': False, 'message': 'Missing slide_id'}), 400
        
        slide_id = data['slide_id']
        slide = BannerSlide.query.get(slide_id)
        
        if not slide:
            return jsonify({'success': False, 'message': 'Slide not found'}), 404
        
        # Initialize impression count if None
        if slide.impression_count is None:
            slide.impression_count = 0
        
        slide.impression_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Impression recorded for slide {slide_id}',
            'impression_count': slide.impression_count
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@banner_api_bp.route('/click', methods=['POST'])
def record_banner_click():
    """Record a banner click."""
    try:
        data = request.get_json()
        if not data or 'slide_id' not in data:
            return jsonify({'success': False, 'message': 'Missing slide_id'}), 400
    
        slide_id = data['slide_id']
        slide = BannerSlide.query.get(slide_id)
        
        if not slide:
            return jsonify({'success': False, 'message': 'Slide not found'}), 404
        
        # Initialize counters if None
        if slide.click_count is None:
            slide.click_count = 0
        if slide.impression_count is None:
            slide.impression_count = 1
        
        slide.click_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Click recorded for slide {slide_id}',
            'click_count': slide.click_count,
            'ctr': round((slide.click_count / slide.impression_count * 100), 2) if slide.impression_count > 0 else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@banner_api_bp.route('/slide/<int:slide_id>/click', methods=['POST'])
def record_slide_click(slide_id):
    """
    Record a click on a banner slide.
    
    Increments the click counter for the slide.
    """
    slide = BannerSlide.query.get_or_404(slide_id)
    
    # Initialize counters if they are None
    if slide.click_count is None:
        slide.click_count = 0
    if slide.impression_count is None:
        slide.impression_count = 1  # Set to 1 to avoid division by zero
    
    slide.click_count += 1
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Click recorded for slide {slide_id}',
        'click_count': slide.click_count,
        'ctr': round((slide.click_count / slide.impression_count * 100), 2) if slide.impression_count > 0 else 0
    })