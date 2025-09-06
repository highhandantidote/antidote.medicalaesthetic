#!/usr/bin/env python3
"""
Generate community threads and replies for the Antidote platform.

This script:
1. Creates patient and doctor user accounts if they don't exist
2. Generates 125 community threads with realistic topics and content
3. Adds 2-4 replies to each thread
4. Creates CSV files for import validation
5. Preserves all existing data

Usage:
    python generate_community_content.py
"""
import os
import sys
import csv
import json
import random
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from pathlib import Path
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("generate_community_content.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PATIENT_USERS = [
    {"username": "patientuser1", "email": "patient1@example.com", "role": "patient", "phone_number": "+919876543201", "name": "Patient User 1"},
    {"username": "patientuser2", "email": "patient2@example.com", "role": "patient", "phone_number": "+919876543202", "name": "Patient User 2"},
    {"username": "testuser", "email": "test@example.com", "role": "patient", "phone_number": "+919876543203", "name": "Test User"},
    {"username": "patient1", "email": "patient1@antidote.com", "role": "patient", "phone_number": "+919876543204", "name": "Patient One"},
    {"username": "patient2", "email": "patient2@antidote.com", "role": "patient", "phone_number": "+919876543205", "name": "Patient Two"},
    {"username": "patient3", "email": "patient3@antidote.com", "role": "patient", "phone_number": "+919876543206", "name": "Patient Three"},
]

DOCTOR_USERS = [
    {"username": "doctor_kumar", "email": "drkumar@example.com", "role": "doctor", "phone_number": "+919876543207", "name": "Dr. Kumar"},
    {"username": "dr.sharma", "email": "dr.sharma@antidote.com", "role": "doctor", "phone_number": "+919876543208", "name": "Dr. Sharma"},
    {"username": "dr.patel", "email": "dr.patel@antidote.com", "role": "doctor", "phone_number": "+919876543209", "name": "Dr. Patel"},
]

# Thread topics by procedure
THREAD_TOPICS = {
    "Rhinoplasty": [
        "Recovery after Rhinoplasty - what to expect?",
        "Rhinoplasty swelling - how long does it last?",
        "Post-operative care for Rhinoplasty patients",
        "Pain management after Rhinoplasty",
        "When will I see final results after Rhinoplasty?",
        "Are revision surgeries common after Rhinoplasty?",
        "Best sleeping position after Rhinoplasty",
        "How to reduce bruising after Rhinoplasty?",
        "Rhinoplasty recovery timeline - week by week",
        "How to clean your nose after Rhinoplasty"
    ],
    "Breast Augmentation": [
        "Breast Augmentation recovery - what to expect?",
        "Choosing the right implant size for Breast Augmentation",
        "Post-operative care after Breast Augmentation",
        "Massage techniques after Breast Augmentation",
        "Exercise restrictions after Breast Augmentation",
        "When can I sleep on my side after Breast Augmentation?",
        "Silicone vs. Saline implants - pros and cons",
        "How long do breast implants last?",
        "Signs of capsular contracture after Breast Augmentation",
        "Recovery timeline after Breast Augmentation"
    ],
    "Liposuction": [
        "Liposuction recovery - what to expect?",
        "Compression garments after Liposuction - how long to wear?",
        "Dealing with swelling after Liposuction",
        "When can I exercise after Liposuction?",
        "Liposuction vs. non-surgical alternatives",
        "Combining Liposuction with other procedures",
        "Pain management after Liposuction",
        "How much fat can be removed with Liposuction?",
        "Maintaining results after Liposuction",
        "Types of Liposuction techniques"
    ],
    "Tummy Tuck": [
        "Tummy Tuck recovery timeline",
        "Pain management after Tummy Tuck",
        "Sleeping positions after Tummy Tuck",
        "When can I exercise after Tummy Tuck?",
        "Tummy Tuck vs. Liposuction - which is right for me?",
        "Dealing with drains after Tummy Tuck",
        "Scar care after Tummy Tuck",
        "Mini Tummy Tuck vs. Full Tummy Tuck",
        "Combining Tummy Tuck with other procedures",
        "Long-term results of Tummy Tuck"
    ],
    "Brazilian Butt Lift": [
        "Brazilian Butt Lift recovery - what to expect?",
        "Sitting restrictions after Brazilian Butt Lift",
        "How long do BBL results last?",
        "Fat survival rate after Brazilian Butt Lift",
        "BBL vs. butt implants - pros and cons",
        "Exercise after Brazilian Butt Lift",
        "Sleeping positions after Brazilian Butt Lift",
        "Safety concerns with Brazilian Butt Lift",
        "Maintaining results after Brazilian Butt Lift",
        "What makes a good candidate for BBL?"
    ],
    "Facelift": [
        "Facelift recovery timeline",
        "Minimizing swelling after Facelift",
        "Sleeping positions after Facelift",
        "Types of Facelifts and their differences",
        "Non-surgical alternatives to Facelift",
        "Scar care after Facelift",
        "How long do Facelift results last?",
        "Pain management after Facelift",
        "Combining Facelift with other procedures",
        "When can I wear makeup after Facelift?"
    ],
    "Hair Transplant": [
        "Hair Transplant recovery - what to expect?",
        "FUE vs. FUT hair transplant techniques",
        "When will I see results after Hair Transplant?",
        "Post-operative care after Hair Transplant",
        "Managing expectations after Hair Transplant",
        "Sleeping positions after Hair Transplant",
        "Hair washing after Hair Transplant",
        "Does Hair Transplant hurt?",
        "How to choose a good Hair Transplant surgeon",
        "Long-term results of Hair Transplant"
    ],
    "Blepharoplasty": [
        "Eyelid surgery (Blepharoplasty) recovery timeline",
        "Reducing swelling after Blepharoplasty",
        "Vision changes after Blepharoplasty",
        "Upper vs. Lower Blepharoplasty",
        "Scar care after Blepharoplasty",
        "When can I wear contacts after Blepharoplasty?",
        "How long do Blepharoplasty results last?",
        "Non-surgical alternatives to Blepharoplasty",
        "Asian Blepharoplasty considerations",
        "Combining Blepharoplasty with other procedures"
    ],
    "General": [
        "How to choose the right plastic surgeon?",
        "Questions to ask during your consultation",
        "Preparing for plastic surgery",
        "Recovery essentials after plastic surgery",
        "Managing expectations in plastic surgery",
        "Plastic surgery abroad - pros and cons",
        "Financing options for plastic surgery",
        "How to tell if you're ready for plastic surgery",
        "Discussing plastic surgery with family and friends",
        "Non-surgical alternatives to plastic surgery",
        "Mental health considerations before plastic surgery",
        "Best age for different plastic surgery procedures",
        "Combining multiple plastic surgery procedures",
        "How to spot red flags when choosing a surgeon",
        "Plastic surgery myths debunked"
    ]
}

# Thread and reply templates
THREAD_CONTENT_TEMPLATES = [
    "Hi everyone, I'm considering getting {procedure} and I'm a bit nervous about the recovery process. Can anyone share their experience? How long did it take you to feel normal again? What was the pain level like? Any tips for making recovery easier? Thanks in advance for any advice!",
    
    "I recently had {procedure} (2 weeks ago) and I'm experiencing quite a bit of swelling and bruising. My doctor says this is normal, but I wanted to check with others who've gone through this. How long did your swelling last? Did you do anything specific that helped reduce it faster? I'm using ice packs and keeping my head elevated as advised.",
    
    "I'm researching {procedure} and trying to understand the different techniques available. I've heard terms like 'open' and 'closed' techniques, but I'm not sure what's best for my situation. Could those who've had this procedure share what technique your surgeon used and why? What were the pros and cons in your experience?",
    
    "Cost question about {procedure} - I've been quoted a wide range of prices from different surgeons for the same procedure. The difference is substantial (almost $3000 between the lowest and highest). What factors should I consider besides cost? Is it always better to go with the more expensive surgeon? What was your experience with pricing?",
    
    "I'm 3 months post-op from my {procedure} and starting to worry about my results. My right side seems different from my left, and I'm not sure if this is just normal asymmetry or something I should be concerned about. How long should I wait before considering a revision? Did anyone else experience uneven results that improved over time?",
    
    "Success story! I had {procedure} 6 months ago and I wanted to share my positive experience. I was so worried before the surgery, but the recovery was much easier than I expected. The results have completely changed how I feel about myself. Happy to answer any questions for those considering this procedure!",
    
    "I'm looking for recommendations for surgeons specializing in {procedure} in the Delhi/NCR region. I've done some research online, but I'd love to hear personal experiences. Who did your procedure? Were you happy with the results and care? Any surgeons I should avoid?",
    
    "Question about exercise after {procedure} - my surgeon said to wait 6 weeks before returning to my normal workout routine, but I'm starting to feel really good at 4 weeks. Has anyone started exercising earlier than recommended? Were there any complications? I do mostly yoga and light weightlifting.",
    
    "I'm concerned about scarring after {procedure}. Could those who've had this surgery share how their scars have healed over time? What scar treatments did you use? Did your surgeon recommend any specific products? I scar easily so this is a major concern for me.",
    
    "I'm debating between {procedure} and a non-surgical alternative. The non-surgical option is less expensive and has no downtime, but I'm worried the results won't be as dramatic or long-lasting. Has anyone tried both approaches? Which did you prefer and why?",
    
    "Post-surgery depression - did anyone else experience this after {procedure}? I'm 2 weeks post-op and feeling unexpectedly down and questioning my decision. The results look good so far, but I can't shake this feeling. Is this a normal part of the recovery process? How long did it last for you?",
    
    "Age considerations for {procedure} - I'm 53 and wondering if I'm too old for this procedure. My surgeon says age isn't an issue, but I'd like to hear from others in my age group who've had this done. Were your results what you expected? Was recovery harder due to age?",
    
    "I had {procedure} 2 years ago and am considering a revision. My initial results were good but not great, and I'm wondering if a revision would be worth it. Has anyone gone through a revision surgery? Were your results better the second time? What questions should I ask my surgeon?",
    
    "I'm planning to have {procedure} but I'm nervous about telling people. How did you handle questions about your procedure? Did you tell people in advance or wait until after? Any advice for dealing with negative reactions from friends or family?",
    
    "Advice needed: I had {procedure} 3 weeks ago and I think I might have an infection. There's redness, increased pain, and some discharge around one of my incisions. I have a call in to my surgeon but haven't heard back yet. Has anyone experienced this? Should I go to the emergency room or wait to hear from my doctor?"
]

REPLY_TEMPLATES = {
    "patient": [
        "I had {procedure} about 6 months ago, and my experience was similar to what you're describing. The swelling took about 3-4 weeks to go down significantly, but I noticed subtle changes for up to 3 months. Arnica gel helped a lot with the bruising. Don't worry, it gets better!",
        
        "My recovery from {procedure} was pretty smooth. The first week was the hardest, but after that, things improved quickly. I followed all my doctor's instructions carefully, which I think made a big difference. Make sure you have someone to help you for at least the first 3-4 days.",
        
        "I went to Dr. {doctor} for my {procedure} and had a great experience. The results exceeded my expectations, and the staff was incredibly supportive throughout the process. The cost was on the higher end, but worth every rupee in my opinion.",
        
        "I had some asymmetry issues after my {procedure} too. I panicked at first, but my surgeon assured me that some asymmetry is normal and that final results take time. Sure enough, by month 4, things had evened out considerably. Try to be patient!",
        
        "I researched {procedure} for almost a year before taking the plunge. The most important factors for me were the surgeon's experience with this specific procedure and before/after photos of their work. Don't just go with the cheapest option - this is your body we're talking about!",
        
        "The scarring from my {procedure} was much less noticeable than I expected. I used silicone sheets and sunscreen religiously. At 1 year post-op, you can barely see the scars unless you're really looking for them.",
        
        "I definitely experienced post-surgery blues after my {procedure}. It hit me around day 10 when the swelling was at its worst, and I questioned my decision. By week 3, as I started to see the real results emerge, my mood improved dramatically. It's more common than people talk about!",
        
        "I'm 55 and had {procedure} last year. Recovery might have been a bit longer than for younger patients, but the results are fantastic. My surgeon said good skin elasticity matters more than actual age, and I had taken good care of my skin over the years."
    ],
    "doctor": [
        "As a plastic surgeon who specializes in {procedure}, I can tell you that what you're experiencing is completely normal. Swelling typically peaks at 48-72 hours post-operation and gradually subsides over 2-3 weeks. Some residual swelling can persist for up to 6 months, especially in the morning. Continue following your surgeon's post-operative care instructions.",
        
        "Regarding your question about technique options for {procedure}, both open and closed approaches have their advantages. The open technique allows for more precise work and is generally preferred for complex cases, while the closed technique results in less visible scarring. Your surgeon should recommend the appropriate technique based on your specific anatomy and aesthetic goals.",
        
        "The price variation you're seeing for {procedure} likely reflects differences in surgeon experience, facility fees, anesthesia type, and geographic location. While cost is a factor, the surgeon's expertise with this specific procedure should be your primary consideration. Ask to see before and after photos of patients with similar concerns to yours.",
        
        "Post-operative asymmetry after {procedure} is not uncommon and often resolves as swelling subsides. However, if significant asymmetry persists beyond 6 months, a follow-up with your surgeon is appropriate. Minor revisions are sometimes necessary, but I recommend waiting at least 6-12 months before considering revision surgery.",
        
        "Exercise restrictions after {procedure} are not arbitrary - they're designed to protect your results and prevent complications. Resuming strenuous activity too soon can lead to increased swelling, bleeding, or compromised results. Even if you feel good, internal healing takes time. Consider gentle walking as an alternative until you reach the 6-week mark.",
        
        "Regarding scarring after {procedure}, proper incision care is crucial. I recommend silicone-based scar treatments starting 2-3 weeks post-op, along with daily sun protection. Genetic factors influence how you scar, but good care significantly improves outcomes. Most surgical scars fade considerably by 12 months.",
        
        "The decision between surgical {procedure} and non-surgical alternatives depends on your specific goals. Surgical approaches offer more dramatic, long-lasting results but require recovery time. Non-surgical options provide subtle improvements with minimal downtime but often require maintenance treatments. A consultation with a board-certified surgeon can help determine the best approach for your situation.",
        
        "Post-surgical depression is a recognized phenomenon that affects many patients. It's often related to anesthesia effects, medication, physical discomfort, and temporary lifestyle limitations. Ensure you're getting adequate rest, nutrition, and gentle activity as permitted. If depression persists or worsens, please discuss it with your surgeon or primary care physician."
    ]
}

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return None
            
        logger.info(f"Connecting to database: {db_url[:20]}...")
        conn = psycopg2.connect(db_url)
        logger.info("Connected to database successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def get_or_create_users(conn, users, role):
    """Get or create user accounts."""
    user_ids = {}
    default_password_hash = generate_password_hash("Password123")
    
    try:
        with conn.cursor() as cursor:
            for user in users:
                # Check if user exists
                cursor.execute(
                    "SELECT id FROM users WHERE email = %s",
                    (user["email"],)
                )
                result = cursor.fetchone()
                
                if result:
                    user_id = result[0]
                    logger.info(f"User {user['username']} already exists with ID {user_id}")
                else:
                    # Create new user
                    cursor.execute(
                        """
                        INSERT INTO users (
                            username, email, role, password_hash, created_at, 
                            is_verified, points, phone_number, name
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            user["username"],
                            user["email"],
                            role,
                            default_password_hash,
                            datetime.now(),
                            True,
                            100,  # Default points
                            user["phone_number"],
                            user["name"]
                        )
                    )
                    user_id = cursor.fetchone()[0]
                    logger.info(f"Created new user {user['username']} with ID {user_id}")
                
                user_ids[user["email"]] = user_id
        
        conn.commit()
        logger.info(f"Successfully processed {len(user_ids)} {role} users")
        return user_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating {role} users: {str(e)}")
        return {}

def get_procedures(conn):
    """Get procedure IDs and names."""
    procedures = {}
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, procedure_name FROM procedures LIMIT 50")
            for procedure_id, procedure_name in cursor.fetchall():
                procedures[procedure_id] = procedure_name
        
        logger.info(f"Found {len(procedures)} procedures")
        return procedures
    except Exception as e:
        logger.error(f"Error getting procedures: {str(e)}")
        return {}

def generate_thread_content(procedure_name):
    """Generate realistic thread content for a procedure."""
    if procedure_name in THREAD_TOPICS:
        title = random.choice(THREAD_TOPICS[procedure_name])
    else:
        title = random.choice(THREAD_TOPICS["General"])
    
    content = random.choice(THREAD_CONTENT_TEMPLATES).format(procedure=procedure_name)
    
    return {
        "title": title,
        "content": content
    }

def random_date(start_date, end_date):
    """Generate a random date between start_date and end_date."""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_days)

def create_community_threads(conn, patient_user_ids, procedures, thread_count=125):
    """Create community threads."""
    threads = []
    start_id = 148  # Start from the next available ID
    
    # Date range from March 15, 2025 to May 15, 2025
    start_date = datetime(2025, 3, 15)
    end_date = datetime(2025, 5, 15)
    
    try:
        with conn.cursor() as cursor:
            for i in range(thread_count):
                # Select random user and procedure
                user_email = random.choice(list(patient_user_ids.keys()))
                user_id = patient_user_ids[user_email]
                procedure_id = random.choice(list(procedures.keys()))
                procedure_name = procedures[procedure_id]
                
                # Generate thread content
                thread_data = generate_thread_content(procedure_name)
                
                # Generate random date
                created_at = random_date(start_date, end_date)
                
                # Generate random view count (50-300)
                view_count = random.randint(50, 300)
                
                # Generate tags
                tags = [t.strip() for t in procedure_name.lower().split()]
                if len(tags) < 3:  # Add more tags if needed
                    additional_tags = ["recovery", "results", "pain", "swelling", "cost", 
                                     "surgeon", "clinic", "before and after", "consultation"]
                    tags.extend(random.sample(additional_tags, random.randint(1, 3)))
                
                # Insert thread
                cursor.execute(
                    """
                    INSERT INTO community (
                        id, user_id, title, content, procedure_id, created_at, 
                        updated_at, view_count, reply_count, tags
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                    """,
                    (
                        start_id + i,
                        user_id,
                        thread_data["title"],
                        thread_data["content"],
                        procedure_id,
                        created_at,
                        created_at,
                        view_count,
                        0,  # Will update this after adding replies
                        tags
                    )
                )
                thread_id = cursor.fetchone()[0]
                
                # Get username for CSV
                username = ""
                for user in PATIENT_USERS:
                    if user["email"] == user_email:
                        username = user["username"]
                        break
                
                # Add to threads list for CSV and replies
                threads.append({
                    "id": thread_id,
                    "title": thread_data["title"],
                    "content": thread_data["content"],
                    "username": username,
                    "email": user_email,
                    "user_role": "patient",
                    "procedure_name": procedure_name,
                    "view_count": view_count,
                    "reply_count": 0,  # Will update this
                    "keywords": ", ".join(tags),
                    "created_at": created_at.strftime("%Y-%m-%d"),
                    "user_id": user_id,
                    "procedure_id": procedure_id
                })
                
                if (i + 1) % 25 == 0:
                    logger.info(f"Created {i + 1} threads")
        
        conn.commit()
        logger.info(f"Successfully created {len(threads)} community threads")
        return threads
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating community threads: {str(e)}")
        return []

def create_thread_replies(conn, threads, patient_user_ids, doctor_user_ids):
    """Create replies for each thread."""
    replies = []
    start_id = 8  # Start from the next available ID
    reply_count = 0
    
    try:
        with conn.cursor() as cursor:
            for thread in threads:
                thread_id = thread["id"]
                procedure_name = thread["procedure_name"]
                thread_date = datetime.strptime(thread["created_at"], "%Y-%m-%d")
                
                # Generate 2-4 replies per thread
                num_replies = random.randint(2, 4)
                thread_replies = []
                
                for j in range(num_replies):
                    # Determine if this is a doctor reply (25% chance)
                    is_doctor = random.random() < 0.25
                    
                    if is_doctor:
                        # Doctor reply
                        user_email = random.choice(list(doctor_user_ids.keys()))
                        user_id = doctor_user_ids[user_email]
                        is_expert_advice = True
                        is_doctor_response = True
                        content = random.choice(REPLY_TEMPLATES["doctor"]).format(
                            procedure=procedure_name,
                            doctor=random.choice(["Sharma", "Patel", "Kumar", "Gupta", "Reddy"])
                        )
                        
                        # Get username
                        username = ""
                        for user in DOCTOR_USERS:
                            if user["email"] == user_email:
                                username = user["username"]
                                break
                    else:
                        # Patient reply
                        user_email = random.choice(list(patient_user_ids.keys()))
                        user_id = patient_user_ids[user_email]
                        is_expert_advice = False
                        is_doctor_response = False
                        content = random.choice(REPLY_TEMPLATES["patient"]).format(
                            procedure=procedure_name,
                            doctor=random.choice(["Sharma", "Patel", "Kumar", "Gupta", "Reddy"])
                        )
                        
                        # Get username
                        username = ""
                        for user in PATIENT_USERS:
                            if user["email"] == user_email:
                                username = user["username"]
                                break
                    
                    # Generate reply date (1-10 days after thread or previous reply)
                    if j == 0:
                        # First reply is 1-5 days after thread creation
                        days_after = random.randint(1, 5)
                        reply_date = thread_date + timedelta(days=days_after)
                    else:
                        # Subsequent replies are 1-3 days after previous reply
                        prev_reply_date = datetime.strptime(thread_replies[-1]["created_at"], "%Y-%m-%d")
                        days_after = random.randint(1, 3)
                        reply_date = prev_reply_date + timedelta(days=days_after)
                    
                    # Ensure reply date is not after May 15, 2025
                    if reply_date > datetime(2025, 5, 15):
                        reply_date = datetime(2025, 5, 15)
                    
                    # Determine parent reply (20% chance for nested reply after first reply)
                    parent_reply_id = None
                    if j > 0 and random.random() < 0.2:
                        parent_reply_id = start_id + reply_count - 1  # Previous reply
                    
                    # Insert reply
                    cursor.execute(
                        """
                        INSERT INTO community_replies (
                            id, thread_id, user_id, parent_reply_id, content, 
                            created_at, is_expert_advice, is_doctor_response,
                            upvotes
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            start_id + reply_count,
                            thread_id,
                            user_id,
                            parent_reply_id,
                            content,
                            reply_date,
                            is_expert_advice,
                            is_doctor_response,
                            random.randint(0, 15)  # Random upvotes
                        )
                    )
                    reply_id = cursor.fetchone()[0]
                    
                    # Add to replies list for CSV
                    reply_data = {
                        "id": reply_id,
                        "thread_id": thread_id,
                        "content": content,
                        "username": username,
                        "email": user_email,
                        "user_role": "doctor" if is_doctor else "patient",
                        "parent_reply_id": parent_reply_id,
                        "created_at": reply_date.strftime("%Y-%m-%d"),
                        "is_expert_advice": "true" if is_expert_advice else "false",
                        "reference": f"r{j+1}"  # r1, r2, etc.
                    }
                    
                    thread_replies.append(reply_data)
                    replies.append(reply_data)
                    reply_count += 1
                
                # Update thread reply count
                cursor.execute(
                    "UPDATE community SET reply_count = %s WHERE id = %s",
                    (num_replies, thread_id)
                )
                
                # Update thread object for CSV output
                thread["reply_count"] = num_replies
                
                if thread_id % 25 == 0:
                    logger.info(f"Added replies for thread {thread_id}")
        
        conn.commit()
        logger.info(f"Successfully created {reply_count} replies for {len(threads)} threads")
        return replies
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating thread replies: {str(e)}")
        return []

def export_to_csv(threads, replies):
    """Export threads and replies to CSV files."""
    try:
        # Create directory for output files
        output_dir = Path("community_data")
        output_dir.mkdir(exist_ok=True)
        
        # Export threads
        thread_fields = [
            "title", "content", "username", "email", "user_role", 
            "procedure_name", "view_count", "reply_count", "keywords",
            "created_at"
        ]
        
        thread_csv_path = output_dir / "Community_Threads.csv"
        with open(thread_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=thread_fields)
            writer.writeheader()
            for thread in threads:
                writer.writerow({k: thread[k] for k in thread_fields})
        
        logger.info(f"Exported {len(threads)} threads to {thread_csv_path}")
        
        # Export replies
        reply_fields = [
            "thread_id", "content", "username", "email", "user_role",
            "parent_reply_id", "created_at", "is_expert_advice", "reference"
        ]
        
        reply_csv_path = output_dir / "Community_Replies.csv"
        with open(reply_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=reply_fields)
            writer.writeheader()
            for reply in replies:
                writer.writerow({k: reply[k] for k in reply_fields})
        
        logger.info(f"Exported {len(replies)} replies to {reply_csv_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        return False

def main():
    """Main function to generate community content."""
    logger.info("=== Starting community content generation ===")
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return 1
    
    try:
        # Create or get users
        patient_user_ids = get_or_create_users(conn, PATIENT_USERS, "patient")
        doctor_user_ids = get_or_create_users(conn, DOCTOR_USERS, "doctor")
        
        if not patient_user_ids or not doctor_user_ids:
            logger.error("Failed to create or get users")
            return 1
        
        # Get procedures
        procedures = get_procedures(conn)
        if not procedures:
            logger.error("Failed to get procedures")
            return 1
        
        # Count existing data
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM community")
            thread_count_before = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM community_replies")
            reply_count_before = cursor.fetchone()[0]
            
            logger.info(f"Before: {thread_count_before} threads, {reply_count_before} replies")
        
        # Create threads
        threads = create_community_threads(conn, patient_user_ids, procedures, thread_count=125)
        if not threads:
            logger.error("Failed to create community threads")
            return 1
        
        # Create replies
        replies = create_thread_replies(conn, threads, patient_user_ids, doctor_user_ids)
        if not replies:
            logger.error("Failed to create thread replies")
            return 1
        
        # Count final data
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM community")
            thread_count_after = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM community_replies")
            reply_count_after = cursor.fetchone()[0]
            
            logger.info(f"After: {thread_count_after} threads, {reply_count_after} replies")
            logger.info(f"Added: {thread_count_after - thread_count_before} threads, {reply_count_after - reply_count_before} replies")
        
        # Export to CSV
        export_to_csv(threads, replies)
        
        logger.info("=== Community content generation completed successfully ===")
        return 0
    except Exception as e:
        logger.error(f"Error during community content generation: {str(e)}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())