#!/usr/bin/env python3
"""
Add a simple education module directly to the database.
This script is designed to be more efficient by using direct SQL commands.
"""

import os
import psycopg2
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_db():
    """Connect to the PostgreSQL database."""
    try:
        # Get connection parameters from environment variables
        db_url = os.environ.get('DATABASE_URL')
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def add_education_modules(conn):
    """Add education modules to the database using SQL."""
    try:
        cursor = conn.cursor()
        
        # Check if Rhinoplasty procedure exists
        cursor.execute("SELECT id FROM procedures WHERE procedure_name = 'Rhinoplasty'")
        procedure_id = cursor.fetchone()
        
        if not procedure_id:
            logger.warning("Rhinoplasty procedure not found. Creating general modules only.")
            procedure_id = None
        else:
            procedure_id = procedure_id[0]
            
        now = datetime.utcnow()
        
        # Add education module 1 (if it doesn't exist yet)
        cursor.execute(
            "SELECT id FROM education_modules WHERE title = 'Understanding Rhinoplasty: What to Expect'"
        )
        if not cursor.fetchone() and procedure_id:
            # Insert Rhinoplasty module
            cursor.execute(
                """
                INSERT INTO education_modules (
                    title, description, content, procedure_id, level, 
                    points, estimated_minutes, created_at, is_active
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
                """,
                (
                    'Understanding Rhinoplasty: What to Expect',
                    'Learn about rhinoplasty procedures, recovery process, and what to expect before and after surgery.',
                    """
                    <h2>What is Rhinoplasty?</h2>
                    <p>Rhinoplasty, also known as a "nose job," is a surgical procedure that modifies the shape or function of the nose. This procedure can be performed for cosmetic reasons to improve appearance, or for medical reasons to correct breathing problems or repair deformities from birth or injury.</p>
                    
                    <h2>Before the Procedure</h2>
                    <p>Before undergoing rhinoplasty, you'll consult with a surgeon to discuss your goals, medical history, and any concerns. Your surgeon may:</p>
                    <ul>
                        <li>Take photographs of your nose from different angles</li>
                        <li>Discuss your expectations and explain what rhinoplasty can and cannot do</li>
                        <li>Describe options for anesthesia and where your surgery will take place</li>
                        <li>Provide specific instructions on preparing for surgery</li>
                    </ul>
                    
                    <h2>During the Procedure</h2>
                    <p>Rhinoplasty is typically performed as an outpatient procedure, meaning you won't need to stay overnight at the hospital. The surgery usually takes 1.5 to 3 hours, depending on complexity.</p>
                    
                    <h2>After the Procedure</h2>
                    <p>Recovery from rhinoplasty is a gradual process. Here's what to expect:</p>
                    <ul>
                        <li>A splint will usually be placed inside your nose and on the outside to support and protect it</li>
                        <li>Swelling and bruising around the eyes and nose is common for the first few days</li>
                        <li>Most people can return to work or school in one to two weeks</li>
                        <li>You'll need to avoid strenuous activities for 3-6 weeks</li>
                        <li>Full results may not be visible for up to a year, as small amounts of swelling can persist</li>
                    </ul>
                    """,
                    procedure_id,
                    2,  # Intermediate level
                    20,  # Points
                    15,  # Estimated minutes
                    now,
                    True
                )
            )
            
            rhinoplasty_module_id = cursor.fetchone()[0]
            logger.info(f"Created Rhinoplasty module with ID: {rhinoplasty_module_id}")
            
            # Add quiz for Rhinoplasty module
            cursor.execute(
                """
                INSERT INTO module_quizzes (
                    module_id, title, description, passing_score, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s
                ) RETURNING id
                """,
                (
                    rhinoplasty_module_id,
                    'Rhinoplasty Knowledge Check',
                    'Test your understanding of rhinoplasty procedures and recovery',
                    70,  # Passing score percentage
                    now
                )
            )
            
            quiz_id = cursor.fetchone()[0]
            logger.info(f"Created quiz with ID: {quiz_id} for module: {rhinoplasty_module_id}")
            
            # Add questions for the quiz
            questions = [
                {
                    'question': 'What is the primary reason people undergo rhinoplasty?',
                    'type': 'multiple_choice',
                    'options': ['To improve appearance', 'To improve breathing function', 'Both appearance and breathing function', 'To treat sinus infections'],
                    'answer': 'Both appearance and breathing function',
                    'explanation': 'Rhinoplasty can be performed for both cosmetic reasons to improve appearance and for medical reasons to correct breathing problems.'
                },
                {
                    'question': 'Approximately how long does a typical rhinoplasty procedure take?',
                    'type': 'multiple_choice',
                    'options': ['30 minutes to 1 hour', '1.5 to 3 hours', '4 to 6 hours', 'Over 8 hours'],
                    'answer': '1.5 to 3 hours',
                    'explanation': 'Most rhinoplasty procedures take between 1.5 to 3 hours to complete, depending on the complexity of the changes being made.'
                },
                {
                    'question': 'True or False: Most people can return to work or school within 1-2 weeks after rhinoplasty.',
                    'type': 'true_false',
                    'options': ['True', 'False'],
                    'answer': 'True',
                    'explanation': 'Most patients can return to work or school within 1-2 weeks after surgery, although they should still avoid strenuous activities.'
                }
            ]
            
            for q in questions:
                cursor.execute(
                    """
                    INSERT INTO quiz_questions (
                        quiz_id, question_text, question_type, options, correct_answer, explanation
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        quiz_id,
                        q['question'],
                        q['type'],
                        q['options'],
                        q['answer'],
                        q['explanation']
                    )
                )
            
            logger.info(f"Added {len(questions)} questions to quiz ID: {quiz_id}")
        else:
            logger.info("Rhinoplasty module already exists. Skipping.")
        
        # Add general education module (not tied to specific procedure)
        cursor.execute(
            "SELECT id FROM education_modules WHERE title = 'Post-Operative Recovery: Essential Tips'"
        )
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO education_modules (
                    title, description, content, level, 
                    points, estimated_minutes, created_at, is_active
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
                """,
                (
                    'Post-Operative Recovery: Essential Tips',
                    'Learn best practices for recovery after surgical procedures, including wound care and pain management.',
                    """
                    <h2>The Importance of Proper Recovery</h2>
                    <p>Recovery after surgery is a critical phase in your overall treatment journey. Following your surgeon's instructions carefully can significantly impact your healing process, minimize complications, and lead to better long-term results.</p>
                    
                    <h2>Managing Pain and Discomfort</h2>
                    <p>Pain management is an essential part of your recovery. Here are some guidelines:</p>
                    <ul>
                        <li>Take prescribed pain medications exactly as directed</li>
                        <li>Don't wait until pain is severe before taking medication</li>
                        <li>Keep track of when you take medications to avoid overlap or missed doses</li>
                        <li>For some procedures, ice packs may help reduce swelling and discomfort</li>
                        <li>Report any unusual or severe pain to your doctor immediately</li>
                    </ul>
                    
                    <h2>Wound Care Basics</h2>
                    <p>Proper wound care helps prevent infection and promotes healing:</p>
                    <ul>
                        <li>Wash your hands thoroughly before touching the incision area</li>
                        <li>Follow specific cleaning instructions provided by your surgeon</li>
                        <li>Keep the incision site clean and dry</li>
                    </ul>
                    """,
                    1,  # Beginner level
                    15,  # Points
                    10,  # Estimated minutes
                    now,
                    True
                )
            )
            
            general_module_id = cursor.fetchone()[0]
            logger.info(f"Created General Recovery module with ID: {general_module_id}")
            
            # Add quiz for general module
            cursor.execute(
                """
                INSERT INTO module_quizzes (
                    module_id, title, description, passing_score, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s
                ) RETURNING id
                """,
                (
                    general_module_id,
                    'Post-Op Care Essentials',
                    'Test your knowledge of post-operative recovery',
                    80,  # Passing score percentage
                    now
                )
            )
            
            general_quiz_id = cursor.fetchone()[0]
            logger.info(f"Created quiz with ID: {general_quiz_id} for module: {general_module_id}")
            
            # Add questions for the general quiz
            gen_questions = [
                {
                    'question': 'Before touching a surgical incision, you should:',
                    'type': 'multiple_choice',
                    'options': ['Apply lotion', 'Wash your hands thoroughly', 'Change your clothes', 'Take a pain medication'],
                    'answer': 'Wash your hands thoroughly',
                    'explanation': 'Hand washing is essential before touching a surgical incision to prevent introducing bacteria that could cause infection.'
                },
                {
                    'question': 'True or False: You should wait until pain is severe before taking prescribed pain medication.',
                    'type': 'true_false',
                    'options': ['True', 'False'],
                    'answer': 'False',
                    'explanation': "It's better to take pain medication as prescribed, rather than waiting for pain to become severe. This helps maintain consistent pain control."
                }
            ]
            
            for q in gen_questions:
                cursor.execute(
                    """
                    INSERT INTO quiz_questions (
                        quiz_id, question_text, question_type, options, correct_answer, explanation
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        general_quiz_id,
                        q['question'],
                        q['type'],
                        q['options'],
                        q['answer'],
                        q['explanation']
                    )
                )
            
            logger.info(f"Added {len(gen_questions)} questions to general quiz ID: {general_quiz_id}")
        else:
            logger.info("General Recovery module already exists. Skipping.")
            
        # Commit the transaction
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding education modules: {str(e)}")
        return False

def main():
    """Main function to add educational modules."""
    logger.info("Starting to add educational modules...")
    try:
        conn = connect_to_db()
        success = add_education_modules(conn)
        
        if success:
            logger.info("Successfully added educational modules.")
        else:
            logger.warning("Failed to add some educational modules. Check the logs for details.")
            
        conn.close()
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
    
    logger.info("Education module addition completed.")

if __name__ == "__main__":
    main()