from flask import Blueprint, request, jsonify, current_app
from models import User, Community, CommunityReply, CommunityModeration
from app import db
from datetime import datetime
import logging

# Create logger
logger = logging.getLogger(__name__)

# Create Blueprint for moderation API routes
moderation_api = Blueprint('moderation_api', __name__, url_prefix='/api/community-moderation')

@moderation_api.route('', methods=['GET'])
def get_moderation_actions():
    """
    Get moderation actions.
    
    Query parameters:
    - moderator_id: Filter by moderator ID
    - community_id: Filter by community thread ID
    - reply_id: Filter by reply ID
    - action: Filter by action type (approve, reject, flag)
    - page: Page number for pagination
    - limit: Number of results per page
    """
    try:
        # Get query parameters
        moderator_id = request.args.get('moderator_id', type=int)
        community_id = request.args.get('community_id', type=int)
        reply_id = request.args.get('reply_id', type=int)
        action = request.args.get('action')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Build query
        query = CommunityModeration.query
        
        if moderator_id:
            query = query.filter_by(moderator_id=moderator_id)
        
        if community_id:
            query = query.filter_by(community_id=community_id)
        
        if reply_id:
            query = query.filter_by(reply_id=reply_id)
        
        if action:
            query = query.filter_by(action=action)
        
        # Apply sorting (newest first)
        query = query.order_by(CommunityModeration.created_at.desc())
        
        # Apply pagination
        total = query.count()
        moderation_actions = query.offset((page - 1) * limit).limit(limit).all()
        
        # Format moderation data
        formatted_actions = []
        for action in moderation_actions:
            action_data = {
                'id': action.id,
                'moderator': {
                    'id': action.moderator.id,
                    'name': action.moderator.name,
                    'username': action.moderator.username
                } if action.moderator else None,
                'action': action.action,
                'reason': action.reason,
                'created_at': action.created_at.isoformat() if action.created_at else None,
            }
            
            if action.community_id:
                thread = action.community
                action_data['target_type'] = 'thread'
                action_data['target'] = {
                    'id': thread.id,
                    'title': thread.title,
                    'user': {
                        'id': thread.user.id,
                        'name': thread.user.name,
                        'username': thread.user.username
                    } if thread.user else None
                } if thread else None
            elif action.reply_id:
                reply = action.reply
                action_data['target_type'] = 'reply'
                action_data['target'] = {
                    'id': reply.id,
                    'content': reply.content[:100] + ('...' if len(reply.content) > 100 else ''),
                    'user': {
                        'id': reply.user.id,
                        'name': reply.user.name,
                        'username': reply.user.username
                    } if reply.user else None,
                    'thread_id': reply.thread_id
                } if reply else None
            
            formatted_actions.append(action_data)
        
        return jsonify({
            'success': True,
            'data': {
                'moderation_actions': formatted_actions,
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': (total + limit - 1) // limit
                }
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting moderation actions: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching moderation actions'
        }), 500

@moderation_api.route('/<int:action_id>', methods=['GET'])
def get_moderation_action(action_id):
    """Get a specific moderation action by ID."""
    try:
        # Get the moderation action
        action = CommunityModeration.query.get(action_id)
        
        if not action:
            return jsonify({
                'success': False,
                'message': 'Moderation action not found'
            }), 404
            
        # Check if user is authorized (admin or moderator)
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
            
        user = User.query.get(user_id)
        if not user or (user.role != 'admin' and user.role != 'moderator'):
            return jsonify({
                'success': False,
                'message': 'Not authorized to view moderation actions'
            }), 403
            
        # Format the action data
        action_data = {
            'id': action.id,
            'action': action.action,
            'reason': action.reason,
            'moderator_id': action.moderator_id,
            'moderator_username': User.query.get(action.moderator_id).username if action.moderator_id else None,
            'created_at': action.created_at.isoformat() if action.created_at else None
        }
        
        # Add target-specific data
        if action.community_id:
            action_data['target_type'] = 'thread'
            action_data['target_id'] = action.community_id
            thread = Community.query.get(action.community_id)
            if thread:
                action_data['target_title'] = thread.title
        elif action.reply_id:
            action_data['target_type'] = 'reply'
            action_data['target_id'] = action.reply_id
            reply = CommunityReply.query.get(action.reply_id)
            if reply:
                action_data['target_thread_id'] = reply.thread_id
                thread = Community.query.get(reply.thread_id)
                if thread:
                    action_data['target_thread_title'] = thread.title
                    
        return jsonify({
            'success': True,
            'data': action_data
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving moderation action: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving the moderation action'
        }), 500
        
@moderation_api.route('', methods=['POST'])
def create_moderation_action():
    """Create a new moderation action."""
    try:
        data = request.json
        required_fields = ['moderator_id', 'action']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Validate action type
        valid_actions = ['approve', 'reject', 'flag']
        if data['action'] not in valid_actions:
            return jsonify({
                'success': False,
                'message': f"Invalid action: {data['action']}. Must be one of: {', '.join(valid_actions)}"
            }), 400
        
        # Verify moderator exists
        moderator = User.query.get(data['moderator_id'])
        if not moderator:
            return jsonify({
                'success': False,
                'message': 'Moderator not found'
            }), 404
        
        # Verify target exists
        if 'community_id' in data and data['community_id']:
            thread = Community.query.get(data['community_id'])
            if not thread:
                return jsonify({
                    'success': False,
                    'message': 'Thread not found'
                }), 404
        elif 'reply_id' in data and data['reply_id']:
            reply = CommunityReply.query.get(data['reply_id'])
            if not reply:
                return jsonify({
                    'success': False,
                    'message': 'Reply not found'
                }), 404
        else:
            return jsonify({
                'success': False,
                'message': 'Either community_id or reply_id must be provided'
            }), 400
        
        # Create new moderation action
        new_action = CommunityModeration(
            moderator_id=data['moderator_id'],
            community_id=data.get('community_id'),
            reply_id=data.get('reply_id'),
            action=data['action'],
            reason=data.get('reason'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_action)
        db.session.commit()
        
        # Perform the actual moderation action
        if data['action'] == 'reject':
            if new_action.community_id:
                # Hide or delete the thread
                thread = Community.query.get(new_action.community_id)
                # In a real implementation you might set a 'hidden' flag rather than delete
                db.session.delete(thread)
                db.session.commit()
            elif new_action.reply_id:
                # Hide or delete the reply
                reply = CommunityReply.query.get(new_action.reply_id)
                # In a real implementation you might set a 'hidden' flag rather than delete
                db.session.delete(reply)
                db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': new_action.id,
                'message': 'Moderation action created successfully'
            }
        }), 201
    except Exception as e:
        logger.error(f"Error creating moderation action: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while creating the moderation action'
        }), 500
        
@moderation_api.route('/<int:action_id>', methods=['PATCH'])
def update_moderation_action(action_id):
    """Update a specific moderation action."""
    try:
        # Get the moderation action
        action = CommunityModeration.query.get(action_id)
        
        if not action:
            return jsonify({
                'success': False,
                'message': 'Moderation action not found'
            }), 404
        
        # Check if user is authorized (admin or moderator)
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
            
        user = User.query.get(user_id)
        if not user or (user.role != 'admin' and user.role != 'moderator'):
            return jsonify({
                'success': False,
                'message': 'Not authorized to update moderation actions'
            }), 403
        
        # Get request data
        data = request.json
        
        # Update fields if provided
        if 'reason' in data:
            action.reason = data['reason']
            
        if 'action' in data:
            # Validate action type
            valid_actions = ['approve', 'reject', 'flag']
            if data['action'] not in valid_actions:
                return jsonify({
                    'success': False,
                    'message': f"Invalid action: {data['action']}. Must be one of: {', '.join(valid_actions)}"
                }), 400
                
            # Only update if action is changing
            if action.action != data['action']:
                old_action = action.action
                action.action = data['action']
                
                # Handle additional logic based on action type change
                if data['action'] == 'reject' and old_action != 'reject':
                    # Content was previously approved but now rejected
                    if action.community_id:
                        thread = Community.query.get(action.community_id)
                        if thread:
                            # In a real implementation you might set a 'hidden' flag rather than delete
                            db.session.delete(thread)
                    elif action.reply_id:
                        reply = CommunityReply.query.get(action.reply_id)
                        if reply:
                            # In a real implementation you might set a 'hidden' flag rather than delete
                            db.session.delete(reply)
                elif data['action'] == 'approve' and old_action == 'reject':
                    # Content was previously rejected but now approved
                    # In a real implementation you might update a 'hidden' flag
                    pass
        
        # Commit changes
        db.session.commit()
        
        # Return updated action
        action_data = {
            'id': action.id,
            'action': action.action,
            'reason': action.reason,
            'moderator_id': action.moderator_id,
            'created_at': action.created_at.isoformat() if action.created_at else None,
            'target_type': 'thread' if action.community_id else 'reply'
        }
        
        return jsonify({
            'success': True,
            'message': 'Moderation action updated successfully',
            'data': action_data
        }), 200
    except Exception as e:
        logger.error(f"Error updating moderation action: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the moderation action'
        }), 500

@moderation_api.route('/<int:action_id>', methods=['DELETE'])
def delete_moderation_action(action_id):
    """Delete a specific moderation action."""
    try:
        # Get the moderation action
        action = CommunityModeration.query.get(action_id)
        
        if not action:
            return jsonify({
                'success': False,
                'message': 'Moderation action not found'
            }), 404
        
        # Check if user is authorized (admin or moderator)
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
            
        user = User.query.get(user_id)
        if not user or (user.role != 'admin' and user.role != 'moderator'):
            return jsonify({
                'success': False,
                'message': 'Not authorized to delete moderation actions'
            }), 403
            
        # Store action info for response
        action_info = {
            'id': action.id,
            'action': action.action,
            'created_at': action.created_at.isoformat() if action.created_at else None,
            'target_type': 'thread' if action.community_id else 'reply'
        }
        
        # Delete the action
        db.session.delete(action)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Moderation action deleted successfully',
            'deleted_action': action_info
        }), 200
    except Exception as e:
        logger.error(f"Error deleting moderation action: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the moderation action'
        }), 500