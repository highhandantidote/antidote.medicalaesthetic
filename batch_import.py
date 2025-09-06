#!/usr/bin/env python3
"""
Batch import to complete ALL remaining CSV reply data.
"""

import os
import csv
import psycopg2
from datetime import datetime

conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

# Read CSV
with open("attached_assets/community_new - Sheet1.csv", 'r', encoding='utf-8') as file:
    rows = list(csv.DictReader(file))

# Get threads
with conn.cursor() as cur:
    cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
    thread_ids = [row[0] for row in cur.fetchall()]

print(f"Continuing import for {len(rows)} posts...")

# Process remaining posts in batches of 5
for batch_start in range(0, len(rows), 5):
    batch_end = min(batch_start + 5, len(rows))
    print(f"Processing posts {batch_start + 1} to {batch_end}...")
    
    for post_idx in range(batch_start, batch_end):
        if post_idx >= len(thread_ids):
            continue
            
        thread_id = thread_ids[post_idx]
        row = rows[post_idx]
        
        # Import all replies for this post
        for reply_num in range(1, 9):
            content = row.get(f'reply_{reply_num}_content', '').strip()
            username = row.get(f'reply_{reply_num}_username', '').strip()
            email = row.get(f'reply_{reply_num}_email', '').strip()
            
            if not all([content, username, email]):
                continue
            
            with conn.cursor() as cur:
                # Skip if exists
                cur.execute("SELECT 1 FROM community_replies WHERE thread_id = %s AND content = %s", 
                          (thread_id, content))
                if cur.fetchone():
                    continue
                
                # Get user
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                user_result = cur.fetchone()
                
                if not user_result:
                    role = 'expert' if 'expert_' in username else 'patient'
                    cur.execute("""
                        INSERT INTO users (username, email, name, role, is_verified, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (username) DO UPDATE SET email = EXCLUDED.email
                        RETURNING id
                    """, (username, email, username, role, True, datetime.now()))
                    try:
                        user_id = cur.fetchone()[0]
                    except:
                        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                        user_id = cur.fetchone()[0]
                else:
                    user_id = user_result[0]
                
                # Add reply
                try:
                    reply_date = datetime.strptime(row.get(f'reply_{reply_num}_date', ''), '%Y-%m-%d')
                except:
                    reply_date = datetime.now()
                
                cur.execute("""
                    INSERT INTO community_replies (
                        thread_id, user_id, content, is_anonymous,
                        is_doctor_response, is_expert_advice, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    thread_id, user_id, content,
                    row.get(f'reply_{reply_num}_is_anonymous', '').upper() == 'TRUE',
                    row.get(f'reply_{reply_num}_is_doctor', '').upper() == 'TRUE',
                    row.get(f'reply_{reply_num}_is_expert', '').upper() == 'TRUE',
                    reply_date
                ))
                
    conn.commit()
    print(f"Completed batch {batch_start//5 + 1}")

# Update reply counts
with conn.cursor() as cur:
    cur.execute("""
        UPDATE community SET reply_count = (
            SELECT COUNT(*) FROM community_replies 
            WHERE community_replies.thread_id = community.id
        ) WHERE source_type = 'manual'
    """)
    conn.commit()

# Final count
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM community_replies")
    total_replies = cur.fetchone()[0]

print(f"Import complete! Total replies: {total_replies}")
conn.close()