#!/usr/bin/env python3
"""
Import community posts and replies from CSV file.
This script imports authentic community data from the provided CSV file.
"""

import os
import csv
import psycopg2
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection using DATABASE_URL environment variable."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def import_community_data():
    """Import community posts and replies from CSV file."""
    csv_file_path = 'archive/attached_assets/community_new - Sheet1.csv'
    
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        return
    
    conn = get_db_connection()
    
    try:
        posts_created = 0
        replies_created = 0
        users_created = 0
        
        logger.info("Starting community data import...")
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                with conn.cursor() as cur:
                    # Get or create main post user
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
                        users_created += 1
                        logger.info(f"Created user: {row['username']}")
                    
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
                    is_anonymous = row['is_anonymous'].upper() == 'TRUE' if row['is_anonymous'] else False
                    view_count = int(row['view_count']) if row['view_count'] else 0
                    
                    try:
                        created_at = datetime.strptime(row['created_at'], '%Y-%m-%d')
                    except:
                        created_at = datetime.now()
                    
                    # Check if post already exists
                    cur.execute("SELECT id FROM community WHERE title = %s AND user_id = %s", 
                              (row['title'], user_id))
                    existing_post = cur.fetchone()
                    
                    if existing_post:
                        thread_id = existing_post[0]
                        logger.info(f"Post already exists: {row['title']}")
                    else:
                        # Insert post
                        cur.execute("""
                            INSERT INTO community (
                                user_id, title, content, procedure_id, category_id,
                                is_anonymous, tags, view_count, created_at, source_type
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            user_id, row['title'], row['content'], procedure_id, category_id,
                            is_anonymous, tags, view_count, created_at, 'csv_import'
                        ))
                        thread_id = cur.fetchone()[0]
                        posts_created += 1
                        logger.info(f"Created post: {row['title']}")
                    
                    # Import replies (up to 8 replies per post)
                    for reply_num in range(1, 9):
                        reply_content = row.get(f'reply_{reply_num}_content', '').strip()
                        reply_username = row.get(f'reply_{reply_num}_username', '').strip()
                        reply_email = row.get(f'reply_{reply_num}_email', '').strip()
                        
                        if not reply_content or not reply_username or not reply_email:
                            continue
                        
                        # Check if reply already exists
                        cur.execute("""
                            SELECT 1 FROM community c
                            JOIN users u ON c.user_id = u.id
                            WHERE c.parent_id = %s AND c.content = %s AND u.username = %s
                            LIMIT 1
                        """, (thread_id, reply_content, reply_username))
                        
                        if cur.fetchone():
                            continue  # Skip if exists
                        
                        # Get or create reply user
                        cur.execute("SELECT id FROM users WHERE email = %s", (reply_email,))
                        result = cur.fetchone()
                        
                        if result:
                            reply_user_id = result[0]
                        else:
                            is_doctor = row.get(f'reply_{reply_num}_is_doctor', 'FALSE').upper() == 'TRUE'
                            is_expert = row.get(f'reply_{reply_num}_is_expert', 'FALSE').upper() == 'TRUE'
                            
                            role = 'doctor' if is_doctor else ('expert' if is_expert else 'patient')
                            
                            cur.execute("""
                                INSERT INTO users (username, email, name, role, is_verified, is_doctor, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                RETURNING id
                            """, (reply_username, reply_email, reply_username, role, True, is_doctor, datetime.now()))
                            reply_user_id = cur.fetchone()[0]
                            users_created += 1
                            logger.info(f"Created reply user: {reply_username}")
                        
                        # Parse reply anonymous flag and date
                        is_reply_anonymous = row.get(f'reply_{reply_num}_is_anonymous', 'FALSE').upper() == 'TRUE'
                        
                        try:
                            reply_date = datetime.strptime(row.get(f'reply_{reply_num}_date', ''), '%Y-%m-%d')
                        except:
                            reply_date = created_at  # Use post date as fallback
                        
                        # Insert reply (replies need a title even if it's just "Reply")
                        cur.execute("""
                            INSERT INTO community (
                                user_id, parent_id, title, content, is_anonymous, created_at, source_type
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            reply_user_id, thread_id, f"Reply to: {row['title']}", reply_content, 
                            is_reply_anonymous, reply_date, 'csv_import'
                        ))
                        replies_created += 1
                        
                        if replies_created % 10 == 0:
                            logger.info(f"Created {replies_created} replies so far...")
                
                # Commit after each post and its replies
                conn.commit()
                
                if posts_created % 5 == 0:
                    logger.info(f"Processed {posts_created} posts so far...")
        
        # Update reply counts for all posts
        logger.info("Updating reply counts...")
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE community 
                SET reply_count = (
                    SELECT COUNT(*) 
                    FROM community c2 
                    WHERE c2.parent_id = community.id
                )
                WHERE parent_id IS NULL
            """)
        
        conn.commit()
        
        logger.info("Community data import completed successfully!")
        logger.info(f"Posts created: {posts_created}")
        logger.info(f"Replies created: {replies_created}")
        logger.info(f"Users created: {users_created}")
        
    except Exception as e:
        logger.error(f"Error during import: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import_community_data()