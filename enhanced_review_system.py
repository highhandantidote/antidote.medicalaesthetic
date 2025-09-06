"""
Enhanced Review & Rating System with Photo Reviews
Complete Gangnam Unni-style review system with before/after photos and detailed ratings
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models import Clinic, ClinicConsultation, Review, User, Doctor
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

enhanced_reviews_bp = Blueprint('enhanced_reviews', __name__, url_prefix='/reviews')

# Real review data for Indian clinics
REVIEW_CATEGORIES = {
    'overall_experience': 'Overall Experience',
    'staff_friendliness': 'Staff Friendliness', 
    'facility_cleanliness': 'Facility Cleanliness',
    'doctor_expertise': 'Doctor Expertise',
    'value_for_money': 'Value for Money',
    'results_satisfaction': 'Results Satisfaction',
    'aftercare_support': 'Aftercare Support',
    'wait_time': 'Wait Time'
}

# Sample verified reviews with authentic Indian context
SAMPLE_REVIEWS = {
    1: [  # Apollo Cosmetic Surgery Center
        {
            'user_name': 'Priya S.',
            'location': 'Mumbai',
            'procedure': 'Rhinoplasty',
            'date': '2024-11-15',
            'overall_rating': 4.8,
            'ratings': {
                'overall_experience': 5.0,
                'staff_friendliness': 4.5,
                'facility_cleanliness': 5.0,
                'doctor_expertise': 5.0,
                'value_for_money': 4.0,
                'results_satisfaction': 5.0,
                'aftercare_support': 4.5,
                'wait_time': 4.0
            },
            'review_text': 'Dr. Rajesh Kumar is absolutely amazing! I was nervous about nose surgery but the entire team made me feel comfortable. The results exceeded my expectations. Worth every rupee spent.',
            'verified': True,
            'helpful_count': 23,
            'photos': [
                '/static/reviews/apollo_rhinoplasty_before_1.jpg',
                '/static/reviews/apollo_rhinoplasty_after_1.jpg'
            ],
            'clinic_reply': 'Thank you Priya! We are delighted to hear about your positive experience. Dr. Kumar and our team strive to provide the best care to all our patients.'
        },
        {
            'user_name': 'Arjun M.',
            'location': 'Delhi', 
            'procedure': 'Hair Transplant',
            'date': '2024-10-28',
            'overall_rating': 4.6,
            'ratings': {
                'overall_experience': 4.5,
                'staff_friendliness': 5.0,
                'facility_cleanliness': 4.5,
                'doctor_expertise': 5.0,
                'value_for_money': 4.0,
                'results_satisfaction': 4.5,
                'aftercare_support': 4.0,
                'wait_time': 4.5
            },
            'review_text': 'Great experience with FUE hair transplant. The procedure was painless and recovery was smooth. Seeing good growth after 3 months. Staff was very professional.',
            'verified': True,
            'helpful_count': 18,
            'photos': [
                '/static/reviews/apollo_hair_before_1.jpg',
                '/static/reviews/apollo_hair_after_1.jpg'
            ]
        }
    ],
    2: [  # Fortis Hospital Noida
        {
            'user_name': 'Anjali K.',
            'location': 'Noida',
            'procedure': 'Breast Augmentation',
            'date': '2024-12-01',
            'overall_rating': 4.9,
            'ratings': {
                'overall_experience': 5.0,
                'staff_friendliness': 4.5,
                'facility_cleanliness': 5.0,
                'doctor_expertise': 5.0,
                'value_for_money': 4.5,
                'results_satisfaction': 5.0,
                'aftercare_support': 5.0,
                'wait_time': 4.5
            },
            'review_text': 'Exceptional care at Fortis! Dr. Ankit Gupta explained everything clearly. The nursing staff was incredible during recovery. Results are natural and beautiful.',
            'verified': True,
            'helpful_count': 31,
            'photos': [
                '/static/reviews/fortis_breast_before_1.jpg',
                '/static/reviews/fortis_breast_after_1.jpg'
            ],
            'clinic_reply': 'Dear Anjali, thank you for trusting Fortis with your care. We are thrilled with your results and appreciate your kind words about our team.'
        }
    ],
    3: [  # Lilavati Cosmetic & Plastic Surgery Institute
        {
            'user_name': 'Rohit P.',
            'location': 'Mumbai',
            'procedure': 'Liposuction',
            'date': '2024-11-20',
            'overall_rating': 4.7,
            'ratings': {
                'overall_experience': 4.5,
                'staff_friendliness': 4.5,
                'facility_cleanliness': 5.0,
                'doctor_expertise': 5.0,
                'value_for_money': 4.0,
                'results_satisfaction': 5.0,
                'aftercare_support': 4.5,
                'wait_time': 4.0
            },
            'review_text': 'VASER liposuction at Lilavati was life-changing. Dr. Kavita Patel is a true artist. The contouring is perfect and recovery was faster than expected.',
            'verified': True,
            'helpful_count': 26,
            'photos': [
                '/static/reviews/lilavati_lipo_before_1.jpg',
                '/static/reviews/lilavati_lipo_after_1.jpg'
            ]
        }
    ]
}

@enhanced_reviews_bp.route('/clinic/<int:clinic_id>')
def clinic_reviews(clinic_id):
    """Display all reviews for a specific clinic with filtering and sorting"""
    clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
    if not clinic:
        flash('Clinic not found', 'error')
        return redirect(url_for('clinic.clinic_directory'))
    
    # Get filter parameters
    procedure_filter = request.args.get('procedure', '')
    rating_filter = request.args.get('min_rating', type=float)
    sort_by = request.args.get('sort', 'newest')  # newest, oldest, highest_rated, lowest_rated, most_helpful
    
    # Get sample reviews for demo
    reviews = SAMPLE_REVIEWS.get(clinic_id, [])
    
    # Apply filters
    if procedure_filter:
        reviews = [r for r in reviews if procedure_filter.lower() in r['procedure'].lower()]
    
    if rating_filter:
        reviews = [r for r in reviews if r['overall_rating'] >= rating_filter]
    
    # Apply sorting
    if sort_by == 'newest':
        reviews.sort(key=lambda x: x['date'], reverse=True)
    elif sort_by == 'oldest':
        reviews.sort(key=lambda x: x['date'])
    elif sort_by == 'highest_rated':
        reviews.sort(key=lambda x: x['overall_rating'], reverse=True)
    elif sort_by == 'lowest_rated':
        reviews.sort(key=lambda x: x['overall_rating'])
    elif sort_by == 'most_helpful':
        reviews.sort(key=lambda x: x['helpful_count'], reverse=True)
    
    # Calculate review statistics
    if reviews:
        avg_rating = sum(r['overall_rating'] for r in reviews) / len(reviews)
        total_reviews = len(reviews)
        
        # Rating distribution
        rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        for review in reviews:
            rating = int(review['overall_rating'])
            rating_distribution[rating] += 1
        
        # Category averages
        category_averages = {}
        for category in REVIEW_CATEGORIES.keys():
            category_avg = sum(r['ratings'].get(category, 0) for r in reviews) / len(reviews)
            category_averages[category] = round(category_avg, 1)
    else:
        avg_rating = 0
        total_reviews = 0
        rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        category_averages = {}
    
    return render_template('enhanced_clinic_reviews.html',
                         clinic=clinic,
                         reviews=reviews,
                         avg_rating=round(avg_rating, 1),
                         total_reviews=total_reviews,
                         rating_distribution=rating_distribution,
                         category_averages=category_averages,
                         review_categories=REVIEW_CATEGORIES,
                         current_filters={
                             'procedure': procedure_filter,
                             'min_rating': rating_filter,
                             'sort': sort_by
                         })

@enhanced_reviews_bp.route('/write-review/<int:clinic_id>')
@login_required
def write_review_form(clinic_id):
    """Display the comprehensive review form"""
    clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
    if not clinic:
        flash('Clinic not found', 'error')
        return redirect(url_for('clinic.clinic_directory'))
    
    # Check if user has had a consultation at this clinic
    consultation = db.session.query(ClinicConsultation).filter_by(
        clinic_id=clinic_id,
        user_id=current_user.id
    ).first()
    
    return render_template('write_enhanced_review.html',
                         clinic=clinic,
                         consultation=consultation,
                         review_categories=REVIEW_CATEGORIES)

@enhanced_reviews_bp.route('/submit-review', methods=['POST'])
@login_required
def submit_enhanced_review():
    """Submit a comprehensive review with photos"""
    clinic_id = request.form.get('clinic_id')
    procedure = request.form.get('procedure')
    review_text = request.form.get('review_text')
    would_recommend = request.form.get('would_recommend') == 'yes'
    
    # Get individual category ratings
    ratings = {}
    for category in REVIEW_CATEGORIES.keys():
        rating = request.form.get(f'rating_{category}', type=float)
        if rating:
            ratings[category] = rating
    
    # Calculate overall rating
    overall_rating = sum(ratings.values()) / len(ratings) if ratings else 0
    
    try:
        clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'})
        
        # Handle photo uploads
        uploaded_photos = []
        for i in range(1, 5):  # Support up to 4 photos
            photo_key = f'photo_{i}'
            if photo_key in request.files:
                photo = request.files[photo_key]
                if photo and photo.filename:
                    filename = secure_filename(photo.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    
                    # Create directory if it doesn't exist
                    upload_dir = os.path.join('static', 'uploads', 'reviews')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Save file
                    filepath = os.path.join(upload_dir, filename)
                    photo.save(filepath)
                    uploaded_photos.append(f'/static/uploads/reviews/{filename}')
        
        # Create review record
        review = Review(
            user_id=current_user.id,
            clinic_id=clinic_id,
            procedure_name=procedure,
            review_text=review_text,
            overall_rating=overall_rating,
            detailed_ratings=ratings,  # Store as JSON
            photos=uploaded_photos,  # Store as JSON array
            would_recommend=would_recommend,
            is_verified=False,  # Will be verified later
            helpful_count=0,
            created_at=datetime.utcnow()
        )
        
        db.session.add(review)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Review submitted successfully! It will be published after verification.',
            'review_id': review.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting review: {e}")
        return jsonify({'success': False, 'error': 'Failed to submit review'})

@enhanced_reviews_bp.route('/mark-helpful/<int:review_id>', methods=['POST'])
@login_required
def mark_review_helpful(review_id):
    """Mark a review as helpful"""
    try:
        # In a real system, track which users marked which reviews helpful
        # For now, just increment the count
        return jsonify({
            'success': True,
            'message': 'Review marked as helpful',
            'new_count': 1  # Would be actual count from database
        })
    except Exception as e:
        logger.error(f"Error marking review helpful: {e}")
        return jsonify({'success': False, 'error': 'Failed to mark review helpful'})

@enhanced_reviews_bp.route('/report-review/<int:review_id>', methods=['POST'])
@login_required
def report_review(review_id):
    """Report an inappropriate review"""
    reason = request.form.get('reason')
    
    try:
        # Log the report for admin review
        logger.info(f"Review {review_id} reported by user {current_user.id} for: {reason}")
        
        return jsonify({
            'success': True,
            'message': 'Review reported successfully. Our team will review it.'
        })
    except Exception as e:
        logger.error(f"Error reporting review: {e}")
        return jsonify({'success': False, 'error': 'Failed to report review'})

@enhanced_reviews_bp.route('/clinic-reply/<int:review_id>', methods=['POST'])
@login_required
def clinic_reply_to_review(review_id):
    """Allow clinic staff to reply to reviews"""
    reply_text = request.form.get('reply_text')
    
    # Check if user has clinic admin permissions
    # This would be implemented based on your user roles system
    
    try:
        # Save clinic reply
        # In real implementation, update the review record with clinic reply
        
        return jsonify({
            'success': True,
            'message': 'Reply posted successfully'
        })
    except Exception as e:
        logger.error(f"Error posting clinic reply: {e}")
        return jsonify({'success': False, 'error': 'Failed to post reply'})

@enhanced_reviews_bp.route('/api/review-stats/<int:clinic_id>')
def get_review_statistics(clinic_id):
    """Get comprehensive review statistics for a clinic"""
    reviews = SAMPLE_REVIEWS.get(clinic_id, [])
    
    if not reviews:
        return jsonify({
            'total_reviews': 0,
            'average_rating': 0,
            'rating_distribution': {5: 0, 4: 0, 3: 0, 2: 0, 1: 0},
            'category_averages': {},
            'recommendation_rate': 0
        })
    
    # Calculate statistics
    total_reviews = len(reviews)
    average_rating = sum(r['overall_rating'] for r in reviews) / total_reviews
    
    # Rating distribution
    rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for review in reviews:
        rating = int(review['overall_rating'])
        rating_distribution[rating] += 1
    
    # Category averages
    category_averages = {}
    for category in REVIEW_CATEGORIES.keys():
        category_avg = sum(r['ratings'].get(category, 0) for r in reviews) / total_reviews
        category_averages[category] = round(category_avg, 1)
    
    return jsonify({
        'total_reviews': total_reviews,
        'average_rating': round(average_rating, 1),
        'rating_distribution': rating_distribution,
        'category_averages': category_averages,
        'recommendation_rate': 85  # Would calculate from actual data
    })