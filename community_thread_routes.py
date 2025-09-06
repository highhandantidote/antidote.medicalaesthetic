"""
Community thread routes.

This module contains routes related to community thread creation and API endpoints for real-time updates.
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Community, CommunityReply, User
from app import db
import logging
from datetime import datetime

# Create logger
logger = logging.getLogger(__name__)

def count_replies_recursive(thread_id):
    """
    Count all replies for a thread, including nested ones.
    
    Args:
        thread_id: ID of the thread to count replies for
        
    Returns:
        Total count of all replies (including nested ones)
    """
    try:
        # Get all replies for this thread
        all_replies = CommunityReply.query.filter_by(thread_id=thread_id).all()
        total_count = len(all_replies)
        logger.debug(f"Found {total_count} total replies for thread {thread_id} using recursive count")
        return total_count
    except Exception as e:
        logger.error(f"Error counting replies for thread {thread_id}: {str(e)}")
        return 0

# Create blueprints with unique names
web = Blueprint('community_thread', __name__, url_prefix='/community')
api = Blueprint('community_trends_api', __name__, url_prefix='/api/community/trends')

@web.route('/create_thread', methods=['POST'])
@login_required
def community_new():
    """Create a new community thread."""
    try:
        data = request.get_json()
        logger.info(f"Received thread creation data: {data}")
        
        if not data:
            logger.error("No JSON data received in request")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        # Verify CSRF token 
        # The CSRF protection is handled by the Flask-WTF middleware
        # We include the token in the headers, but don't need to manually validate it here
            
        # Check for title and content specifically
        title = data.get('title', '').strip() if data.get('title') else ''
        content = data.get('content', '').strip() if data.get('content') else ''
        
        logger.info(f"Thread title: '{title}', length: {len(title)}")
        logger.info(f"Thread content: '{content}', length: {len(content)}")
        
        if not title or not content:
            logger.error(f"Title or content missing: title='{title}', content='{content}'")
            return jsonify({
                'success': False, 
                'message': 'Title and content are required',
                'debug': {
                    'title': title,
                    'content': content,
                    'title_length': len(title),
                    'content_length': len(content)
                }
            }), 400
            
        # Create the new thread
        logger.info(f"Creating new thread with title: {title}")
        new_thread = Community(
            user_id=current_user.id,
            title=title,
            content=content,
            created_at=datetime.utcnow()
        )
        
        # Add optional fields if provided
        if 'category_id' in data:
            new_thread.category_id = data['category_id']
            logger.info(f"Adding category_id: {data['category_id']}")
        if 'procedure_id' in data:
            new_thread.procedure_id = data['procedure_id']
            logger.info(f"Adding procedure_id: {data['procedure_id']}")
        if 'is_anonymous' in data:
            new_thread.is_anonymous = data['is_anonymous']
            logger.info(f"Thread is anonymous: {data['is_anonymous']}")
        
        # Add to session and commit
        db.session.add(new_thread)
        db.session.commit()
        logger.info(f"Thread created with ID: {new_thread.id}")
        
        # Set initial analytics values directly on the thread
        try:
            new_thread.view_count = 0
            new_thread.reply_count = 0
            db.session.commit()
            logger.info(f"Thread analytics initialized for thread ID: {new_thread.id}")
        except Exception as analytics_error:
            logger.warning(f"Non-critical error initializing thread analytics: {str(analytics_error)}")
            # Continue even if analytics initialization fails
        
        return jsonify({
            'success': True, 
            'message': 'Thread created successfully', 
            'thread_id': new_thread.id
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating community thread: {str(e)}")
        logger.exception(e)  # Log full traceback
        return jsonify({
            'success': False, 
            'message': f'Database error: {str(e)}'
        }), 500

@web.route('/thread/<int:thread_id>', methods=['GET'])
def get_thread_api(thread_id):
    """Get thread data for API requests."""
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # For API requests that need authentication, check if user is logged in
            if current_user.is_authenticated:
                # First, check if the current user owns the thread (for editing)
                thread = Community.query.filter_by(id=thread_id, user_id=current_user.id).first()
                
                # If not found or not owned by user, get any thread for viewing
                if not thread:
                    thread = Community.query.get(thread_id)
                    if not thread:
                        logger.warning(f"Thread {thread_id} not found")
                        return jsonify({
                            'success': False, 
                            'message': 'Thread not found'
                        }), 404
                    
                    # Log that we're returning thread for viewing, not editing
                    logger.info(f"Returning thread {thread_id} for viewing only (not owned by user {current_user.id})")
                    # Check if user can edit this thread
                    can_edit = False
                else:
                    # User owns this thread, can edit
                    can_edit = True
                    logger.info(f"Returning thread {thread_id} for editing (owned by user {current_user.id})")
            else:
                # User not logged in, only allow viewing
                thread = Community.query.get(thread_id)
                if not thread:
                    logger.warning(f"Thread {thread_id} not found")
                    return jsonify({
                        'success': False, 
                        'message': 'Thread not found'
                    }), 404
                
                logger.info(f"Returning thread {thread_id} for public viewing (no user logged in)")
                can_edit = False
                
            # Return thread data as JSON
            return jsonify({
                'success': True, 
                'thread': {
                    'id': thread.id,
                    'title': thread.title,
                    'content': thread.content,
                    'created_at': thread.created_at.isoformat() if thread.created_at else None,
                    'is_anonymous': thread.is_anonymous,
                    'can_edit': can_edit
                }
            })
        
        except Exception as e:
            logger.error(f"Error retrieving thread data: {str(e)}")
            return jsonify({
                'success': False, 
                'message': f'An error occurred: {str(e)}'
            }), 500
    
    # If not an AJAX request, let the main routes handle thread viewing
    # This prevents redirect loops - the main routes.py will handle /community/thread/<id>
    from flask import abort
    abort(404)  # Let main routes handle this URL pattern

# Removed duplicate route - handled by main routes.py community_thread_detail function
# @web.route('/thread/<int:thread_id>')
def community_thread_disabled(thread_id):
    """View a community thread - this route exists to match the template's url_for(community_thread)."""
    try:
        # Get the thread
        thread = Community.query.get_or_404(thread_id)
        
        # Get user data
        if thread.user_id:
            thread.user = User.query.get(thread.user_id)
            
        # Increment view count
        thread.view_count = (thread.view_count or 0) + 1
        db.session.commit()
        
        # Get sort order from query parameters (defaulting to "oldest")
        sort_order = request.args.get('sort', 'oldest')
        logger.debug(f"Displaying thread {thread_id} with sort order: {sort_order}")
        
        # Get replies - for now get top-level replies
        if sort_order == 'newest':
            top_replies = CommunityReply.query.filter_by(
                thread_id=thread_id, 
                parent_reply_id=None
            ).order_by(CommunityReply.created_at.desc()).all()
        elif sort_order == 'popular':
            top_replies = CommunityReply.query.filter_by(
                thread_id=thread_id, 
                parent_reply_id=None
            ).order_by(CommunityReply.upvotes.desc(), CommunityReply.created_at.asc()).all()
        else:  # default to 'oldest'
            top_replies = CommunityReply.query.filter_by(
                thread_id=thread_id, 
                parent_reply_id=None
            ).order_by(CommunityReply.created_at.asc()).all()
        
        # Count all replies, including nested ones
        total_replies = count_replies_recursive(thread_id)
        logger.debug(f"Found {total_replies} total replies for thread {thread_id}")
        
        logger.debug(f"Found {len(top_replies)} top-level replies for thread {thread_id}")
        
        # Get user data for each reply
        for reply in top_replies:
            if not reply.is_anonymous and reply.user_id:
                reply.user = User.query.get(reply.user_id)
        
        # Get all replies and organize them into a hierarchical structure
        reply_map = {}
        all_replies = CommunityReply.query.filter_by(thread_id=thread_id).all()
        
        # Create a map of reply_id -> reply object for quick lookup
        for reply in all_replies:
            reply_map[reply.id] = reply
            reply.child_replies = []  # Initialize empty list for child replies
            if not reply.is_anonymous and reply.user_id:
                reply.user = User.query.get(reply.user_id)
        
        # Build the parent-child relationship structure
        for reply in all_replies:
            if reply.parent_reply_id and reply.parent_reply_id in reply_map:
                parent = reply_map[reply.parent_reply_id]
                parent.child_replies.append(reply.id)
        
        # Count total replies for thread (for debugging purposes)
        top_level_count = len(top_replies)
        total_recursive_count = count_replies_recursive(thread_id)
        logger.debug(f"Thread {thread_id}: {top_level_count} top-level replies, {total_recursive_count} total replies")
        
        return render_template(
            'thread.html',
            thread=thread,
            top_replies=top_replies,
            reply_map=reply_map,
            sort_order=sort_order
        )
    except Exception as e:
        logger.error(f"Error viewing thread {thread_id}: {str(e)}")
        flash(f"Error viewing thread: {str(e)}", "danger")
        return redirect(url_for('web.community'))

@web.route('/edit_thread/<int:thread_id>', methods=['POST'])
@login_required
def edit_thread(thread_id):
    """Edit an existing community thread."""
    try:
        # Get the thread to edit - only allow users to edit their own threads
        thread = Community.query.filter_by(id=thread_id, user_id=current_user.id).first()
        
        if not thread:
            logger.warning(f"Thread {thread_id} not found or not owned by user {current_user.id}")
            return jsonify({
                'success': False, 
                'message': 'Thread not found or you do not have permission to edit it'
            }), 404
            
        # Get the request data
        data = request.get_json()
        
        if not data:
            logger.error("No JSON data received in edit request")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        # Check for title and content
        title = data.get('title', '').strip() if data.get('title') else ''
        content = data.get('content', '').strip() if data.get('content') else ''
        
        if not title or not content:
            logger.error(f"Title or content missing in edit: title='{title}', content='{content}'")
            return jsonify({'success': False, 'message': 'Title and content are required'}), 400
            
        # Update the thread
        thread.title = title
        thread.content = content
        
        # Optional fields
        if 'category_id' in data:
            thread.category_id = data['category_id']
        if 'procedure_id' in data:
            thread.procedure_id = data['procedure_id']
        if 'is_anonymous' in data:
            thread.is_anonymous = data['is_anonymous']
        
        # Save changes
        db.session.commit()
        logger.info(f"Thread {thread_id} updated successfully")
        
        return jsonify({
            'success': True, 
            'message': 'Thread updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating thread {thread_id}: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

@web.route('/delete_thread/<int:thread_id>', methods=['POST'])
@login_required
def delete_thread(thread_id):
    """Delete a community thread."""
    try:
        # Get the thread to delete - only allow users to delete their own threads
        thread = Community.query.filter_by(id=thread_id, user_id=current_user.id).first()
        
        if not thread:
            logger.warning(f"Thread {thread_id} not found or not owned by user {current_user.id}")
            return jsonify({
                'success': False, 
                'message': 'Thread not found or you do not have permission to delete it'
            }), 404
            
        # Delete the thread from the database
        db.session.delete(thread)
        db.session.commit()
        logger.info(f"Thread {thread_id} deleted successfully")
        
        return jsonify({
            'success': True, 
            'message': 'Thread deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting thread {thread_id}: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

@api.route('', methods=['GET'])
def api_community_trends():
    """Return current community analytics data in JSON format for real-time updates."""
    try:
        # Get top threads by views and replies
        top_threads = Community.query.order_by(Community.view_count.desc()).limit(5).all()
        recent_threads = Community.query.order_by(Community.created_at.desc()).limit(5).all()
        
        # Format data for API response
        return jsonify({
            'success': True,
            'data': {
                'top_threads': [
                    {
                        'id': thread.id,
                        'title': thread.title,
                        'views': thread.view_count,
                        'replies': thread.reply_count,
                        'created_at': thread.created_at.isoformat() if thread.created_at else None
                    } for thread in top_threads
                ],
                'recent_threads': [
                    {
                        'id': thread.id,
                        'title': thread.title,
                        'created_at': thread.created_at.isoformat() if thread.created_at else None
                    } for thread in recent_threads
                ]
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting community trends: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching community trends'
        }), 500