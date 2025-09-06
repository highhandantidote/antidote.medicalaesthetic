from datetime import datetime, timedelta
import random
from app import db, create_app
from models import (
    BodyPart, Category, Procedure, User, Doctor, DoctorCategory,
    DoctorProcedure, Review, Community, CommunityReply, 
    CommunityTagging, UserPreference, Notification, Interaction,
    DoctorPhoto, DoctorAvailability, Lead, Message, CommunityModeration
)

def seed_users():
    """Create sample users."""
    print("Creating users...")
    
    users = [
        User(
            name="John Doe",
            email="john@example.com",
            username="johndoe",
            role="user",
            role_type="user",
            phone_number="555-123-4567",
            bio="Just a patient exploring plastic surgery options",
            badge="Verified Patient",
            points=150,
            is_verified=True,
            created_at=datetime.utcnow()
        ),
        User(
            name="Jane Smith",
            email="jane@example.com",
            username="janesmith",
            role="user",
            role_type="user",
            phone_number="555-234-5678",
            bio="Looking to get advice about rhinoplasty",
            badge="Active Member",
            points=75,
            is_verified=True,
            created_at=datetime.utcnow()
        ),
        User(
            name="Dr. Michael Johnson",
            email="michael@example.com",
            username="drjohnson",
            role="doctor",
            role_type="doctor",
            phone_number="555-345-6789",
            bio="Board certified plastic surgeon with 15 years of experience",
            badge="Verified Doctor",
            points=350,
            is_verified=True,
            created_at=datetime.utcnow()
        ),
        User(
            name="Dr. Sarah Thompson",
            email="sarah@example.com",
            username="drthompson",
            role="doctor",
            role_type="doctor",
            phone_number="555-456-7890",
            bio="Specializing in facial procedures and reconstructive surgery",
            badge="Expert Contributor",
            points=420,
            is_verified=True,
            created_at=datetime.utcnow()
        ),
        User(
            name="Emily Wilson",
            email="emily@example.com",
            username="emilyw",
            role="user",
            role_type="expert",
            phone_number="555-567-8901",
            bio="Certified aesthetic nurse and skin care specialist",
            badge="Expert Advisor",
            points=280,
            is_verified=True,
            created_at=datetime.utcnow()
        )
    ]
    
    db.session.add_all(users)
    db.session.commit()
    
    return users

def seed_categories():
    """Create sample categories."""
    print("Creating categories...")
    
    body_part = BodyPart(
        name="Face",
        description="Facial procedures for aesthetic enhancement",
        icon_url="face_icon.svg",
        created_at=datetime.utcnow()
    )
    db.session.add(body_part)
    db.session.commit()
    
    categories = [
        Category(
            name="Facial Surgery",
            description="Surgical procedures to enhance facial features",
            body_part_id=body_part.id,
            created_at=datetime.utcnow()
        ),
        Category(
            name="Non-Surgical Treatments",
            description="Non-invasive procedures for facial enhancement",
            body_part_id=body_part.id,
            created_at=datetime.utcnow()
        )
    ]
    
    db.session.add_all(categories)
    db.session.commit()
    
    return categories

def seed_procedures(categories):
    """Create sample procedures."""
    print("Creating procedures...")
    
    procedures = [
        Procedure(
            procedure_name="Rhinoplasty",
            short_description="Nose reshaping surgery",
            overview="Rhinoplasty is surgery that changes the shape of the nose.",
            procedure_details="The surgery involves reshaping the bone and cartilage.",
            ideal_candidates="Good candidates are those looking to improve the appearance of their nose.",
            min_cost=5000,
            max_cost=15000,
            recovery_time="1-2 weeks",
            results_duration="Permanent",
            risks="Swelling, bruising, and potential breathing difficulties",
            procedure_types=["Open Rhinoplasty", "Closed Rhinoplasty"],
            category_id=categories[0].id,
            created_at=datetime.utcnow()
        ),
        Procedure(
            procedure_name="Botox",
            short_description="Injectable treatment to reduce wrinkles",
            overview="Botox is a popular non-surgical injection that temporarily reduces or eliminates facial fine lines and wrinkles.",
            procedure_details="The procedure involves injecting small amounts of botulinum toxin into targeted muscles.",
            ideal_candidates="Adults who want to improve the appearance of wrinkles.",
            min_cost=300,
            max_cost=800,
            recovery_time="None to 1-2 days",
            results_duration="3-6 months",
            risks="Bruising, headache, and temporary facial weakness",
            procedure_types=["Cosmetic Botox", "Therapeutic Botox"],
            category_id=categories[1].id,
            created_at=datetime.utcnow()
        )
    ]
    
    db.session.add_all(procedures)
    db.session.commit()
    
    return procedures

def seed_community_threads(users, categories, procedures):
    """Create sample community threads."""
    print("Creating community threads...")
    
    threads = [
        Community(
            user_id=users[0].id,
            title="My Rhinoplasty Experience - Before and After",
            content="I had rhinoplasty surgery 3 months ago and wanted to share my experience with everyone. The recovery was tough for the first week, but I'm so happy with the results now! Has anyone else had a similar experience? I'd love to hear your thoughts.",
            is_anonymous=False,
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow() - timedelta(days=30),
            view_count=125,
            reply_count=4,
            featured=True,
            tags=["rhinoplasty", "recovery", "experience", "before-after"],
            category_id=categories[0].id,
            procedure_id=procedures[0].id,
            photo_url="https://example.com/rhinoplasty-before-after.jpg"
        ),
        Community(
            user_id=users[1].id,
            title="Botox for the First Time - What to Expect?",
            content="I'm considering getting Botox for the first time to address some forehead wrinkles. I'm a bit nervous and would love to hear from people who have experience. What should I expect during and after the procedure? How much does it typically cost? Any advice would be greatly appreciated!",
            is_anonymous=False,
            created_at=datetime.utcnow() - timedelta(days=14),
            updated_at=datetime.utcnow() - timedelta(days=14),
            view_count=87,
            reply_count=3,
            featured=False,
            tags=["botox", "first-time", "advice", "cost"],
            category_id=categories[1].id,
            procedure_id=procedures[1].id
        ),
        Community(
            user_id=users[4].id,
            title="Expert Guide: Choosing the Right Surgeon for Your Procedure",
            content="As an aesthetic specialist, I've seen many patients struggle with finding the right surgeon. Here are my top tips for selecting a qualified professional:\n\n1. Check board certifications\n2. Review before/after photos\n3. Read patient reviews\n4. Schedule consultation to assess communication\n5. Ask about complication rates\n\nWhat other factors do you consider important when choosing a surgeon?",
            is_anonymous=False,
            created_at=datetime.utcnow() - timedelta(days=7),
            updated_at=datetime.utcnow() - timedelta(days=7),
            view_count=156,
            reply_count=6,
            featured=True,
            tags=["expert", "surgeon", "advice", "selection-tips"],
            category_id=None,
            procedure_id=None
        )
    ]
    
    db.session.add_all(threads)
    db.session.commit()
    
    return threads

def seed_community_replies(users, threads):
    """Create sample community replies."""
    print("Creating community replies...")
    
    replies = [
        CommunityReply(
            thread_id=threads[0].id,
            user_id=users[1].id,
            content="Thanks for sharing your experience! I'm scheduled for rhinoplasty next month and I'm both excited and nervous. Did you have any breathing issues during recovery?",
            is_anonymous=False,
            is_doctor_response=False,
            created_at=datetime.utcnow() - timedelta(days=29),
            upvotes=8
        ),
        CommunityReply(
            thread_id=threads[0].id,
            user_id=users[0].id,
            content="I had some congestion for about a week, but nothing too serious. Just make sure to follow your doctor's post-op instructions carefully!",
            is_anonymous=False,
            is_doctor_response=False,
            created_at=datetime.utcnow() - timedelta(days=29),
            upvotes=5,
            parent_reply_id=1  # Reply to the first reply
        ),
        CommunityReply(
            thread_id=threads[0].id,
            user_id=users[2].id,
            content="Great results! As a surgeon who performs rhinoplasties, I'd like to add that the final results typically take up to a year to fully develop as swelling continues to subside. The improvements you're seeing at 3 months will likely get even better!",
            is_anonymous=False,
            is_doctor_response=True,
            created_at=datetime.utcnow() - timedelta(days=28),
            upvotes=15
        ),
        CommunityReply(
            thread_id=threads[1].id,
            user_id=users[3].id,
            content="Botox is a great option for forehead wrinkles. The procedure itself only takes about 10-15 minutes, and you'll feel small pinches during the injections. Most patients see results within 3-7 days, but full results take up to 2 weeks. Cost varies by region, but expect $300-600 for forehead treatment. Avoid exercise for 24 hours after treatment, and don't rub the area.",
            is_anonymous=False,
            is_doctor_response=True,
            is_expert_advice=True,
            created_at=datetime.utcnow() - timedelta(days=13),
            upvotes=12
        ),
        CommunityReply(
            thread_id=threads[1].id,
            user_id=users[4].id,
            content="I've been getting Botox for 3 years now, and it's been great for my confidence. The first time is a bit nerve-wracking, but it's really quick and relatively painless. Just make sure you go to a reputable provider!",
            is_anonymous=False,
            is_doctor_response=False,
            is_expert_advice=True,
            created_at=datetime.utcnow() - timedelta(days=12),
            upvotes=7
        ),
        CommunityReply(
            thread_id=threads[2].id,
            user_id=users[2].id,
            content="Excellent advice! I'd also recommend patients ask about the surgeon's experience specifically with the procedure they're considering. Volume matters - a surgeon who performs your procedure frequently will likely have better outcomes than one who does it occasionally.",
            is_anonymous=False,
            is_doctor_response=True,
            created_at=datetime.utcnow() - timedelta(days=6),
            upvotes=10
        ),
        CommunityReply(
            thread_id=threads[2].id,
            user_id=users[0].id,
            content="I found that bringing photos of the results I wanted helped a lot during my consultation. It made it easier to communicate my expectations.",
            is_anonymous=False,
            is_doctor_response=False,
            created_at=datetime.utcnow() - timedelta(days=5),
            upvotes=6
        )
    ]
    
    db.session.add_all(replies)
    db.session.commit()

def seed_notifications(users):
    """Create sample notifications."""
    print("Creating notifications...")
    
    notifications = [
        Notification(
            user_id=users[0].id,
            message="Dr. Johnson replied to your thread about rhinoplasty",
            type="reply",
            is_read=False,
            created_at=datetime.utcnow() - timedelta(days=28),
            response_type="doctor"
        ),
        Notification(
            user_id=users[1].id,
            message="Dr. Thompson replied to your question about Botox",
            type="reply",
            is_read=True,
            created_at=datetime.utcnow() - timedelta(days=13),
            response_type="doctor"
        ),
        Notification(
            user_id=users[0].id,
            message="Jane Smith mentioned you in a reply",
            type="mention",
            is_read=False,
            created_at=datetime.utcnow() - timedelta(days=29),
            mentioned_username=users[0].username
        )
    ]
    
    db.session.add_all(notifications)
    db.session.commit()

def seed_messages(users):
    """Create sample messages."""
    print("Creating messages...")
    
    messages = [
        Message(
            sender_id=users[0].id,
            receiver_id=users[2].id,
            content="Hi Dr. Johnson, I have a few questions about my upcoming rhinoplasty consultation. Do you have time to chat?",
            is_read=True,
            created_at=datetime.utcnow() - timedelta(days=5, hours=3)
        ),
        Message(
            sender_id=users[2].id,
            receiver_id=users[0].id,
            content="Hello John, of course! I'm happy to answer any questions you may have. What specifically would you like to know?",
            is_read=True,
            created_at=datetime.utcnow() - timedelta(days=5, hours=2)
        ),
        Message(
            sender_id=users[0].id,
            receiver_id=users[2].id,
            content="Thank you for responding! I'm wondering what type of anesthesia you typically use for rhinoplasty and what the recovery timeline looks like.",
            is_read=True,
            created_at=datetime.utcnow() - timedelta(days=5, hours=1)
        ),
        Message(
            sender_id=users[2].id,
            receiver_id=users[0].id,
            content="For rhinoplasty, I typically use general anesthesia to ensure patient comfort. Recovery timeline: 1 week with nasal splint, 2-3 weeks for initial swelling to subside, and up to a year for final results. Most patients return to work after 7-10 days. Any other questions?",
            is_read=False,
            created_at=datetime.utcnow() - timedelta(days=4, hours=23)
        )
    ]
    
    db.session.add_all(messages)
    db.session.commit()

def main():
    """Run all seed functions."""
    app = create_app()
    with app.app_context():
        users = seed_users()
        categories = seed_categories()
        procedures = seed_procedures(categories)
        threads = seed_community_threads(users, categories, procedures)
        seed_community_replies(users, threads)
        seed_notifications(users)
        seed_messages(users)
        
        print("Seeding completed successfully!")

if __name__ == "__main__":
    main()