#!/usr/bin/env python3
"""
Complete CSV import in small batches to avoid timeouts.
Import all authentic reply data from community_new - Sheet1.csv
"""

import os
import csv
import psycopg2
from datetime import datetime

def import_csv_batch(start_post, end_post):
    """Import a batch of posts from CSV."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Get thread IDs
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        thread_ids = [row[0] for row in cur.fetchall()]
    
    # Read CSV
    with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    
    imported = 0
    
    # Process the specified batch
    for post_idx in range(start_post, min(end_post, len(rows), len(thread_ids))):
        row = rows[post_idx]
        thread_id = thread_ids[post_idx]
        
        print(f"Processing post {post_idx + 1}: {row['title'][:30]}...")
        
        # Import all replies for this post
        for reply_num in range(1, 9):  # Up to 8 replies per post
            content = row.get(f'reply_{reply_num}_content', '').strip()
            username = row.get(f'reply_{reply_num}_username', '').strip() 
            email = row.get(f'reply_{reply_num}_email', '').strip()
            
            if not content or not username or not email:
                continue
            
            # Check if this exact reply already exists
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM community_replies cr 
                    JOIN users u ON cr.user_id = u.id
                    WHERE cr.thread_id = %s AND u.username = %s AND cr.content = %s
                """, (thread_id, username, content))
                
                if cur.fetchone():
                    continue  # Skip if exists
            
            # Get user details
            is_expert = row.get(f'reply_{reply_num}_is_expert', 'FALSE').upper() == 'TRUE'
            is_doctor = row.get(f'reply_{reply_num}_is_doctor', 'FALSE').upper() == 'TRUE'
            
            # Get or create user
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                
                if not user:
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash, is_expert, is_doctor, created_at)
                        VALUES (%s, %s, 'hash', %s, %s, %s) RETURNING id
                    """, (username, email, is_expert, is_doctor, datetime.now()))
                    user_id = cur.fetchone()[0]
                else:
                    user_id = user[0]
            
            # Insert reply
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO community_replies (thread_id, user_id, content, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (thread_id, user_id, content, datetime.now()))
                imported += 1
                
            print(f"  ✅ {username}")
    
    # Update reply counts for processed posts
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE community SET reply_count = (
                SELECT COUNT(*) FROM community_replies 
                WHERE thread_id = community.id
            ) WHERE source_type = 'manual'
        """)
    
    conn.commit()
    conn.close()
    
    return imported

def main():
    """Import all CSV data in batches."""
    batch_size = 5
    total_imported = 0
    
    # Process in batches of 5 posts each
    for start in range(0, 34, batch_size):
        end = start + batch_size
        print(f"\n📥 Importing batch: posts {start + 1} to {min(end, 34)}")
        
        try:
            batch_imported = import_csv_batch(start, end)
            total_imported += batch_imported
            print(f"Batch complete: {batch_imported} replies imported")
        except Exception as e:
            print(f"Batch error: {e}")
            continue
    
    # Final status
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community_replies")
        total_replies = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM community WHERE source_type = 'manual' AND reply_count > 0")
        posts_with_replies = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n🎉 CSV Import Complete!")
    print(f"Total replies imported this run: {total_imported}")
    print(f"Total replies in database: {total_replies}")
    print(f"Posts with replies: {posts_with_replies}/34")

if __name__ == "__main__":
    main()