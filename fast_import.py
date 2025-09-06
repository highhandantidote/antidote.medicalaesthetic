#!/usr/bin/env python3
"""
Fast import of community posts from CSV.
"""

import os
import csv
import psycopg2
from datetime import datetime

def main():
    """Fast import community posts."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Create a few essential users first
    users = {}
    with conn.cursor() as cur:
        essential_users = [
            ('NebulaNoodle', 'nebulanoodle@example.com'),
            ('MossyMoon', 'mossymoon@example.com'),
            ('FernFizz', 'fernfizz@example.com'),
            ('ZodiacPeach', 'zodiacpeach@example.com'),
            ('PetalDrift', 'petaldrift@example.com'),
            ('CloudberryPop', 'cloudberrypop@example.com'),
            ('GalaxiGlow', 'galaxiglow@example.com'),
            ('StardustMoss', 'stardustmoss@example.com'),
            ('OrbitBunny', 'orbitbunny@example.com'),
            ('LeafLagoon', 'leaflagoon@example.com'),
            ('expert_wyvern', 'expert_wyvern@antidote.com'),
            ('expert_sequoia', 'expert_sequoia@antidote.com'),
            ('expert_fenrir', 'expert_fenrir@antidote.com'),
            ('expert_onyx', 'expert_onyx@antidote.com')
        ]
        
        for username, email in essential_users:
            role = 'expert' if 'expert_' in username else 'patient'
            cur.execute("""
                INSERT INTO users (username, email, name, role, is_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                RETURNING id
            """, (username, email, username, role, True, datetime.now()))
            
            result = cur.fetchone()
            if result:
                users[username] = result[0]
            else:
                # Get existing user
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                users[username] = cur.fetchone()[0]
    
    conn.commit()
    
    # Import posts
    with open("attached_assets/community_new - Sheet1.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for i, row in enumerate(reader, 1):
            if i > 10:  # Import first 10 posts to start
                break
                
            print(f"Importing post {i}: {row['title']}")
            
            # Get user ID
            username = row['username']
            user_id = users.get(username)
            if not user_id:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO users (username, email, name, role, is_verified, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (username, row['email'], username, 'patient', True, datetime.now()))
                    user_id = cur.fetchone()[0]
                    users[username] = user_id
                    conn.commit()
            
            # Get procedure and category IDs
            procedure_id = None
            category_id = None
            
            with conn.cursor() as cur:
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
            
            # Create post
            tags = [tag.strip() for tag in row['tags'].split(',') if tag.strip()] if row['tags'] else []
            
            try:
                created_at = datetime.strptime(row['created_at'], '%Y-%m-%d')
            except:
                created_at = datetime.now()
            
            with conn.cursor() as cur:
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
                conn.commit()
                print(f"Created post ID {thread_id}")
    
    # Check final count
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM community")
        count = cur.fetchone()[0]
        print(f"Total posts imported: {count}")
    
    conn.close()

if __name__ == "__main__":
    main()