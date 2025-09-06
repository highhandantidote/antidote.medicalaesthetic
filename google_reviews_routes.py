"""
Google Reviews management routes for clinic dashboard.
Allows clinic owners to configure Google Business URL and sync reviews automatically.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Clinic, GoogleReview
from google_places_service import google_places_service
import logging

google_reviews_bp = Blueprint('google_reviews', __name__)
logger = logging.getLogger(__name__)

@google_reviews_bp.route('/clinic/google-reviews')
@login_required
def google_reviews_dashboard():
    """Google Reviews management dashboard for clinic owners."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        flash('Clinic profile not found', 'error')
        return redirect(url_for('routes.index'))
    
    # Get Google reviews for display
    google_reviews = GoogleReview.query.filter_by(
        clinic_id=clinic.id, 
        is_active=True
    ).order_by(GoogleReview.time.desc()).limit(10).all()
    
    # Calculate sync status
    sync_status = {
        'configured': bool(clinic.google_place_id),
        'last_sync': clinic.last_review_sync,
        'total_reviews': len(google_reviews),
        'avg_rating': clinic.google_rating,
        'google_review_count': clinic.google_review_count
    }
    
    return render_template('clinic/google_reviews.html',
                         clinic=clinic,
                         google_reviews=google_reviews,
                         sync_status=sync_status)

@google_reviews_bp.route('/clinic/google-reviews/configure', methods=['POST'])
@login_required
def configure_google_business():
    """Configure Google Business URL for clinic."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        return jsonify({'success': False, 'error': 'Clinic not found'})
    
    google_url = request.form.get('google_business_url', '').strip()
    if not google_url:
        return jsonify({'success': False, 'error': 'Google Business URL is required'})
    
    # Validate URL and extract Place ID
    validation_result = google_places_service.validate_google_url(google_url)
    
    if not validation_result['valid']:
        return jsonify({
            'success': False, 
            'error': f"Invalid Google Business URL: {validation_result.get('error', 'Unknown error')}"
        })
    
    try:
        # Update clinic with Google Business info
        clinic.google_business_url = google_url
        clinic.google_place_id = validation_result['place_id']
        clinic.google_sync_enabled = True
        
        # Update basic info from Google
        if validation_result.get('rating'):
            clinic.google_rating = validation_result['rating']
        if validation_result.get('review_count'):
            clinic.google_review_count = validation_result['review_count']
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Google Business URL configured successfully',
            'place_info': {
                'name': validation_result.get('name'),
                'rating': validation_result.get('rating'),
                'review_count': validation_result.get('review_count'),
                'address': validation_result.get('address')
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error configuring Google Business URL: {e}")
        return jsonify({'success': False, 'error': 'Database error occurred'})

@google_reviews_bp.route('/clinic/google-reviews/sync', methods=['POST'])
@login_required
def sync_google_reviews():
    """Manually sync Google reviews for clinic."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        return jsonify({'success': False, 'error': 'Clinic not found'})
    
    if not clinic.google_place_id:
        return jsonify({'success': False, 'error': 'Google Business URL not configured'})
    
    # Perform sync
    sync_result = google_places_service.sync_clinic_reviews(clinic.id)
    
    if sync_result['success']:
        return jsonify({
            'success': True,
            'message': f"Sync completed: {sync_result['new_reviews']} new reviews, {sync_result['updated_reviews']} updated",
            'stats': {
                'new_reviews': sync_result['new_reviews'],
                'updated_reviews': sync_result['updated_reviews'],
                'total_reviews': sync_result['total_reviews'],
                'google_rating': sync_result['google_rating'],
                'google_review_count': sync_result['google_review_count']
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': sync_result.get('error', 'Sync failed')
        })

@google_reviews_bp.route('/clinic/google-reviews/toggle-sync', methods=['POST'])
@login_required
def toggle_sync():
    """Enable/disable automatic sync for clinic."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        return jsonify({'success': False, 'error': 'Clinic not found'})
    
    enable_sync = request.form.get('enable_sync') == 'true'
    
    try:
        clinic.google_sync_enabled = enable_sync
        db.session.commit()
        
        status = "enabled" if enable_sync else "disabled"
        return jsonify({
            'success': True,
            'message': f'Automatic sync {status}',
            'sync_enabled': enable_sync
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling sync: {e}")
        return jsonify({'success': False, 'error': 'Database error occurred'})

@google_reviews_bp.route('/clinic/google-reviews/hide/<int:review_id>', methods=['POST'])
@login_required
def hide_review(review_id):
    """Hide a specific Google review from display."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        return jsonify({'success': False, 'error': 'Clinic not found'})
    
    review = GoogleReview.query.filter_by(
        id=review_id,
        clinic_id=clinic.id
    ).first()
    
    if not review:
        return jsonify({'success': False, 'error': 'Review not found'})
    
    try:
        review.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Review hidden from display'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error hiding review: {e}")
        return jsonify({'success': False, 'error': 'Database error occurred'})

@google_reviews_bp.route('/clinic/google-reviews/list')
@login_required
def list_clinic_reviews():
    """List Google reviews for the current clinic (for dashboard display)."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        return jsonify({'success': False, 'error': 'Clinic not found'})
    
    reviews = GoogleReview.query.filter_by(
        clinic_id=clinic.id,
        is_active=True
    ).order_by(GoogleReview.time.desc()).limit(10).all()
    
    review_data = []
    for review in reviews:
        review_data.append({
            'id': review.id,
            'author_name': review.author_name,
            'profile_photo_url': review.profile_photo_url,
            'rating': review.rating,
            'text': review.text,
            'time': review.time.isoformat() if review.time else None,
            'relative_time_description': review.relative_time_description,
            'language': review.language
        })
    
    return jsonify({
        'success': True,
        'reviews': review_data,
        'google_rating': clinic.google_rating,
        'google_review_count': clinic.google_review_count,
        'last_sync': clinic.last_review_sync.isoformat() if clinic.last_review_sync else None
    })

@google_reviews_bp.route('/api/clinic/<int:clinic_id>/google-reviews')
def api_get_google_reviews(clinic_id):
    """API endpoint to get Google reviews for a clinic (for public display)."""
    clinic = Clinic.query.filter_by(id=clinic_id, is_approved=True).first()
    if not clinic:
        return jsonify({'error': 'Clinic not found'}), 404
    
    # Prioritize reviews with profile pictures, then by time
    from sqlalchemy import case, func
    reviews = GoogleReview.query.filter_by(
        clinic_id=clinic_id,
        is_active=True
    ).order_by(
        case(
            (func.coalesce(GoogleReview.profile_photo_url, '') != '', 0),
            else_=1
        ),
        GoogleReview.time.desc()
    ).limit(20).all()
    
    review_data = []
    for review in reviews:
        review_data.append({
            'id': review.id,
            'author_name': review.author_name,
            'profile_photo_url': review.profile_photo_url,
            'rating': review.rating,
            'text': review.text,
            'time': review.time.isoformat() if review.time else None,
            'relative_time': review.relative_time_description,
            'language': review.language
        })
    
    return jsonify({
        'clinic_name': clinic.name,
        'google_rating': clinic.google_rating,
        'google_review_count': clinic.google_review_count,
        'last_sync': clinic.last_review_sync.isoformat() if clinic.last_review_sync else None,
        'reviews': review_data
    })

# Utility function for background sync (can be called by cron job)
def sync_all_enabled_clinics():
    """Sync reviews for all clinics with Google sync enabled."""
    clinics = Clinic.query.filter_by(google_sync_enabled=True).all()
    
    results = {
        'total_clinics': len(clinics),
        'successful_syncs': 0,
        'failed_syncs': 0,
        'errors': []
    }
    
    for clinic in clinics:
        if clinic.google_place_id:
            sync_result = google_places_service.sync_clinic_reviews(clinic.id)
            
            if sync_result['success']:
                results['successful_syncs'] += 1
                logger.info(f"Successfully synced reviews for clinic {clinic.id}: {sync_result['new_reviews']} new reviews")
            else:
                results['failed_syncs'] += 1
                error_msg = f"Failed to sync clinic {clinic.id}: {sync_result.get('error', 'Unknown error')}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
    
    return results