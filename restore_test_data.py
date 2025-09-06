"""
Restore test data for the Antidote application.

This script creates:
1. Test user (testuser@antidote.com)
2. Test doctor (testdoctor@antidote.com)
3. Basic categories and procedures
4. Links between doctors and procedures
"""
import os
import sys
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database connection from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not found")
    sys.exit(1)

try:
    # Connect to the database
    logger.info("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # 1. Create test user
    logger.info("Creating test user...")
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = %s", ('testuser@antidote.com',))
    user = cursor.fetchone()
    
    if user:
        user_id = user['id']
        logger.info(f"Test user already exists with ID: {user_id}")
    else:
        cursor.execute("""
            INSERT INTO users (username, email, phone_number, role, password_hash, is_verified, created_at, role_type, name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            'testuser',
            'testuser@antidote.com',
            '9876543210',
            'user',
            generate_password_hash('Test1234'),
            True,
            datetime.now(),
            'patient',
            'Test User'
        ))
        user_id = cursor.fetchone()[0]
        logger.info(f"Created test user with ID: {user_id}")
        
    # 2. Create test doctor user
    logger.info("Creating test doctor user...")
    
    cursor.execute("SELECT id FROM users WHERE email = %s", ('testdoctor@antidote.com',))
    doctor_user = cursor.fetchone()
    
    if doctor_user:
        doctor_user_id = doctor_user['id']
        logger.info(f"Test doctor user already exists with ID: {doctor_user_id}")
    else:
        cursor.execute("""
            INSERT INTO users (username, email, phone_number, role, password_hash, is_verified, created_at, role_type, name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            'testdoctor',
            'testdoctor@antidote.com',
            '1234567890',
            'doctor',
            generate_password_hash('Doctor1234'),
            True,
            datetime.now(),
            'physician',
            'Dr. John Smith'
        ))
        doctor_user_id = cursor.fetchone()[0]
        logger.info(f"Created test doctor user with ID: {doctor_user_id}")
        
    # 3. Create doctor profile
    logger.info("Creating doctor profile...")
    
    cursor.execute("SELECT id FROM doctors WHERE user_id = %s", (doctor_user_id,))
    doctor = cursor.fetchone()
    
    if doctor:
        doctor_id = doctor['id']
        logger.info(f"Doctor profile already exists with ID: {doctor_id}")
    else:
        cursor.execute("""
            INSERT INTO doctors (user_id, name, specialty, experience, city, state, hospital, 
                            consultation_fee, is_verified, rating, review_count, created_at, bio,
                            verification_status, verification_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            doctor_user_id,
            'Dr. John Smith',
            'Plastic Surgery',
            10,
            'Mumbai',
            'Maharashtra',
            'City Hospital',
            2000,
            True,
            4.8,
            25,
            datetime.now(),
            'Board certified plastic surgeon with expertise in facial procedures.',
            'approved',
            datetime.now()
        ))
        doctor_id = cursor.fetchone()[0]
        logger.info(f"Created doctor profile with ID: {doctor_id}")
        
    # 4. Create body part
    logger.info("Creating body parts...")
    
    cursor.execute("SELECT id FROM body_parts WHERE name = %s", ('Face',))
    face = cursor.fetchone()
    
    if face:
        face_id = face['id']
        logger.info(f"Face body part already exists with ID: {face_id}")
    else:
        cursor.execute("""
            INSERT INTO body_parts (name, description)
            VALUES (%s, %s) RETURNING id
        """, (
            'Face',
            'Facial procedures and treatments'
        ))
        face_id = cursor.fetchone()[0]
        logger.info(f"Created Face body part with ID: {face_id}")
        
    # Create another body part
    cursor.execute("SELECT id FROM body_parts WHERE name = %s", ('Nose',))
    nose = cursor.fetchone()
    
    if nose:
        nose_id = nose['id']
        logger.info(f"Nose body part already exists with ID: {nose_id}")
    else:
        cursor.execute("""
            INSERT INTO body_parts (name, description)
            VALUES (%s, %s) RETURNING id
        """, (
            'Nose',
            'Nasal procedures and treatments'
        ))
        nose_id = cursor.fetchone()[0]
        logger.info(f"Created Nose body part with ID: {nose_id}")
        
    # 5. Create categories
    logger.info("Creating categories...")
    
    cursor.execute("SELECT id FROM categories WHERE name = %s", ('Facial Procedures',))
    category = cursor.fetchone()
    
    if category:
        category_id = category['id']
        logger.info(f"Facial Procedures category already exists with ID: {category_id}")
    else:
        cursor.execute("""
            INSERT INTO categories (name, body_part_id, description)
            VALUES (%s, %s, %s) RETURNING id
        """, (
            'Facial Procedures',
            face_id,
            'Procedures that focus on enhancing facial features'
        ))
        category_id = cursor.fetchone()[0]
        logger.info(f"Created Facial Procedures category with ID: {category_id}")
        
    # Create another category
    cursor.execute("SELECT id FROM categories WHERE name = %s", ('Rhinoplasty',))
    rhino_category = cursor.fetchone()
    
    if rhino_category:
        rhino_category_id = rhino_category['id']
        logger.info(f"Rhinoplasty category already exists with ID: {rhino_category_id}")
    else:
        cursor.execute("""
            INSERT INTO categories (name, body_part_id, description)
            VALUES (%s, %s, %s) RETURNING id
        """, (
            'Rhinoplasty',
            nose_id,
            'Nose reshaping procedures'
        ))
        rhino_category_id = cursor.fetchone()[0]
        logger.info(f"Created Rhinoplasty category with ID: {rhino_category_id}")
        
    # 6. Create procedures
    logger.info("Creating procedures...")
    
    cursor.execute("SELECT id FROM procedures WHERE procedure_name = %s", ('Rhinoplasty',))
    procedure = cursor.fetchone()
    
    if procedure:
        procedure_id = procedure['id']
        logger.info(f"Rhinoplasty procedure already exists with ID: {procedure_id}")
    else:
        cursor.execute("""
            INSERT INTO procedures (procedure_name, short_description, overview, procedure_details,
                             ideal_candidates, recovery_process, recovery_time, results_duration,
                             min_cost, max_cost, benefits, risks, procedure_types, 
                             alternative_procedures, category_id, popularity_score, body_part, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            'Rhinoplasty',
            'Nose reshaping surgery',
            'Rhinoplasty is a surgical procedure that changes the shape of your nose by modifying the bone or cartilage.',
            'The surgeon makes cuts within the nostrils or across the base of the nose, then reshapes the inner bone and cartilage to produce a more pleasing appearance.',
            'People who are physically healthy, don\'t smoke, and have realistic goals.',
            'Swelling and bruising around the eyes and nose for 1-2 weeks. Final result visible after 1 year when all swelling subsides.',
            '1-2 weeks for initial recovery',
            'Permanent',
            35000,
            100000,
            'Improved appearance, better breathing, enhanced self-confidence',
            'Bleeding, infection, adverse anesthesia reactions, changes in skin sensation',
            'Open rhinoplasty, closed rhinoplasty',
            'Non-surgical rhinoplasty using fillers',
            rhino_category_id,
            90,
            'Nose',
            ['Surgical', 'Cosmetic']
        ))
        procedure_id = cursor.fetchone()[0]
        logger.info(f"Created Rhinoplasty procedure with ID: {procedure_id}")
    
    # Create another procedure
    cursor.execute("SELECT id FROM procedures WHERE procedure_name = %s", ('Facelift',))
    procedure2 = cursor.fetchone()
    
    if procedure2:
        procedure2_id = procedure2['id']
        logger.info(f"Facelift procedure already exists with ID: {procedure2_id}")
    else:
        cursor.execute("""
            INSERT INTO procedures (procedure_name, short_description, overview, procedure_details,
                             ideal_candidates, recovery_process, recovery_time, results_duration,
                             min_cost, max_cost, benefits, risks, procedure_types, 
                             alternative_procedures, category_id, popularity_score, body_part, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            'Facelift',
            'Surgical procedure to reduce visible signs of aging in the face and neck',
            'A facelift (rhytidectomy) is a surgical procedure that improves visible signs of aging in the face and neck.',
            'During a facelift, excess facial skin is removed, with the remaining skin redraped over the newly repositioned facial tissues.',
            'People in good health who have sagging in their face or neck but still have some skin elasticity.',
            'Swelling, bruising, and numbness for 1-2 weeks. Final healing can take several months.',
            '2-4 weeks for initial recovery',
            '5-10 years',
            60000,
            150000,
            'More youthful appearance, reduced sagging, improved facial contours',
            'Scarring, nerve injury, hair loss around incisions, infection',
            'Traditional facelift, mini facelift, neck lift',
            'Fillers, botox, laser treatments',
            category_id,
            80,
            'Face',
            ['Surgical', 'Anti-aging']
        ))
        procedure2_id = cursor.fetchone()[0]
        logger.info(f"Created Facelift procedure with ID: {procedure2_id}")
        
    # 7. Link doctor to category
    logger.info("Linking doctor to categories...")
    
    cursor.execute("SELECT id FROM doctor_categories WHERE doctor_id = %s AND category_id = %s", 
                (doctor_id, category_id))
    doctor_category = cursor.fetchone()
    
    if doctor_category:
        logger.info(f"Doctor already linked to category")
    else:
        cursor.execute("""
            INSERT INTO doctor_categories (doctor_id, category_id, is_verified, created_at)
            VALUES (%s, %s, %s, %s)
        """, (
            doctor_id,
            category_id,
            True,
            datetime.now()
        ))
        logger.info(f"Linked doctor to category")
        
    # Link to second category
    cursor.execute("SELECT id FROM doctor_categories WHERE doctor_id = %s AND category_id = %s", 
                (doctor_id, rhino_category_id))
    doctor_category2 = cursor.fetchone()
    
    if doctor_category2:
        logger.info(f"Doctor already linked to rhinoplasty category")
    else:
        cursor.execute("""
            INSERT INTO doctor_categories (doctor_id, category_id, is_verified, created_at)
            VALUES (%s, %s, %s, %s)
        """, (
            doctor_id,
            rhino_category_id,
            True,
            datetime.now()
        ))
        logger.info(f"Linked doctor to rhinoplasty category")
        
    # 8. Link doctor to procedures
    logger.info("Linking doctor to procedures...")
    
    cursor.execute("SELECT id FROM doctor_procedures WHERE doctor_id = %s AND procedure_id = %s", 
                (doctor_id, procedure_id))
    doctor_procedure = cursor.fetchone()
    
    if doctor_procedure:
        logger.info(f"Doctor already linked to Rhinoplasty procedure")
    else:
        cursor.execute("""
            INSERT INTO doctor_procedures (doctor_id, procedure_id, created_at)
            VALUES (%s, %s, %s)
        """, (
            doctor_id,
            procedure_id,
            datetime.now()
        ))
        logger.info(f"Linked doctor to Rhinoplasty procedure")
        
    # Link to second procedure
    cursor.execute("SELECT id FROM doctor_procedures WHERE doctor_id = %s AND procedure_id = %s", 
                (doctor_id, procedure2_id))
    doctor_procedure2 = cursor.fetchone()
    
    if doctor_procedure2:
        logger.info(f"Doctor already linked to Facelift procedure")
    else:
        cursor.execute("""
            INSERT INTO doctor_procedures (doctor_id, procedure_id, created_at)
            VALUES (%s, %s, %s)
        """, (
            doctor_id,
            procedure2_id,
            datetime.now()
        ))
        logger.info(f"Linked doctor to Facelift procedure")
    
    # 9. Create a community thread
    logger.info("Creating community thread...")
    
    cursor.execute("SELECT id FROM community WHERE title = %s", ('Rhinoplasty Recovery Tips',))
    thread = cursor.fetchone()
    
    if thread:
        thread_id = thread['id']
        logger.info(f"Community thread already exists with ID: {thread_id}")
    else:
        cursor.execute("""
            INSERT INTO community (user_id, title, content, is_anonymous, created_at, 
                           updated_at, view_count, reply_count, featured, tags, 
                           category_id, procedure_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            user_id,
            'Rhinoplasty Recovery Tips',
            'I recently had rhinoplasty surgery and wanted to share some recovery tips that helped me. What was your recovery experience like?',
            False,
            datetime.now(),
            datetime.now(),
            15,
            2,
            True,
            ['Recovery', 'Tips', 'Rhinoplasty'],
            rhino_category_id,
            procedure_id
        ))
        thread_id = cursor.fetchone()[0]
        logger.info(f"Created community thread with ID: {thread_id}")
        
    # 10. Create thread replies
    logger.info("Creating thread replies...")
    
    cursor.execute("SELECT id FROM community_replies WHERE thread_id = %s AND user_id = %s", 
                 (thread_id, doctor_user_id))
    reply = cursor.fetchone()
    
    if reply:
        reply_id = reply['id']
        logger.info(f"Doctor reply already exists with ID: {reply_id}")
    else:
        cursor.execute("""
            INSERT INTO community_replies (thread_id, user_id, content, is_anonymous, 
                                  is_doctor_response, created_at, upvotes, is_expert_advice)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            thread_id,
            doctor_user_id,
            'As a doctor who performs rhinoplasty, I recommend using cold compresses, keeping your head elevated, and avoiding blowing your nose for at least two weeks after surgery.',
            False,
            True,
            datetime.now(),
            5,
            True
        ))
        reply_id = cursor.fetchone()[0]
        logger.info(f"Created doctor reply with ID: {reply_id}")
        
    # Add another reply from the regular user
    cursor.execute("SELECT COUNT(*) FROM community_replies WHERE thread_id = %s AND user_id = %s AND content LIKE %s", 
                 (thread_id, user_id, 'Thank you%'))
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.info(f"User reply already exists")
    else:
        cursor.execute("""
            INSERT INTO community_replies (thread_id, user_id, content, is_anonymous, 
                                  is_doctor_response, created_at, upvotes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            thread_id,
            user_id,
            'Thank you Dr. Smith! Those tips were really helpful during my recovery.',
            False,
            False,
            datetime.now(),
            2
        ))
        logger.info(f"Created user reply")
        
    # Commit all changes
    conn.commit()
    logger.info("All test data has been created successfully!")
    
except Exception as e:
    conn.rollback()
    logger.error(f"Error creating test data: {str(e)}")
    sys.exit(1)
    
finally:
    # Close cursor and connection
    cursor.close()
    conn.close()
    
print("Test data creation completed successfully!")
print("Created test user: testuser@antidote.com / Test1234")
print("Created test doctor: testdoctor@antidote.com / Doctor1234")
print("Created procedures: Rhinoplasty, Facelift")
print("Created community thread with replies")