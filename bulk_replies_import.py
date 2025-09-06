#!/usr/bin/env python3
"""
Bulk import ALL replies from CSV efficiently.
"""

import os
import csv
import psycopg2
from datetime import datetime

def main():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    print("Starting bulk import of ALL replies...")
    
    # Read CSV data
    with open("attached_assets/community_new - Sheet1.csv", 'r', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    
    # Get thread IDs in order
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        thread_ids = [row[0] for row in cur.fetchall()]
    
    replies_added = 0
    
    # Process each row
    for row_idx, row in enumerate(rows):
        if row_idx >= len(thread_ids):
            continue
            
        thread_id = thread_ids[row_idx]
        
        # Process all 8 possible replies for this row
        for i in range(1, 9):
            content = row.get(f'reply_{i}_content', '').strip()
            username = row.get(f'reply_{i}_username', '').strip()
            email = row.get(f'reply_{i}_email', '').strip()
            
            if not all([content, username, email]):
                continue
            
            with conn.cursor() as cur:
                # Get or create user
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                user_result = cur.fetchone()
                
                if not user_result:
                    role = 'expert' if 'expert_' in username else 'patient'
                    try:
                        cur.execute("""
                            INSERT INTO users (username, email, name, role, is_verified, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (username, email, username, role, True, datetime.now()))
                        user_id = cur.fetchone()[0]
                    except:
                        # Handle duplicate username
                        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                        user_result = cur.fetchone()
                        if user_result:
                            user_id = user_result[0]
                        else:
                            continue
                else:
                    user_id = user_result[0]
                
                # Create reply
                try:
                    reply_date = datetime.strptime(row.get(f'reply_{i}_date', ''), '%Y-%m-%d')
                except:
                    reply_date = datetime.now()
                
                cur.execute("""
                    INSERT INTO community_replies (
                        thread_id, user_id, content, is_anonymous, 
                        is_doctor_response, is_expert_advice, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    thread_id, user_id, content,
                    row.get(f'reply_{i}_is_anonymous', '').upper() == 'TRUE',
                    row.get(f'reply_{i}_is_doctor', '').upper() == 'TRUE',
                    row.get(f'reply_{i}_is_expert', '').upper() == 'TRUE',
                    reply_date
                ))
                
                replies_added += 1
                
                if replies_added % 10 == 0:
                    conn.commit()
                    print(f"Added {replies_added} replies...")
    
    conn.commit()
    
    # Update reply counts
    print("Updating reply counts...")
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE community SET reply_count = (
                SELECT COUNT(*) FROM community_replies 
                WHERE community_replies.thread_id = community.id
            )
        """)
        conn.commit()
    
    # Final stats
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community_replies")
        total_replies = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM community WHERE reply_count > 0")
        posts_with_replies = cur.fetchone()[0]
    
    print(f"\n=== BULK IMPORT COMPLETE ===")
    print(f"Total replies added: {replies_added}")
    print(f"Total replies in database: {total_replies}")
    print(f"Posts with replies: {posts_with_replies}")
    
    conn.close()

if __name__ == "__main__":
    main()