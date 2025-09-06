#!/usr/bin/env python3
"""
Complete the CSV import for all community post replies.
This script will import all remaining authentic discussion data from the CSV file.
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
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def import_all_csv_replies():
    """Import all remaining authentic replies from the CSV file."""
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            # Get all community post IDs
            cursor.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
            thread_ids = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found {len(thread_ids)} community posts to process")
            
            # Read the CSV file
            csv_file_path = 'attached_assets/community_new - Sheet1.csv'
            if not os.path.exists(csv_file_path):
                logger.error(f"CSV file not found: {csv_file_path}")
                return
                
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                rows = list(csv.DictReader(file))
                logger.info(f"Found {len(rows)} rows in CSV file")
            
            total_added = 0
            posts_processed = 0
            
            # Process each post
            for i, thread_id in enumerate(thread_ids, 1):
                logger.info(f"Processing post {i}/{len(thread_ids)} (ID: {thread_id})")
                
                # Clear existing replies for this post to avoid duplicates
                cursor.execute("DELETE FROM community_replies WHERE thread_id = %s", (thread_id,))
                
                # Find replies for this post in CSV
                post_replies = []
                for row in rows:
                    if row.get('Post') and str(i) in row['Post']:
                        if row.get('Reply') and row['Reply'].strip():
                            post_replies.append(row)
                
                if not post_replies:
                    logger.info(f"  No replies found for post {i}")
                    continue
                
                logger.info(f"  Found {len(post_replies)} replies for post {i}")
                replies_added_for_post = 0
                
                # Import replies for this post
                for reply_row in post_replies:
                    try:
                        username = reply_row.get('Username', '').strip()
                        content = reply_row.get('Reply', '').strip()
                        
                        if not username or not content:
                            continue
                            
                        # Create or get user
                        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                        user_result = cursor.fetchone()
                        
                        if not user_result:
                            # Create new user
                            email = f"{username.lower()}@community.antidote.com"
                            cursor.execute("""
                                INSERT INTO users (username, email, is_verified, created_at, role)
                                VALUES (%s, %s, TRUE, %s, %s)
                                RETURNING id
                            """, (username, email, datetime.now(), 
                                 'expert' if 'expert_' in username.lower() else 'patient'))
                            user_id = cursor.fetchone()[0]
                            logger.info(f"    Created user: {username}")
                        else:
                            user_id = user_result[0]
                        
                        # Add the reply
                        cursor.execute("""
                            INSERT INTO community_replies (thread_id, user_id, content, created_at, upvotes)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (thread_id, user_id, content, datetime.now(), 0))
                        
                        replies_added_for_post += 1
                        total_added += 1
                        
                    except Exception as e:
                        logger.error(f"    Error adding reply: {str(e)}")
                        continue
                
                if replies_added_for_post > 0:
                    # Update reply count for the post
                    cursor.execute("""
                        UPDATE community SET reply_count = %s WHERE id = %s
                    """, (replies_added_for_post, thread_id))
                    posts_processed += 1
                    logger.info(f"  ✅ Added {replies_added_for_post} replies to post {i}")
                
                # Commit after each post to avoid losing progress
                conn.commit()
            
            logger.info(f"\n🎉 CSV Import Complete!")
            logger.info(f"✅ Posts processed: {posts_processed}")
            logger.info(f"✅ Total replies imported: {total_added}")
            
            # Final status check
            cursor.execute("""
                SELECT COUNT(*) as total_replies, 
                       COUNT(DISTINCT thread_id) as posts_with_replies,
                       ROUND(AVG(reply_count), 1) as avg_replies_per_post
                FROM community_replies cr 
                JOIN community c ON cr.thread_id = c.id 
                WHERE c.source_type = 'manual'
            """)
            result = cursor.fetchone()
            if result:
                logger.info(f"📊 Final Status:")
                logger.info(f"   Total authentic replies: {result[0]}")
                logger.info(f"   Posts with discussions: {result[1]}")
                logger.info(f"   Average replies per post: {result[2]}")
            
    except Exception as e:
        logger.error(f"Error during import: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    import_all_csv_replies()