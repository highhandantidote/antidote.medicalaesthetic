#!/usr/bin/env python3
"""
Import replies for community posts from CSV.
"""

import os
import csv
import psycopg2
from datetime import datetime

def main():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    print("Importing replies for community posts...")
    
    replies_created = 0
    
    with open("attached_assets/community_new - Sheet1.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, 1):
            with conn.cursor() as cur:
                # Get the community post ID (should match row number since we imported sequentially)
                cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id LIMIT 1 OFFSET %s", (row_num - 1,))
                result = cur.fetchone()
                
                if not result:
                    print(f"Could not find post for row {row_num}")
                    continue
                
                thread_id = result[0]
                
                # Import up to 4 replies per post
                reply_ids = {}
                thread_reply_count = 0
                
                for i in range(1, 5):  # replies 1-4
                    reply_content = row.get(f'reply_{i}_content', '').strip()
                    reply_username = row.get(f'reply_{i}_username', '').strip()
                    reply_email = row.get(f'reply_{i}_email', '').strip()
                    
                    if not reply_content or not reply_username or not reply_email:
                        continue
                    
                    # Get or create reply user
                    cur.execute("SELECT id FROM users WHERE email = %s", (reply_email,))
                    user_result = cur.fetchone()
                    
                    if user_result:
                        reply_user_id = user_result[0]
                    else:
                        # Create reply user
                        role = 'expert' if 'expert_' in reply_username else 'patient'
                        cur.execute("""
                            INSERT INTO users (username, email, name, role, is_verified, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (reply_username, reply_email, reply_username, role, True, datetime.now()))
                        reply_user_id = cur.fetchone()[0]
                    
                    # Parse reply date
                    try:
                        reply_date = datetime.strptime(row.get(f'reply_{i}_date', ''), '%Y-%m-%d')
                    except:
                        reply_date = datetime.now()
                    
                    # Check for parent reply
                    parent_reply_str = row.get(f'reply_{i}_parent_reply', '').strip()
                    parent_reply_id = None
                    if parent_reply_str and parent_reply_str.isdigit():
                        parent_reply_id = reply_ids.get(int(parent_reply_str))
                    
                    # Create reply
                    cur.execute("""
                        INSERT INTO community_replies (
                            thread_id, user_id, content, parent_reply_id,
                            is_anonymous, is_doctor_response, is_expert_advice, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        thread_id,
                        reply_user_id,
                        reply_content,
                        parent_reply_id,
                        row.get(f'reply_{i}_is_anonymous', '').upper() == 'TRUE',
                        row.get(f'reply_{i}_is_doctor', '').upper() == 'TRUE',
                        row.get(f'reply_{i}_is_expert', '').upper() == 'TRUE',
                        reply_date
                    ))
                    
                    reply_id = cur.fetchone()[0]
                    reply_ids[i] = reply_id
                    replies_created += 1
                    thread_reply_count += 1
                    
                    print(f"Created reply {i} for post {row_num} by {reply_username}")
                
                # Update reply count for the thread
                if thread_reply_count > 0:
                    cur.execute("UPDATE community SET reply_count = %s WHERE id = %s", 
                              (thread_reply_count, thread_id))
                
                conn.commit()
    
    # Final count
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community_replies")
        total_replies = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM community WHERE reply_count > 0")
        posts_with_replies = cur.fetchone()[0]
    
    print(f"=== REPLIES IMPORT COMPLETE ===")
    print(f"Total replies created: {replies_created}")
    print(f"Total replies in database: {total_replies}")
    print(f"Posts with replies: {posts_with_replies}")
    
    conn.close()

if __name__ == "__main__":
    main()