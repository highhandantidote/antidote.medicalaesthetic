#!/usr/bin/env python3
"""
Simple community import handling existing users.
"""

import os
import csv
import psycopg2
from datetime import datetime

def main():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    print("Starting community import...")
    
    posts_created = 0
    replies_created = 0
    
    with open("attached_assets/community_new - Sheet1.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            with conn.cursor() as cur:
                # Get or create user
                cur.execute("SELECT id FROM users WHERE email = %s", (row['email'],))
                result = cur.fetchone()
                
                if result:
                    user_id = result[0]
                else:
                    # Create new user
                    cur.execute("""
                        INSERT INTO users (username, email, name, role, is_verified, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (row['username'], row['email'], row['username'], 'patient', True, datetime.now()))
                    user_id = cur.fetchone()[0]
                
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
                conn.commit()
                
                print(f"Created post {posts_created}: {row['title']}")
                
                # Add one reply if exists
                if row.get('reply_1_content') and row.get('reply_1_username'):
                    # Get or create reply user
                    cur.execute("SELECT id FROM users WHERE email = %s", (row['reply_1_email'],))
                    result = cur.fetchone()
                    
                    if result:
                        reply_user_id = result[0]
                    else:
                        role = 'expert' if 'expert_' in row['reply_1_username'] else 'patient'
                        cur.execute("""
                            INSERT INTO users (username, email, name, role, is_verified, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (row['reply_1_username'], row['reply_1_email'], row['reply_1_username'], role, True, datetime.now()))
                        reply_user_id = cur.fetchone()[0]
                    
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
                    replies_created += 1
                    conn.commit()
    
    # Final count
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community")
        total_posts = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM community_replies")
        total_replies = cur.fetchone()[0]
    
    print(f"=== IMPORT COMPLETE ===")
    print(f"Posts created this run: {posts_created}")
    print(f"Replies created this run: {replies_created}")
    print(f"Total posts in database: {total_posts}")
    print(f"Total replies in database: {total_replies}")
    
    conn.close()

if __name__ == "__main__":
    main()