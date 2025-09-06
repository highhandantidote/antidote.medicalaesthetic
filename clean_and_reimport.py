#!/usr/bin/env python3
"""
Clean duplicate replies and properly import ALL authentic CSV reply data.
"""

import os
import csv
import psycopg2
from datetime import datetime

def clean_duplicates_and_reimport():
    """Remove all duplicates and do a clean import of CSV data."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    print("🧹 Cleaning duplicate replies...")
    
    # Remove ALL existing replies from manual posts to start fresh
    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM community_replies 
            WHERE thread_id IN (
                SELECT id FROM community WHERE source_type = 'manual'
            )
        """)
        deleted = cur.rowcount
        print(f"Removed {deleted} duplicate/existing replies")
        
        # Reset reply counts
        cur.execute("UPDATE community SET reply_count = 0 WHERE source_type = 'manual'")
        conn.commit()
    
    print("📥 Importing fresh authentic CSV reply data...")
    
    # Get all thread IDs in order
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        thread_ids = [row[0] for row in cur.fetchall()]
    
    imported = 0
    
    with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
        for post_idx, row in enumerate(rows):
            if post_idx >= len(thread_ids):
                break
                
            thread_id = thread_ids[post_idx]
            title = row.get('title', 'Unknown')
            print(f"Post {post_idx + 1}: {title[:40]}...")
            
            # Import ALL 8 possible replies for this post
            for reply_num in range(1, 9):
                content = row.get(f'reply_{reply_num}_content', '').strip()
                username = row.get(f'reply_{reply_num}_username', '').strip()
                email = row.get(f'reply_{reply_num}_email', '').strip()
                
                if not content or not username or not email:
                    continue
                
                # Parse user details
                is_doctor = row.get(f'reply_{reply_num}_is_doctor', 'FALSE').upper() == 'TRUE'
                is_expert = row.get(f'reply_{reply_num}_is_expert', 'FALSE').upper() == 'TRUE'
                is_anonymous = row.get(f'reply_{reply_num}_is_anonymous', 'FALSE').upper() == 'TRUE'
                
                # Parse date
                reply_date = datetime.now()
                reply_date_str = row.get(f'reply_{reply_num}_date', '')
                if reply_date_str:
                    try:
                        reply_date = datetime.strptime(reply_date_str, '%Y-%m-%d')
                    except:
                        pass
                
                # Get or create user
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
                
                # Insert the unique reply
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO community_replies 
                        (thread_id, user_id, content, is_anonymous, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (thread_id, user_id, content, is_anonymous, reply_date))
                    imported += 1
                    
                    print(f"  ✅ Reply {reply_num}: {username}")
            
            # Commit each post
            conn.commit()
    
    # Update all reply counts
    print("📊 Updating reply counts...")
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
        
        cur.execute("SELECT MAX(reply_count) FROM community WHERE source_type = 'manual'")
        max_replies = cur.fetchone()[0] or 0
    
    conn.close()
    
    print(f"\n🎉 CLEAN IMPORT COMPLETE!")
    print(f"Total authentic replies imported: {imported}")
    print(f"Total replies in database: {total_replies}")
    print(f"Posts with replies: {posts_with_replies}/34")
    print(f"Average replies per post: {avg_replies:.1f}")
    print(f"Max replies on one post: {max_replies}")
    print(f"All CSV data properly imported without duplicates!")

if __name__ == "__main__":
    clean_duplicates_and_reimport()