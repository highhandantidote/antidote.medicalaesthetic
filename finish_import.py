#!/usr/bin/env python3
"""
Complete the remaining CSV import efficiently.
"""

import os
import csv
import psycopg2
from datetime import datetime

def main():
    """Complete the remaining import."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Get posts that still need replies (have 0 or very few replies)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM community 
            WHERE source_type = 'manual' AND reply_count < 3
            ORDER BY id
        """)
        posts_needing_more = [row[0] for row in cur.fetchall()]
        
        # Get all thread IDs in order
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        all_threads = [row[0] for row in cur.fetchall()]
    
    print(f"Processing {len(posts_needing_more)} posts that need more replies...")
    
    imported = 0
    
    with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
        # Process only posts that need more replies
        for post_idx, row in enumerate(rows):
            if post_idx >= len(all_threads):
                break
                
            thread_id = all_threads[post_idx]
            
            # Skip if this post doesn't need more replies
            if thread_id not in posts_needing_more:
                continue
                
            print(f"Post {post_idx + 1}: {row.get('title', '')[:40]}...")
            
            # Import replies 1-8 for this post
            for i in range(1, 9):
                content = row.get(f'reply_{i}_content', '').strip()
                username = row.get(f'reply_{i}_username', '').strip()
                email = row.get(f'reply_{i}_email', '').strip()
                
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
                        continue
                
                # Get user ID or create user
                is_expert = row.get(f'reply_{i}_is_expert', 'FALSE').upper() == 'TRUE'
                is_doctor = row.get(f'reply_{i}_is_doctor', 'FALSE').upper() == 'TRUE'
                
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
                
                # Insert the reply
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO community_replies (thread_id, user_id, content, created_at)
                        VALUES (%s, %s, %s, %s)
                    """, (thread_id, user_id, content, datetime.now()))
                    imported += 1
                    
                print(f"  ✅ Added reply by {username}")
        
        # Commit all changes
        conn.commit()
    
    # Update reply counts
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE community SET reply_count = (
                SELECT COUNT(*) FROM community_replies 
                WHERE community_replies.thread_id = community.id
            ) WHERE source_type = 'manual'
        """)
        conn.commit()
        
        # Get final stats
        cur.execute("SELECT COUNT(*) FROM community_replies")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM community WHERE source_type = 'manual' AND reply_count > 0")
        with_replies = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n🎉 Import complete!")
    print(f"Added {imported} new replies")
    print(f"Total replies: {total}")
    print(f"Posts with replies: {with_replies}/34")

if __name__ == "__main__":
    main()