"""
Community API routes.

This module contains API routes for community threads and replies.
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import Community, CommunityReply, User
from app import db
import logging
from datetime import datetime

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create blueprints with unique names
api = Blueprint('community_replies_api', __name__, url_prefix='/api/community')

@api.route('/<int:thread_id>/replies', methods=['POST'])
@login_required
def create_reply_api(thread_id):
    """Create a new reply to a thread via API."""
    try:
        # Debug incoming request
        logger.debug(f"API reply request received for thread ID: {thread_id}")
        logger.debug(f"Request content type: {request.content_type}")
        logger.debug(f"Request headers: {request.headers}")
        logger.debug(f"Request method: {request.method}")
        logger.debug(f"Raw request data: {request.data}")
        
        # Parse the JSON data
        try:
            data = request.get_json(force=True)  # Force=True to avoid content-type issues
            logger.info(f"Received API reply data: {data}")
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
            logger.error(f"Content missing in API reply: content='{content}'")
            return jsonify({'success': False, 'message': 'Content is required'}), 400
            
        # Verify thread exists
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
        logger.info(f"Reply created with ID: {new_reply.id} for thread {thread_id} via API")
        
        return jsonify({
            'success': True, 
            'message': 'Reply posted successfully!', 
            'reply_id': new_reply.id
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating API reply: {str(e)}")
        logger.exception(e)
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

@api.route('/<int:thread_id>/replies/<int:reply_id>', methods=['PUT'])
@login_required
def update_reply_api(thread_id, reply_id):
    """Update an existing reply via API."""
    try:
        # Get the reply to edit - only allow users to edit their own replies
        reply = CommunityReply.query.filter_by(id=reply_id, thread_id=thread_id, user_id=current_user.id).first()
        
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
        logger.info(f"Reply {reply_id} updated successfully via API")
        
        return jsonify({
            'success': True, 
            'message': 'Reply updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating reply {reply_id} via API: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

@api.route('/<int:thread_id>/replies/<int:reply_id>', methods=['DELETE'])
@login_required
def delete_reply_api(thread_id, reply_id):
    """Delete a reply via API."""
    try:
        # Get the reply to delete - only allow users to delete their own replies
        reply = CommunityReply.query.filter_by(id=reply_id, thread_id=thread_id, user_id=current_user.id).first()
        
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
        logger.info(f"Reply {reply_id} deleted successfully via API")
        
        return jsonify({
            'success': True, 
            'message': 'Reply deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting reply {reply_id} via API: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500