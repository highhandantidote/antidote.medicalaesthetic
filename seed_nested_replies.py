#!/usr/bin/env python3
"""
Script to seed nested replies for testing community functionality.
"""
import logging
from datetime import datetime, timedelta
from app import create_app, db
from models import Community, CommunityReply, User

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_nested_replies():
    """Create nested replies for testing."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check for existing threads
            thread = Community.query.first()
            if not thread:
                logger.error("No community threads found. Please create threads first.")
                return
            
            logger.info(f"Creating nested replies for thread: {thread.title} (ID: {thread.id})")
            
            # Get users 
            admin = User.query.filter_by(role="admin").first()
            doctor = User.query.filter_by(role="doctor").first()
            
            if not admin or not doctor:
                logger.error("Admin or doctor user not found.")
                return
            
            logger.info(f"Using admin user: {admin.username} and doctor user: {doctor.username}")
            
            # Create parent replies
            parent_replies = []
            for i in range(2):
                parent = CommunityReply.query.filter_by(
                    thread_id=thread.id,
                    content=f"Parent reply {i+1} for testing nested replies"
                ).first()
                
                if not parent:
                    parent = CommunityReply(
                        thread_id=thread.id,
                        user_id=admin.id if i % 2 == 0 else doctor.id,
                        content=f"Parent reply {i+1} for testing nested replies",
                        is_anonymous=False,
                        is_doctor_response=(i % 2 == 1),
                        created_at=datetime.utcnow() - timedelta(days=i),
                        upvotes=5 - i
                    )
                    db.session.add(parent)
                    db.session.commit()
                    logger.info(f"Created parent reply {i+1} with ID: {parent.id}")
                else:
                    logger.info(f"Parent reply {i+1} already exists with ID: {parent.id}")
                
                parent_replies.append(parent)
            
            # Create child replies (nested level 1)
            child_replies = []
            for i, parent in enumerate(parent_replies):
                for j in range(2):
                    child = CommunityReply.query.filter_by(
                        thread_id=thread.id,
                        parent_id=parent.id,
                        content=f"Child reply {j+1} to parent {i+1}"
                    ).first()
                    
                    if not child:
                        child = CommunityReply(
                            thread_id=thread.id,
                            parent_id=parent.id,
                            user_id=doctor.id if j % 2 == 0 else admin.id,
                            content=f"Child reply {j+1} to parent {i+1}",
                            is_anonymous=False,
                            is_doctor_response=(j % 2 == 0),
                            created_at=datetime.utcnow() - timedelta(hours=j),
                            upvotes=3 - j
                        )
                        db.session.add(child)
                        db.session.commit()
                        logger.info(f"Created child reply {j+1} to parent {i+1} with ID: {child.id}")
                    else:
                        logger.info(f"Child reply {j+1} to parent {i+1} already exists with ID: {child.id}")
                    
                    child_replies.append(child)
            
            # Create grandchild replies (nested level 2)
            for i, child in enumerate(child_replies):
                grandchild = CommunityReply.query.filter_by(
                    thread_id=thread.id,
                    parent_id=child.id,
                    content=f"Grandchild reply to child {i+1}"
                ).first()
                
                if not grandchild:
                    grandchild = CommunityReply(
                        thread_id=thread.id,
                        parent_id=child.id,
                        user_id=admin.id if i % 2 == 0 else doctor.id,
                        content=f"Grandchild reply to child {i+1}",
                        is_anonymous=False,
                        is_doctor_response=(i % 2 == 1),
                        created_at=datetime.utcnow() - timedelta(minutes=30*i),
                        upvotes=1
                    )
                    db.session.add(grandchild)
                    db.session.commit()
                    logger.info(f"Created grandchild reply to child {i+1} with ID: {grandchild.id}")
                else:
                    logger.info(f"Grandchild reply to child {i+1} already exists with ID: {grandchild.id}")
            
            # Update thread reply_count
            total_replies = CommunityReply.query.filter_by(thread_id=thread.id).count()
            thread.reply_count = total_replies
            db.session.commit()
            logger.info(f"Updated thread reply count to {total_replies}")
            
            logger.info("Nested replies created successfully!")
            
        except Exception as e:
            logger.error(f"Error creating nested replies: {e}")
            db.session.rollback()
            raise

def check_nesting():
    """Check the nesting structure of replies."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("\nChecking nested reply structure...")
            
            # Get first thread
            thread = Community.query.first()
            if not thread:
                logger.error("No community threads found.")
                return
            
            # Get top-level replies (no parent)
            top_replies = CommunityReply.query.filter_by(
                thread_id=thread.id,
                parent_id=None
            ).all()
            
            logger.info(f"Thread '{thread.title}' has {len(top_replies)} top-level replies")
            
            for i, reply in enumerate(top_replies):
                logger.info(f"Top Reply {i+1}: ID={reply.id}, Content='{reply.content[:30]}...'")
                
                # Get children
                children = CommunityReply.query.filter_by(
                    parent_id=reply.id
                ).all()
                
                logger.info(f"  Has {len(children)} children")
                
                for j, child in enumerate(children):
                    logger.info(f"    Child {j+1}: ID={child.id}, Content='{child.content[:30]}...'")
                    
                    # Get grandchildren
                    grandchildren = CommunityReply.query.filter_by(
                        parent_id=child.id
                    ).all()
                    
                    logger.info(f"      Has {len(grandchildren)} grandchildren")
                    
                    for k, grandchild in enumerate(grandchildren):
                        logger.info(f"        Grandchild {k+1}: ID={grandchild.id}, Content='{grandchild.content[:30]}...'")
            
            # Calculate maximum nesting depth
            max_depth = 1  # Start with top-level replies
            
            for reply in top_replies:
                children = CommunityReply.query.filter_by(parent_id=reply.id).all()
                if children:
                    max_depth = max(max_depth, 2)  # At least level 2
                    
                    for child in children:
                        grandchildren = CommunityReply.query.filter_by(parent_id=child.id).all()
                        if grandchildren:
                            max_depth = max(max_depth, 3)  # At least level 3
                            
                            for grandchild in grandchildren:
                                great_grandchildren = CommunityReply.query.filter_by(parent_id=grandchild.id).all()
                                if great_grandchildren:
                                    max_depth = max(max_depth, 4)  # At least level 4
            
            logger.info(f"\nMaximum nesting depth: {max_depth}")
            
        except Exception as e:
            logger.error(f"Error checking nesting structure: {e}")
            raise

def main():
    """Seed nested replies and check the structure."""
    logger.info("Starting nested replies seeding...")
    
    # Create nested replies
    create_nested_replies()
    
    # Check the nesting structure
    check_nesting()
    
    logger.info("\nNested replies seeding completed!")
    logger.info("\nTesting Instructions:")
    logger.info("1. Navigate to any community thread detail page")
    logger.info("2. Verify that the nested replies are displayed correctly")
    logger.info("3. Test replying to different levels of the nesting structure")

if __name__ == "__main__":
    main()