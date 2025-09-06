#!/usr/bin/env python3
"""
Add education modules and quizzes to the database.

This script creates educational modules, quizzes, and questions for the Antidote platform.
"""

import logging
from datetime import datetime
from flask import Flask
from app import db
from models import (
    EducationModule, 
    ModuleQuiz, 
    QuizQuestion, 
    Procedure, 
    Category
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_rhinoplasty_module():
    """Create educational module for Rhinoplasty."""
    try:
        # Check if procedure exists
        procedure = Procedure.query.filter_by(procedure_name="Rhinoplasty").first()
        if not procedure:
            logger.warning("Rhinoplasty procedure not found. Skipping module creation.")
            return None
        
        # Create module
        module = EducationModule(
            title="Understanding Rhinoplasty: What to Expect",
            description="Learn about rhinoplasty procedures, recovery process, and what to expect before and after surgery.",
            content="""
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
                <p>Rhinoplasty is typically performed as an outpatient procedure, meaning you won't need to stay overnight at the hospital. The surgery usually takes 1.5 to 3 hours, depending on complexity. The steps include:</p>
                <ol>
                    <li>Administration of anesthesia (local or general)</li>
                    <li>Making incisions (either inside the nose or across the columella)</li>
                    <li>Reshaping the inner bone and cartilage to create the desired appearance</li>
                    <li>Correcting any breathing issues if needed</li>
                    <li>Closing the incisions and placing splints or packing for support</li>
                </ol>
                
                <h2>After the Procedure</h2>
                <p>Recovery from rhinoplasty is a gradual process. Here's what to expect:</p>
                <ul>
                    <li>A splint will usually be placed inside your nose and on the outside to support and protect it</li>
                    <li>Swelling and bruising around the eyes and nose is common for the first few days</li>
                    <li>Most people can return to work or school in one to two weeks</li>
                    <li>You'll need to avoid strenuous activities for 3-6 weeks</li>
                    <li>Full results may not be visible for up to a year, as small amounts of swelling can persist</li>
                </ul>
                
                <h2>Risks and Considerations</h2>
                <p>Like any surgical procedure, rhinoplasty carries certain risks such as:</p>
                <ul>
                    <li>Bleeding and infection</li>
                    <li>Difficulty breathing through the nose</li>
                    <li>Permanent numbness in or around the nose</li>
                    <li>Possibility of uneven results or dissatisfaction with appearance</li>
                    <li>The need for additional surgery</li>
                </ul>
                
                <h2>Results and Satisfaction</h2>
                <p>Studies show that most patients report high satisfaction rates after rhinoplasty, with improvements in both appearance and breathing function. However, it's important to maintain realistic expectations and understand that the final outcome may take months to fully appear as swelling subsides.</p>
            """,
            category_id=None,  # Using procedure association instead
            procedure_id=procedure.id,
            level=2,  # Intermediate
            points=20,
            estimated_minutes=15,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        db.session.add(module)
        db.session.flush()  # Flush to get the module ID
        
        # Create quiz for the module
        quiz = ModuleQuiz(
            module_id=module.id,
            title="Rhinoplasty Knowledge Check",
            description="Test your understanding of rhinoplasty procedures and recovery",
            passing_score=70,
            created_at=datetime.utcnow()
        )
        
        db.session.add(quiz)
        db.session.flush()  # Flush to get the quiz ID
        
        # Create questions for the quiz
        questions = [
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="What is the primary reason people undergo rhinoplasty?",
                question_type="multiple_choice",
                options=["To improve appearance", "To improve breathing function", "Both appearance and breathing function", "To treat sinus infections"],
                correct_answer="Both appearance and breathing function",
                explanation="Rhinoplasty can be performed for both cosmetic reasons to improve appearance and for medical reasons to correct breathing problems."
            ),
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="Approximately how long does a typical rhinoplasty procedure take?",
                question_type="multiple_choice",
                options=["30 minutes to 1 hour", "1.5 to 3 hours", "4 to 6 hours", "Over 8 hours"],
                correct_answer="1.5 to 3 hours",
                explanation="Most rhinoplasty procedures take between 1.5 to 3 hours to complete, depending on the complexity of the changes being made."
            ),
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="How long might it take to see the final results of rhinoplasty?",
                question_type="multiple_choice",
                options=["1-2 weeks", "1-2 months", "6 months", "Up to a year"],
                correct_answer="Up to a year",
                explanation="While most swelling subsides within a few weeks, residual swelling can persist for up to a year, meaning the final, refined result may not be visible until then."
            ),
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="True or False: Most people can return to work or school within 1-2 weeks after rhinoplasty.",
                question_type="true_false",
                options=["True", "False"],
                correct_answer="True",
                explanation="Most patients can return to work or school within 1-2 weeks after surgery, although they should still avoid strenuous activities."
            ),
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="Which of the following is NOT a common risk associated with rhinoplasty?",
                question_type="multiple_choice",
                options=["Bleeding", "Infection", "Permanent changes in sense of taste", "Difficulty breathing through the nose"],
                correct_answer="Permanent changes in sense of taste",
                explanation="While rhinoplasty can temporarily affect your sense of smell (and indirectly taste), permanent changes in sense of taste are not a common risk. Common risks include bleeding, infection, difficulty breathing, and numbness."
            )
        ]
        
        for question in questions:
            db.session.add(question)
        
        db.session.commit()
        logger.info(f"Created Rhinoplasty module with ID: {module.id} and quiz with ID: {quiz.id}")
        return module
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating Rhinoplasty module: {str(e)}")
        return None

def create_postop_recovery_module():
    """Create educational module for Post-Operative Recovery."""
    try:
        # Create general education module (not tied to specific procedure)
        module = EducationModule(
            title="Post-Operative Recovery: Essential Tips for Healing",
            description="Learn best practices for recovery after surgical procedures, including wound care, pain management, and when to contact your doctor.",
            content="""
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
                    <li>Change dressings as recommended by your healthcare provider</li>
                    <li>Avoid applying lotions, creams, or ointments unless specifically prescribed</li>
                </ul>
                
                <h2>Activity Restrictions</h2>
                <p>After surgery, you'll need to modify your activities:</p>
                <ul>
                    <li>Rest is crucial - your body needs energy to heal</li>
                    <li>Avoid lifting heavy objects for the specified period</li>
                    <li>Return to normal activities gradually, not all at once</li>
                    <li>Follow specific guidelines about when you can resume exercise</li>
                    <li>Consider arranging help for household chores during early recovery</li>
                </ul>
                
                <h2>Nutrition for Healing</h2>
                <p>What you eat can impact how quickly and effectively you heal:</p>
                <ul>
                    <li>Consume adequate protein - the building block for tissue repair</li>
                    <li>Stay well-hydrated to support circulation and cellular function</li>
                    <li>Eat plenty of fruits and vegetables for vitamins and minerals</li>
                    <li>Consider supplements if recommended by your healthcare provider</li>
                    <li>Avoid alcohol, which can interfere with medication and healing</li>
                </ul>
                
                <h2>When to Call Your Doctor</h2>
                <p>Contact your healthcare provider immediately if you experience:</p>
                <ul>
                    <li>Fever over 101.5°F (38.6°C)</li>
                    <li>Increasing pain, redness, swelling, or warmth at the incision site</li>
                    <li>Drainage or pus from the incision</li>
                    <li>Bleeding that doesn't stop with light pressure</li>
                    <li>Shortness of breath or chest pain</li>
                    <li>Severe nausea or vomiting</li>
                </ul>
                
                <h2>Follow-Up Appointments</h2>
                <p>Even if you feel you're recovering well, attending all scheduled follow-up appointments is essential. These visits allow your surgeon to monitor your healing, address any concerns, and adjust your recovery plan if needed.</p>
            """,
            category_id=None,  # General module
            procedure_id=None,  # General module
            level=1,  # Beginner
            points=15,
            estimated_minutes=10,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        db.session.add(module)
        db.session.flush()  # Flush to get the module ID
        
        # Create quiz for the module
        quiz = ModuleQuiz(
            module_id=module.id,
            title="Post-Operative Care Quiz",
            description="Test your knowledge of essential post-op recovery guidelines",
            passing_score=80,
            created_at=datetime.utcnow()
        )
        
        db.session.add(quiz)
        db.session.flush()  # Flush to get the quiz ID
        
        # Create questions for the quiz
        questions = [
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="Before touching a surgical incision, you should:",
                question_type="multiple_choice",
                options=["Apply lotion", "Wash your hands thoroughly", "Change your clothes", "Take a pain medication"],
                correct_answer="Wash your hands thoroughly",
                explanation="Hand washing is essential before touching a surgical incision to prevent introducing bacteria that could cause infection."
            ),
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="True or False: You should wait until pain is severe before taking prescribed pain medication.",
                question_type="true_false",
                options=["True", "False"],
                correct_answer="False",
                explanation="It's better to take pain medication as prescribed, rather than waiting for pain to become severe. This helps maintain consistent pain control."
            ),
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="Which of the following is an important reason to attend all follow-up appointments?",
                question_type="multiple_choice",
                options=[
                    "To get more pain medication", 
                    "To have the doctor monitor your healing progress", 
                    "To schedule your next surgery", 
                    "To meet other patients"
                ],
                correct_answer="To have the doctor monitor your healing progress",
                explanation="Follow-up appointments allow your surgeon to monitor healing, catch any complications early, and adjust your recovery plan if needed."
            ),
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="Which symptom should prompt an immediate call to your doctor?",
                question_type="multiple_choice",
                options=[
                    "Mild soreness at the incision site", 
                    "Feeling tired after activity", 
                    "Fever over 101.5°F (38.6°C)", 
                    "Decreased appetite"
                ],
                correct_answer="Fever over 101.5°F (38.6°C)",
                explanation="A high fever could indicate an infection or other complication that requires prompt medical attention."
            ),
            QuizQuestion(
                quiz_id=quiz.id,
                question_text="True or False: You should return to normal activities all at once as soon as you feel better.",
                question_type="true_false",
                options=["True", "False"],
                correct_answer="False",
                explanation="You should gradually return to normal activities as recommended by your doctor, not all at once, even if you feel better."
            )
        ]
        
        for question in questions:
            db.session.add(question)
        
        db.session.commit()
        logger.info(f"Created Post-Op Recovery module with ID: {module.id} and quiz with ID: {quiz.id}")
        return module
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating Post-Op Recovery module: {str(e)}")
        return None

def main():
    """Main function to add educational modules."""
    logger.info("Starting to add educational modules...")
    
    # Import the app from main.py
    from main import app
    
    with app.app_context():
        # Add modules
        rhinoplasty_module = create_rhinoplasty_module()
        recovery_module = create_postop_recovery_module()
        
        # Log results
        if rhinoplasty_module and recovery_module:
            logger.info("Successfully added all educational modules.")
        else:
            logger.warning("Some modules could not be added. Check the logs for details.")
    
    logger.info("Education module addition completed.")

if __name__ == "__main__":
    main()