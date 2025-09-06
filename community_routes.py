from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import or_, func
from models import (
    User, Community, CommunityReply, Category, 
    Procedure, CommunityTagging, Notification, CommunityModeration
)
from app import db
from datetime import datetime
import logging

# Create logger
logger = logging.getLogger(__name__)

# Create Blueprint for community API routes
community_api = Blueprint('community_api', __name__, url_prefix='/api/community')

@community_api.route('', methods=['GET'])
def get_threads():
    """
    Get community threads with optional filtering.
    
    Query parameters:
    - category_id: Filter by category ID
    - procedure_id: Filter by procedure ID
    - username: Filter by username
    - tag: Filter by tag
    - featured: Filter featured threads (true/false)
    - sort: Sort order (latest, popular, oldest)
    - page: Page number for pagination
    - limit: Number of results per page
    """
    try:
        # Get query parameters
        category_id = request.args.get('category_id', type=int)
        procedure_id = request.args.get('procedure_id', type=int)
        username = request.args.get('username')
        tag = request.args.get('tag')
        featured = request.args.get('featured')
        sort = request.args.get('sort', 'latest')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Base query
        query = Community.query
        
        # Apply filters
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if procedure_id:
            query = query.filter_by(procedure_id=procedure_id)
        
        if username:
            user = User.query.filter_by(username=username).first()
            if user:
                query = query.filter_by(user_id=user.id)
            else:
                return jsonify({
                    'success': False,
                    'message': f'User with username {username} not found'
                }), 404
        
        if tag:
            query = query.filter(Community.tags.contains([tag]))
        
        if featured == 'true':
            query = query.filter_by(featured=True)
            
        # Only get top-level threads (no parent_id)
        query = query.filter(Community.parent_id.is_(None))
        
        # Apply sorting
        if sort == 'latest':
            query = query.order_by(Community.created_at.desc())
        elif sort == 'oldest':
            query = query.order_by(Community.created_at.asc())
        elif sort == 'popular':
            query = query.order_by(Community.view_count.desc())
        
        # Apply pagination
        total = query.count()
        threads = query.offset((page - 1) * limit).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': {
                'threads': [
                    {
                        'id': thread.id,
                        'title': thread.title,
                        'content': thread.content,
                        'user': {
                            'id': thread.user.id,
                            'name': thread.user.name if not thread.is_anonymous else 'Anonymous',
                            'username': thread.user.username if not thread.is_anonymous else None,
                            'role': thread.user.role if not thread.is_anonymous else None,
                            'role_type': thread.user.role_type if not thread.is_anonymous else None,
                            'badge': thread.user.badge if not thread.is_anonymous else None
                        } if thread.user else None,
                        'created_at': thread.created_at.isoformat() if thread.created_at else None,
                        'updated_at': thread.updated_at.isoformat() if thread.updated_at else None,
                        'is_anonymous': thread.is_anonymous,
                        'view_count': thread.view_count,
                        'reply_count': thread.reply_count,
                        'featured': thread.featured,
                        'category': {
                            'id': thread.category.id,
                            'name': thread.category.name
                        } if thread.category else None,
                        'procedure': {
                            'id': thread.procedure.id,
                            'name': thread.procedure.procedure_name
                        } if thread.procedure else None,
                        'tags': thread.tags,
                        'photo_url': thread.photo_url,
                        'video_url': thread.video_url,
                        'has_children': len(thread.child_threads) > 0
                    } for thread in threads
                ],
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': (total + limit - 1) // limit
                }
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting community threads: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching community threads'
        }), 500

@community_api.route('/<int:thread_id>', methods=['GET'])
def get_thread(thread_id):
    """Get a specific community thread by ID."""
    try:
        thread = Community.query.get(thread_id)
        
        if not thread:
            return jsonify({
                'success': False,
                'message': 'Thread not found'
            }), 404
            
        # Increment view count
        thread.view_count += 1
        db.session.commit()
        
        # Get child threads if any
        child_threads = []
        if thread.child_threads:
            for child in thread.child_threads:
                child_threads.append({
                    'id': child.id,
                    'title': child.title,
                    'content': child.content,
                    'user': {
                        'id': child.user.id,
                        'name': child.user.name if not child.is_anonymous else 'Anonymous',
                        'username': child.user.username if not child.is_anonymous else None
                    } if child.user else None,
                    'created_at': child.created_at.isoformat() if child.created_at else None,
                    'view_count': child.view_count,
                    'reply_count': child.reply_count
                })
                
        return jsonify({
            'success': True,
            'data': {
                'id': thread.id,
                'title': thread.title,
                'content': thread.content,
                'user': {
                    'id': thread.user.id,
                    'name': thread.user.name if not thread.is_anonymous else 'Anonymous',
                    'username': thread.user.username if not thread.is_anonymous else None,
                    'role': thread.user.role if not thread.is_anonymous else None,
                    'role_type': thread.user.role_type if not thread.is_anonymous else None,
                    'badge': thread.user.badge if not thread.is_anonymous else None
                } if thread.user else None,
                'created_at': thread.created_at.isoformat() if thread.created_at else None,
                'updated_at': thread.updated_at.isoformat() if thread.updated_at else None,
                'is_anonymous': thread.is_anonymous,
                'view_count': thread.view_count,
                'reply_count': thread.reply_count,
                'featured': thread.featured,
                'category': {
                    'id': thread.category.id,
                    'name': thread.category.name
                } if thread.category else None,
                'procedure': {
                    'id': thread.procedure.id,
                    'name': thread.procedure.procedure_name
                } if thread.procedure else None,
                'tags': thread.tags,
                'photo_url': thread.photo_url,
                'video_url': thread.video_url,
                'parent_thread': {
                    'id': thread.parent_thread.id,
                    'title': thread.parent_thread.title
                } if thread.parent_thread else None,
                'child_threads': child_threads
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting community thread: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching the community thread'
        }), 500

@community_api.route('', methods=['POST'])
def create_thread():
    """Create a new community thread."""
    try:
        data = request.json
        required_fields = ['title', 'content', 'user_id']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Create new thread
        new_thread = Community(
            title=data['title'],
            content=data['content'],
            user_id=data['user_id'],
            is_anonymous=data.get('is_anonymous', False),
            category_id=data.get('category_id'),
            procedure_id=data.get('procedure_id'),
            tags=data.get('tags', []),
            parent_id=data.get('parent_id'),
            photo_url=data.get('photo_url'),
            video_url=data.get('video_url'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_thread)
        db.session.commit()
        
        # If this is a child thread, update parent's reply count
        if new_thread.parent_id:
            parent = Community.query.get(new_thread.parent_id)
            if parent:
                parent.reply_count += 1
                db.session.commit()
        
        # Process tag mentions (@username)
        if data.get('mentioned_usernames'):
            for username in data.get('mentioned_usernames', []):
                mentioned_user = User.query.filter_by(username=username).first()
                if mentioned_user:
                    notification = Notification(
                        user_id=mentioned_user.id,
                        message=f"{new_thread.user.username or new_thread.user.name} mentioned you in a thread: {new_thread.title}",
                        type="mention",
                        mentioned_username=username,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(notification)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': new_thread.id,
                'title': new_thread.title,
                'message': 'Thread created successfully'
            }
        }), 201
    except Exception as e:
        logger.error(f"Error creating community thread: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while creating the community thread'
        }), 500

@community_api.route('/<int:thread_id>', methods=['PATCH'])
def update_thread(thread_id):
    """Update an existing community thread."""
    try:
        thread = Community.query.get(thread_id)
        
        if not thread:
            return jsonify({
                'success': False,
                'message': 'Thread not found'
            }), 404
        
        data = request.json
        
        # Update allowed fields
        if 'title' in data:
            thread.title = data['title']
        if 'content' in data:
            thread.content = data['content']
        if 'is_anonymous' in data:
            thread.is_anonymous = data['is_anonymous']
        if 'category_id' in data:
            thread.category_id = data['category_id']
        if 'procedure_id' in data:
            thread.procedure_id = data['procedure_id']
        if 'tags' in data:
            thread.tags = data['tags']
        if 'featured' in data:
            thread.featured = data['featured']
        if 'photo_url' in data:
            thread.photo_url = data['photo_url']
        if 'video_url' in data:
            thread.video_url = data['video_url']
        
        thread.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Thread updated successfully'
        }), 200
    except Exception as e:
        logger.error(f"Error updating community thread: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the community thread'
        }), 500

@community_api.route('/<int:thread_id>', methods=['DELETE'])
def delete_thread(thread_id):
    """Delete a community thread."""
    try:
        thread = Community.query.get(thread_id)
        
        if not thread:
            return jsonify({
                'success': False,
                'message': 'Thread not found'
            }), 404
        
        # If this is a child thread, update parent's reply count
        if thread.parent_id:
            parent = Community.query.get(thread.parent_id)
            if parent:
                parent.reply_count = max(0, parent.reply_count - 1)
                db.session.commit()
        
        db.session.delete(thread)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Thread deleted successfully'
        }), 200
    except Exception as e:
        logger.error(f"Error deleting community thread: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the community thread'
        }), 500

@community_api.route('/search', methods=['GET'])
def search_threads():
    """
    Search community threads.
    
    Query parameters:
    - q: Search query (required)
    - category_id: Filter by category ID
    - procedure_id: Filter by procedure ID
    - username: Filter by username
    - tag: Filter by tag
    - featured: Filter featured threads (true/false)
    - sort: Sort order (latest, popular, oldest)
    - page: Page number for pagination
    - limit: Number of results per page
    """
    try:
        # Get search query
        query_text = request.args.get('q')
        if not query_text:
            return jsonify({
                'success': False,
                'message': 'Search query is required'
            }), 400
        
        # Get other filtering parameters
        category_id = request.args.get('category_id', type=int)
        procedure_id = request.args.get('procedure_id', type=int)
        username = request.args.get('username')
        tag = request.args.get('tag')
        featured = request.args.get('featured')
        sort = request.args.get('sort', 'latest')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Base query with search
        query = Community.query.filter(
            or_(
                Community.title.ilike(f'%{query_text}%'),
                Community.content.ilike(f'%{query_text}%'),
                Community.tags.contains([query_text.lower()])
            )
        )
        
        # Apply filters
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if procedure_id:
            query = query.filter_by(procedure_id=procedure_id)
        
        if username:
            user = User.query.filter_by(username=username).first()
            if user:
                query = query.filter_by(user_id=user.id)
        
        if tag:
            query = query.filter(Community.tags.contains([tag]))
        
        if featured == 'true':
            query = query.filter_by(featured=True)
        
        # Apply sorting
        if sort == 'latest':
            query = query.order_by(Community.created_at.desc())
        elif sort == 'oldest':
            query = query.order_by(Community.created_at.asc())
        elif sort == 'popular':
            query = query.order_by(Community.view_count.desc())
        
        # Apply pagination
        total = query.count()
        threads = query.offset((page - 1) * limit).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': {
                'threads': [
                    {
                        'id': thread.id,
                        'title': thread.title,
                        'content': thread.content,
                        'user': {
                            'id': thread.user.id,
                            'name': thread.user.name if not thread.is_anonymous else 'Anonymous',
                            'username': thread.user.username if not thread.is_anonymous else None
                        } if thread.user else None,
                        'created_at': thread.created_at.isoformat() if thread.created_at else None,
                        'is_anonymous': thread.is_anonymous,
                        'view_count': thread.view_count,
                        'reply_count': thread.reply_count,
                        'featured': thread.featured,
                        'category': {
                            'id': thread.category.id,
                            'name': thread.category.name
                        } if thread.category else None,
                        'procedure': {
                            'id': thread.procedure.id,
                            'name': thread.procedure.procedure_name
                        } if thread.procedure else None,
                        'tags': thread.tags
                    } for thread in threads
                ],
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': (total + limit - 1) // limit
                }
            }
        }), 200
    except Exception as e:
        logger.error(f"Error searching community threads: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while searching community threads'
        }), 500