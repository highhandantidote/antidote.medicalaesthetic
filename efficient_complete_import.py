#!/usr/bin/env python3
"""
Efficient complete import - finish all remaining authentic CSV replies
"""
import os
import csv
import psycopg2

def process_remaining_replies():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Get current status
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community_replies")
        current_count = cur.fetchone()[0]
    
    print(f"Starting from {current_count} replies...")
    
    # Get thread IDs
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        thread_ids = [row[0] for row in cur.fetchall()]
    
    imported = 0
    
    # Process CSV efficiently
    with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for post_idx, row in enumerate(reader):
            if post_idx >= len(thread_ids):
                break
                
            thread_id = thread_ids[post_idx]
            
            for reply_num in range(1, 9):
                content = row.get(f'reply_{reply_num}_content', '').strip()
                username = row.get(f'reply_{reply_num}_username', '').strip()
                email = row.get(f'reply_{reply_num}_email', '').strip()
                
                if not content or not username or not email:
                    continue
                
                # Quick duplicate check
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 1 FROM community_replies cr
                        JOIN users u ON cr.user_id = u.id
                        WHERE cr.thread_id = %s AND u.username = %s 
                        LIMIT 1
                    """, (thread_id, username))
                    
                    if cur.fetchone():
                        continue
                
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
                            VALUES (%s, %s, %s, %s, TRUE, NOW()) RETURNING id
                        """, (username, email, username, role))
                        user_id = cur.fetchone()[0]
                
                # Insert reply
                is_anonymous = row.get(f'reply_{reply_num}_is_anonymous', 'FALSE').upper() == 'TRUE'
                
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO community_replies (thread_id, user_id, content, is_anonymous, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (thread_id, user_id, content, is_anonymous))
                
                imported += 1
                print(f"✓ {username} (Post {post_idx+1})")
                
                # Commit frequently
                if imported % 10 == 0:
                    conn.commit()
                    print(f"  {imported} new replies imported...")
    
    # Final updates
    conn.commit()
    
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE community SET reply_count = (
                SELECT COUNT(*) FROM community_replies 
                WHERE community_replies.thread_id = community.id
            ) WHERE source_type = 'manual'
        """)
        conn.commit()
        
        cur.execute("SELECT COUNT(*) FROM community_replies")
        final_count = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n🎉 IMPORT COMPLETE!")
    print(f"Started with: {current_count} replies")
    print(f"Added: {imported} new authentic replies")
    print(f"Total now: {final_count} replies")
    print(f"CSV Target: {final_count}/129")

if __name__ == "__main__":
    process_remaining_replies()