from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import or_, and_, func
from models import User, Message
from app import db
from datetime import datetime
import logging

# Create logger
logger = logging.getLogger(__name__)

# Create Blueprint for messaging API routes
message_api = Blueprint('message_api', __name__, url_prefix='/api/messages')

@message_api.route('', methods=['GET'])
def get_messages():
    """
    Get messages for a user.
    
    Query parameters:
    - user_id: The ID of the current user (required)
    - conversation_with: User ID to get a specific conversation
    - page: Page number for pagination
    - limit: Number of results per page
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', type=int)
        conversation_with = request.args.get('conversation_with', type=int)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        
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
        
        # If conversation_with is provided, get messages between these two users
        if conversation_with:
            # Verify other user exists
            other_user = User.query.get(conversation_with)
            if not other_user:
                return jsonify({
                    'success': False,
                    'message': 'Conversation partner not found'
                }), 404
            
            # Get conversation between these two users
            query = Message.query.filter(
                or_(
                    and_(Message.sender_id == user_id, Message.receiver_id == conversation_with),
                    and_(Message.sender_id == conversation_with, Message.receiver_id == user_id)
                )
            ).order_by(Message.created_at.desc())
            
            # Mark messages as read
            unread_messages = Message.query.filter_by(
                sender_id=conversation_with,
                receiver_id=user_id,
                is_read=False
            ).all()
            
            for message in unread_messages:
                message.is_read = True
            
            db.session.commit()
            
            # Apply pagination
            total = query.count()
            messages = query.offset((page - 1) * limit).limit(limit).all()
            
            # Format messages
            formatted_messages = []
            for message in messages:
                formatted_messages.append({
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender_id,
                    'receiver_id': message.receiver_id,
                    'is_read': message.is_read,
                    'created_at': message.created_at.isoformat() if message.created_at else None,
                    'is_from_user': message.sender_id == user_id
                })
            
            # Reverse to show oldest first
            formatted_messages.reverse()
            
            return jsonify({
                'success': True,
                'data': {
                    'messages': formatted_messages,
                    'conversation_with': {
                        'id': other_user.id,
                        'name': other_user.name,
                        'username': other_user.username
                    },
                    'pagination': {
                        'total': total,
                        'page': page,
                        'limit': limit,
                        'pages': (total + limit - 1) // limit
                    }
                }
            }), 200
        else:
            # Get list of conversations for this user
            # This query gets the most recent message for each conversation
            conversations = db.session.query(
                func.max(Message.id).label('latest_message_id'),
                func.min(
                    func.case(
                        [(Message.sender_id == user_id, Message.receiver_id)],
                        else_=Message.sender_id
                    )
                ).label('conversation_partner_id')
            ).filter(
                or_(
                    Message.sender_id == user_id,
                    Message.receiver_id == user_id
                )
            ).group_by(
                func.case(
                    [(Message.sender_id == user_id, Message.receiver_id)],
                    else_=Message.sender_id
                )
            ).all()
            
            # Get the actual message and partner info for each conversation
            conversation_list = []
            for conv in conversations:
                latest_message = Message.query.get(conv.latest_message_id)
                partner = User.query.get(conv.conversation_partner_id)
                
                if latest_message and partner:
                    # Count unread messages
                    unread_count = Message.query.filter_by(
                        sender_id=partner.id,
                        receiver_id=user_id,
                        is_read=False
                    ).count()
                    
                    conversation_list.append({
                        'conversation_partner': {
                            'id': partner.id,
                            'name': partner.name,
                            'username': partner.username
                        },
                        'latest_message': {
                            'id': latest_message.id,
                            'content': latest_message.content,
                            'is_read': latest_message.is_read,
                            'created_at': latest_message.created_at.isoformat() if latest_message.created_at else None,
                            'is_from_user': latest_message.sender_id == user_id
                        },
                        'unread_count': unread_count
                    })
            
            # Sort by latest message time
            conversation_list.sort(
                key=lambda x: x['latest_message']['created_at'],
                reverse=True
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'conversations': conversation_list
                }
            }), 200
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching messages'
        }), 500

@message_api.route('', methods=['POST'])
def send_message():
    """Send a new message."""
    try:
        data = request.json
        required_fields = ['sender_id', 'receiver_id', 'content']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Verify sender exists
        sender = User.query.get(data['sender_id'])
        if not sender:
            return jsonify({
                'success': False,
                'message': 'Sender not found'
            }), 404
        
        # Verify receiver exists
        receiver = User.query.get(data['receiver_id'])
        if not receiver:
            return jsonify({
                'success': False,
                'message': 'Receiver not found'
            }), 404
        
        # Prevent sending message to self
        if data['sender_id'] == data['receiver_id']:
            return jsonify({
                'success': False,
                'message': 'Cannot send message to yourself'
            }), 400
        
        # Create new message
        new_message = Message(
            sender_id=data['sender_id'],
            receiver_id=data['receiver_id'],
            content=data['content'],
            is_read=False,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': new_message.id,
                'content': new_message.content,
                'sender_id': new_message.sender_id,
                'receiver_id': new_message.receiver_id,
                'is_read': new_message.is_read,
                'created_at': new_message.created_at.isoformat() if new_message.created_at else None,
                'message': 'Message sent successfully'
            }
        }), 201
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while sending the message'
        }), 500

@message_api.route('/unread-count', methods=['GET'])
def get_unread_count():
    """Get count of unread messages for a user."""
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
        
        # Count unread messages
        unread_count = Message.query.filter_by(
            receiver_id=user_id,
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

@message_api.route('/mark-read', methods=['POST'])
def mark_messages_read():
    """Mark messages as read."""
    try:
        data = request.json
        
        if not data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
        
        user_id = data['user_id']
        sender_id = data.get('sender_id')  # Optional
        message_id = data.get('message_id')  # Optional
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Different marking logic based on provided params
        if message_id:
            # Mark specific message as read
            message = Message.query.get(message_id)
            if not message:
                return jsonify({
                    'success': False,
                    'message': 'Message not found'
                }), 404
                
            if message.receiver_id != user_id:
                return jsonify({
                    'success': False,
                    'message': 'Cannot mark message as read if not the receiver'
                }), 403
                
            message.is_read = True
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Message marked as read'
            }), 200
        elif sender_id:
            # Mark all messages from sender as read
            messages = Message.query.filter_by(
                sender_id=sender_id,
                receiver_id=user_id,
                is_read=False
            ).all()
            
            for message in messages:
                message.is_read = True
                
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'All messages from user {sender_id} marked as read'
            }), 200
        else:
            # Mark all messages as read
            messages = Message.query.filter_by(
                receiver_id=user_id,
                is_read=False
            ).all()
            
            for message in messages:
                message.is_read = True
                
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'All messages marked as read'
            }), 200
    except Exception as e:
        logger.error(f"Error marking messages as read: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while marking messages as read'
        }), 500
        
@message_api.route('/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a specific message."""
    try:
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({
                'success': False,
                'message': 'Message not found'
            }), 404
        
        # Check if user is authorized to delete this message
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
            
        # Users can only delete messages they sent or received
        if message.sender_id != user_id and message.receiver_id != user_id:
            return jsonify({
                'success': False,
                'message': 'Not authorized to delete this message'
            }), 403
        
        # Store message info for response
        message_info = {
            'id': message.id,
            'sender_id': message.sender_id,
            'receiver_id': message.receiver_id,
            'sent_at': message.sent_at.isoformat() if message.sent_at else None
        }
        
        # Delete the message
        db.session.delete(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message deleted successfully',
            'deleted_message': message_info
        }), 200
    except Exception as e:
        logger.error(f"Error deleting message: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the message'
        }), 500