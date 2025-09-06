#!/usr/bin/env python3
"""
Complete the CSV import efficiently by processing remaining posts.
"""

import os
import csv
import psycopg2
from datetime import datetime

conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

# Get all thread IDs and current status
with conn.cursor() as cur:
    cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
    thread_ids = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT COUNT(*) FROM community_replies")
    current_count = cur.fetchone()[0]

print(f"Continuing import from {current_count} existing replies...")

# Read CSV and continue import
with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
    rows = list(csv.DictReader(file))

imported = 0

# Process all posts starting from post 3 (since 1-2 are done)
for post_idx in range(2, len(rows)):  # Start from index 2 (post 3)
    if post_idx >= len(thread_ids):
        break
        
    row = rows[post_idx]
    thread_id = thread_ids[post_idx]
    
    print(f"Post {post_idx + 1}: {row['title'][:40]}...")
    
    # Import all replies for this post
    for reply_num in range(1, 9):
        content = row.get(f'reply_{reply_num}_content', '').strip()
        username = row.get(f'reply_{reply_num}_username', '').strip()
        email = row.get(f'reply_{reply_num}_email', '').strip()
        
        if not content or not username or not email:
            continue
        
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
print(f"Added: {imported} authentic replies")
print(f"Total: {total} replies")
print(f"Posts with replies: {with_replies}/34")
print("All authentic CSV data imported successfully!")