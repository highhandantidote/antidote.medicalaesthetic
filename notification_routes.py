from flask import Blueprint, request, jsonify, current_app
from models import User, Notification
from app import db
from datetime import datetime
import logging

# Create logger
logger = logging.getLogger(__name__)

# Create Blueprint for notification API routes
notification_api = Blueprint('notification_api', __name__, url_prefix='/api/notifications')

@notification_api.route('', methods=['GET'])
def get_notifications():
    """
    Get notifications for a user.
    
    Query parameters:
    - user_id: The ID of the user (required)
    - type: Filter by notification type
    - is_read: Filter by read status (true/false)
    - page: Page number for pagination
    - limit: Number of results per page
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', type=int)
        notification_type = request.args.get('type')
        is_read = request.args.get('is_read')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Build query
        query = Notification.query.filter_by(user_id=user_id)
        
        if notification_type:
            query = query.filter_by(type=notification_type)
        
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            query = query.filter_by(is_read=is_read_bool)
        
        # Apply sorting (newest first)
        query = query.order_by(Notification.created_at.desc())
        
        # Apply pagination
        total = query.count()
        notifications = query.offset((page - 1) * limit).limit(limit).all()
        
        # Format notification data
        formatted_notifications = []
        for notification in notifications:
            formatted_notifications.append({
                'id': notification.id,
                'message': notification.message,
                'type': notification.type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat() if notification.created_at else None,
                'mentioned_username': notification.mentioned_username,
                'response_type': notification.response_type
            })
        
        return jsonify({
            'success': True,
            'data': {
                'notifications': formatted_notifications,
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': (total + limit - 1) // limit
                }
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching notifications'
        }), 500

@notification_api.route('', methods=['POST'])
def create_notification():
    """Create a new notification."""
    try:
        data = request.json
        required_fields = ['user_id', 'message', 'type']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Verify user exists
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Create new notification
        new_notification = Notification(
            user_id=data['user_id'],
            message=data['message'],
            type=data['type'],
            is_read=False,
            created_at=datetime.utcnow(),
            mentioned_username=data.get('mentioned_username'),
            response_type=data.get('response_type')
        )
        
        db.session.add(new_notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': new_notification.id,
                'message': 'Notification created successfully'
            }
        }), 201
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while creating the notification'
        }), 500

@notification_api.route('/unread-count', methods=['GET'])
def get_unread_count():
    """Get count of unread notifications for a user."""
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Count unread notifications
        unread_count = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'unread_count': unread_count
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching unread count'
        }), 500

@notification_api.route('/mark-read', methods=['POST'])
def mark_notifications_read():
    """Mark notifications as read."""
    try:
        data = request.json
        
        if not data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
        
        user_id = data['user_id']
        notification_id = data.get('notification_id')  # Optional
        notification_type = data.get('type')  # Optional
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Different marking logic based on provided params
        if notification_id:
            # Mark specific notification as read
            notification = Notification.query.get(notification_id)
            if not notification:
                return jsonify({
                    'success': False,
                    'message': 'Notification not found'
                }), 404
                
            if notification.user_id != user_id:
                return jsonify({
                    'success': False,
                    'message': 'Cannot mark notification as read if not the recipient'
                }), 403
                
            notification.is_read = True
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            }), 200
        elif notification_type:
            # Mark all notifications of a specific type as read
            notifications = Notification.query.filter_by(
                user_id=user_id,
                type=notification_type,
                is_read=False
            ).all()
            
            for notification in notifications:
                notification.is_read = True
                
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'All notifications of type {notification_type} marked as read'
            }), 200
        else:
            # Mark all notifications as read
            notifications = Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).all()
            
            for notification in notifications:
                notification.is_read = True
                
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'All notifications marked as read'
            }), 200
    except Exception as e:
        logger.error(f"Error marking notifications as read: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while marking notifications as read'
        }), 500
        
@notification_api.route('/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a specific notification."""
    try:
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return jsonify({
                'success': False,
                'message': 'Notification not found'
            }), 404
        
        # Store notification info for response
        notification_info = {
            'id': notification.id,
            'type': notification.type,
            'created_at': notification.created_at.isoformat() if notification.created_at else None
        }
        
        # Delete the notification
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification deleted successfully',
            'deleted_notification': notification_info
        }), 200
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the notification'
        }), 500