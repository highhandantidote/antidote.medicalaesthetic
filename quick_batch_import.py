#!/usr/bin/env python3
"""
Quick batch import for remaining community replies.
Process in smaller batches to avoid timeouts.
"""

import os
import csv
import psycopg2
from datetime import datetime

def process_batch(start_post, batch_size):
    """Process a batch of posts."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Get thread IDs
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        thread_ids = [row[0] for row in cur.fetchall()]
    
    imported = 0
    
    with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
        end_post = min(start_post + batch_size, len(rows))
        print(f"Processing posts {start_post + 1} to {end_post}...")
        
        for post_idx in range(start_post, end_post):
            row = rows[post_idx]
            thread_id = thread_ids[post_idx]
            
            for reply_num in range(1, 9):
                content = row.get(f'reply_{reply_num}_content', '').strip()
                username = row.get(f'reply_{reply_num}_username', '').strip()
                email = row.get(f'reply_{reply_num}_email', '').strip()
                
                if not content or not username or not email:
                    continue
                
                # Quick check if reply exists
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 1 FROM community_replies cr
                        JOIN users u ON cr.user_id = u.id
                        WHERE cr.thread_id = %s AND u.username = %s AND cr.content = %s
                    """, (thread_id, username, content))
                    
                    if cur.fetchone():
                        continue
                
                # Get or create user
                is_expert = row.get(f'reply_{reply_num}_is_expert', 'FALSE').upper() == 'TRUE'
                is_doctor = row.get(f'reply_{reply_num}_is_doctor', 'FALSE').upper() == 'TRUE'
                is_anonymous = row.get(f'reply_{reply_num}_is_anonymous', 'FALSE').upper() == 'TRUE'
                
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                    user = cur.fetchone()
                    
                    if not user:
                        cur.execute("""
                            INSERT INTO users (username, email, password_hash, is_expert, is_doctor, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (username, email, 'hashed_password', is_expert, is_doctor, datetime.now()))
                        user_id = cur.fetchone()[0]
                    else:
                        user_id = user[0]
                
                # Insert reply
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO community_replies 
                        (thread_id, user_id, content, is_anonymous, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (thread_id, user_id, content, is_anonymous, datetime.now()))
                    imported += 1
        
        conn.commit()
    
    conn.close()
    return imported

def main():
    """Process all posts in batches."""
    total_imported = 0
    batch_size = 5
    
    for start in range(0, 34, batch_size):
        batch_imported = process_batch(start, batch_size)
        total_imported += batch_imported
        print(f"Batch imported {batch_imported} replies")
        
        if batch_imported == 0:
            break
    
    # Update reply counts
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE community SET reply_count = (
                SELECT COUNT(*) FROM community_replies 
                WHERE community_replies.thread_id = community.id
            ) WHERE source_type = 'manual'
        """)
        conn.commit()
        
        # Get statistics
        cur.execute("SELECT COUNT(*) FROM community_replies")
        total_replies = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM community WHERE source_type = 'manual' AND reply_count > 0")
        posts_with_replies = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n✅ Import complete!")
    print(f"New replies: {total_imported}")
    print(f"Total replies: {total_replies}")
    print(f"Posts with replies: {posts_with_replies}/34")

if __name__ == "__main__":
    main()