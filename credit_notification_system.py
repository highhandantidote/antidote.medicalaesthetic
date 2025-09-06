"""
Credit Transaction Notification System
Automatically creates notifications for clinics when credit transactions occur.
"""

import logging
from datetime import datetime, timezone
import pytz
from flask import current_app
from models import db, Notification, Clinic, User, CreditTransaction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CreditNotificationService:
    """Service class for managing credit transaction notifications."""
    
    @staticmethod
    def create_credit_notification(transaction_id, clinic_id, transaction_type, amount, description=None):
        """
        Create a notification for a credit transaction.
        
        Args:
            transaction_id: ID of the credit transaction
            clinic_id: ID of the clinic
            transaction_type: Type of transaction (manual_allocation, lead_deduction, etc.)
            amount: Transaction amount (positive or negative)
            description: Optional description
        """
        try:
            # Get clinic information
            clinic = Clinic.query.get(clinic_id)
            if not clinic:
                logger.error(f"Clinic not found: {clinic_id}")
                return False
            
            # Get clinic owner/admin user
            clinic_user = User.query.filter_by(email=clinic.email).first()
            if not clinic_user:
                logger.warning(f"No user found for clinic {clinic.name} with email {clinic.email}")
                # Create notification without user_id for now
                clinic_user = None
            
            # Create notification title and message based on transaction type
            title, message = CreditNotificationService._generate_notification_content(
                transaction_type, amount, clinic.name, description
            )
            
            # Get IST timezone
            ist_timezone = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(timezone.utc).astimezone(ist_timezone)
            
            # Create notification (combining title and message since model only has message field)
            full_message = f"{title}: {message}"
            notification = Notification(
                user_id=clinic_user.id if clinic_user else None,
                message=full_message,
                type='credit_transaction',
                is_read=False,
                created_at=current_time
            )
            
            db.session.add(notification)
            db.session.commit()
            
            logger.info(f"Credit notification created for clinic {clinic.name} (Transaction #{transaction_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error creating credit notification: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def _generate_notification_content(transaction_type, amount, clinic_name, description):
        """Generate notification title and message based on transaction details."""
        
        amount_str = f"{'+' if amount > 0 else ''}{amount:,}"
        
        if transaction_type == 'manual_allocation':
            title = "Credits Added to Your Account"
            message = f"Your clinic has received {amount_str} credits. Thank you for being part of Antidote!"
            
        elif transaction_type == 'admin_adjustment':
            if amount > 0:
                title = "Credit Adjustment - Credits Added"
                message = f"An admin adjustment has added {amount_str} credits to your account."
            else:
                title = "Credit Adjustment - Credits Deducted"
                message = f"An admin adjustment has deducted {abs(amount):,} credits from your account."
                
        elif transaction_type == 'lead_deduction':
            title = "Credits Used for Lead"
            message = f"{abs(amount):,} credits have been deducted for a new patient lead."
            
        elif transaction_type == 'purchase':
            title = "Credits Purchased"
            message = f"You have successfully purchased {amount_str} credits."
            
        elif transaction_type == 'bonus':
            title = "Bonus Credits Awarded"
            message = f"Congratulations! You've received {amount_str} bonus credits."
            
        elif transaction_type == 'refund':
            title = "Credit Refund Processed"
            message = f"A refund of {amount_str} credits has been processed to your account."
            
        else:
            title = "Credit Transaction"
            message = f"Your account has been updated with {amount_str} credits."
        
        # Add description if provided
        if description:
            message += f" Reason: {description}"
        
        return title, message
    
    @staticmethod
    def get_clinic_credit_notifications(clinic_id, limit=10):
        """Get recent credit notifications for a specific clinic."""
        try:
            # Get clinic user
            clinic = Clinic.query.get(clinic_id)
            if not clinic:
                return []
            
            clinic_user = User.query.filter_by(email=clinic.email).first()
            if not clinic_user:
                return []
            
            notifications = Notification.query.filter_by(
                user_id=clinic_user.id,
                type='credit_transaction'
            ).order_by(Notification.created_at.desc()).limit(limit).all()
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting clinic credit notifications: {str(e)}")
            return []
    
    @staticmethod
    def mark_notification_read(notification_id, user_id):
        """Mark a notification as read."""
        try:
            notification = Notification.query.filter_by(
                id=notification_id,
                user_id=user_id
            ).first()
            
            if notification:
                notification.is_read = True
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread credit notifications for a user."""
        try:
            count = Notification.query.filter_by(
                user_id=user_id,
                type='credit_transaction',
                is_read=False
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread notification count: {str(e)}")
            return 0

def create_notification_for_transaction(transaction_id):
    """
    Create a notification for an existing transaction.
    Used to backfill notifications for existing transactions.
    """
    try:
        transaction = CreditTransaction.query.get(transaction_id)
        if not transaction:
            logger.error(f"Transaction not found: {transaction_id}")
            return False
        
        return CreditNotificationService.create_credit_notification(
            transaction_id=transaction.id,
            clinic_id=transaction.clinic_id,
            transaction_type=transaction.transaction_type,
            amount=transaction.amount,
            description=transaction.description
        )
        
    except Exception as e:
        logger.error(f"Error creating notification for transaction {transaction_id}: {str(e)}")
        return False

def backfill_notifications_for_recent_transactions(days=30):
    """
    Create notifications for recent transactions that don't have them.
    
    Args:
        days: Number of days back to check for transactions
    """
    try:
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get recent transactions
        transactions = CreditTransaction.query.filter(
            CreditTransaction.created_at >= cutoff_date
        ).all()
        
        created_count = 0
        
        for transaction in transactions:
            # Check if notification already exists
            existing_notification = Notification.query.filter_by(
                type='credit_transaction'
            ).filter(
                Notification.metadata.contains({'transaction_id': transaction.id})
            ).first()
            
            if not existing_notification:
                success = create_notification_for_transaction(transaction.id)
                if success:
                    created_count += 1
        
        logger.info(f"Created {created_count} notifications for recent transactions")
        return created_count
        
    except Exception as e:
        logger.error(f"Error backfilling notifications: {str(e)}")
        return 0

if __name__ == "__main__":
    # Script to backfill notifications for recent transactions
    from app import create_app
    
    app = create_app()
    with app.app_context():
        print("Backfilling notifications for recent credit transactions...")
        count = backfill_notifications_for_recent_transactions(days=90)
        print(f"Created {count} notifications")