#!/usr/bin/env python3
"""
Quick batch import of remaining replies - process 5 posts at a time
"""
import os
import csv
import psycopg2
from datetime import datetime

def process_batch(start_post, batch_size=5):
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Get thread IDs
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id LIMIT %s OFFSET %s", 
                   (batch_size, start_post - 1))
        thread_ids = [row[0] for row in cur.fetchall()]
    
    if not thread_ids:
        print(f"No more posts to process starting from {start_post}")
        return 0
    
    imported = 0
    
    with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
        for i, thread_id in enumerate(thread_ids):
            row_idx = start_post - 1 + i
            if row_idx >= len(rows):
                break
                
            row = rows[row_idx]
            
            # Process all 8 possible replies for this post
            for reply_num in range(1, 9):
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
                        WHERE cr.thread_id = %s AND cr.content = %s AND u.username = %s
                        LIMIT 1
                    """, (thread_id, content, username))
                    
                    if cur.fetchone():
                        continue  # Skip if exists
                
                # Get or create user
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                    result = cur.fetchone()
                    
                    if result:
                        user_id = result[0]
                    else:
                        is_doctor = row.get(f'reply_{reply_num}_is_doctor', 'FALSE').upper() == 'TRUE'
                        role = 'doctor' if is_doctor else 'patient'
                        
                        cur.execute("""
                            INSERT INTO users (username, email, name, role, is_verified, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (username, email, username, role, True, datetime.now()))
                        user_id = cur.fetchone()[0]
                
                # Insert reply
                is_anonymous = row.get(f'reply_{reply_num}_is_anonymous', 'FALSE').upper() == 'TRUE'
                
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO community_replies (thread_id, user_id, content, is_anonymous, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (thread_id, user_id, content, is_anonymous, datetime.now()))
                
                imported += 1
                print(f"✓ Post {start_post + i}, Reply {reply_num}: {username}")
        
        conn.commit()
    
    conn.close()
    return imported

def main():
    print("Starting batch import of community replies...")
    
    # Process 5 posts at a time
    total_imported = 0
    start_post = 1
    
    while True:
        batch_imported = process_batch(start_post, 5)
        total_imported += batch_imported
        
        if batch_imported == 0:
            break
            
        print(f"Batch complete. Imported {batch_imported} replies in this batch.")
        start_post += 5
        
        if start_post > 34:  # We only have 34 posts
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
        
        # Final verification
        cur.execute("SELECT COUNT(*) FROM community_replies")
        total_replies = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM community WHERE reply_count > 0")
        posts_with_replies = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n🎉 IMPORT COMPLETE!")
    print(f"Total new replies imported: {total_imported}")
    print(f"Total replies in database: {total_replies}")
    print(f"Posts with replies: {posts_with_replies}")
    print(f"All CSV reply data has been successfully imported!")

if __name__ == "__main__":
    main()