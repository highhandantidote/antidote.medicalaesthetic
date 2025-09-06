"""
Enhanced Community Blueprint - Modern Medical Community Platform
Comprehensive community features with voting, reactions, nested replies, and more.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from sqlalchemy import desc, asc, func, text, and_, or_
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import uuid
import logging
from models import (
    db, Community, CommunityReply, User, Category, Procedure, 
    ThreadVote, ReplyVote, ThreadSave, ThreadFollow, ThreadReaction,
    UserBadge, UserReputation, UserProfile, Message, Notification
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
community_bp = Blueprint('community_enhanced', __name__, url_prefix='/community')

# Configuration
UPLOAD_FOLDER = 'static/uploads/community'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user():
    """Get current user from session."""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def calculate_trending_score(thread):
    """Calculate trending score based on engagement metrics."""
    now = datetime.utcnow()
    hours_since_creation = (now - thread.created_at).total_seconds() / 3600
    
    # Prevent division by zero
    if hours_since_creation < 1:
        hours_since_creation = 1
    
    # Score based on votes, views, replies with time decay (handle NULL values)
    upvotes = thread.upvotes or 0
    downvotes = thread.downvotes or 0
    view_count = thread.view_count or 0
    reply_count = thread.reply_count or 0
    
    score = (
        (upvotes * 2 - downvotes) + 
        (view_count * 0.1) + 
        (reply_count * 3)
    ) / (hours_since_creation ** 0.8)
    
    return max(0, score)

def award_reputation(user_id, action_type, points, reason=None):
    """Award reputation points to user."""
    try:
        reputation = UserReputation(
            user_id=user_id,
            action_type=action_type,
            points=points,
            reason=reason
        )
        db.session.add(reputation)
        
        # Update user's total reputation
        user = User.query.get(user_id)
        if user:
            user.points = (user.points or 0) + points
        
        db.session.commit()
        logger.info(f"Awarded {points} reputation to user {user_id} for {action_type}")
    except Exception as e:
        logger.error(f"Error awarding reputation: {e}")
        db.session.rollback()

@community_bp.route('/')
def index():
    """Enhanced community index with modern features."""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 15
        
        # Get filter parameters
        category_id = request.args.get('category_id', type=int)
        sort_by = request.args.get('sort', 'trending')
        search_query = request.args.get('search', '')
        filter_type = request.args.get('filter', 'all')  # all, saved, following
        
        # Base query with eager loading
        query = Community.query.options(
            joinedload(Community.user),
            joinedload(Community.category),
            joinedload(Community.procedure),
            joinedload(Community.votes),
            joinedload(Community.reactions)
        ).filter(Community.is_deleted == False)
        
        # Apply filters
        if category_id:
            query = query.filter(Community.category_id == category_id)
        
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                or_(
                    Community.title.ilike(search_term),
                    Community.content.ilike(search_term),
                    Community.tags.any(text(f"'{search_query}' = ANY(community.tags)"))
                )
            )
        
        # User-specific filters
        current_user = get_current_user()
        if current_user and filter_type == 'saved':
            saved_thread_ids = [s.thread_id for s in ThreadSave.query.filter_by(user_id=current_user.id).all()]
            query = query.filter(Community.id.in_(saved_thread_ids))
        elif current_user and filter_type == 'following':
            followed_thread_ids = [f.thread_id for f in ThreadFollow.query.filter_by(user_id=current_user.id).all()]
            query = query.filter(Community.id.in_(followed_thread_ids))
        
        # Apply sorting
        if sort_by == 'trending':
            query = query.order_by(desc(Community.upvotes), desc(Community.created_at))
        elif sort_by == 'newest':
            query = query.order_by(desc(Community.created_at))
        elif sort_by == 'oldest':
            query = query.order_by(asc(Community.created_at))
        elif sort_by == 'most_voted':
            query = query.order_by(desc(Community.upvotes), desc(Community.created_at))
        elif sort_by == 'most_replies':
            query = query.order_by(desc(Community.reply_count), desc(Community.created_at))
        
        # Paginate results
        threads_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get categories and procedures for filters
        categories = Category.query.order_by(Category.name).all()
        procedures = Procedure.query.order_by(Procedure.procedure_name).limit(50).all()
        
        # Get user's saved and followed threads if logged in
        user_saves = set()
        user_follows = set()
        if current_user:
            user_saves = {s.thread_id for s in ThreadSave.query.filter_by(user_id=current_user.id).all()}
            user_follows = {f.thread_id for f in ThreadFollow.query.filter_by(user_id=current_user.id).all()}
        
        # Get trending topics (simplified for now)
        trending_tags = []
        
        # Get all threads for display
        all_threads = Community.query.order_by(desc(Community.created_at)).all()
        
        return render_template('community_enhanced/index.html',
                             threads=all_threads,
                             pagination=threads_pagination,
                             categories=categories,
                             procedures=procedures,
                             current_sort=sort_by,
                             current_category=category_id,
                             search_query=search_query,
                             filter_type=filter_type,
                             user_saves=user_saves,
                             user_follows=user_follows,
                             trending_tags=trending_tags,
                             current_user=current_user)
                             
    except Exception as e:
        logger.error(f"Error in community index: {e}")
        flash('Error loading community discussions.', 'error')
        return render_template('community_enhanced/index.html',
                             threads=[],
                             pagination=None,
                             categories=[],
                             procedures=[])

@community_bp.route('/create', methods=['GET', 'POST'])
def create_thread():
    """Create new thread with rich content support."""
    current_user = get_current_user()
    if not current_user:
        flash('Please log in to create a discussion.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            category_id = request.form.get('category_id', type=int)
            procedure_id = request.form.get('procedure_id', type=int)
            is_anonymous = request.form.get('is_anonymous') == 'on'
            tags = request.form.get('tags', '').split(',')
            tags = [tag.strip() for tag in tags if tag.strip()]
            
            # Validation
            if not title or not content:
                flash('Title and content are required.', 'error')
                return redirect(url_for('community_enhanced.create_thread'))
            
            if len(title) > 200:
                flash('Title must be less than 200 characters.', 'error')
                return redirect(url_for('community_enhanced.create_thread'))
            
            # Handle file uploads
            photo_url = None
            video_url = None
            
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                    
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    photo_url = f"/static/uploads/community/{unique_filename}"
            
            # Create thread
            thread = Community(
                user_id=current_user.id,
                title=title,
                content=content,
                category_id=category_id if category_id else None,
                procedure_id=procedure_id if procedure_id else None,
                is_anonymous=is_anonymous,
                tags=tags,
                photo_url=photo_url,
                video_url=video_url,
                content_type='image' if photo_url else 'text'
            )
            
            db.session.add(thread)
            db.session.commit()
            
            # Award reputation for creating thread
            award_reputation(current_user.id, 'thread_created', 5, 'Created new discussion thread')
            
            # Auto-follow thread for creator
            follow = ThreadFollow(user_id=current_user.id, thread_id=thread.id)
            db.session.add(follow)
            db.session.commit()
            
            flash('Discussion created successfully!', 'success')
            return redirect(url_for('community_enhanced.view_thread', thread_id=thread.id))
            
        except Exception as e:
            logger.error(f"Error creating thread: {e}")
            db.session.rollback()
            flash('Error creating discussion. Please try again.', 'error')
    
    # GET request - show form
    categories = Category.query.order_by(Category.name).all()
    procedures = Procedure.query.order_by(Procedure.procedure_name).limit(100).all()
    
    return render_template('community_enhanced/create_thread.html',
                         categories=categories,
                         procedures=procedures)

@community_bp.route('/thread/<int:thread_id>')
def view_thread(thread_id):
    """View thread with nested replies and interactions."""
    try:
        # Get thread with related data
        thread = Community.query.options(
            joinedload(Community.user),
            joinedload(Community.category),
            joinedload(Community.procedure)
        ).filter_by(id=thread_id, is_deleted=False).first_or_404()
        
        # Increment view count
        thread.view_count = (thread.view_count or 0) + 1
        db.session.commit()
        
        # Get nested replies with user data
        replies = CommunityReply.query.options(
            joinedload(CommunityReply.user),
            joinedload(CommunityReply.parent_reply)
        ).filter_by(thread_id=thread_id).order_by(CommunityReply.created_at).all()
        
        # Organize replies into nested structure
        reply_tree = {}
        root_replies = []
        
        for reply in replies:
            reply_tree[reply.id] = {
                'reply': reply,
                'children': []
            }
        
        for reply in replies:
            if reply.parent_reply_id:
                if reply.parent_reply_id in reply_tree:
                    reply_tree[reply.parent_reply_id]['children'].append(reply_tree[reply.id])
            else:
                root_replies.append(reply_tree[reply.id])
        
        # Get current user interactions
        current_user = get_current_user()
        user_vote = None
        user_saved = False
        user_following = False
        user_reactions = {}
        
        if current_user:
            # Get user's vote on this thread
            vote = ThreadVote.query.filter_by(
                user_id=current_user.id, 
                thread_id=thread_id
            ).first()
            user_vote = vote.vote_type if vote else None
            
            # Check if user saved this thread
            save = ThreadSave.query.filter_by(
                user_id=current_user.id, 
                thread_id=thread_id
            ).first()
            user_saved = bool(save)
            
            # Check if user is following this thread
            follow = ThreadFollow.query.filter_by(
                user_id=current_user.id, 
                thread_id=thread_id
            ).first()
            user_following = bool(follow)
            
            # Get user's reactions
            reactions = ThreadReaction.query.filter_by(
                user_id=current_user.id, 
                thread_id=thread_id
            ).all()
            user_reactions = {r.reaction_type: True for r in reactions}
        
        # Get reaction counts
        reaction_counts = {}
        reactions = ThreadReaction.query.filter_by(thread_id=thread_id).all()
        for reaction in reactions:
            reaction_counts[reaction.reaction_type] = reaction_counts.get(reaction.reaction_type, 0) + 1
        
        # Get similar threads
        similar_threads = []
        if thread.category_id or thread.procedure_id:
            similar_query = Community.query.filter(
                Community.id != thread_id,
                Community.is_deleted == False
            )
            
            if thread.category_id:
                similar_query = similar_query.filter(Community.category_id == thread.category_id)
            if thread.procedure_id:
                similar_query = similar_query.filter(Community.procedure_id == thread.procedure_id)
                
            similar_threads = similar_query.order_by(
                desc(Community.upvotes), 
                desc(Community.created_at)
            ).limit(5).all()
        
        return render_template('community_enhanced/thread_detail.html',
                             thread=thread,
                             replies=root_replies,
                             user_vote=user_vote,
                             user_saved=user_saved,
                             user_following=user_following,
                             user_reactions=user_reactions,
                             reaction_counts=reaction_counts,
                             similar_threads=similar_threads,
                             current_user=current_user)
                             
    except Exception as e:
        logger.error(f"Error viewing thread {thread_id}: {e}")
        flash('Error loading discussion.', 'error')
        return redirect(url_for('community_enhanced.index'))

@community_bp.route('/api/vote', methods=['POST'])
def vote_thread():
    """Vote on a thread (upvote/downvote)."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': 'Please log in to vote.'})
    
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        vote_type = data.get('vote_type')  # 'upvote' or 'downvote'
        
        if not thread_id or vote_type not in ['upvote', 'downvote']:
            return jsonify({'success': False, 'message': 'Invalid vote data.'})
        
        thread = Community.query.get_or_404(thread_id)
        
        # Check existing vote
        existing_vote = ThreadVote.query.filter_by(
            user_id=current_user.id,
            thread_id=thread_id
        ).first()
        
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Remove vote if clicking same button
                db.session.delete(existing_vote)
                
                # Update thread counts
                if vote_type == 'upvote':
                    thread.upvotes = max(0, (thread.upvotes or 0) - 1)
                else:
                    thread.downvotes = max(0, (thread.downvotes or 0) - 1)
                
                vote_type = None  # User removed their vote
            else:
                # Change vote type
                old_vote = existing_vote.vote_type
                existing_vote.vote_type = vote_type
                
                # Update counts
                if old_vote == 'upvote':
                    thread.upvotes = max(0, (thread.upvotes or 0) - 1)
                    thread.downvotes = (thread.downvotes or 0) + 1
                else:
                    thread.downvotes = max(0, (thread.downvotes or 0) - 1)
                    thread.upvotes = (thread.upvotes or 0) + 1
        else:
            # Create new vote
            new_vote = ThreadVote(
                user_id=current_user.id,
                thread_id=thread_id,
                vote_type=vote_type
            )
            db.session.add(new_vote)
            
            # Update thread counts
            if vote_type == 'upvote':
                thread.upvotes = (thread.upvotes or 0) + 1
                # Award reputation to thread author
                if thread.user_id != current_user.id:
                    award_reputation(thread.user_id, 'thread_upvote', 2, 'Thread received upvote')
            else:
                thread.downvotes = (thread.downvotes or 0) + 1
        
        # Update total votes
        thread.total_votes = (thread.upvotes or 0) - (thread.downvotes or 0)
        
        # Update trending score
        thread.trending_score = calculate_trending_score(thread)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'upvotes': thread.upvotes or 0,
            'downvotes': thread.downvotes or 0,
            'total_votes': thread.total_votes or 0,
            'user_vote': vote_type
        })
        
    except Exception as e:
        logger.error(f"Error voting on thread: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error processing vote.'})

@community_bp.route('/api/save', methods=['POST'])
def save_thread():
    """Save/unsave a thread."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': 'Please log in to save threads.'})
    
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        
        if not thread_id:
            return jsonify({'success': False, 'message': 'Invalid thread ID.'})
        
        thread = Community.query.get_or_404(thread_id)
        
        # Check existing save
        existing_save = ThreadSave.query.filter_by(
            user_id=current_user.id,
            thread_id=thread_id
        ).first()
        
        if existing_save:
            # Remove save
            db.session.delete(existing_save)
            saved = False
            message = 'Thread removed from saved list.'
        else:
            # Add save
            new_save = ThreadSave(
                user_id=current_user.id,
                thread_id=thread_id
            )
            db.session.add(new_save)
            saved = True
            message = 'Thread saved successfully.'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'saved': saved,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error saving thread: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error saving thread.'})

@community_bp.route('/api/follow', methods=['POST'])
def follow_thread():
    """Follow/unfollow a thread for notifications."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': 'Please log in to follow threads.'})
    
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        
        if not thread_id:
            return jsonify({'success': False, 'message': 'Invalid thread ID.'})
        
        thread = Community.query.get_or_404(thread_id)
        
        # Check existing follow
        existing_follow = ThreadFollow.query.filter_by(
            user_id=current_user.id,
            thread_id=thread_id
        ).first()
        
        if existing_follow:
            # Unfollow
            db.session.delete(existing_follow)
            following = False
            message = 'Stopped following thread.'
        else:
            # Follow
            new_follow = ThreadFollow(
                user_id=current_user.id,
                thread_id=thread_id
            )
            db.session.add(new_follow)
            following = True
            message = 'Now following thread.'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'following': following,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error following thread: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error following thread.'})

@community_bp.route('/api/react', methods=['POST'])
def react_to_thread():
    """Add/remove emoji reaction to thread."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': 'Please log in to react.'})
    
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        reaction_type = data.get('reaction_type')
        
        if not thread_id or not reaction_type:
            return jsonify({'success': False, 'message': 'Invalid reaction data.'})
        
        # Validate reaction type
        allowed_reactions = ['heart', 'thumbs_up', 'clap', 'thinking', 'surprised', 'laugh']
        if reaction_type not in allowed_reactions:
            return jsonify({'success': False, 'message': 'Invalid reaction type.'})
        
        thread = Community.query.get_or_404(thread_id)
        
        # Check existing reaction
        existing_reaction = ThreadReaction.query.filter_by(
            user_id=current_user.id,
            thread_id=thread_id,
            reaction_type=reaction_type
        ).first()
        
        if existing_reaction:
            # Remove reaction
            db.session.delete(existing_reaction)
            reacted = False
        else:
            # Add reaction
            new_reaction = ThreadReaction(
                user_id=current_user.id,
                thread_id=thread_id,
                reaction_type=reaction_type
            )
            db.session.add(new_reaction)
            reacted = True
        
        db.session.commit()
        
        # Get updated reaction count
        reaction_count = ThreadReaction.query.filter_by(
            thread_id=thread_id,
            reaction_type=reaction_type
        ).count()
        
        return jsonify({
            'success': True,
            'reacted': reacted,
            'count': reaction_count
        })
        
    except Exception as e:
        logger.error(f"Error reacting to thread: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error processing reaction.'})

@community_bp.route('/api/reply', methods=['POST'])
def create_reply():
    """Create a reply to a thread or another reply."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'message': 'Please log in to reply.'})
    
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        content = data.get('content', '').strip()
        parent_reply_id = data.get('parent_reply_id')
        is_anonymous = data.get('is_anonymous', False)
        
        if not thread_id or not content:
            return jsonify({'success': False, 'message': 'Thread ID and content are required.'})
        
        thread = Community.query.get_or_404(thread_id)
        
        # Check if user is a doctor
        is_doctor_response = False
        if current_user.role == 'doctor' or hasattr(current_user, 'doctor'):
            is_doctor_response = True
        
        # Create reply
        reply = CommunityReply(
            thread_id=thread_id,
            user_id=current_user.id,
            content=content,
            parent_reply_id=parent_reply_id if parent_reply_id else None,
            is_anonymous=is_anonymous,
            is_doctor_response=is_doctor_response
        )
        
        db.session.add(reply)
        
        # Update thread reply count
        thread.reply_count = (thread.reply_count or 0) + 1
        
        # Update trending score
        thread.trending_score = calculate_trending_score(thread)
        
        # Award reputation
        award_reputation(current_user.id, 'reply_posted', 2, 'Posted helpful reply')
        
        # If it's a doctor response, mark thread as having doctor response
        if is_doctor_response:
            thread.doctor_verified = True
            award_reputation(current_user.id, 'doctor_response', 10, 'Provided expert medical response')
        
        db.session.commit()
        
        # Send notifications to followers
        followers = ThreadFollow.query.filter_by(thread_id=thread_id).all()
        for follower in followers:
            if follower.user_id != current_user.id:  # Don't notify self
                notification = Notification(
                    user_id=follower.user_id,
                    message=f"New reply in thread: {thread.title}",
                    type='thread_reply',
                    response_type='doctor' if is_doctor_response else 'user'
                )
                db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reply posted successfully!',
            'reply_id': reply.id
        })
        
    except Exception as e:
        logger.error(f"Error creating reply: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error posting reply.'})

# Add more API endpoints for user profiles, messaging, etc.