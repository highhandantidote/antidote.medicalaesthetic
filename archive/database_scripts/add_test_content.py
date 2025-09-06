"""
Add test content to the database, including categories, procedures, and threads.
"""
import os
import psycopg2
import logging
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def add_test_content():
    """Add test content to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Add body parts
        cursor.execute("SELECT COUNT(*) FROM body_parts")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO body_parts (name, description, created_at)
                VALUES 
                ('Face', 'Facial procedures and treatments', %s),
                ('Breast', 'Breast augmentation and reduction', %s),
                ('Body', 'Body contouring and sculpting', %s)
                RETURNING id
            """, (datetime.utcnow(), datetime.utcnow(), datetime.utcnow()))
            body_part_ids = cursor.fetchall()
            logger.info(f"Added body parts with IDs: {[bp[0] for bp in body_part_ids]}")
            
            # Get the face body part ID
            cursor.execute("SELECT id FROM body_parts WHERE name = 'Face'")
            face_id = cursor.fetchone()[0]
            
            # Add categories
            cursor.execute("""
                INSERT INTO categories (name, body_part_id, description, created_at)
                VALUES
                ('Rhinoplasty', %s, 'Nose reshaping procedures', %s),
                ('Facial Rejuvenation', %s, 'Procedures to restore youthful appearance', %s),
                ('Non-Surgical Treatments', %s, 'Non-invasive facial procedures', %s)
                RETURNING id
            """, (face_id, datetime.utcnow(), face_id, datetime.utcnow(), face_id, datetime.utcnow()))
            category_ids = cursor.fetchall()
            logger.info(f"Added categories with IDs: {[cat[0] for cat in category_ids]}")
            
            # Get the rhinoplasty category ID
            cursor.execute("SELECT id FROM categories WHERE name = 'Rhinoplasty'")
            rhinoplasty_id = cursor.fetchone()[0]
            
            # Add procedures
            cursor.execute("""
                INSERT INTO procedures 
                (procedure_name, short_description, overview, procedure_details, 
                ideal_candidates, recovery_process, recovery_time, results_duration,
                min_cost, max_cost, benefits, risks, procedure_types, category_id, created_at)
                VALUES 
                (
                    'Rhinoplasty', 
                    'Reshape the nose for improved appearance and function', 
                    'Rhinoplasty is a surgical procedure that changes the shape or size of the nose.', 
                    'The surgeon makes incisions to access the bones and cartilage that support the nose.',
                    'Candidates should be in good health and have realistic expectations.',
                    'Recovery typically takes 1-2 weeks for initial healing.',
                    '1-2 weeks for initial recovery, up to 1 year for final results',
                    'Permanent',
                    5000, 15000,
                    'Improved appearance, better breathing, boosted confidence',
                    'Infection, scarring, breathing difficulties, unsatisfactory results',
                    'Surgical',
                    %s,
                    %s
                )
                RETURNING id
            """, (rhinoplasty_id, datetime.utcnow()))
            procedure_id = cursor.fetchone()[0]
            logger.info(f"Added procedure with ID: {procedure_id}")
            
            # Add threads
            cursor.execute("""
                INSERT INTO threads
                (title, content, created_at, procedure_id, view_count, reply_count, keywords, user_id)
                VALUES
                (
                    'Rhinoplasty Experience', 
                    'I recently had rhinoplasty surgery and wanted to share my experience with the community.',
                    %s,
                    %s,
                    25,
                    2,
                    ARRAY['rhinoplasty', 'experience', 'recovery'],
                    2
                ),
                (
                    'Recovery Timeline After Rhinoplasty',
                    'How long did it take everyone to fully recover from rhinoplasty surgery?',
                    %s,
                    %s,
                    15,
                    1,
                    ARRAY['rhinoplasty', 'recovery', 'timeline'],
                    2
                ),
                (
                    'Cost of Rhinoplasty in Mumbai',
                    'I am considering rhinoplasty and wanted to know the average cost in Mumbai.',
                    %s,
                    %s,
                    30,
                    3,
                    ARRAY['rhinoplasty', 'cost', 'Mumbai'],
                    2
                )
                RETURNING id
            """, (datetime.utcnow(), procedure_id, datetime.utcnow(), procedure_id, datetime.utcnow(), procedure_id))
            thread_ids = cursor.fetchall()
            logger.info(f"Added threads with IDs: {[t[0] for t in thread_ids]}")
        else:
            logger.info("Content already exists, skipping addition.")
            
        conn.commit()
        logger.info("All test content added successfully.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding test content: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the test content creation."""
    try:
        add_test_content()
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())