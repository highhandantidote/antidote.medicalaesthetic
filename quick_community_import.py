#!/usr/bin/env python3
"""
Quick community import using direct SQL approach.
"""

import os
import csv
import psycopg2
from datetime import datetime

def main():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    print("Creating essential users...")
    # Create users first
    users_to_create = set()
    
    with open("attached_assets/community_new - Sheet1.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            users_to_create.add((row['username'], row['email']))
            # Add reply users too
            for i in range(1, 5):
                username = row.get(f'reply_{i}_username')
                email = row.get(f'reply_{i}_email')
                if username and email:
                    users_to_create.add((username, email))
    
    # Create all users
    user_ids = {}
    with conn.cursor() as cur:
        for username, email in users_to_create:
            if not username or not email:
                continue
            
            role = 'expert' if 'expert_' in username else 'patient'
            cur.execute("""
                INSERT INTO users (username, email, name, role, is_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET username = EXCLUDED.username
                RETURNING id
            """, (username, email, username, role, True, datetime.now()))
            
            result = cur.fetchone()
            if result:
                user_ids[username] = result[0]
            else:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                result = cur.fetchone()
                if result:
                    user_ids[username] = result[0]
    
    conn.commit()
    print(f"Created {len(user_ids)} users")
    
    # Import posts
    print("Importing community posts...")
    posts_created = 0
    
    with open("attached_assets/community_new - Sheet1.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        with conn.cursor() as cur:
            for row in reader:
                user_id = user_ids.get(row['username'])
                if not user_id:
                    continue
                
                # Get procedure and category IDs  
                procedure_id = None
                category_id = None
                
                if row['procedure_name']:
                    cur.execute("SELECT id FROM procedures WHERE LOWER(procedure_name) = LOWER(%s) LIMIT 1", 
                              (row['procedure_name'],))
                    result = cur.fetchone()
                    if result:
                        procedure_id = result[0]
                
                if row['category_name']:
                    cur.execute("SELECT id FROM categories WHERE LOWER(name) = LOWER(%s) LIMIT 1", 
                              (row['category_name'],))
                    result = cur.fetchone()
                    if result:
                        category_id = result[0]
                
                # Parse data
                tags = [tag.strip() for tag in row['tags'].split(',') if tag.strip()] if row['tags'] else []
                
                try:
                    created_at = datetime.strptime(row['created_at'], '%Y-%m-%d')
                except:
                    created_at = datetime.now()
                
                # Insert post
                cur.execute("""
                    INSERT INTO community (
                        user_id, title, content, procedure_id, category_id,
                        is_anonymous, tags, view_count, created_at, reply_count, source_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user_id, row['title'], row['content'], procedure_id, category_id,
                    row['is_anonymous'].upper() == 'TRUE', tags,
                    int(row['view_count']) if row['view_count'] else 0,
                    created_at, 0, 'manual'
                ))
                
                thread_id = cur.fetchone()[0]
                posts_created += 1
                
                # Add first reply only for speed
                if row.get('reply_1_content'):
                    reply_user_id = user_ids.get(row.get('reply_1_username'))
                    if reply_user_id:
                        try:
                            reply_date = datetime.strptime(row.get('reply_1_date', ''), '%Y-%m-%d')
                        except:
                            reply_date = datetime.now()
                        
                        cur.execute("""
                            INSERT INTO community_replies (
                                thread_id, user_id, content, is_anonymous, 
                                is_doctor_response, is_expert_advice, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            thread_id, reply_user_id, row['reply_1_content'],
                            row.get('reply_1_is_anonymous', '').upper() == 'TRUE',
                            row.get('reply_1_is_doctor', '').upper() == 'TRUE',
                            row.get('reply_1_is_expert', '').upper() == 'TRUE',
                            reply_date
                        ))
                        
                        # Update reply count
                        cur.execute("UPDATE community SET reply_count = 1 WHERE id = %s", (thread_id,))
                
                if posts_created % 5 == 0:
                    conn.commit()
                    print(f"Imported {posts_created} posts...")
    
    conn.commit()
    
    # Final count
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community")
        total_posts = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM community_replies")
        total_replies = cur.fetchone()[0]
    
    print(f"=== IMPORT COMPLETE ===")
    print(f"Total posts: {total_posts}")
    print(f"Total replies: {total_replies}")
    
    conn.close()

if __name__ == "__main__":
    main()