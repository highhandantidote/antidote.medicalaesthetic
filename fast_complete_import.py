#!/usr/bin/env python3
"""
Fast Complete Import - Import all remaining CSV replies efficiently
"""

import os
import csv
import psycopg2
from datetime import datetime

def main():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    print("Starting fast import of remaining replies...")
    
    # Get thread IDs
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        thread_ids = [row[0] for row in cur.fetchall()]
    
    # Count current replies per thread
    reply_counts = {}
    with conn.cursor() as cur:
        for thread_id in thread_ids:
            cur.execute("SELECT COUNT(*) FROM community_replies WHERE thread_id = %s", (thread_id,))
            reply_counts[thread_id] = cur.fetchone()[0]
    
    print(f"Current reply counts: {sum(reply_counts.values())} total replies")
    
    total_imported = 0
    
    # Import from CSV
    with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for post_idx, row in enumerate(reader, 1):
            if post_idx > len(thread_ids):
                break
                
            thread_id = thread_ids[post_idx - 1]
            current_replies = reply_counts[thread_id]
            
            # Import replies starting from where we left off
            for i in range(1, 9):  # Check all 8 possible replies
                content = row.get(f'reply_{i}_content', '').strip()
                username = row.get(f'reply_{i}_username', '').strip()
                email = row.get(f'reply_{i}_email', '').strip()
                
                if not content or not username or not email:
                    continue
                
                # Skip if we already have enough replies for this thread
                if i <= current_replies:
                    continue
                
                # Get or create user
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                    result = cur.fetchone()
                    
                    if result:
                        user_id = result[0]
                    else:
                        is_doctor = row.get(f'reply_{i}_is_doctor', 'FALSE').upper() == 'TRUE'
                        role = 'doctor' if is_doctor else 'patient'
                        
                        cur.execute("""
                            INSERT INTO users (username, email, name, role, is_verified, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (username, email, username, role, True, datetime.now()))
                        user_id = cur.fetchone()[0]
                
                # Insert reply
                is_anonymous = row.get(f'reply_{i}_is_anonymous', 'FALSE').upper() == 'TRUE'
                
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO community_replies (thread_id, user_id, content, is_anonymous, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (thread_id, user_id, content, is_anonymous, datetime.now()))
                
                total_imported += 1
                print(f"Imported reply {i} for post {post_idx}: {username}")
            
            conn.commit()
            
            if post_idx % 10 == 0:
                print(f"Processed {post_idx} posts, imported {total_imported} new replies")
    
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
        final_count = cur.fetchone()[0]
    
    print(f"\n=== IMPORT COMPLETE ===")
    print(f"New replies imported: {total_imported}")
    print(f"Total replies now: {final_count}")
    print(f"CSV import fully completed!")
    
    conn.close()

if __name__ == "__main__":
    main()