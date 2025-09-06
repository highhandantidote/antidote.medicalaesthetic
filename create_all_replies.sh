#!/bin/bash

# Create all replies in small batches (5 threads at a time)
echo "Starting reply generation for all threads in small batches"

# Create a modified version of the batch script with smaller batch size
cat > generate_micro_batch.py << 'EOF'
#!/usr/bin/env python3
"""
Generate community thread replies in tiny batches.

This script:
1. Processes a very small batch of threads (5 at a time)
2. Adds 2-4 replies to each thread
3. Preserves all existing data

Usage:
    python generate_micro_batch.py [thread_id]

Example:
    python generate_micro_batch.py 148  # Process thread ID 148
"""
import os
import sys
import logging
import random
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"generate_micro_batch.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# User IDs (hardcoded to avoid repeated lookups)
PATIENT_USER_IDS = {
    "patient1@example.com": 147,
    "patient2@example.com": 148,
    "test@example.com": 149,
    "patient1@antidote.com": 150,
    "patient2@antidote.com": 151,
    "patient3@antidote.com": 152
}

DOCTOR_USER_IDS = {
    "drkumar@example.com": 153,
    "dr.sharma@antidote.com": 154,
    "dr.patel@antidote.com": 155
}

# Reply templates
REPLY_TEMPLATES = {
    "patient": [
        "I had {procedure} about 6 months ago, and my experience was similar to what you're describing. The swelling took about 3-4 weeks to go down significantly, but I noticed subtle changes for up to 3 months. Arnica gel helped a lot with the bruising. Don't worry, it gets better!",
        "My recovery from {procedure} was pretty smooth. The first week was the hardest, but after that, things improved quickly. I followed all my doctor's instructions carefully, which I think made a big difference. Make sure you have someone to help you for at least the first 3-4 days.",
        "I went to Dr. {doctor} for my {procedure} and had a great experience. The results exceeded my expectations, and the staff was incredibly supportive throughout the process. The cost was on the higher end, but worth every rupee in my opinion."
    ],
    "doctor": [
        "As a plastic surgeon who specializes in {procedure}, I can tell you that what you're experiencing is completely normal. Swelling typically peaks at 48-72 hours post-operation and gradually subsides over 2-3 weeks. Some residual swelling can persist for up to 6 months, especially in the morning. Continue following your surgeon's post-operative care instructions.",
        "Regarding your question about technique options for {procedure}, both open and closed approaches have their advantages. The open technique allows for more precise work and is generally preferred for complex cases, while the closed technique results in less visible scarring. Your surgeon should recommend the appropriate technique based on your specific anatomy and aesthetic goals.",
        "The price variation you're seeing for {procedure} likely reflects differences in surgeon experience, facility fees, anesthesia type, and geographic location. While cost is a factor, the surgeon's expertise with this specific procedure should be your primary consideration. Ask to see before and after photos of patients with similar concerns to yours."
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

def get_thread_info(conn, thread_id):
    """Get information about a specific thread."""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.content, c.created_at, c.procedure_id, c.reply_count,
                       p.procedure_name, u.username, u.email
                FROM community c
                JOIN users u ON c.user_id = u.id
                JOIN procedures p ON c.procedure_id = p.id
                WHERE c.id = %s
            """, (thread_id,))
            
            result = cursor.fetchone()
            
            if result:
                logger.info(f"Found thread {thread_id}: {result['title']}")
                return dict(result)
            else:
                logger.error(f"Thread {thread_id} not found")
                return None
    except Exception as e:
        logger.error(f"Error getting thread info: {str(e)}")
        return None

def get_next_reply_id(conn):
    """Get the next available reply ID."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) FROM community_replies")
            result = cursor.fetchone()
            if result and result[0]:
                return result[0] + 1
            else:
                return 1
    except Exception as e:
        logger.error(f"Error getting next reply ID: {str(e)}")
        return 1

def create_replies_for_thread(conn, thread):
    """Create 2-4 replies for a specific thread."""
    thread_id = thread["id"]
    procedure_name = thread["procedure_name"]
    thread_date = thread["created_at"]
    
    # Check if thread already has replies
    if thread["reply_count"] > 0:
        logger.info(f"Thread {thread_id} already has {thread['reply_count']} replies. Skipping.")
        return []
    
    # Get next reply ID
    next_id = get_next_reply_id(conn)
    logger.info(f"Next reply ID: {next_id}")
    
    # Generate 2-4 replies
    num_replies = random.randint(2, 4)
    replies = []
    
    try:
        for i in range(num_replies):
            # Determine if this is a doctor reply (25% chance)
            is_doctor = random.random() < 0.25
            
            if is_doctor:
                # Doctor reply
                user_email = random.choice(list(DOCTOR_USER_IDS.keys()))
                user_id = DOCTOR_USER_IDS[user_email]
                is_expert_advice = True
                is_doctor_response = True
                content = random.choice(REPLY_TEMPLATES["doctor"]).format(
                    procedure=procedure_name,
                    doctor=random.choice(["Sharma", "Patel", "Kumar", "Gupta", "Reddy"])
                )
            else:
                # Patient reply
                user_email = random.choice(list(PATIENT_USER_IDS.keys()))
                user_id = PATIENT_USER_IDS[user_email]
                is_expert_advice = False
                is_doctor_response = False
                content = random.choice(REPLY_TEMPLATES["patient"]).format(
                    procedure=procedure_name,
                    doctor=random.choice(["Sharma", "Patel", "Kumar", "Gupta", "Reddy"])
                )
            
            # Generate reply date
            if i == 0:
                days_after = random.randint(1, 5)
                reply_date = thread_date + timedelta(days=days_after)
            else:
                prev_date = replies[-1]["created_at"]
                days_after = random.randint(1, 3)
                reply_date = prev_date + timedelta(days=days_after)
            
            # Ensure date is not in the future
            now = datetime.now()
            if reply_date > now:
                reply_date = now
            
            # Create reply
            reply_id = next_id + i
            reply = {
                "id": reply_id,
                "thread_id": thread_id,
                "user_id": user_id,
                "parent_reply_id": None,
                "is_expert_advice": is_expert_advice,
                "is_ai_response": False,
                "is_anonymous": False,
                "is_doctor_response": is_doctor_response,
                "created_at": reply_date,
                "upvotes": random.randint(0, 15),
                "content": content
            }
            
            replies.append(reply)
        
        # Insert replies
        with conn.cursor() as cursor:
            for reply in replies:
                cursor.execute("""
                    INSERT INTO community_replies (
                        id, thread_id, user_id, parent_reply_id, is_expert_advice,
                        is_ai_response, is_anonymous, is_doctor_response, created_at,
                        upvotes, content
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    reply["id"],
                    reply["thread_id"],
                    reply["user_id"],
                    reply["parent_reply_id"],
                    reply["is_expert_advice"],
                    reply["is_ai_response"],
                    reply["is_anonymous"],
                    reply["is_doctor_response"],
                    reply["created_at"],
                    reply["upvotes"],
                    reply["content"]
                ))
            
            # Update thread reply count
            cursor.execute(
                "UPDATE community SET reply_count = %s WHERE id = %s",
                (num_replies, thread_id)
            )
        
        conn.commit()
        logger.info(f"Created {num_replies} replies for thread {thread_id}")
        
        return replies
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating replies for thread {thread_id}: {str(e)}")
        return []

def main():
    """Main function to generate replies for a single thread."""
    if len(sys.argv) < 2:
        logger.error("Please provide a thread ID")
        return 1
    
    try:
        thread_id = int(sys.argv[1])
    except ValueError:
        logger.error("Invalid thread ID")
        return 1
    
    logger.info(f"=== Generating replies for thread {thread_id} ===")
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return 1
    
    try:
        # Get thread info
        thread = get_thread_info(conn, thread_id)
        if not thread:
            logger.error(f"Thread {thread_id} not found")
            return 1
        
        # Create replies
        replies = create_replies_for_thread(conn, thread)
        
        if replies:
            logger.info(f"Successfully created {len(replies)} replies for thread {thread_id}")
            return 0
        else:
            logger.warning(f"No replies created for thread {thread_id}")
            return 0
    except Exception as e:
        logger.error(f"Error generating replies for thread {thread_id}: {str(e)}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
EOF

# Make the script executable
chmod +x generate_micro_batch.py

# Get the list of thread IDs that need replies
echo "Getting list of threads that need replies..."
THREAD_IDS=$(python3 -c "
import os
import psycopg2

conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cursor = conn.cursor()
cursor.execute('''
    SELECT id FROM community 
    WHERE reply_count = 0 
    ORDER BY id DESC 
    LIMIT 125
''')
for row in cursor.fetchall():
    print(row[0])
conn.close()
")

# Process each thread
echo "Found $(echo "$THREAD_IDS" | wc -l) threads to process"
for thread_id in $THREAD_IDS; do
    echo "Processing thread ID: $thread_id"
    python generate_micro_batch.py $thread_id
    
    # Check if we need to continue
    REPLY_COUNT=$(python3 -c "
import os
import psycopg2

conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM community_replies')
count = cursor.fetchone()[0]
print(count)
conn.close()
")
    
    echo "Current reply count: $REPLY_COUNT"
    
    # Check if we've reached our target (about 300 replies)
    if [ "$REPLY_COUNT" -ge "300" ]; then
        echo "Reached target reply count. Stopping."
        break
    fi
done

echo "Reply generation complete!"