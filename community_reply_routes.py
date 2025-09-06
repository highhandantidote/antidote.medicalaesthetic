"""
Community reply routes.

This module contains routes related to community thread replies.
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Community, CommunityReply, User
from app import db
import logging
from datetime import datetime

# Create logger
logger = logging.getLogger(__name__)

# Create blueprints with unique names
reply_web = Blueprint('community_reply', __name__, url_prefix='/community/reply')

# API blueprint for community replies
community_reply_api = Blueprint('community_reply_api', __name__, url_prefix='/api/community-replies')

# Thread reply blueprint - specifically for the thread/<id>/reply endpoint requested by user
thread_reply_web = Blueprint('thread_reply_web', __name__, url_prefix='/community')

# Community thread replies API blueprint
community_thread_replies_api = Blueprint('community_thread_replies_api', __name__, url_prefix='/api/community')

# Add debug logger with higher visibility
logger.setLevel(logging.DEBUG)

def check_doctor_status(reply, user_id):
    """
    Check if a reply is from a doctor and mark it accordingly.
    
    Args:
        reply: The CommunityReply object to check
        user_id: The user ID to check for doctor status
        
    Returns:
        True if user is a doctor, False otherwise
    """
    try:
        from models import Doctor
        # Check if user has a doctor profile
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if doctor:
            reply.is_doctor_response = True
            logger.info(f"Marked reply as doctor response from doctor ID: {doctor.id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking doctor status: {str(e)}")
        return False

@reply_web.route('/create', methods=['POST'])
@login_required
def create_reply():
    """Create a new reply to a community thread."""
    try:
        data = request.get_json()
        logger.info(f"Received reply creation data: {data}")
        
        if not data:
            logger.error("No JSON data received in request")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        # Check for thread_id and content
        thread_id = data.get('thread_id')
        content = data.get('content', '').strip() if data.get('content') else ''
        
        if not thread_id or not content:
            logger.error(f"Thread ID or content missing: thread_id={thread_id}, content='{content}'")
            return jsonify({
                'success': False, 
                'message': 'Thread ID and content are required'
            }), 400
            
        # Verify thread exists
        thread = Community.query.get(thread_id)
        if not thread:
            logger.error(f"Thread with ID {thread_id} not found")
            return jsonify({
                'success': False, 
                'message': 'Thread not found'
            }), 404
            
        # Create new reply
        new_reply = CommunityReply(
            thread_id=thread_id,
            user_id=current_user.id,
            content=content,
            created_at=datetime.utcnow()
        )
        
        # Handle optional fields
        if 'is_anonymous' in data:
            new_reply.is_anonymous = data['is_anonymous']
        
        # Check if the current user is a doctor and mark reply accordingly
        check_doctor_status(new_reply, current_user.id)
        
        # Handle nested replies
        if 'parent_reply_id' in data and data['parent_reply_id']:
            # Verify parent reply exists
            parent_reply = CommunityReply.query.get(data['parent_reply_id'])
            if not parent_reply:
                logger.error(f"Parent reply with ID {data['parent_reply_id']} not found")
                return jsonify({
                    'success': False, 
                    'message': 'Parent reply not found'
                }), 404
            new_reply.parent_reply_id = data['parent_reply_id']
        
        # Add to session and commit
        db.session.add(new_reply)
        
        # Increment reply count on thread
        thread.reply_count = (thread.reply_count or 0) + 1
        
        db.session.commit()
        logger.info(f"Reply created with ID: {new_reply.id} for thread {thread_id}")
        
        return jsonify({
            'success': True, 
            'message': 'Reply created successfully', 
            'reply_id': new_reply.id
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating reply: {str(e)}")
        logger.exception(e)  # Log full traceback
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

@reply_web.route('/edit/<int:reply_id>', methods=['POST'])
@login_required
def edit_reply(reply_id):
    """Edit an existing reply."""
    try:
        # Get the reply to edit - only allow users to edit their own replies
        reply = CommunityReply.query.filter_by(id=reply_id, user_id=current_user.id).first()
        
        if not reply:
            logger.warning(f"Reply {reply_id} not found or not owned by user {current_user.id}")
            return jsonify({
                'success': False, 
                'message': 'Reply not found or you do not have permission to edit it'
            }), 404
            
        # Get the request data
        data = request.get_json()
        
        if not data:
            logger.error("No JSON data received in edit request")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        # Check for content
        content = data.get('content', '').strip() if data.get('content') else ''
        
        if not content:
            logger.error(f"Content missing in edit: content='{content}'")
            return jsonify({'success': False, 'message': 'Content is required'}), 400
            
        # Update the reply
        reply.content = content
        
        # Optional fields
        if 'is_anonymous' in data:
            reply.is_anonymous = data['is_anonymous']
        
        # Save changes
        db.session.commit()
        logger.info(f"Reply {reply_id} updated successfully")
        
        return jsonify({
            'success': True, 
            'message': 'Reply updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating reply {reply_id}: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

@reply_web.route('/delete/<int:reply_id>', methods=['POST'])
@login_required
def delete_reply(reply_id):
    """Delete a reply."""
    try:
        # Get the reply to delete - only allow users to delete their own replies
        reply = CommunityReply.query.filter_by(id=reply_id, user_id=current_user.id).first()
        
        if not reply:
            logger.warning(f"Reply {reply_id} not found or not owned by user {current_user.id}")
            return jsonify({
                'success': False, 
                'message': 'Reply not found or you do not have permission to delete it'
            }), 404
            
        # Get thread to update reply count
        thread = Community.query.get(reply.thread_id)
        
        # Delete the reply from the database
        db.session.delete(reply)
        
        # Decrement reply count on thread
        if thread and thread.reply_count > 0:
            thread.reply_count -= 1
            
        db.session.commit()
        logger.info(f"Reply {reply_id} deleted successfully")
        
        return jsonify({
            'success': True, 
            'message': 'Reply deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting reply {reply_id}: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

@reply_web.route('/upvote/<int:reply_id>', methods=['POST'])
@login_required
def upvote_reply(reply_id):
    """Upvote a reply."""
    try:
        # Get the reply to upvote
        reply = CommunityReply.query.get(reply_id)
        
        if not reply:
            logger.warning(f"Reply {reply_id} not found")
            return jsonify({
                'success': False, 
                'message': 'Reply not found'
            }), 404
            
        # Increment upvote count
        reply.upvotes = (reply.upvotes or 0) + 1
        db.session.commit()
        logger.info(f"Reply {reply_id} upvoted successfully")
        
        return jsonify({
            'success': True, 
            'message': 'Reply upvoted successfully',
            'data': {
                'upvotes': reply.upvotes
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error upvoting reply {reply_id}: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

# Thread reply route - for the specific endpoint format requested by the user
@thread_reply_web.route('/thread/<int:thread_id>/reply', methods=['POST'])
@login_required
def post_thread_reply(thread_id):
    """Create a new reply to a thread using the format requested by the user."""
    try:
        # Debug incoming request
        logger.debug(f"Thread reply request received for thread ID: {thread_id}")
        logger.debug(f"Request content type: {request.content_type}")
        logger.debug(f"Request headers: {request.headers}")
        logger.debug(f"Request method: {request.method}")
        logger.debug(f"Raw request data: {request.data}")
        
        # Parse the JSON data
        try:
            data = request.get_json(force=True)  # Force=True to avoid content-type issues
            logger.info(f"Received thread reply data: {data}")
        except Exception as json_err:
            logger.error(f"Error parsing JSON: {str(json_err)}")
            return jsonify({'success': False, 'message': f'Invalid JSON data: {str(json_err)}'}), 400
        
        if not data:
            logger.error("No JSON data received in request")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        content = data.get('content', '').strip() if data.get('content') else ''
        is_anonymous = data.get('is_anonymous', False)
        parent_reply_id = data.get('parent_reply_id', None)
        
        if not content:
            logger.error(f"Content missing in thread reply: content='{content}'")
            return jsonify({'success': False, 'message': 'Content is required'}), 400
            
        # Verify thread exists - using the correct model name
        thread = Community.query.get(thread_id)
        if not thread:
            logger.error(f"Thread with ID {thread_id} not found")
            return jsonify({'success': False, 'message': 'Thread not found'}), 404
            
        # Create new reply
        new_reply = CommunityReply(
            thread_id=thread_id,
            user_id=current_user.id,
            content=content,
            is_anonymous=is_anonymous,
            created_at=datetime.utcnow()
        )
        
        # Use our helper function to check doctor status
        check_doctor_status(new_reply, current_user.id)
        
        # Handle parent reply if provided
        if parent_reply_id:
            parent_reply = CommunityReply.query.get(parent_reply_id)
            if not parent_reply:
                logger.error(f"Parent reply with ID {parent_reply_id} not found")
                return jsonify({'success': False, 'message': 'Parent reply not found'}), 404
            new_reply.parent_reply_id = parent_reply_id
        
        # Add to session and commit
        db.session.add(new_reply)
        
        # Increment reply count on thread
        thread.reply_count = (thread.reply_count or 0) + 1
        
        db.session.commit()
        logger.info(f"Reply created with ID: {new_reply.id} for thread {thread_id}")
        
        return jsonify({
            'success': True, 
            'message': 'Reply posted successfully!', 
            'reply_id': new_reply.id
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating thread reply: {str(e)}")
        logger.exception(e)
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

# API endpoint for creating replies to threads (matches the endpoint used in the JavaScript)
@community_thread_replies_api.route('/<int:thread_id>/replies', methods=['POST'])
@login_required
def thread_reply_api(thread_id):
    """Create a new reply to a thread via API."""
    try:
        # Debug incoming request
        logger.debug(f"Thread reply API request received for thread ID: {thread_id}")
        logger.debug(f"Request headers: {request.headers}")
        
        # Get CSRF token from request
        csrf_token = None
        if 'X-CSRFToken' in request.headers:
            csrf_token = request.headers.get('X-CSRFToken')
            logger.debug(f"Found CSRF token in header: {csrf_token}")
        
        # Parse the JSON data
        try:
            data = request.get_json(force=True)  # Force=True to avoid content-type issues
            logger.info(f"Received thread reply data: {data}")
            
            # If the token is in the request body but not headers, use it
            if not csrf_token and 'csrf_token' in data:
                csrf_token = data.get('csrf_token')
                logger.debug(f"Found CSRF token in body: {csrf_token}")
        except Exception as json_err:
            logger.error(f"Error parsing JSON: {str(json_err)}")
            return jsonify({'success': False, 'message': f'Invalid JSON data: {str(json_err)}'}), 400
        
        if not data:
            logger.error("No JSON data received in request")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        content = data.get('content', '').strip() if data.get('content') else ''
        is_anonymous = data.get('is_anonymous', False)
        parent_reply_id = data.get('parent_reply_id', None)
        
        if not content:
            logger.error(f"Content missing in thread reply: content='{content}'")
            return jsonify({'success': False, 'message': 'Content is required'}), 400
            
        # Verify thread exists - using the correct model name
        thread = Community.query.get(thread_id)
        if not thread:
            logger.error(f"Thread with ID {thread_id} not found")
            return jsonify({'success': False, 'message': 'Thread not found'}), 404
            
        # Create new reply
        new_reply = CommunityReply(
            thread_id=thread_id,
            user_id=current_user.id,
            content=content,
            is_anonymous=is_anonymous,
            created_at=datetime.utcnow()
        )
        
        # Check if the current user is a doctor and mark reply accordingly
        check_doctor_status(new_reply, current_user.id)
        
        # Handle parent reply if provided
        if parent_reply_id:
            parent_reply = CommunityReply.query.get(parent_reply_id)
            if not parent_reply:
                logger.error(f"Parent reply with ID {parent_reply_id} not found")
                return jsonify({'success': False, 'message': 'Parent reply not found'}), 404
            new_reply.parent_reply_id = parent_reply_id
        
        # Add to session and commit
        db.session.add(new_reply)
        
        # Increment reply count on thread
        thread.reply_count = (thread.reply_count or 0) + 1
        
        db.session.commit()
        logger.info(f"Reply created with ID: {new_reply.id} for thread {thread_id}")
        
        return jsonify({
            'success': True, 
            'message': 'Reply created successfully', 
            'reply_id': new_reply.id
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating thread reply via API: {str(e)}")
        logger.exception(e)
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

# API Routes for AJAX requests

@community_reply_api.route('/<int:reply_id>/upvote', methods=['POST'])
@login_required
def api_upvote_reply(reply_id):
    """Upvote a reply through AJAX API."""
    try:
        # Get the reply to upvote
        reply = CommunityReply.query.get(reply_id)
        
        if not reply:
            logger.warning(f"Reply {reply_id} not found")
            return jsonify({
                'success': False, 
                'message': 'Reply not found'
            }), 404
            
        # Increment upvote count
        reply.upvotes = (reply.upvotes or 0) + 1
        db.session.commit()
        logger.info(f"Reply {reply_id} upvoted successfully through API")
        
        return jsonify({
            'success': True, 
            'message': 'Reply upvoted successfully',
            'data': {
                'upvotes': reply.upvotes
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error upvoting reply {reply_id} through API: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

@community_reply_api.route('/<int:reply_id>', methods=['GET'])
def api_get_reply(reply_id):
    """Get reply details through AJAX API."""
    try:
        reply = CommunityReply.query.get(reply_id)
        
        if not reply:
            logger.warning(f"Reply {reply_id} not found")
            return jsonify({
                'success': False, 
                'message': 'Reply not found'
            }), 404
        
        # Get user if not anonymous
        username = 'Anonymous'
        if not reply.is_anonymous and reply.user_id:
            user = User.query.get(reply.user_id)
            username = user.username if user else 'Unknown'
        
        # Format the reply data for JSON response
        return jsonify({
            'success': True,
            'reply': {
                'id': reply.id,
                'content': reply.content,
                'created_at': reply.created_at.isoformat() if reply.created_at else None,
                'upvotes': reply.upvotes or 0,
                'username': username,
                'is_anonymous': reply.is_anonymous,
                'is_doctor_response': reply.is_doctor_response,
                'is_expert_advice': reply.is_expert_advice,
                'parent_reply_id': reply.parent_reply_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting reply {reply_id}: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

@community_reply_api.route('/', methods=['POST'])
@login_required
def api_create_reply():
    """Create a new reply through AJAX API."""
    try:
        data = request.get_json()
        logger.info(f"Received reply creation data via API: {data}")
        
        if not data:
            logger.error("No JSON data received in request")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        # Check for thread_id and content
        thread_id = data.get('thread_id')
        content = data.get('content', '').strip() if data.get('content') else ''
        
        if not thread_id or not content:
            logger.error(f"Thread ID or content missing: thread_id={thread_id}, content='{content}'")
            return jsonify({
                'success': False, 
                'message': 'Thread ID and content are required'
            }), 400
            
        # Verify thread exists
        thread = Community.query.get(thread_id)
        if not thread:
            logger.error(f"Thread with ID {thread_id} not found")
            return jsonify({
                'success': False, 
                'message': 'Thread not found'
            }), 404
            
        # Create new reply
        new_reply = CommunityReply(
            thread_id=thread_id,
            user_id=current_user.id,
            content=content,
            created_at=datetime.utcnow()
        )
        
        # Handle optional fields
        if 'is_anonymous' in data:
            new_reply.is_anonymous = data['is_anonymous']
            
        # Check if user is a doctor
        check_doctor_status(new_reply, current_user.id)
        
        # Handle nested replies
        if 'parent_reply_id' in data and data['parent_reply_id']:
            # Verify parent reply exists
            parent_reply = CommunityReply.query.get(data['parent_reply_id'])
            if not parent_reply:
                logger.error(f"Parent reply with ID {data['parent_reply_id']} not found")
                return jsonify({
                    'success': False, 
                    'message': 'Parent reply not found'
                }), 404
            new_reply.parent_reply_id = data['parent_reply_id']
        
        # Add to session and commit
        db.session.add(new_reply)
        
        # Increment reply count on thread
        thread.reply_count = (thread.reply_count or 0) + 1
        
        db.session.commit()
        logger.info(f"Reply created with ID: {new_reply.id} for thread {thread_id} via API")
        
        # Get username for response
        username = 'Anonymous' if new_reply.is_anonymous else current_user.username
        
        return jsonify({
            'success': True, 
            'message': 'Reply created successfully',
            'reply': {
                'id': new_reply.id,
                'content': new_reply.content,
                'created_at': new_reply.created_at.isoformat() if new_reply.created_at else None,
                'upvotes': 0,
                'username': username,
                'is_anonymous': new_reply.is_anonymous,
                'parent_reply_id': new_reply.parent_reply_id
            }
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating reply via API: {str(e)}")
        logger.exception(e)  # Log full traceback
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500