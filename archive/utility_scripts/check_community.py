"""
Script to validate community thread and nested replies functionality.
"""
from models import Community, CommunityReply
from app import db, create_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask application
app = create_app()

def format_reply_log(reply, depth=0):
    """Format a reply for display in logs with proper indentation."""
    indent = "  " * depth
    return f"{indent}Reply {reply.id}: {reply.content[:30]}... (parent_id: {reply.parent_id})"

def check_thread_replies(thread_id):
    """Check and log the nested replies for a thread."""
    logger.info(f"Checking thread {thread_id}")
    
    # Get the thread
    thread = Community.query.get(thread_id)
    if not thread:
        logger.error(f"Thread {thread_id} not found!")
        return
    
    logger.info(f"Thread: {thread.title}")
    logger.info(f"Content: {thread.content[:100]}...")
    
    # Get all replies
    replies = CommunityReply.query.filter_by(thread_id=thread_id).all()
    logger.info(f"Total replies: {len(replies)}")
    
    # Create a map for lookup
    reply_map = {reply.id: reply for reply in replies}
    
    # Identify top-level replies
    top_level_replies = [r for r in replies if r.parent_id is None]
    logger.info(f"Top-level replies: {len(top_level_replies)}")
    
    # Build and log reply tree
    for reply in top_level_replies:
        logger.info(format_reply_log(reply))
        log_children(reply, reply_map, depth=1)
    
def log_children(reply, reply_map, depth=1):
    """Recursively log children of a reply."""
    children = [r for r in reply_map.values() if r.parent_id == reply.id]
    for child in children:
        logger.info(format_reply_log(child, depth))
        log_children(child, reply_map, depth+1)

def count_reply_depth(reply_id, reply_map):
    """Calculate the maximum depth of a reply tree."""
    reply = reply_map.get(reply_id)
    if not reply:
        return 0
    
    children = [r for r in reply_map.values() if r.parent_id == reply.id]
    if not children:
        return 1
    
    return 1 + max(count_reply_depth(child.id, reply_map) for child in children)

def check_max_depth(thread_id):
    """Check the maximum depth of replies in a thread."""
    replies = CommunityReply.query.filter_by(thread_id=thread_id).all()
    reply_map = {reply.id: reply for reply in replies}
    
    # Get top-level replies
    top_level_replies = [r for r in replies if r.parent_id is None]
    
    max_depths = []
    for reply in top_level_replies:
        max_depth = count_reply_depth(reply.id, reply_map)
        max_depths.append(max_depth)
        logger.info(f"Reply {reply.id} max depth: {max_depth}")
    
    if max_depths:
        overall_max = max(max_depths)
        logger.info(f"Overall maximum depth: {overall_max}")
        return overall_max
    return 0

if __name__ == "__main__":
    # Check thread 3 (the one mentioned in requirements)
    thread_id = 3
    
    # Use app context for database operations
    with app.app_context():
        check_thread_replies(thread_id)
        max_depth = check_max_depth(thread_id)
        
        if max_depth >= 5:
            logger.info("✅ Thread has 5 or more levels of nested replies as required")
        else:
            logger.warning(f"⚠️ Thread only has {max_depth} levels of nesting, requirement is 5 levels")