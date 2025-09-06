#!/usr/bin/env python3
"""
Import community posts from CSV file with replies and nested discussions.

This script imports community posts and their replies from the provided CSV file,
ensuring proper relationships and no routing issues.
"""

import os
import sys
import csv
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def get_or_create_user(conn, username, email, role='patient'):
    """Get user ID or create user if doesn't exist."""
    try:
        with conn.cursor() as cursor:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Create new user
            cursor.execute("""
                INSERT INTO users (username, email, name, role, is_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (username, email, username, role, True, datetime.now()))
            
            user_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Created new user: {username}")
            return user_id
            
    except Exception as e:
        logger.error(f"Error getting/creating user {username}: {str(e)}")
        conn.rollback()
        return None

def get_procedure_id(conn, procedure_name):
    """Get procedure ID by name."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM procedures WHERE LOWER(procedure_name) = LOWER(%s)", (procedure_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting procedure ID for {procedure_name}: {str(e)}")
        return None

def get_category_id(conn, category_name):
    """Get category ID by name."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM categories WHERE LOWER(name) = LOWER(%s)", (category_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting category ID for {category_name}: {str(e)}")
        return None

def parse_date(date_str):
    """Parse date string to datetime object."""
    try:
        if not date_str or date_str.strip() == '':
            return datetime.now()
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except:
            return datetime.now()

def create_community_post(conn, post_data):
    """Create a community post."""
    try:
        # Get user ID
        user_id = get_or_create_user(conn, post_data['username'], post_data['email'])
        if not user_id:
            logger.error(f"Failed to get user ID for {post_data['username']}")
            return None
        
        # Get procedure and category IDs
        procedure_id = get_procedure_id(conn, post_data['procedure_name'])
        category_id = get_category_id(conn, post_data['category_name'])
        
        # Parse tags
        tags = [tag.strip() for tag in post_data['tags'].split(',') if tag.strip()] if post_data['tags'] else []
        
        # Parse date
        created_at = parse_date(post_data['created_at'])
        
        # Create community post
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO community (
                    user_id, title, content, procedure_id, category_id,
                    is_anonymous, tags, view_count, created_at,
                    reply_count, source_type
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                user_id,
                post_data['title'],
                post_data['content'],
                procedure_id,
                category_id,
                post_data['is_anonymous'].upper() == 'TRUE',
                tags,
                int(post_data['view_count']) if post_data['view_count'] else 0,
                created_at,
                0,  # Will update this after adding replies
                'manual'
            ))
            
            thread_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Created community post: {post_data['title']} (ID: {thread_id})")
            return thread_id
            
    except Exception as e:
        logger.error(f"Error creating community post {post_data['title']}: {str(e)}")
        conn.rollback()
        return None

def create_reply(conn, thread_id, reply_data, parent_reply_id=None):
    """Create a reply to a community post."""
    try:
        if not reply_data['content'] or reply_data['content'].strip() == '':
            return None
        
        # Determine user role
        role = 'patient'
        if reply_data['is_expert'].upper() == 'TRUE':
            role = 'expert'
        elif reply_data['is_doctor'].upper() == 'TRUE':
            role = 'doctor'
        
        # Get user ID
        user_id = get_or_create_user(conn, reply_data['username'], reply_data['email'], role)
        if not user_id:
            logger.error(f"Failed to get user ID for reply by {reply_data['username']}")
            return None
        
        # Parse date
        created_at = parse_date(reply_data['date'])
        
        # Create reply
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO community_replies (
                    thread_id, user_id, content, parent_reply_id,
                    is_anonymous, is_doctor_response, is_expert_advice, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                thread_id,
                user_id,
                reply_data['content'],
                parent_reply_id,
                reply_data['is_anonymous'].upper() == 'TRUE',
                reply_data['is_doctor'].upper() == 'TRUE',
                reply_data['is_expert'].upper() == 'TRUE',
                created_at
            ))
            
            reply_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Created reply by {reply_data['username']} for thread {thread_id}")
            return reply_id
            
    except Exception as e:
        logger.error(f"Error creating reply by {reply_data['username']}: {str(e)}")
        conn.rollback()
        return None

def update_reply_count(conn, thread_id):
    """Update reply count for a thread."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM community_replies WHERE thread_id = %s", (thread_id,))
            reply_count = cursor.fetchone()[0]
            
            cursor.execute("UPDATE community SET reply_count = %s WHERE id = %s", (reply_count, thread_id))
            conn.commit()
            
    except Exception as e:
        logger.error(f"Error updating reply count for thread {thread_id}: {str(e)}")

def import_csv_data(conn, csv_file_path):
    """Import community data from CSV file."""
    try:
        imported_posts = 0
        imported_replies = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Create main post
                thread_id = create_community_post(conn, row)
                if not thread_id:
                    continue
                
                imported_posts += 1
                
                # Process replies (up to 8 replies)
                reply_ids = {}  # Store reply IDs for nested replies
                
                for i in range(1, 9):  # replies 1-8
                    reply_prefix = f'reply_{i}_'
                    
                    # Check if reply exists
                    if not row.get(f'{reply_prefix}content') or row.get(f'{reply_prefix}content').strip() == '':
                        continue
                    
                    # Prepare reply data
                    reply_data = {
                        'content': row.get(f'{reply_prefix}content', ''),
                        'username': row.get(f'{reply_prefix}username', ''),
                        'email': row.get(f'{reply_prefix}email', ''),
                        'is_doctor': row.get(f'{reply_prefix}is_doctor', 'FALSE'),
                        'is_expert': row.get(f'{reply_prefix}is_expert', 'FALSE'),
                        'is_anonymous': row.get(f'{reply_prefix}is_anonymous', 'FALSE'),
                        'date': row.get(f'{reply_prefix}date', ''),
                    }
                    
                    # Check if this is a nested reply
                    parent_reply_str = row.get(f'{reply_prefix}parent_reply', '') or ''
                    parent_reply_num = parent_reply_str.strip()
                    parent_reply_id = None
                    
                    if parent_reply_num and parent_reply_num.isdigit():
                        parent_reply_id = reply_ids.get(int(parent_reply_num))
                    
                    # Create reply
                    reply_id = create_reply(conn, thread_id, reply_data, parent_reply_id)
                    if reply_id:
                        reply_ids[i] = reply_id
                        imported_replies += 1
                
                # Update reply count for the thread
                update_reply_count(conn, thread_id)
        
        logger.info(f"Successfully imported {imported_posts} posts and {imported_replies} replies")
        return imported_posts, imported_replies
        
    except Exception as e:
        logger.error(f"Error importing CSV data: {str(e)}")
        return 0, 0

def main():
    """Main function to import community CSV data."""
    logger.info("Starting community CSV import...")
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return 1
    
    try:
        # Import CSV data
        csv_file_path = "attached_assets/community_new - Sheet1.csv"
        posts_count, replies_count = import_csv_data(conn, csv_file_path)
        
        # Final summary
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM community WHERE source_type = 'manual'")
            total_manual_posts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM community_replies")
            total_replies = cursor.fetchone()[0]
        
        logger.info(f"=== IMPORT SUMMARY ===")
        logger.info(f"Imported Posts: {posts_count}")
        logger.info(f"Imported Replies: {replies_count}")
        logger.info(f"Total Manual Posts in DB: {total_manual_posts}")
        logger.info(f"Total Replies in DB: {total_replies}")
        logger.info(f"=== CSV import completed successfully ===")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during CSV import: {str(e)}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())