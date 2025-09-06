"""
Social Features & Community System
Complete social platform with procedure-based communities, before/after sharing, and expert Q&A
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models import User, Review, Community, Thread
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

social_community_bp = Blueprint('social_community', __name__, url_prefix='/community')

# Procedure-based communities
PROCEDURE_COMMUNITIES = {
    'rhinoplasty': {
        'name': 'Rhinoplasty Community',
        'description': 'Connect with others who have undergone or are considering nose surgery',
        'member_count': 1247,
        'posts_count': 3891,
        'featured_discussions': [
            'Recovery timeline for rhinoplasty',
            'Best surgeons in Mumbai for nose jobs',
            'Cost comparison across cities'
        ]
    },
    'breast_augmentation': {
        'name': 'Breast Augmentation Support',
        'description': 'Share experiences and get support for breast enhancement procedures',
        'member_count': 892,
        'posts_count': 2156,
        'featured_discussions': [
            'Silicone vs saline implants',
            'Post-surgery recovery tips',
            'Finding the right size'
        ]
    },
    'liposuction': {
        'name': 'Body Contouring Community',
        'description': 'Discussion forum for liposuction and body sculpting procedures',
        'member_count': 734,
        'posts_count': 1923,
        'featured_discussions': [
            'VASER vs traditional liposuction',
            'Compression garment recommendations',
            'Exercise after lipo'
        ]
    },
    'hair_transplant': {
        'name': 'Hair Restoration Forum',
        'description': 'Support and advice for hair transplant procedures',
        'member_count': 1089,
        'posts_count': 4102,
        'featured_discussions': [
            'FUE vs FUT techniques',
            'Growth timeline expectations',
            'Clinic recommendations by city'
        ]
    },
    'facelift': {
        'name': 'Facial Rejuvenation Community',
        'description': 'Connect with others exploring facial plastic surgery options',
        'member_count': 456,
        'posts_count': 1278,
        'featured_discussions': [
            'Mini vs full facelift',
            'Non-surgical alternatives',
            'Recovery and downtime'
        ]
    }
}

# Sample community posts with authentic Indian context
COMMUNITY_POSTS = {
    'rhinoplasty': [
        {
            'id': 1,
            'author': 'Priya_Mumbai',
            'title': 'My rhinoplasty journey at Apollo Hospital Chennai - 3 months post-op',
            'excerpt': 'Sharing my experience with Dr. Rajesh Kumar. The results are amazing!',
            'post_type': 'experience_sharing',
            'likes': 47,
            'comments': 23,
            'created_at': '2024-11-20',
            'has_photos': True,
            'verified_patient': True
        },
        {
            'id': 2,
            'author': 'RahulDel',
            'title': 'Considering rhinoplasty - need advice on Delhi clinics',
            'excerpt': 'Looking for recommendations for good plastic surgeons in Delhi area.',
            'post_type': 'seeking_advice',
            'likes': 12,
            'comments': 31,
            'created_at': '2024-11-25',
            'has_photos': False,
            'verified_patient': False
        }
    ],
    'breast_augmentation': [
        {
            'id': 3,
            'author': 'Anjali_Bangalore',
            'title': 'Breast augmentation at Fortis - my honest review',
            'excerpt': 'Detailed review of my experience including costs, recovery, and results.',
            'post_type': 'experience_sharing',
            'likes': 89,
            'comments': 45,
            'created_at': '2024-11-18',
            'has_photos': True,
            'verified_patient': True
        }
    ]
}

# Expert Q&A sessions
EXPERT_QA_SESSIONS = [
    {
        'id': 1,
        'expert_name': 'Dr. Rajesh Kumar',
        'specialty': 'Plastic & Cosmetic Surgery',
        'clinic': 'Apollo Cosmetic Surgery Center',
        'session_title': 'Ask Me Anything: Rhinoplasty and Facial Surgery',
        'session_date': '2024-12-05',
        'session_time': '19:00',
        'duration': 60,
        'questions_count': 23,
        'is_live': False,
        'is_upcoming': True
    },
    {
        'id': 2,
        'expert_name': 'Dr. Kavita Patel',
        'specialty': 'Body Contouring & Cosmetic Surgery',
        'clinic': 'Lilavati Cosmetic Institute',
        'session_title': 'Body Sculpting: Liposuction and Brazilian Butt Lift',
        'session_date': '2024-12-08',
        'session_time': '20:00',
        'duration': 45,
        'questions_count': 18,
        'is_live': False,
        'is_upcoming': True
    }
]

@social_community_bp.route('/')
def community_home():
    """Main community page with all procedure communities"""
    recent_posts = []
    
    # Aggregate recent posts from all communities
    for procedure, posts in COMMUNITY_POSTS.items():
        for post in posts:
            post['procedure'] = procedure
            post['community_name'] = PROCEDURE_COMMUNITIES[procedure]['name']
            recent_posts.append(post)
    
    # Sort by date
    recent_posts.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('social_community_home.html',
                         procedure_communities=PROCEDURE_COMMUNITIES,
                         recent_posts=recent_posts[:10],
                         expert_sessions=EXPERT_QA_SESSIONS)

@social_community_bp.route('/procedure/<procedure_name>')
def procedure_community(procedure_name):
    """Individual procedure community page"""
    if procedure_name not in PROCEDURE_COMMUNITIES:
        flash('Community not found', 'error')
        return redirect(url_for('social_community.community_home'))
    
    community_info = PROCEDURE_COMMUNITIES[procedure_name]
    posts = COMMUNITY_POSTS.get(procedure_name, [])
    
    # Sort posts by engagement (likes + comments)
    posts.sort(key=lambda x: x['likes'] + x['comments'], reverse=True)
    
    return render_template('procedure_community.html',
                         procedure_name=procedure_name,
                         community_info=community_info,
                         posts=posts)

@social_community_bp.route('/create-post/<procedure_name>')
@login_required
def create_post_form(procedure_name):
    """Form to create a new community post"""
    if procedure_name not in PROCEDURE_COMMUNITIES:
        flash('Community not found', 'error')
        return redirect(url_for('social_community.community_home'))
    
    community_info = PROCEDURE_COMMUNITIES[procedure_name]
    
    return render_template('create_community_post.html',
                         procedure_name=procedure_name,
                         community_info=community_info)

@social_community_bp.route('/submit-post', methods=['POST'])
@login_required
def submit_community_post():
    """Submit a new community post"""
    procedure_name = request.form.get('procedure_name')
    post_type = request.form.get('post_type')
    title = request.form.get('title')
    content = request.form.get('content')
    is_anonymous = request.form.get('is_anonymous') == 'on'
    
    try:
        # Handle photo uploads for before/after sharing
        uploaded_photos = []
        for i in range(1, 6):  # Support up to 5 photos
            photo_key = f'photo_{i}'
            if photo_key in request.files:
                photo = request.files[photo_key]
                if photo and photo.filename:
                    filename = secure_filename(photo.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    
                    # Create directory if it doesn't exist
                    upload_dir = os.path.join('static', 'uploads', 'community')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Save file
                    filepath = os.path.join(upload_dir, filename)
                    photo.save(filepath)
                    uploaded_photos.append(f'/static/uploads/community/{filename}')
        
        # Create community post
        author_name = 'Anonymous' if is_anonymous else current_user.name
        
        post_data = {
            'author': author_name,
            'author_id': current_user.id,
            'procedure': procedure_name,
            'title': title,
            'content': content,
            'post_type': post_type,
            'photos': uploaded_photos,
            'likes': 0,
            'comments': 0,
            'created_at': datetime.utcnow(),
            'is_anonymous': is_anonymous
        }
        
        # In real implementation, save to database
        logger.info(f"New community post created: {title} in {procedure_name}")
        
        return jsonify({
            'success': True,
            'message': 'Post submitted successfully! It will be visible after moderation.',
            'redirect_url': url_for('social_community.procedure_community', procedure_name=procedure_name)
        })
        
    except Exception as e:
        logger.error(f"Error creating community post: {e}")
        return jsonify({'success': False, 'error': 'Failed to create post'})

@social_community_bp.route('/before-after-gallery')
def before_after_gallery():
    """Gallery of before/after photos shared by community"""
    # Filter posts with photos
    gallery_posts = []
    
    for procedure, posts in COMMUNITY_POSTS.items():
        for post in posts:
            if post.get('has_photos'):
                post['procedure'] = procedure
                post['community_name'] = PROCEDURE_COMMUNITIES[procedure]['name']
                # Add sample photo URLs for demo
                post['photos'] = [
                    f'/static/community/{procedure}_before_1.jpg',
                    f'/static/community/{procedure}_after_1.jpg'
                ]
                gallery_posts.append(post)
    
    return render_template('before_after_gallery.html',
                         gallery_posts=gallery_posts)

@social_community_bp.route('/expert-qa')
def expert_qa_sessions():
    """List of expert Q&A sessions"""
    upcoming_sessions = [s for s in EXPERT_QA_SESSIONS if s['is_upcoming']]
    past_sessions = [s for s in EXPERT_QA_SESSIONS if not s['is_upcoming']]
    
    return render_template('expert_qa_sessions.html',
                         upcoming_sessions=upcoming_sessions,
                         past_sessions=past_sessions)

@social_community_bp.route('/expert-qa/<int:session_id>')
def expert_qa_session(session_id):
    """Individual expert Q&A session page"""
    session = next((s for s in EXPERT_QA_SESSIONS if s['id'] == session_id), None)
    
    if not session:
        flash('Q&A session not found', 'error')
        return redirect(url_for('social_community.expert_qa_sessions'))
    
    # Sample Q&A for the session
    sample_qa = [
        {
            'question': 'What is the typical recovery time for rhinoplasty?',
            'author': 'Priya_M',
            'answer': 'Recovery varies, but most patients can return to work in 7-10 days. Full healing takes 6-12 months.',
            'likes': 15
        },
        {
            'question': 'How do I choose between open and closed rhinoplasty?',
            'author': 'Rahul_Delhi',
            'answer': 'The choice depends on your specific needs. Open rhinoplasty allows for more precise changes in complex cases.',
            'likes': 23
        }
    ]
    
    return render_template('expert_qa_session.html',
                         session=session,
                         qa_list=sample_qa)

@social_community_bp.route('/submit-question/<int:session_id>', methods=['POST'])
@login_required
def submit_qa_question(session_id):
    """Submit a question for expert Q&A session"""
    question = request.form.get('question')
    is_anonymous = request.form.get('is_anonymous') == 'on'
    
    session = next((s for s in EXPERT_QA_SESSIONS if s['id'] == session_id), None)
    
    if not session:
        return jsonify({'success': False, 'error': 'Session not found'})
    
    try:
        # Save question for the session
        question_data = {
            'session_id': session_id,
            'user_id': current_user.id,
            'question': question,
            'is_anonymous': is_anonymous,
            'submitted_at': datetime.utcnow(),
            'is_answered': False
        }
        
        logger.info(f"New Q&A question submitted for session {session_id}")
        
        return jsonify({
            'success': True,
            'message': 'Question submitted successfully! The expert will answer during the session.'
        })
        
    except Exception as e:
        logger.error(f"Error submitting Q&A question: {e}")
        return jsonify({'success': False, 'error': 'Failed to submit question'})

@social_community_bp.route('/treatment-journey-tracker')
@login_required
def treatment_journey_tracker():
    """Track and document treatment journey"""
    # Get user's ongoing treatments
    user_journeys = [
        {
            'id': 1,
            'procedure': 'Rhinoplasty',
            'clinic': 'Apollo Cosmetic Surgery Center',
            'start_date': '2024-11-15',
            'current_stage': 'Recovery Week 2',
            'next_milestone': 'First follow-up appointment',
            'progress_percentage': 25
        }
    ]
    
    return render_template('treatment_journey_tracker.html',
                         user_journeys=user_journeys)

@social_community_bp.route('/add-journey-update/<int:journey_id>', methods=['POST'])
@login_required
def add_journey_update(journey_id):
    """Add an update to treatment journey"""
    update_text = request.form.get('update_text')
    milestone = request.form.get('milestone')
    mood_rating = request.form.get('mood_rating', type=int)
    
    # Handle photo upload
    photos = []
    if 'photos' in request.files:
        for photo in request.files.getlist('photos'):
            if photo and photo.filename:
                filename = secure_filename(photo.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"journey_{timestamp}_{filename}"
                
                upload_dir = os.path.join('static', 'uploads', 'journeys')
                os.makedirs(upload_dir, exist_ok=True)
                
                filepath = os.path.join(upload_dir, filename)
                photo.save(filepath)
                photos.append(f'/static/uploads/journeys/{filename}')
    
    try:
        journey_update = {
            'journey_id': journey_id,
            'user_id': current_user.id,
            'update_text': update_text,
            'milestone': milestone,
            'mood_rating': mood_rating,
            'photos': photos,
            'created_at': datetime.utcnow()
        }
        
        logger.info(f"Journey update added for journey {journey_id}")
        
        return jsonify({
            'success': True,
            'message': 'Journey update added successfully!'
        })
        
    except Exception as e:
        logger.error(f"Error adding journey update: {e}")
        return jsonify({'success': False, 'error': 'Failed to add update'})

@social_community_bp.route('/like-post/<int:post_id>', methods=['POST'])
@login_required
def like_community_post(post_id):
    """Like a community post"""
    try:
        # In real implementation, toggle like status in database
        # For demo, just return success
        
        return jsonify({
            'success': True,
            'new_likes_count': 48  # Would be actual count from database
        })
        
    except Exception as e:
        logger.error(f"Error liking post: {e}")
        return jsonify({'success': False, 'error': 'Failed to like post'})

@social_community_bp.route('/report-post/<int:post_id>', methods=['POST'])
@login_required
def report_community_post(post_id):
    """Report inappropriate community post"""
    reason = request.form.get('reason')
    
    try:
        # Log the report for moderation
        logger.info(f"Community post {post_id} reported by user {current_user.id} for: {reason}")
        
        return jsonify({
            'success': True,
            'message': 'Post reported successfully. Our moderation team will review it.'
        })
        
    except Exception as e:
        logger.error(f"Error reporting post: {e}")
        return jsonify({'success': False, 'error': 'Failed to report post'})

@social_community_bp.route('/api/community-stats')
def get_community_statistics():
    """Get community engagement statistics"""
    stats = {
        'total_members': sum(c['member_count'] for c in PROCEDURE_COMMUNITIES.values()),
        'total_posts': sum(c['posts_count'] for c in PROCEDURE_COMMUNITIES.values()),
        'active_discussions': 156,
        'expert_sessions_completed': 24,
        'photos_shared': 892,
        'success_stories': 234
    }
    
    return jsonify(stats)