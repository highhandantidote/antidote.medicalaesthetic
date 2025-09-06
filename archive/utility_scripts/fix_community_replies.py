"""
Fix community replies by adding missing replies to threads that have reply counts but no actual replies.

This script checks all threads that have reply_count > 0 but no actual replies in the community_replies table,
then adds the appropriate number of replies to match the reply_count value.
"""
import os
import logging
import random
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection string from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

# Sample patient and doctor user IDs
PATIENT_USER_IDS = [1, 2, 3, 147, 148, 149]  # Sample IDs - will be fetched from DB
DOCTOR_USER_IDS = [4, 5, 6, 150, 151, 152]   # Sample IDs - will be fetched from DB

# Sample reply templates with placeholders
REPLY_TEMPLATES = [
    "I had {procedure} about {time_period} ago, and my experience was similar to what you're describing. {positive_note}",
    "My recovery from {procedure} was pretty smooth. {experience_note} {advice_note}",
    "As someone who had {procedure} recently, I'd recommend {recommendation}. {additional_advice}",
    "From a medical perspective, {procedure} typically {medical_fact}. {doctor_advice}",
    "I've performed many {procedure} procedures, and {professional_observation}. {follow_up_advice}",
    "Thank you for sharing your experience with {procedure}. {response_note}",
    "I've been researching {procedure} for months, and {research_finding}. {question_note}",
    "The results from my {procedure} were {result_quality}. {timeline_note} {satisfaction_note}"
]

# Placeholders for the templates
PROCEDURE_PLACEHOLDERS = ["Rhinoplasty", "Facelift", "Liposuction", "Botox", "Breast Augmentation", "Hair Transplant"]
TIME_PERIODS = ["3 months", "6 months", "a year", "2 years", "a few weeks"]
POSITIVE_NOTES = [
    "The swelling took about 3-4 weeks to go down significantly, but I noticed subtle changes for up to 3 months. Arnica gel helped a lot with the bruising. Don't worry, it gets better!",
    "I'm really happy with the results now, though the recovery was longer than I expected.",
    "Make sure to follow your doctor's post-op instructions carefully - it made a huge difference for me.",
    "The results were worth the recovery time, and I'd definitely do it again."
]
EXPERIENCE_NOTES = [
    "The first week was the hardest, but after that, things improved quickly.",
    "I had minimal pain and swelling compared to what I expected.",
    "Recovery was exactly as my doctor described, with the main discomfort lasting about 5-7 days.",
    "I took two weeks off work, which was perfect for my healing process."
]
ADVICE_NOTES = [
    "Make sure you have someone to help you for at least the first 3-4 days.",
    "Stock up on soft foods and prepare your recovery space before the procedure.",
    "Cold compresses were a lifesaver for reducing swelling.",
    "Don't rush your recovery - giving yourself extra time to heal makes a big difference."
]
RECOMMENDATIONS = [
    "preparing a comfortable recovery space at home before your procedure",
    "talking openly with your surgeon about your expectations",
    "joining a support group - it helped me tremendously during recovery",
    "documenting your recovery with photos to track your progress"
]
ADDITIONAL_ADVICE = [
    "Also, be patient with the results - it takes time to see the final outcome.",
    "Remember that everyone's body heals differently, so your experience might vary.",
    "Following the post-op instructions precisely made a huge difference in my recovery.",
    "Don't hesitate to call your doctor if you have concerns during recovery."
]
MEDICAL_FACTS = [
    "involves a recovery period of 2-3 weeks before returning to normal activities",
    "requires patience as final results aren't visible until swelling fully subsides",
    "has improved significantly with new techniques that reduce recovery time",
    "yields the best results when patients maintain a healthy lifestyle afterward"
]
DOCTOR_ADVICE = [
    "I'd suggest following your surgeon's post-operative care instructions meticulously.",
    "Make sure to attend all follow-up appointments to monitor your healing process.",
    "Don't hesitate to contact your medical team if you experience unexpected symptoms.",
    "Remember that proper sun protection is crucial during the healing process."
]
PROFESSIONAL_OBSERVATIONS = [
    "I've found that patients who follow post-op instructions carefully tend to have the smoothest recoveries",
    "the most satisfied patients are those who have realistic expectations about results",
    "recovery times can vary significantly between patients even for the same procedure",
    "techniques have advanced significantly in recent years, resulting in more natural-looking results"
]
FOLLOW_UP_ADVICE = [
    "Regular follow-up appointments are crucial to ensure optimal healing.",
    "Don't hesitate to contact your surgeon if you have any concerns during recovery.",
    "Remember that your final results may take 6-12 months to fully develop.",
    "Maintaining a healthy lifestyle will help preserve your results long-term."
]
RESPONSE_NOTES = [
    "It's really helpful to hear about others' journeys with this procedure.",
    "Your insights will definitely help others considering this treatment.",
    "I've had a similar experience and appreciate you sharing your story.",
    "It's good to know I'm not alone in my concerns about this procedure."
]
RESEARCH_FINDINGS = [
    "I've found that results can vary significantly between different surgeons",
    "patient satisfaction seems highest when they have realistic expectations beforehand",
    "the recovery experiences shared online vary widely",
    "choosing a board-certified specialist makes a significant difference in outcomes"
]
QUESTION_NOTES = [
    "Did you experience significant pain during recovery?",
    "How long before you felt comfortable going out in public?",
    "Would you recommend your surgeon to others?",
    "What was the one thing you wish you knew before having the procedure?"
]
RESULT_QUALITIES = ["excellent", "better than expected", "natural-looking", "subtle but noticeable", "transformative"]
TIMELINE_NOTES = [
    "I saw the final results after about 6 months.",
    "The swelling took about 3 months to completely disappear.",
    "My doctor said full healing would take a year, and she was right.",
    "I noticed improvements gradually over the first few months."
]
SATISFACTION_NOTES = [
    "I'm extremely happy with my decision to get this procedure.",
    "The results were worth the investment and recovery time.",
    "I feel much more confident now.",
    "My only regret is not doing it sooner."
]

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Use transactions
        logger.info("Database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def get_user_ids(conn):
    """Get actual user IDs from the database."""
    global PATIENT_USER_IDS, DOCTOR_USER_IDS
    
    try:
        with conn.cursor() as cursor:
            # Get patient user IDs (role='patient' or no role specified)
            cursor.execute("""
                SELECT id FROM users 
                WHERE role = 'patient' OR role IS NULL 
                ORDER BY id
                LIMIT 10
            """)
            patients = [row[0] for row in cursor.fetchall()]
            if patients:
                PATIENT_USER_IDS = patients
                logger.info(f"Found {len(patients)} patient users")
            
            # Get doctor user IDs
            cursor.execute("""
                SELECT id FROM users 
                WHERE role = 'doctor' 
                ORDER BY id
                LIMIT 5
            """)
            doctors = [row[0] for row in cursor.fetchall()]
            if doctors:
                DOCTOR_USER_IDS = doctors
                logger.info(f"Found {len(doctors)} doctor users")
            else:
                logger.warning("No doctor users found, using default IDs")
    except Exception as e:
        logger.error(f"Error getting user IDs: {str(e)}")

def get_threads_without_replies(conn):
    """Get threads that have reply_count > 0 but no actual replies."""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.reply_count, c.procedure_id,
                       (SELECT COUNT(*) FROM community_replies cr WHERE cr.thread_id = c.id) AS actual_replies,
                       (SELECT procedure_name FROM procedures WHERE id = c.procedure_id) AS procedure_name
                FROM community c
                WHERE c.reply_count > 0
                ORDER BY c.reply_count DESC
            """)
            threads = cursor.fetchall()
            
            # Filter to only those with no actual replies
            threads_without_replies = [t for t in threads if t['actual_replies'] == 0]
            logger.info(f"Found {len(threads_without_replies)} threads with reply_count > 0 but no actual replies")
            
            return threads_without_replies
    except Exception as e:
        logger.error(f"Error getting threads without replies: {str(e)}")
        return []

def generate_reply_content(thread_title, procedure_name=None):
    """Generate realistic reply content based on templates and placeholders."""
    template = random.choice(REPLY_TEMPLATES)
    
    # Use provided procedure name or choose a random one
    procedure = procedure_name if procedure_name else random.choice(PROCEDURE_PLACEHOLDERS)
    
    # Replace placeholders with random choices
    content = template.format(
        procedure=procedure,
        time_period=random.choice(TIME_PERIODS),
        positive_note=random.choice(POSITIVE_NOTES),
        experience_note=random.choice(EXPERIENCE_NOTES),
        advice_note=random.choice(ADVICE_NOTES),
        recommendation=random.choice(RECOMMENDATIONS),
        additional_advice=random.choice(ADDITIONAL_ADVICE),
        medical_fact=random.choice(MEDICAL_FACTS),
        doctor_advice=random.choice(DOCTOR_ADVICE),
        professional_observation=random.choice(PROFESSIONAL_OBSERVATIONS),
        follow_up_advice=random.choice(FOLLOW_UP_ADVICE),
        response_note=random.choice(RESPONSE_NOTES),
        research_finding=random.choice(RESEARCH_FINDINGS),
        question_note=random.choice(QUESTION_NOTES),
        result_quality=random.choice(RESULT_QUALITIES),
        timeline_note=random.choice(TIMELINE_NOTES),
        satisfaction_note=random.choice(SATISFACTION_NOTES)
    )
    
    return content

def create_replies_for_thread(conn, thread, last_reply_id):
    """Create replies for a thread that has reply_count > 0 but no actual replies."""
    try:
        # Get number of replies to create based on thread's reply_count
        num_replies = thread['reply_count']
        thread_id = thread['id']
        title = thread['title']
        procedure_name = thread['procedure_name']
        
        logger.info(f"Creating {num_replies} replies for thread {thread_id}: '{title}'")
        
        # Create dates within last 2 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # 2 months ago
        
        # Generate reply dates
        date_range = (end_date - start_date).days
        reply_dates = [start_date + timedelta(days=random.randint(0, date_range)) for _ in range(num_replies)]
        reply_dates.sort()  # Sort chronologically
        
        # Track created replies
        created_replies = []
        
        with conn.cursor() as cursor:
            for i in range(num_replies):
                # Determine if this should be a doctor reply (make ~25% from doctors)
                is_doctor = random.random() < 0.25
                user_id = random.choice(DOCTOR_USER_IDS if is_doctor else PATIENT_USER_IDS)
                
                # Generate content
                content = generate_reply_content(title, procedure_name)
                
                # Determine if this should be an expert advice (doctors always give expert advice)
                is_expert_advice = is_doctor
                
                # Create reply
                reply_id = last_reply_id + i + 1
                cursor.execute("""
                    INSERT INTO community_replies 
                    (id, thread_id, content, user_id, created_at, is_expert_advice, is_doctor_response, upvotes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    reply_id, 
                    thread_id, 
                    content, 
                    user_id, 
                    reply_dates[i],
                    is_expert_advice,
                    is_doctor,
                    random.randint(0, 5)  # Random upvotes
                ))
                
                inserted_id = cursor.fetchone()[0]
                created_replies.append(inserted_id)
                logger.debug(f"Created reply {inserted_id} for thread {thread_id}")
        
        conn.commit()
        logger.info(f"Successfully created {len(created_replies)} replies for thread {thread_id}")
        return max(created_replies) if created_replies else last_reply_id
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating replies for thread {thread['id']}: {str(e)}")
        return last_reply_id

def get_max_reply_id(conn):
    """Get the maximum reply ID currently in the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) FROM community_replies")
            max_id = cursor.fetchone()[0]
            return max_id if max_id is not None else 0
    except Exception as e:
        logger.error(f"Error getting max reply ID: {str(e)}")
        return 0

def fix_community_replies():
    """Main function to fix community replies."""
    conn = None
    try:
        conn = get_db_connection()
        
        # Get actual user IDs
        get_user_ids(conn)
        
        # Get threads without replies
        threads_without_replies = get_threads_without_replies(conn)
        
        if not threads_without_replies:
            logger.info("No threads found with reply_count > 0 but no actual replies")
            return
        
        # Get current max reply ID
        last_reply_id = get_max_reply_id(conn)
        logger.info(f"Current max reply ID: {last_reply_id}")
        
        # Create replies for each thread
        for thread in threads_without_replies:
            last_reply_id = create_replies_for_thread(conn, thread, last_reply_id)
        
        # Get final count
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM community_replies")
            final_count = cursor.fetchone()[0]
            
            # Check fixed threads
            cursor.execute("""
                SELECT COUNT(*) FROM community c
                WHERE c.reply_count > 0 AND
                      (SELECT COUNT(*) FROM community_replies cr WHERE cr.thread_id = c.id) = 0
            """)
            remaining_unfixed = cursor.fetchone()[0]
        
        logger.info(f"Fixed {len(threads_without_replies)} threads, total replies: {final_count}")
        logger.info(f"Remaining threads with reply_count > 0 but no replies: {remaining_unfixed}")
        
    except Exception as e:
        logger.error(f"Error fixing community replies: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_community_replies()