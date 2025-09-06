"""
Add image_url field to procedures table for popular procedure images.

This script adds an optional image_url field to store images for featured procedures
on the homepage, without requiring images for all 500+ procedures.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def add_image_field():
    """Add image_url field to procedures table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'procedures' AND column_name = 'image_url'
        """)
        
        if cursor.fetchone():
            print("✅ image_url field already exists in procedures table")
            return
        
        # Add the image_url column
        cursor.execute("""
            ALTER TABLE procedures 
            ADD COLUMN image_url VARCHAR(500)
        """)
        
        print("✅ Successfully added image_url field to procedures table")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error adding image_url field: {e}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the migration."""
    print("Adding image_url field to procedures table...")
    add_image_field()
    print("Migration complete!")

if __name__ == "__main__":
    main()