#!/usr/bin/env python3
"""
Final CSV Complete Import - Get all 129 replies imported
"""
import os
import csv
import psycopg2
from datetime import datetime

def main():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    print("Starting final complete import...")
    print("Expected: 129 replies from CSV")
    
    # Get current count
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community_replies")
        current_count = cur.fetchone()[0]
    
    print(f"Current: {current_count} replies in database")
    
    # Get thread IDs in order
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        thread_ids = [row[0] for row in cur.fetchall()]
    
    imported = 0
    
    # Process CSV completely
    with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for post_idx, row in enumerate(reader, 1):
            if post_idx > len(thread_ids):
                break
                
            thread_id = thread_ids[post_idx - 1]
            
            # Process all 8 replies for this post
            for reply_num in range(1, 9):
                content = row.get(f'reply_{reply_num}_content', '').strip()
                username = row.get(f'reply_{reply_num}_username', '').strip() 
                email = row.get(f'reply_{reply_num}_email', '').strip()
                
                if not content or not username or not email:
                    continue
                
                # Skip if exists (quick check)
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 1 FROM community_replies cr
                        JOIN users u ON cr.user_id = u.id
                        WHERE cr.thread_id = %s AND u.username = %s AND cr.content = %s
                    """, (thread_id, username, content))
                    
                    if cur.fetchone():
                        continue
                
                # Create user if needed
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
                            VALUES (%s, %s, %s, %s, TRUE, %s)
                            RETURNING id
                        """, (username, email, username, role, datetime.now()))
                        user_id = cur.fetchone()[0]
                
                # Add reply
                is_anonymous = row.get(f'reply_{reply_num}_is_anonymous', 'FALSE').upper() == 'TRUE'
                
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO community_replies (thread_id, user_id, content, is_anonymous, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (thread_id, user_id, content, is_anonymous, datetime.now()))
                
                imported += 1
                print(f"✓ Added reply {reply_num} for post {post_idx} by {username}")
            
            # Commit every 5 posts
            if post_idx % 5 == 0:
                conn.commit()
                print(f"Committed batch - {imported} new replies so far")
    
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
    
    # Final verification
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community_replies")
        final_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM community WHERE reply_count > 0")
        posts_with_replies = cur.fetchone()[0]
        
        cur.execute("SELECT SUM(reply_count) FROM community WHERE source_type = 'manual'")
        total_manual_replies = cur.fetchone()[0] or 0
    
    conn.close()
    
    print(f"\n🎉 COMPLETE CSV IMPORT FINISHED!")
    print(f"New replies imported: {imported}")
    print(f"Total replies in database: {final_count}")
    print(f"Posts with replies: {posts_with_replies}/34")
    print(f"Total manual post replies: {total_manual_replies}")
    print(f"CSV target achieved: {final_count >= 129}")

if __name__ == "__main__":
    main()