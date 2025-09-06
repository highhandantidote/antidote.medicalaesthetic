#!/usr/bin/env python3
"""
Complete CSV Replies Import - Final Script
Import ALL remaining replies from the CSV file to complete the community data.
"""

import os
import csv
import psycopg2
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database."""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def get_or_create_user(conn, username, email, is_doctor=False, is_expert=False):
    """Get or create a user account."""
    try:
        with conn.cursor() as cur:
            # Check if user exists
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            result = cur.fetchone()
            
            if result:
                return result[0]
            
            # Create new user
            role = 'doctor' if is_doctor else 'patient'
            cur.execute("""
                INSERT INTO users (username, email, name, role, is_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (username, email, username, role, True, datetime.now()))
            
            user_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Created user: {username} ({email})")
            return user_id
            
    except Exception as e:
        logger.error(f"Error creating user {username}: {str(e)}")
        conn.rollback()
        return None

def reply_exists(conn, thread_id, content, username):
    """Check if a reply already exists to avoid duplicates."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cr.id FROM community_replies cr
                JOIN users u ON cr.user_id = u.id
                WHERE cr.thread_id = %s AND cr.content = %s AND u.username = %s
            """, (thread_id, content, username))
            return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking reply existence: {str(e)}")
        return False

def import_replies_for_post(conn, row, thread_id, post_index):
    """Import all replies for a single post."""
    reply_ids = {}  # Store reply IDs for nested replies
    replies_imported = 0
    
    try:
        # Process replies 1-8
        for i in range(1, 9):
            reply_prefix = f'reply_{i}_'
            
            # Get reply data
            content = row.get(f'{reply_prefix}content', '').strip()
            username = row.get(f'{reply_prefix}username', '').strip()
            email = row.get(f'{reply_prefix}email', '').strip()
            is_doctor = row.get(f'{reply_prefix}is_doctor', 'FALSE').upper() == 'TRUE'
            is_expert = row.get(f'{reply_prefix}is_expert', 'FALSE').upper() == 'TRUE'
            is_anonymous = row.get(f'{reply_prefix}is_anonymous', 'FALSE').upper() == 'TRUE'
            reply_date = row.get(f'{reply_prefix}date', '').strip()
            parent_reply = row.get(f'{reply_prefix}parent_reply', '').strip()
            
            # Skip if no content or essential data missing
            if not content or not username or not email:
                continue
            
            # Check if reply already exists
            if reply_exists(conn, thread_id, content, username):
                logger.info(f"Reply {i} for post {post_index} already exists, skipping")
                continue
            
            # Get or create user
            user_id = get_or_create_user(conn, username, email, is_doctor, is_expert)
            if not user_id:
                logger.error(f"Failed to create user for reply {i} in post {post_index}")
                continue
            
            # Parse date
            created_at = datetime.now()
            if reply_date:
                try:
                    created_at = datetime.strptime(reply_date, '%Y-%m-%d')
                except:
                    pass
            
            # Handle parent reply
            parent_reply_id = None
            if parent_reply and parent_reply.isdigit():
                parent_reply_num = int(parent_reply)
                if parent_reply_num in reply_ids:
                    parent_reply_id = reply_ids[parent_reply_num]
            
            # Insert reply
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO community_replies 
                    (thread_id, user_id, content, is_anonymous, parent_reply_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (thread_id, user_id, content, is_anonymous, parent_reply_id, created_at))
                
                reply_id = cur.fetchone()[0]
                reply_ids[i] = reply_id
                replies_imported += 1
                
                logger.info(f"Imported reply {i} for post {post_index}: {username}")
        
        conn.commit()
        return replies_imported
        
    except Exception as e:
        logger.error(f"Error importing replies for post {post_index}: {str(e)}")
        conn.rollback()
        return 0

def update_reply_counts(conn):
    """Update reply counts for all community posts."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE community SET reply_count = (
                    SELECT COUNT(*) FROM community_replies 
                    WHERE community_replies.thread_id = community.id
                ) WHERE source_type = 'manual'
            """)
            conn.commit()
            logger.info("Updated reply counts for all posts")
    except Exception as e:
        logger.error(f"Error updating reply counts: {str(e)}")
        conn.rollback()

def main():
    """Main function to import all replies."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return
    
    # Check current status
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community WHERE source_type = 'manual'")
        result = cur.fetchone()
        total_posts = result[0] if result else 0
        
        cur.execute("SELECT COUNT(*) FROM community_replies")
        result = cur.fetchone()
        current_replies = result[0] if result else 0
    
    logger.info(f"Starting import - {total_posts} posts, {current_replies} current replies")
    
    # Get all thread IDs in order
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        results = cur.fetchall()
        thread_ids = [row[0] for row in results] if results else []
    
    total_replies_imported = 0
    
    # Import replies from CSV
    try:
        with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for post_index, row in enumerate(csv_reader, 1):
                if post_index > len(thread_ids):
                    logger.warning(f"More CSV rows than database posts, stopping at row {post_index}")
                    break
                
                thread_id = thread_ids[post_index - 1]
                logger.info(f"Processing replies for post {post_index} (thread_id: {thread_id})")
                
                replies_imported = import_replies_for_post(conn, row, thread_id, post_index)
                total_replies_imported += replies_imported
                
                # Commit after each post to save progress
                if post_index % 5 == 0:
                    logger.info(f"Processed {post_index} posts, imported {total_replies_imported} replies so far")
    
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        return
    
    # Update reply counts
    update_reply_counts(conn)
    
    # Final verification
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community_replies")
        result = cur.fetchone()
        final_replies = result[0] if result else 0
        
        cur.execute("SELECT COUNT(*) FROM community WHERE reply_count > 0")
        result = cur.fetchone()
        posts_with_replies = result[0] if result else 0
        
        cur.execute("SELECT AVG(reply_count) FROM community WHERE source_type = 'manual'")
        result = cur.fetchone()
        avg_replies = result[0] if result else 0
    
    logger.info(f"\n=== IMPORT COMPLETE ===")
    logger.info(f"Replies before import: {current_replies}")
    logger.info(f"Replies after import: {final_replies}")
    logger.info(f"New replies imported: {final_replies - current_replies}")
    logger.info(f"Posts with replies: {posts_with_replies}")
    logger.info(f"Average replies per post: {avg_replies:.1f}")
    
    conn.close()

if __name__ == "__main__":
    main()