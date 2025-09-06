#!/usr/bin/env python3
"""
Check data in the database directly using SQL queries.

This script uses psycopg2 to connect directly to the database and query the relevant tables.
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(db_url)

def check_data():
    """Check data in the database and print counts and details."""
    try:
        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("\n===== DATABASE DATA CHECK =====\n")
        
        # Check users
        cur.execute("""
            SELECT id, email, role, name 
            FROM users 
            ORDER BY id
        """)
        users = cur.fetchall()
        print(f"Users: {len(users)}")
        for user in users:
            print(f"  ID: {user[0]} - Email: {user[1] or 'No email'} - Role: {user[2] or 'No role'} - Name: {user[3] or 'No name'}")
        print()
        
        # Check doctors
        cur.execute("""
            SELECT d.id, d.name, d.specialty, u.name as user_name 
            FROM doctors d
            LEFT JOIN users u ON d.user_id = u.id
            ORDER BY d.id
        """)
        doctors = cur.fetchall()
        print(f"Doctors: {len(doctors)}")
        for doctor in doctors:
            doctor_name = doctor[1] or doctor[3] or 'N/A'
            print(f"  ID: {doctor[0]} - Name: {doctor_name} - Specialty: {doctor[2] or 'No specialty'}")
        print()
        
        # Check procedures
        cur.execute("""
            SELECT p.id, p.procedure_name, c.name as category_name 
            FROM procedures p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.id
            LIMIT 11
        """)
        procedures = cur.fetchall()
        print(f"Procedures: {len(procedures) if len(procedures) < 11 else '10+'}")
        for procedure in procedures[:10]:
            print(f"  ID: {procedure[0]} - Name: {procedure[1] or 'No name'} - Category: {procedure[2] or 'N/A'}")
        if len(procedures) > 10:
            cur.execute("SELECT COUNT(*) FROM procedures")
            total_procedures = cur.fetchone()[0]
            print(f"  ... and {total_procedures - 10} more procedures")
        print()
        
        # Check categories
        cur.execute("""
            SELECT id, name 
            FROM categories 
            ORDER BY id
        """)
        categories = cur.fetchall()
        print(f"Categories: {len(categories)}")
        for category in categories:
            print(f"  ID: {category[0]} - Name: {category[1] or 'No name'}")
        print()
        
        # Check body parts
        cur.execute("""
            SELECT id, name 
            FROM body_parts 
            ORDER BY id
        """)
        body_parts = cur.fetchall()
        print(f"Body Parts: {len(body_parts)}")
        for body_part in body_parts:
            print(f"  ID: {body_part[0]} - Name: {body_part[1] or 'No name'}")
        print()
        
        # Check reviews
        cur.execute("""
            SELECT id, rating, content, procedure_id, doctor_id 
            FROM reviews 
            ORDER BY id
            LIMIT 11
        """)
        reviews = cur.fetchall()
        print(f"Reviews: {len(reviews) if len(reviews) < 11 else '10+'}")
        for review in reviews[:10]:
            content = review[2][:50] + '...' if review[2] and len(review[2]) > 50 else (review[2] or 'No content')
            print(f"  ID: {review[0]} - Rating: {review[1]} - Content: {content}")
        if len(reviews) > 10:
            cur.execute("SELECT COUNT(*) FROM reviews")
            total_reviews = cur.fetchone()[0]
            print(f"  ... and {total_reviews - 10} more reviews")
        print()
        
        # Check community threads
        cur.execute("""
            SELECT c.id, c.title, cat.name as category_name
            FROM community c
            LEFT JOIN categories cat ON c.category_id = cat.id
            ORDER BY c.id
            LIMIT 11
        """)
        threads = cur.fetchall()
        print(f"Community Threads: {len(threads) if len(threads) < 11 else '10+'}")
        for thread in threads[:10]:
            print(f"  ID: {thread[0]} - Title: {thread[1] or 'No title'} - Category: {thread[2] or 'N/A'}")
        if len(threads) > 10:
            cur.execute("SELECT COUNT(*) FROM community")
            total_threads = cur.fetchone()[0]
            print(f"  ... and {total_threads - 10} more threads")
            
        print("\n===== END OF DATABASE CHECK =====\n")
        
        # Close connection
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error checking database data: {str(e)}")

if __name__ == '__main__':
    check_data()