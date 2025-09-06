#!/usr/bin/env python3
"""
Continue importing remaining community posts.
"""

import os
import csv
import psycopg2
from datetime import datetime

def main():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Check current count
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community WHERE source_type = 'manual'")
        current_count = cur.fetchone()[0]
    
    print(f"Current posts: {current_count}, continuing import...")
    
    posts_created = 0
    
    with open("attached_assets/community_new - Sheet1.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
        # Skip already imported posts
        for i, row in enumerate(rows[current_count:], current_count + 1):
            if posts_created >= 10:  # Import 10 more posts at a time
                break
                
            with conn.cursor() as cur:
                # Get or create user
                cur.execute("SELECT id FROM users WHERE email = %s", (row['email'],))
                result = cur.fetchone()
                
                if result:
                    user_id = result[0]
                else:
                    cur.execute("""
                        INSERT INTO users (username, email, name, role, is_verified, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (row['username'], row['email'], row['username'], 'patient', True, datetime.now()))
                    user_id = cur.fetchone()[0]
                
                # Get procedure/category IDs
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
                
                print(f"Created post {current_count + posts_created}: {row['title']}")
    
    # Final count
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community")
        total_posts = cur.fetchone()[0]
    
    print(f"Import batch complete. Total posts now: {total_posts}")
    conn.close()

if __name__ == "__main__":
    main()