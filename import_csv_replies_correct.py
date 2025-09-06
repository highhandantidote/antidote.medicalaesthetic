#!/usr/bin/env python3
"""
Import all CSV replies using the correct column structure.
This script processes the authentic community discussions from your CSV file.
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

def import_csv_replies():
    """Import all authentic replies from the CSV file."""
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            # Get all community post IDs
            cursor.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
            thread_ids = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found {len(thread_ids)} community posts to process")
            
            # Read the CSV file
            csv_file_path = 'attached_assets/community_new - Sheet1.csv'
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                logger.info(f"Found {len(rows)} rows in CSV file")
            
            total_added = 0
            posts_processed = 0
            
            # Process each row in CSV
            for i, row in enumerate(rows, 1):
                if i > len(thread_ids):
                    logger.info(f"Skipping row {i} - no corresponding thread")
                    continue
                    
                thread_id = thread_ids[i-1]  # CSV row 1 maps to first thread
                logger.info(f"Processing CSV row {i} for thread {thread_id}")
                
                # Clear existing replies for this thread
                cursor.execute("DELETE FROM community_replies WHERE thread_id = %s", (thread_id,))
                
                replies_added = 0
                
                # Process up to 8 replies per row
                for reply_num in range(1, 9):
                    content_col = f'reply_{reply_num}_content'
                    username_col = f'reply_{reply_num}_username'
                    email_col = f'reply_{reply_num}_email'
                    is_expert_col = f'reply_{reply_num}_is_expert'
                    
                    content = row.get(content_col, '').strip()
                    username = row.get(username_col, '').strip()
                    email = row.get(email_col, '').strip()
                    is_expert = row.get(is_expert_col, '').strip().upper() == 'TRUE'
                    
                    if not content or not username:
                        continue  # Skip empty replies
                    
                    try:
                        # Create or get user
                        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                        user_result = cursor.fetchone()
                        
                        if not user_result:
                            # Create new user
                            if not email:
                                email = f"{username.lower()}@community.antidote.com"
                            
                            role = 'expert' if is_expert or 'expert_' in username.lower() else 'patient'
                            
                            cursor.execute("""
                                INSERT INTO users (username, email, is_verified, created_at, role)
                                VALUES (%s, %s, TRUE, %s, %s)
                                RETURNING id
                            """, (username, email, datetime.now(), role))
                            user_id = cursor.fetchone()[0]
                            logger.info(f"    Created user: {username} ({role})")
                        else:
                            user_id = user_result[0]
                        
                        # Add the reply
                        cursor.execute("""
                            INSERT INTO community_replies (thread_id, user_id, content, created_at, upvotes)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (thread_id, user_id, content, datetime.now(), 0))
                        
                        replies_added += 1
                        total_added += 1
                        logger.info(f"    Added reply {reply_num} from {username}")
                        
                    except Exception as e:
                        logger.error(f"    Error adding reply {reply_num}: {str(e)}")
                        continue
                
                if replies_added > 0:
                    # Update reply count for the thread
                    cursor.execute("""
                        UPDATE community SET reply_count = %s WHERE id = %s
                    """, (replies_added, thread_id))
                    posts_processed += 1
                    logger.info(f"  ✅ Added {replies_added} authentic replies to thread {thread_id}")
                
                # Commit after each post
                conn.commit()
            
            logger.info(f"\n🎉 CSV Import Complete!")
            logger.info(f"✅ Posts processed: {posts_processed}")
            logger.info(f"✅ Total authentic replies imported: {total_added}")
            
            # Final status check
            cursor.execute("""
                SELECT COUNT(*) as total_replies, 
                       COUNT(DISTINCT thread_id) as posts_with_replies,
                       ROUND(AVG(reply_count), 1) as avg_replies_per_post,
                       MAX(reply_count) as max_replies_per_post
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
                logger.info(f"   Max replies on one post: {result[3]}")
            
    except Exception as e:
        logger.error(f"Error during import: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    import_csv_replies()