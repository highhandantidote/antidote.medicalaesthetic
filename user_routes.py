from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import or_, func
from models import (
    User, Community, CommunityReply, Notification, Message
)
from app import db
from datetime import datetime
import logging
import random
import string

# Create logger
logger = logging.getLogger(__name__)

# Create Blueprint for user API routes
user_api = Blueprint('user_api', __name__, url_prefix='/api/users')

@user_api.route('/<username>', methods=['GET'])
def get_user_profile(username):
    """Get user profile data."""
    try:
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get user stats
        thread_count = Community.query.filter_by(user_id=user.id).count()
        reply_count = CommunityReply.query.filter_by(user_id=user.id).count()
        
        # Get total upvotes received on replies
        upvotes = db.session.query(func.sum(CommunityReply.upvotes)) \
            .filter_by(user_id=user.id) \
            .scalar() or 0
        
        return jsonify({
            'success': True,
            'data': {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'role': user.role,
                'role_type': user.role_type,
                'bio': user.bio,
                'badge': user.badge,
                'points': user.points,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'stats': {
                    'thread_count': thread_count,
                    'reply_count': reply_count,
                    'upvotes': upvotes
                }
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching user profile'
        }), 500

@user_api.route('/<username>/posts', methods=['GET'])
def get_user_posts(username):
    """
    Get posts (threads and replies) by a specific user.
    
    Query parameters:
    - type: Type of posts to retrieve (threads, replies, all)
    - sort: Sort order (latest, popular)
    - page: Page number for pagination
    - limit: Number of results per page
    """
    try:
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get query parameters
        post_type = request.args.get('type', 'all')
        sort = request.args.get('sort', 'latest')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        threads = []
        replies = []
        total = 0
        
        # Get threads if requested
        if post_type in ['threads', 'all']:
            thread_query = Community.query.filter_by(user_id=user.id)
            
            if sort == 'latest':
                thread_query = thread_query.order_by(Community.created_at.desc())
            elif sort == 'popular':
                thread_query = thread_query.order_by(Community.view_count.desc())
                
            if post_type == 'all':
                thread_offset = 0
                thread_limit = limit // 2
            else:
                thread_offset = (page - 1) * limit
                thread_limit = limit
                
            user_threads = thread_query.offset(thread_offset).limit(thread_limit).all()
            
            for thread in user_threads:
                threads.append({
                    'id': thread.id,
                    'title': thread.title,
                    'content': thread.content,
                    'type': 'thread',
                    'created_at': thread.created_at.isoformat() if thread.created_at else None,
                    'view_count': thread.view_count,
                    'reply_count': thread.reply_count,
                    'category': {
                        'id': thread.category.id,
                        'name': thread.category.name
                    } if thread.category else None
                })
        
        # Get replies if requested
        if post_type in ['replies', 'all']:
            reply_query = CommunityReply.query.filter_by(user_id=user.id)
            
            if sort == 'latest':
                reply_query = reply_query.order_by(CommunityReply.created_at.desc())
            elif sort == 'popular':
                reply_query = reply_query.order_by(CommunityReply.upvotes.desc())
                
            if post_type == 'all':
                reply_offset = 0
                reply_limit = limit // 2
            else:
                reply_offset = (page - 1) * limit
                reply_limit = limit
                
            user_replies = reply_query.offset(reply_offset).limit(reply_limit).all()
            
            for reply in user_replies:
                thread = Community.query.get(reply.thread_id)
                replies.append({
                    'id': reply.id,
                    'content': reply.content,
                    'type': 'reply',
                    'created_at': reply.created_at.isoformat() if reply.created_at else None,
                    'upvotes': reply.upvotes,
                    'thread': {
                        'id': thread.id,
                        'title': thread.title
                    } if thread else None
                })
        
        # Combine and sort if both types requested
        if post_type == 'all':
            posts = threads + replies
            # Sort combined results by created_at
            posts.sort(key=lambda x: x['created_at'], reverse=(sort == 'latest'))
            # Count total for pagination
            thread_count = Community.query.filter_by(user_id=user.id).count()
            reply_count = CommunityReply.query.filter_by(user_id=user.id).count()
            total = thread_count + reply_count
        elif post_type == 'threads':
            posts = threads
            total = Community.query.filter_by(user_id=user.id).count()
        else:
            posts = replies
            total = CommunityReply.query.filter_by(user_id=user.id).count()
        
        return jsonify({
            'success': True,
            'data': {
                'posts': posts,
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': (total + limit - 1) // limit
                }
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting user posts: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching user posts'
        }), 500

@user_api.route('/check-username', methods=['POST'])
def check_username():
    """Check if a username is available."""
    try:
        data = request.json
        
        if not data or 'username' not in data:
            return jsonify({
                'success': False,
                'message': 'Username is required'
            }), 400
        
        username = data['username']
        
        # Check username format (alphanumeric, underscore, minimum 3 chars)
        if not username or not username.replace('_', '').isalnum() or len(username) < 3:
            return jsonify({
                'success': False,
                'available': False,
                'message': 'Username must be at least 3 characters and contain only letters, numbers, and underscores'
            }), 400
        
        # Check if username exists
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            return jsonify({
                'success': True,
                'available': False,
                'message': 'Username is already taken'
            }), 200
        else:
            return jsonify({
                'success': True,
                'available': True,
                'message': 'Username is available'
            }), 200
    except Exception as e:
        logger.error(f"Error checking username: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while checking username availability'
        }), 500

@user_api.route('/signup', methods=['POST'])
def signup():
    """Update user with username during signup."""
    try:
        data = request.json
        required_fields = ['user_id', 'username']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        user = User.query.get(data['user_id'])
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Check username format
        username = data['username']
        if not username or not username.replace('_', '').isalnum() or len(username) < 3:
            return jsonify({
                'success': False,
                'message': 'Username must be at least 3 characters and contain only letters, numbers, and underscores'
            }), 400
        
        # Check if username exists
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user and existing_user.id != user.id:
            return jsonify({
                'success': False,
                'message': 'Username is already taken'
            }), 409
        
        # Update user with username and other details
        user.username = username
        
        if 'bio' in data:
            user.bio = data['bio']
        
        if 'role_type' in data:
            # Validate role_type
            valid_role_types = ['user', 'doctor', 'expert']
            if data['role_type'] in valid_role_types:
                user.role_type = data['role_type']
            else:
                return jsonify({
                    'success': False,
                    'message': f'Invalid role_type: {data["role_type"]}'
                }), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': user.id,
                'username': user.username,
                'message': 'User updated successfully'
            }
        }), 200
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating user'
        }), 500

@user_api.route('/update-profile', methods=['POST'])
def update_profile():
    """Update user profile information."""
    try:
        data = request.json
        
        if not data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
        
        user = User.query.get(data['user_id'])
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Update user with provided fields
        if 'bio' in data:
            user.bio = data['bio']
        
        if 'username' in data:
            # Check username format
            username = data['username']
            if not username or not username.replace('_', '').isalnum() or len(username) < 3:
                return jsonify({
                    'success': False,
                    'message': 'Username must be at least 3 characters and contain only letters, numbers, and underscores'
                }), 400
            
            # Check if username exists
            existing_user = User.query.filter_by(username=username).first()
            
            if existing_user and existing_user.id != user.id:
                return jsonify({
                    'success': False,
                    'message': 'Username is already taken'
                }), 409
                
            user.username = username
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': user.id,
                'username': user.username,
                'bio': user.bio,
                'message': 'Profile updated successfully'
            }
        }), 200
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating profile'
        }), 500

def generate_username(name):
    """Generate a unique username based on name."""
    # Convert name to lowercase and replace spaces
    base_username = name.lower().replace(' ', '_')
    
    # Remove non-alphanumeric characters (keep underscore)
    base_username = ''.join(c for c in base_username if c.isalnum() or c == '_')
    
    # Ensure minimum length
    if len(base_username) < 3:
        base_username = f"user_{base_username}"
    
    # Check if username exists
    username = base_username
    existing_user = User.query.filter_by(username=username).first()
    
    # If exists, add random suffix
    if existing_user:
        username = f"{base_username}_{random.randint(100, 999)}"
        existing_user = User.query.filter_by(username=username).first()
        
        # In the unlikely case that also exists, try with different suffix
        if existing_user:
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
            username = f"{base_username}_{suffix}"
    
    return username

@user_api.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user account."""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Save user info for response
        user_info = {
            'id': user.id,
            'username': user.username
        }
        
        # Delete related data first (cascading delete)
        # This could be handled by SQLAlchemy cascades as well
        
        # Delete community posts
        community_posts = Community.query.filter_by(user_id=user_id).all()
        for post in community_posts:
            db.session.delete(post)
        
        # Delete community replies
        community_replies = CommunityReply.query.filter_by(user_id=user_id).all()
        for reply in community_replies:
            db.session.delete(reply)
        
        # Delete notifications
        notifications = Notification.query.filter_by(user_id=user_id).all()
        for notification in notifications:
            db.session.delete(notification)
        
        # Delete messages
        messages_sent = Message.query.filter_by(from_user_id=user_id).all()
        for message in messages_sent:
            db.session.delete(message)
            
        messages_received = Message.query.filter_by(to_user_id=user_id).all()
        for message in messages_received:
            db.session.delete(message)
        
        # Finally delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {user_info["username"]} successfully deleted',
            'deleted_user': user_info
        }), 200
    except Exception as e:
        logger.error(f"Error deleting user account: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the user account'
        }), 500