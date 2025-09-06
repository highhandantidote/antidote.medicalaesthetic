#!/usr/bin/env python3
"""
Complete the final CSV import for remaining community posts.
"""

import os
import csv
import psycopg2
from datetime import datetime

conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

# Get posts that need replies (have 0 replies)
with conn.cursor() as cur:
    cur.execute("SELECT id FROM community WHERE source_type = 'manual' AND reply_count = 0 ORDER BY id")
    empty_posts = [row[0] for row in cur.fetchall()]
    
    # Get all thread IDs
    cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
    all_threads = [row[0] for row in cur.fetchall()]

print(f"Importing replies for {len(empty_posts)} posts...")

with open('attached_assets/community_new - Sheet1.csv', 'r') as file:
    rows = list(csv.DictReader(file))
    
    added = 0
    
    for i, row in enumerate(rows):
        if i >= len(all_threads):
            break
            
        thread_id = all_threads[i]
        
        # Only process posts that need replies
        if thread_id not in empty_posts:
            continue
            
        print(f"Post {i+1}: {row['title'][:40]}...")
        
        # Import all replies for this post
        for j in range(1, 9):
            content = row.get(f'reply_{j}_content', '').strip()
            username = row.get(f'reply_{j}_username', '').strip()
            email = row.get(f'reply_{j}_email', '').strip()
            
            if not content or not username or not email:
                continue
            
            # Create user if needed
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                
                if not user:
                    is_expert = row.get(f'reply_{j}_is_expert', 'FALSE').upper() == 'TRUE'
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash, is_expert, created_at)
                        VALUES (%s, %s, 'hash', %s, %s) RETURNING id
                    """, (username, email, is_expert, datetime.now()))
                    user_id = cur.fetchone()[0]
                else:
                    user_id = user[0]
                
                # Insert reply
                cur.execute("""
                    INSERT INTO community_replies (thread_id, user_id, content, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (thread_id, user_id, content, datetime.now()))
                added += 1
                
            print(f"  ✅ {username}")

# Update reply counts
with conn.cursor() as cur:
    cur.execute("""
        UPDATE community SET reply_count = (
            SELECT COUNT(*) FROM community_replies 
            WHERE thread_id = community.id
        ) WHERE source_type = 'manual'
    """)
    
    # Get final stats
    cur.execute("SELECT COUNT(*) FROM community_replies")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM community WHERE source_type = 'manual' AND reply_count > 0")
    with_replies = cur.fetchone()[0]

conn.commit()
conn.close()

print(f"\n🎉 CSV Import Complete!")
print(f"Added: {added} replies")
print(f"Total: {total} replies")
print(f"Posts with replies: {with_replies}/34")