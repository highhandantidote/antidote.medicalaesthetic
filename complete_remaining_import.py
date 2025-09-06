#!/usr/bin/env python3
"""
Complete the remaining CSV import efficiently.
Process the remaining authentic discussions from your CSV file.
"""

import os
import csv
import psycopg2
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def complete_import():
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            # Get threads and current progress
            cursor.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
            thread_ids = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT COUNT(DISTINCT thread_id) FROM community_replies cr JOIN community c ON cr.thread_id = c.id WHERE c.source_type = 'manual'")
            completed_threads = cursor.fetchone()[0]
            
            logger.info(f"Continuing from thread {completed_threads + 1}")
            
            # Read CSV
            with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
                rows = list(csv.DictReader(file))
            
            total_added = 0
            
            # Process remaining rows starting from where we left off
            for i in range(completed_threads, min(len(rows), len(thread_ids))):
                row = rows[i]
                thread_id = thread_ids[i]
                
                logger.info(f"Processing row {i+1}/{len(rows)} for thread {thread_id}")
                
                # Skip if already has replies
                cursor.execute("SELECT COUNT(*) FROM community_replies WHERE thread_id = %s", (thread_id,))
                if cursor.fetchone()[0] > 0:
                    logger.info(f"  Thread {thread_id} already has replies, skipping")
                    continue
                
                replies_added = 0
                
                # Process replies for this row
                for reply_num in range(1, 9):
                    content = row.get(f'reply_{reply_num}_content', '').strip()
                    username = row.get(f'reply_{reply_num}_username', '').strip()
                    email = row.get(f'reply_{reply_num}_email', '').strip()
                    is_expert = row.get(f'reply_{reply_num}_is_expert', '').strip().upper() == 'TRUE'
                    
                    if not content or not username:
                        continue
                    
                    try:
                        # Get or create user
                        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                        user_result = cursor.fetchone()
                        
                        if not user_result:
                            if not email:
                                email = f"{username.lower()}@community.antidote.com"
                            role = 'expert' if is_expert or 'expert_' in username.lower() else 'patient'
                            
                            cursor.execute("""
                                INSERT INTO users (username, email, is_verified, created_at, role)
                                VALUES (%s, %s, TRUE, %s, %s) RETURNING id
                            """, (username, email, datetime.now(), role))
                            user_id = cursor.fetchone()[0]
                        else:
                            user_id = user_result[0]
                        
                        # Add reply
                        cursor.execute("""
                            INSERT INTO community_replies (thread_id, user_id, content, created_at, upvotes)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (thread_id, user_id, content, datetime.now(), 0))
                        
                        replies_added += 1
                        total_added += 1
                        
                    except Exception as e:
                        logger.error(f"    Error with reply {reply_num}: {str(e)}")
                        continue
                
                if replies_added > 0:
                    cursor.execute("UPDATE community SET reply_count = %s WHERE id = %s", (replies_added, thread_id))
                    logger.info(f"  ✅ Added {replies_added} replies to thread {thread_id}")
                
                conn.commit()
                
                # Process in smaller batches to avoid timeout
                if (i + 1) % 5 == 0:
                    logger.info(f"Completed batch ending at row {i+1}")
            
            # Final status
            cursor.execute("""
                SELECT COUNT(*) as total_replies, COUNT(DISTINCT thread_id) as posts_with_replies
                FROM community_replies cr JOIN community c ON cr.thread_id = c.id 
                WHERE c.source_type = 'manual'
            """)
            result = cursor.fetchone()
            logger.info(f"🎉 Import Progress: {result[0]} total replies across {result[1]} posts")
            logger.info(f"✅ Added {total_added} new authentic replies in this batch")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    complete_import()