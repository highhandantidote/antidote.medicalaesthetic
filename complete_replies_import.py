#!/usr/bin/env python3
"""
Complete the community replies import from CSV.
This script imports ALL remaining reply data from the CSV file.
"""

import os
import csv
import psycopg2
from datetime import datetime

def get_db_connection():
    """Get a connection to the database."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def create_user_if_not_exists(conn, username, email, is_expert=False, is_doctor=False):
    """Create a user if they don't exist."""
    with conn.cursor() as cur:
        # Check if user exists
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if user:
            return user[0]
        
        # Create new user
        cur.execute("""
            INSERT INTO users (username, email, password_hash, is_expert, is_doctor, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, email, 'hashed_password', is_expert, is_doctor, datetime.now()))
        
        return cur.fetchone()[0]

def reply_exists(conn, thread_id, username, content):
    """Check if a reply already exists."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM community_replies cr
            JOIN users u ON cr.user_id = u.id
            WHERE cr.thread_id = %s AND u.username = %s AND cr.content = %s
        """, (thread_id, username, content))
        return cur.fetchone() is not None

def import_all_replies():
    """Import all remaining replies from the CSV."""
    conn = get_db_connection()
    
    # Get all thread IDs in order
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM community WHERE source_type = 'manual' ORDER BY id")
        thread_ids = [row[0] for row in cur.fetchall()]
    
    print(f"Found {len(thread_ids)} community posts to process...")
    
    imported = 0
    
    with open('attached_assets/community_new - Sheet1.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
        for post_idx, row in enumerate(rows):
            thread_id = thread_ids[post_idx]
            print(f"Processing post {post_idx + 1}: {row.get('title', 'Unknown')[:50]}...")
            
            # Process all 8 possible replies
            reply_ids = {}  # Store reply IDs for parent references
            
            for reply_num in range(1, 9):
                content = row.get(f'reply_{reply_num}_content', '').strip()
                username = row.get(f'reply_{reply_num}_username', '').strip()
                email = row.get(f'reply_{reply_num}_email', '').strip()
                
                if not content or not username or not email:
                    continue
                
                # Skip if reply already exists
                if reply_exists(conn, thread_id, username, content):
                    print(f"  Reply {reply_num} already exists, skipping...")
                    continue
                
                # Parse reply details
                is_doctor = row.get(f'reply_{reply_num}_is_doctor', 'FALSE').upper() == 'TRUE'
                is_expert = row.get(f'reply_{reply_num}_is_expert', 'FALSE').upper() == 'TRUE'
                is_anonymous = row.get(f'reply_{reply_num}_is_anonymous', 'FALSE').upper() == 'TRUE'
                reply_date_str = row.get(f'reply_{reply_num}_date', '')
                parent_reply_num = row.get(f'reply_{reply_num}_parent_reply', '').strip()
                
                # Parse date
                reply_date = datetime.now()
                if reply_date_str:
                    try:
                        reply_date = datetime.strptime(reply_date_str, '%Y-%m-%d')
                    except:
                        pass
                
                # Create user
                user_id = create_user_if_not_exists(conn, username, email, is_expert, is_doctor)
                
                # Handle parent reply
                parent_reply_id = None
                if parent_reply_num and parent_reply_num.isdigit():
                    parent_num = int(parent_reply_num)
                    if parent_num in reply_ids:
                        parent_reply_id = reply_ids[parent_num]
                
                # Insert reply
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO community_replies 
                        (thread_id, user_id, content, is_anonymous, parent_reply_id, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (thread_id, user_id, content, is_anonymous, parent_reply_id, reply_date))
                    
                    reply_id = cur.fetchone()[0]
                    reply_ids[reply_num] = reply_id
                    imported += 1
                    
                    print(f"  ✅ Imported reply {reply_num} by {username}")
            
            # Commit every post
            conn.commit()
    
    # Update reply counts for all posts
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
    
    print(f"\n🎉 IMPORT COMPLETE!")
    print(f"New replies imported: {imported}")
    print(f"Total replies in database: {total_replies}")
    print(f"Posts with replies: {posts_with_replies}/34")
    print(f"Average replies per post: {avg_replies:.1f}")
    print(f"Target achieved: {total_replies >= 120} ({'✅' if total_replies >= 120 else '❌'})")

if __name__ == "__main__":
    import_all_replies()