#!/usr/bin/env python3
"""
Import remaining community posts from CSV in smaller batches.
"""

import os
import sys
import csv
import logging
from datetime import datetime
import psycopg2

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        database_url = os.environ.get('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def get_or_create_user(conn, username, email, role='patient'):
    """Get user ID or create user if doesn't exist."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            cursor.execute("""
                INSERT INTO users (username, email, name, role, is_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (username, email, username, role, True, datetime.now()))
            
            user_id = cursor.fetchone()[0]
            conn.commit()
            return user_id
            
    except Exception as e:
        logger.error(f"Error with user {username}: {str(e)}")
        conn.rollback()
        return None

def get_procedure_id(conn, procedure_name):
    """Get procedure ID by name."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM procedures WHERE LOWER(procedure_name) = LOWER(%s)", (procedure_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    except:
        return None

def get_category_id(conn, category_name):
    """Get category ID by name."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM categories WHERE LOWER(name) = LOWER(%s)", (category_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    except:
        return None

def parse_date(date_str):
    """Parse date string to datetime object."""
    try:
        if not date_str or date_str.strip() == '':
            return datetime.now()
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return datetime.now()

def import_batch(conn, csv_file_path, start_row=1, batch_size=5):
    """Import a batch of posts starting from start_row."""
    try:
        imported_posts = 0
        imported_replies = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            rows = list(csv_reader)
            
            # Process only the specified batch
            end_row = min(start_row + batch_size, len(rows))
            
            for i in range(start_row, end_row):
                if i >= len(rows):
                    break
                    
                row = rows[i]
                logger.info(f"Processing post {i+1}: {row['title']}")
                
                # Get user ID
                user_id = get_or_create_user(conn, row['username'], row['email'])
                if not user_id:
                    continue
                
                # Get IDs
                procedure_id = get_procedure_id(conn, row['procedure_name'])
                category_id = get_category_id(conn, row['category_name'])
                
                # Parse data
                tags = [tag.strip() for tag in row['tags'].split(',') if tag.strip()] if row['tags'] else []
                created_at = parse_date(row['created_at'])
                
                # Create post
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
                        user_id, row['title'], row['content'], procedure_id, category_id,
                        row['is_anonymous'].upper() == 'TRUE', tags,
                        int(row['view_count']) if row['view_count'] else 0,
                        created_at, 0, 'manual'
                    ))
                    
                    thread_id = cursor.fetchone()[0]
                    conn.commit()
                    imported_posts += 1
                
                # Add replies
                reply_count = 0
                reply_ids = {}
                
                for j in range(1, 9):
                    reply_prefix = f'reply_{j}_'
                    content = row.get(f'{reply_prefix}content', '')
                    
                    if not content or content.strip() == '':
                        continue
                    
                    # Determine role
                    role = 'patient'
                    if row.get(f'{reply_prefix}is_expert', '').upper() == 'TRUE':
                        role = 'expert'
                    elif row.get(f'{reply_prefix}is_doctor', '').upper() == 'TRUE':
                        role = 'doctor'
                    
                    # Get user
                    reply_user_id = get_or_create_user(conn, 
                        row.get(f'{reply_prefix}username', ''),
                        row.get(f'{reply_prefix}email', ''), role)
                    
                    if not reply_user_id:
                        continue
                    
                    # Check for parent reply
                    parent_reply_str = row.get(f'{reply_prefix}parent_reply', '') or ''
                    parent_reply_id = None
                    if parent_reply_str.strip().isdigit():
                        parent_reply_id = reply_ids.get(int(parent_reply_str.strip()))
                    
                    # Create reply
                    reply_date = parse_date(row.get(f'{reply_prefix}date', ''))
                    
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO community_replies (
                                thread_id, user_id, content, parent_reply_id,
                                is_anonymous, is_doctor_response, is_expert_advice, created_at
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s
                            ) RETURNING id
                        """, (
                            thread_id, reply_user_id, content, parent_reply_id,
                            row.get(f'{reply_prefix}is_anonymous', '').upper() == 'TRUE',
                            row.get(f'{reply_prefix}is_doctor', '').upper() == 'TRUE',
                            row.get(f'{reply_prefix}is_expert', '').upper() == 'TRUE',
                            reply_date
                        ))
                        
                        reply_id = cursor.fetchone()[0]
                        reply_ids[j] = reply_id
                        reply_count += 1
                        imported_replies += 1
                        conn.commit()
                
                # Update reply count
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE community SET reply_count = %s WHERE id = %s", 
                                 (reply_count, thread_id))
                    conn.commit()
        
        logger.info(f"Batch complete: imported {imported_posts} posts and {imported_replies} replies")
        return imported_posts, imported_replies
        
    except Exception as e:
        logger.error(f"Error in batch import: {str(e)}")
        return 0, 0

def main():
    """Import remaining posts in batches."""
    conn = get_db_connection()
    if not conn:
        return 1
    
    try:
        # Check current count
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM community")
            current_count = cursor.fetchone()[0]
        
        logger.info(f"Current posts in database: {current_count}")
        
        csv_file_path = "attached_assets/community_new - Sheet1.csv"
        
        # Import remaining posts in batches of 5
        total_posts = 0
        total_replies = 0
        
        for start_row in range(current_count, 34, 5):
            logger.info(f"Processing batch starting from row {start_row + 1}")
            posts, replies = import_batch(conn, csv_file_path, start_row, 5)
            total_posts += posts
            total_replies += replies
            
            if posts == 0:
                break
        
        # Final count
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM community")
            final_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM community_replies")
            final_replies = cursor.fetchone()[0]
        
        logger.info(f"=== FINAL SUMMARY ===")
        logger.info(f"Total posts imported this run: {total_posts}")
        logger.info(f"Total replies imported this run: {total_replies}")
        logger.info(f"Final posts in database: {final_count}")
        logger.info(f"Final replies in database: {final_replies}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())