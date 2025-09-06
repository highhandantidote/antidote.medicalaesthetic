#!/usr/bin/env python3
"""
Final batch import - complete the remaining authentic CSV replies
"""
import os
import csv
import psycopg2
from datetime import datetime

def main():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Get thread IDs
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        thread_ids = [row[0] for row in cur.fetchall()]
    
    imported = 0
    
    with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
        # Process posts 21-34 to complete the import
        for post_idx in range(20, len(rows)):
            row = rows[post_idx]
            thread_id = thread_ids[post_idx]
            
            for reply_num in range(1, 9):
                content = row.get(f'reply_{reply_num}_content', '').strip()
                username = row.get(f'reply_{reply_num}_username', '').strip()
                email = row.get(f'reply_{reply_num}_email', '').strip()
                
                if not content or not username or not email:
                    continue
                
                # Check if reply exists
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 1 FROM community_replies cr
                        JOIN users u ON cr.user_id = u.id
                        WHERE cr.thread_id = %s AND u.username = %s AND cr.content = %s
                    """, (thread_id, username, content))
                    
                    if cur.fetchone():
                        continue
                
                # Get/create user
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
                            VALUES (%s, %s, %s, %s, TRUE, %s) RETURNING id
                        """, (username, email, username, role, datetime.now()))
                        user_id = cur.fetchone()[0]
                
                # Insert reply
                is_anonymous = row.get(f'reply_{reply_num}_is_anonymous', 'FALSE').upper() == 'TRUE'
                
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO community_replies (thread_id, user_id, content, is_anonymous, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (thread_id, user_id, content, is_anonymous, datetime.now()))
                
                imported += 1
                print(f"✓ Post {post_idx+1} Reply {reply_num}: {username}")
            
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
        
        cur.execute("SELECT COUNT(*) FROM community_replies")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM community WHERE reply_count > 0")
        posts_with_replies = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n🎉 FINAL BATCH COMPLETE!")
    print(f"New replies added: {imported}")
    print(f"Total replies now: {total}")
    print(f"Posts with replies: {posts_with_replies}/34")
    print(f"CSV Import Status: {total}/129 authentic replies")

if __name__ == "__main__":
    main()