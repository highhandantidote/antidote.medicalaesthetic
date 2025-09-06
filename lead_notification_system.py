"""
Lead Notification System
Provides immediate notifications to clinics when new leads are generated.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import text
from models import db
import logging
from datetime import datetime

notification_bp = Blueprint('notifications', __name__)
logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing lead notifications."""
    
    @staticmethod
    def send_lead_notification(clinic_id, lead_data):
        """Send immediate notification about new lead."""
        try:
            # Create in-app notification
            db.session.execute(text("""
                INSERT INTO notifications 
                (clinic_id, type, title, message, is_read, created_at)
                VALUES (:clinic_id, 'new_lead', :title, :message, false, :created_at)
            """), {
                "clinic_id": clinic_id,
                "title": f"New Lead: {lead_data.get('procedure_name', 'Unknown Procedure')}",
                "message": f"New lead from {lead_data.get('user_name')} for {lead_data.get('procedure_name')}. Credit cost: {lead_data.get('credit_cost', 0)} credits.",
                "created_at": datetime.utcnow()
            })
            
            db.session.commit()
            logger.info(f"Notification sent to clinic {clinic_id} for new lead")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_clinic_notifications(clinic_id, limit=20):
        """Get recent notifications for a clinic."""
        try:
            result = db.session.execute(text("""
                SELECT * FROM notifications 
                WHERE clinic_id = :clinic_id 
                ORDER BY created_at DESC 
                LIMIT :limit
            """), {"clinic_id": clinic_id, "limit": limit})
            
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching notifications: {e}")
            return []
    
    @staticmethod
    def mark_notification_read(notification_id, clinic_id):
        """Mark a notification as read."""
        try:
            db.session.execute(text("""
                UPDATE notifications 
                SET is_read = true 
                WHERE id = :notification_id AND clinic_id = :clinic_id
            """), {"notification_id": notification_id, "clinic_id": clinic_id})
            
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            db.session.rollback()
            return False

@notification_bp.route('/api/notifications/clinic')
@login_required
def get_notifications():
    """Get notifications for current clinic."""
    try:
        # Get clinic
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'}), 404
        
        clinic_id = clinic_result.id
        notifications = NotificationService.get_clinic_notifications(clinic_id)
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'unread_count': len([n for n in notifications if not n.get('is_read', False)])
        })
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'success': False, 'message': 'Error fetching notifications'}), 500

@notification_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark notification as read."""
    try:
        # Get clinic
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'}), 404
        
        clinic_id = clinic_result.id
        success = NotificationService.mark_notification_read(notification_id, clinic_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Notification marked as read'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update notification'}), 500
            
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return jsonify({'success': False, 'message': 'Error updating notification'}), 500