#!/usr/bin/env python3
"""
Cleanup script for test data.

This script removes all test data from the database, including:
- Doctor records
- Procedure records
- Community threads and replies
- Test users
- Notifications
"""
import logging
import sys
from app import create_app, db
from datetime import datetime

# Configure logging
LOG_FILE = f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def cleanup_test_data():
    """Remove all test data from the database."""
    logger.info("Starting cleanup of test data...")
    
    try:
        # Import models within the application context
        from models import Doctor, Procedure, Community, CommunityReply, User, Notification
        
        # Delete community replies first (due to foreign key constraints)
        reply_count = db.session.query(CommunityReply).delete()
        logger.info(f"Deleted {reply_count} community replies")
        
        # Delete community threads
        thread_count = db.session.query(Community).delete()
        logger.info(f"Deleted {thread_count} community threads")
        
        # Delete procedures
        procedure_count = db.session.query(Procedure).delete()
        logger.info(f"Deleted {procedure_count} procedures")
        
        # Delete notifications
        notification_count = db.session.query(Notification).delete()
        logger.info(f"Deleted {notification_count} notifications")
        
        # Delete test doctors
        doctor_count = db.session.query(Doctor).delete()
        logger.info(f"Deleted {doctor_count} doctors")
        
        # Delete test users
        test_user_count = db.session.query(User).filter(
            User.username.in_(['admin_test', 'doctor_test', 'doctor_test2'])
        ).delete(synchronize_session=False)
        logger.info(f"Deleted {test_user_count} test users")
        
        # Commit the changes
        db.session.commit()
        logger.info("Test data successfully removed")
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cleaning up test data: {str(e)}")
        return False

def main():
    """Run the cleanup script."""
    logger.info("Initializing cleanup script...")
    
    # Create the application context
    app = create_app()
    
    with app.app_context():
        success = cleanup_test_data()
    
    if success:
        logger.info("Cleanup completed successfully")
        return 0
    else:
        logger.error("Cleanup failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())