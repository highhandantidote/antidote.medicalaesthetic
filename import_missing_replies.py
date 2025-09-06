#!/usr/bin/env python3
"""
Import missing replies for posts that have 0 replies but should have data from CSV.
"""

import os
import csv
import psycopg2
from datetime import datetime

def import_missing_replies():
    """Import replies for posts that currently have 0 replies."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Get posts with 0 replies
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM community 
            WHERE source_type = 'manual' AND reply_count = 0 
            ORDER BY id
        """)
        posts_needing_replies = [row[0] for row in cur.fetchall()]
        
        # Get all thread IDs in order
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        all_thread_ids = [row[0] for row in cur.fetchall()]
    
    print(f"Found {len(posts_needing_replies)} posts with 0 replies that need data imported")
    
    imported = 0
    
    with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
        for post_idx, row in enumerate(rows):
            thread_id = all_thread_ids[post_idx]
            
            # Skip posts that already have replies
            if thread_id not in posts_needing_replies:
                continue
                
            print(f"Importing replies for post {post_idx + 1}: {row.get('title', 'Unknown')[:50]}...")
            
            # Process all 8 possible replies for this post
            for reply_num in range(1, 9):
                content = row.get(f'reply_{reply_num}_content', '').strip()
                username = row.get(f'reply_{reply_num}_username', '').strip()
                email = row.get(f'reply_{reply_num}_email', '').strip()
                
                if not content or not username or not email:
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
                
                # Parse date
                reply_date = datetime.now()
                reply_date_str = row.get(f'reply_{reply_num}_date', '')
                if reply_date_str:
                    try:
                        reply_date = datetime.strptime(reply_date_str, '%Y-%m-%d')
                    except:
                        pass
                
                # Insert reply
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO community_replies 
                        (thread_id, user_id, content, is_anonymous, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (thread_id, user_id, content, is_anonymous, reply_date))
                    imported += 1
                    
                    print(f"  ✅ Imported reply {reply_num} by {username}")
            
            conn.commit()
    
    # Update reply counts
    print("\nUpdating reply counts...")
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE community SET reply_count = (
                SELECT COUNT(*) FROM community_replies 
                WHERE community_replies.thread_id = community.id
            ) WHERE source_type = 'manual'
        """)
        conn.commit()
        
        # Get final statistics
        cur.execute("SELECT COUNT(*) FROM community_replies")
        total_replies = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM community WHERE source_type = 'manual' AND reply_count > 0")
        posts_with_replies = cur.fetchone()[0]
        
        cur.execute("SELECT AVG(reply_count) FROM community WHERE source_type = 'manual'")
        avg_replies = cur.fetchone()[0] or 0
    
    conn.close()
    
    print(f"\n🎉 MISSING REPLIES IMPORT COMPLETE!")
    print(f"New replies imported: {imported}")
    print(f"Total replies in database: {total_replies}")
    print(f"Posts with replies: {posts_with_replies}/34")
    print(f"Average replies per post: {avg_replies:.1f}")

if __name__ == "__main__":
    import_missing_replies()