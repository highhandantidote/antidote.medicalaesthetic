"""
Modern Community API Routes - Reddit-style functionality
Enhanced API endpoints for the new community interface
"""

from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy import desc, func, text, or_, and_
from datetime import datetime, timedelta
import json
import logging
from app import db
from models import (
    Community, CommunityReply, User, Doctor, Category, Procedure,
    ThreadVote, ReplyVote, ThreadSave, RedditImport, ProfessionalResponse
)

# Create blueprint
community_modern_api = Blueprint('community_modern_api', __name__, url_prefix='/api/community')

logger = logging.getLogger(__name__)

@community_modern_api.route('/posts', methods=['GET'])
def get_posts():
    """Get community posts with Reddit-style sorting and filtering."""
    try:
        # Get parameters
        sort = request.args.get('sort', 'hot')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        category_filter = request.args.get('category')
        source_filter = request.args.get('source')  # native, reddit, imported
        
        # Base query - only get main posts (not replies)
        query = db.session.query(Community).filter(
            Community.is_deleted == False,
            Community.parent_id.is_(None)  # Only main posts, not replies
        )
        
        # Apply filters
        if category_filter:
            query = query.filter(Community.category_id == category_filter)
        
        if source_filter:
            if source_filter == 'imported':
                query = query.filter(Community.source_type.in_(['reddit', 'imported']))
            elif source_filter == 'professional':
                query = query.filter(Community.is_professional_verified == True)
            else:
                query = query.filter(Community.source_type == source_filter)
        
        # Apply sorting
        if sort == 'hot':
            # Reddit-style hot algorithm: engagement score based on votes and time
            query = query.order_by(desc(Community.engagement_score))
        elif sort == 'new':
            query = query.order_by(desc(Community.created_at))
        elif sort == 'top':
            query = query.order_by(desc(Community.total_votes))
        elif sort == 'imported':
            query = query.filter(Community.source_type.in_(['reddit', 'imported'])).order_by(desc(Community.imported_at))
        elif sort == 'professional':
            query = query.filter(Community.is_professional_verified == True).order_by(desc(Community.created_at))
        
        # Pagination
        offset = (page - 1) * per_page
        posts = query.offset(offset).limit(per_page).all()
        
        # Serialize posts
        posts_data = []
        for post in posts:
            # Get user vote if authenticated
            user_vote = None
            if current_user.is_authenticated:
                vote = ThreadVote.query.filter_by(
                    user_id=current_user.id,
                    thread_id=post.id
                ).first()
                user_vote = vote.vote_type if vote else None
            
            post_data = {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'upvotes': post.upvotes or 0,
                'downvotes': post.downvotes or 0,
                'total_votes': (post.upvotes or 0) - (post.downvotes or 0),
                'reply_count': post.reply_count or 0,
                'view_count': post.view_count or 0,
                'created_at': post.created_at.isoformat() if post.created_at else None,
                'is_anonymous': post.is_anonymous,
                'is_professional_verified': post.is_professional_verified,
                'source_type': post.source_type,
                'source_url': post.source_url,
                'reddit_author': post.reddit_author,
                'user_vote': user_vote,
                'user': {
                    'id': post.user.id if post.user else None,
                    'username': post.user.username if post.user and not post.is_anonymous and post.user.role == 'doctor' else 'Anonymous',
                    'role': post.user.role if post.user and not post.is_anonymous and post.user.role == 'doctor' else None
                },
                'category': {
                    'id': post.category.id,
                    'name': post.category.name
                } if post.category else None,
                'procedure': {
                    'id': post.procedure.id,
                    'name': post.procedure.procedure_name
                } if post.procedure else None,
                'tags': post.tags or [],
                'media_urls': post.media_urls or []
            }
            posts_data.append(post_data)
        
        return jsonify({
            'success': True,
            'posts': posts_data,
            'page': page,
            'per_page': per_page,
            'has_more': len(posts) == per_page
        })
        
    except Exception as e:
        logger.error(f"Error getting posts: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load posts'
        }), 500

@community_modern_api.route('/vote', methods=['POST'])
@login_required
def vote_post():
    """Vote on a community post (Reddit-style upvote/downvote)."""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        vote_type = data.get('vote_type')  # 'upvote' or 'downvote'
        
        if not post_id or vote_type not in ['upvote', 'downvote']:
            return jsonify({
                'success': False,
                'message': 'Invalid vote data'
            }), 400
        
        # Get the post
        post = Community.query.get_or_404(post_id)
        
        # Check if user already voted
        existing_vote = ThreadVote.query.filter_by(
            user_id=current_user.id,
            thread_id=post_id
        ).first()
        
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Remove vote (toggle off)
                db.session.delete(existing_vote)
                
                # Update post vote counts
                if vote_type == 'upvote':
                    post.upvotes = max(0, (post.upvotes or 0) - 1)
                else:
                    post.downvotes = max(0, (post.downvotes or 0) - 1)
                    
                new_vote = None
            else:
                # Change vote type
                existing_vote.vote_type = vote_type
                existing_vote.created_at = datetime.utcnow()
                
                # Update post vote counts
                if vote_type == 'upvote':
                    post.upvotes = (post.upvotes or 0) + 1
                    post.downvotes = max(0, (post.downvotes or 0) - 1)
                else:
                    post.downvotes = (post.downvotes or 0) + 1
                    post.upvotes = max(0, (post.upvotes or 0) - 1)
                    
                new_vote = vote_type
        else:
            # Create new vote
            new_vote = ThreadVote(
                user_id=current_user.id,
                thread_id=post_id,
                vote_type=vote_type
            )
            db.session.add(new_vote)
            
            # Update post vote counts
            if vote_type == 'upvote':
                post.upvotes = (post.upvotes or 0) + 1
            else:
                post.downvotes = (post.downvotes or 0) + 1
                
            new_vote = vote_type
        
        # Update total votes and engagement score
        post.total_votes = (post.upvotes or 0) - (post.downvotes or 0)
        post.engagement_score = calculate_engagement_score(post)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_vote': new_vote,
            'upvotes': post.upvotes or 0,
            'downvotes': post.downvotes or 0,
            'total_votes': post.total_votes
        })
        
    except Exception as e:
        logger.error(f"Error voting on post: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to vote on post'
        }), 500

@community_modern_api.route('/save', methods=['POST'])
@login_required
def save_post():
    """Save/unsave a post for later reading."""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        
        if not post_id:
            return jsonify({
                'success': False,
                'message': 'Post ID required'
            }), 400
        
        # Check if already saved
        existing_save = ThreadSave.query.filter_by(
            user_id=current_user.id,
            thread_id=post_id
        ).first()
        
        if existing_save:
            # Remove save
            db.session.delete(existing_save)
            saved = False
        else:
            # Add save
            save = ThreadSave(
                user_id=current_user.id,
                thread_id=post_id
            )
            db.session.add(save)
            saved = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'saved': saved
        })
        
    except Exception as e:
        logger.error(f"Error saving post: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to save post'
        }), 500

@community_modern_api.route('/trending', methods=['GET'])
def get_trending_topics():
    """Get trending topics and hashtags."""
    try:
        # Get top categories by recent activity
        trending_categories = db.session.query(
            Category.id,
            Category.name,
            func.count(Community.id).label('post_count'),
            func.sum(Community.total_votes).label('total_engagement')
        ).join(Community).filter(
            Community.created_at >= datetime.utcnow() - timedelta(days=7),
            Community.is_deleted == False
        ).group_by(Category.id, Category.name).order_by(
            desc('total_engagement')
        ).limit(10).all()
        
        # Get trending procedures
        trending_procedures = db.session.query(
            Procedure.id,
            Procedure.procedure_name,
            func.count(Community.id).label('post_count')
        ).join(Community).filter(
            Community.created_at >= datetime.utcnow() - timedelta(days=7),
            Community.is_deleted == False
        ).group_by(Procedure.id, Procedure.procedure_name).order_by(
            desc('post_count')
        ).limit(5).all()
        
        trending_data = {
            'categories': [{
                'id': cat.id,
                'name': cat.name,
                'post_count': cat.post_count,
                'engagement': cat.total_engagement or 0
            } for cat in trending_categories],
            'procedures': [{
                'id': proc.id,
                'name': proc.procedure_name,
                'post_count': proc.post_count
            } for proc in trending_procedures]
        }
        
        return jsonify({
            'success': True,
            'trending': trending_data
        })
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load trending topics'
        }), 500

@community_modern_api.route('/experts', methods=['GET'])
def get_featured_experts():
    """Get featured expert doctors and their recent activity."""
    try:
        # Get doctors who have been active in community
        expert_doctors = db.session.query(
            Doctor,
            func.count(Community.id).label('post_count'),
            func.avg(Community.total_votes).label('avg_engagement')
        ).join(User).join(Community, User.id == Community.user_id).filter(
            User.role == 'doctor',
            Community.created_at >= datetime.utcnow() - timedelta(days=30),
            Community.is_deleted == False
        ).group_by(Doctor.id).order_by(
            desc('avg_engagement')
        ).limit(8).all()
        
        experts_data = []
        for doctor, post_count, avg_engagement in expert_doctors:
            experts_data.append({
                'id': doctor.id,
                'name': doctor.name,
                'specialization': doctor.specialization,
                'location': doctor.location,
                'experience_years': doctor.experience_years,
                'post_count': post_count,
                'avg_engagement': float(avg_engagement or 0),
                'profile_url': f'/doctor/{doctor.id}'
            })
        
        return jsonify({
            'success': True,
            'experts': experts_data
        })
        
    except Exception as e:
        logger.error(f"Error getting featured experts: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load featured experts'
        }), 500

def calculate_engagement_score(post):
    """Calculate Reddit-style engagement score for hot sorting."""
    try:
        # Get time since posting (in hours)
        hours_since_post = (datetime.utcnow() - post.created_at).total_seconds() / 3600
        
        # Calculate score based on votes, comments, and time decay
        upvotes = post.upvotes or 0
        downvotes = post.downvotes or 0
        comments = post.reply_count or 0
        
        # Reddit-style scoring
        score = upvotes - downvotes
        order_magnitude = max(abs(score), 1)
        
        # Time decay factor (posts become less "hot" over time)
        time_decay = max(0.1, 1 / (1 + hours_since_post / 6))  # 6-hour half-life
        
        # Include comment engagement
        comment_bonus = comments * 0.5
        
        # Professional verification bonus
        professional_bonus = 2 if post.is_professional_verified else 0
        
        engagement_score = (score + comment_bonus + professional_bonus) * time_decay
        
        return round(engagement_score, 2)
        
    except Exception as e:
        logger.error(f"Error calculating engagement score: {str(e)}")
        return 0.0

# Register the blueprint in routes.py
def register_community_modern_api(app):
    """Register the modern community API routes."""
    app.register_blueprint(community_modern_api)