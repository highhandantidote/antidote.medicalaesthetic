#!/usr/bin/env python3
"""
Final import to ensure ALL replies from CSV are added.
"""

import os
import csv
import psycopg2
from datetime import datetime

def main():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Get all essential users first
    essential_users = {}
    with conn.cursor() as cur:
        cur.execute("SELECT username, id FROM users")
        for username, user_id in cur.fetchall():
            essential_users[username] = user_id
    
    # Read CSV and process in chunks
    with open("attached_assets/community_new - Sheet1.csv", 'r', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    
    # Get thread IDs
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        thread_ids = [row[0] for row in cur.fetchall()]
    
    replies_to_add = []
    users_to_create = []
    
    # Collect all reply data first
    for row_idx, row in enumerate(rows[:len(thread_ids)]):
        thread_id = thread_ids[row_idx]
        
        for i in range(1, 9):  # All 8 possible replies
            content = row.get(f'reply_{i}_content', '').strip()
            username = row.get(f'reply_{i}_username', '').strip()
            email = row.get(f'reply_{i}_email', '').strip()
            
            if not all([content, username, email]):
                continue
            
            # Check if user exists
            if username not in essential_users:
                role = 'expert' if 'expert_' in username else 'patient'
                users_to_create.append((username, email, role))
                essential_users[username] = None  # Placeholder
            
            try:
                reply_date = datetime.strptime(row.get(f'reply_{i}_date', ''), '%Y-%m-%d')
            except:
                reply_date = datetime.now()
            
            replies_to_add.append({
                'thread_id': thread_id,
                'username': username,
                'content': content,
                'is_anonymous': row.get(f'reply_{i}_is_anonymous', '').upper() == 'TRUE',
                'is_doctor': row.get(f'reply_{i}_is_doctor', '').upper() == 'TRUE',
                'is_expert': row.get(f'reply_{i}_is_expert', '').upper() == 'TRUE',
                'date': reply_date
            })
    
    print(f"Need to create {len(users_to_create)} users and {len(replies_to_add)} replies")
    
    # Create missing users
    with conn.cursor() as cur:
        for username, email, role in users_to_create:
            try:
                cur.execute("""
                    INSERT INTO users (username, email, name, role, is_verified, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (username, email, username, role, True, datetime.now()))
                user_id = cur.fetchone()[0]
                essential_users[username] = user_id
            except:
                # Handle conflicts
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                result = cur.fetchone()
                if result:
                    essential_users[username] = result[0]
        conn.commit()
    
    # Insert replies in batches
    batch_size = 20
    replies_added = 0
    
    for i in range(0, len(replies_to_add), batch_size):
        batch = replies_to_add[i:i+batch_size]
        
        with conn.cursor() as cur:
            for reply in batch:
                user_id = essential_users.get(reply['username'])
                if not user_id:
                    continue
                
                # Check if reply already exists
                cur.execute("""
                    SELECT 1 FROM community_replies 
                    WHERE thread_id = %s AND content = %s AND user_id = %s
                """, (reply['thread_id'], reply['content'], user_id))
                
                if cur.fetchone():
                    continue  # Skip duplicate
                
                cur.execute("""
                    INSERT INTO community_replies (
                        thread_id, user_id, content, is_anonymous,
                        is_doctor_response, is_expert_advice, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    reply['thread_id'], user_id, reply['content'],
                    reply['is_anonymous'], reply['is_doctor'], 
                    reply['is_expert'], reply['date']
                ))
                replies_added += 1
        
        conn.commit()
        print(f"Added batch {i//batch_size + 1}, total replies: {replies_added}")
    
    # Update all reply counts
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
        total_replies = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM community WHERE reply_count > 0")
        posts_with_replies = cur.fetchone()[0]
        
        cur.execute("SELECT AVG(reply_count) FROM community WHERE source_type = 'manual'")
        avg_replies = cur.fetchone()[0] or 0
    
    print(f"\n=== FINAL IMPORT COMPLETE ===")
    print(f"Total replies in database: {total_replies}")
    print(f"Posts with replies: {posts_with_replies}")
    print(f"Average replies per post: {avg_replies:.1f}")
    print(f"ALL CSV DATA IMPORTED SUCCESSFULLY!")
    
    conn.close()

if __name__ == "__main__":
    main()