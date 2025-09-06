#!/usr/bin/env python3
"""
Add sample community posts to showcase the enhanced community platform.
"""
import os
import sys
from datetime import datetime, timedelta
import random

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Community, User, Category, Procedure

def create_sample_posts():
    """Create sample community posts to showcase the platform."""
    app = create_app()
    
    with app.app_context():
        print("🌟 Creating sample community posts...")
        
        # Get some users for posts (create a test user if none exist)
        users = User.query.limit(5).all()
        if not users:
            # Create a sample user
            sample_user = User(
                name="Sarah Johnson",
                username="sarah_j",
                email="sarah@example.com",
                phone_number="1234567890"
            )
            db.session.add(sample_user)
            db.session.commit()
            users = [sample_user]
        
        # Get some procedures and categories
        procedures = Procedure.query.limit(10).all()
        categories = Category.query.limit(5).all()
        
        # Sample community posts
        sample_posts = [
            {
                "title": "My Rhinoplasty Journey - 6 Months Post-Op Update",
                "content": "Hi everyone! I wanted to share my experience 6 months after my rhinoplasty procedure. The recovery was easier than I expected, and I'm absolutely thrilled with the results!\n\nInitially, I was nervous about the procedure, but Dr. Patel made me feel completely comfortable. The first week was the most challenging with swelling and some discomfort, but it got better each day.\n\nNow at 6 months, the swelling has completely subsided and I love my new nose! It looks so natural and exactly what I hoped for. Happy to answer any questions for those considering this procedure.",
                "procedure_id": procedures[0].id if procedures else None,
                "category_id": categories[0].id if categories else None,
                "upvotes": 24,
                "downvotes": 1,
                "view_count": 156,
                "reply_count": 8,
                "is_pinned": False
            },
            {
                "title": "Questions about Breast Augmentation Recovery",
                "content": "I'm scheduled for breast augmentation next month and feeling a bit anxious about the recovery process. \n\nFor those who have had this procedure:\n• How long did you take off work?\n• When could you exercise again?\n• Any tips for managing discomfort?\n\nI work a desk job, so I'm hoping to return relatively quickly. Any advice would be greatly appreciated! 🙏",
                "procedure_id": procedures[1].id if len(procedures) > 1 else None,
                "category_id": categories[1].id if len(categories) > 1 else None,
                "upvotes": 15,
                "downvotes": 0,
                "view_count": 89,
                "reply_count": 12,
                "is_pinned": False
            },
            {
                "title": "Choosing the Right Surgeon - Red Flags to Avoid",
                "content": "After extensive research and consultations, I wanted to share some important red flags I noticed when choosing a plastic surgeon:\n\n🚩 Pressuring you to book immediately\n🚩 No board certification displayed\n🚩 Unwilling to show before/after photos\n🚩 No clear discussion of risks\n🚩 Prices that seem too good to be true\n\nTake your time, do your research, and trust your instincts. A good surgeon will want you to feel completely informed and comfortable with your decision.\n\nWhat other red flags have you encountered?",
                "upvotes": 45,
                "downvotes": 2,
                "view_count": 234,
                "reply_count": 18,
                "is_pinned": True
            },
            {
                "title": "Tummy Tuck - 2 Weeks Post-Op Progress",
                "content": "Sharing my 2-week update after my tummy tuck procedure! \n\nThe first few days were definitely challenging - I won't sugarcoat it. Having a compression garment and taking it easy were crucial. My surgeon's team was amazing with follow-up care.\n\nI'm already seeing such a difference in my silhouette and feeling more confident. The incision is healing beautifully and the swelling is going down each day.\n\nFor anyone considering this procedure, make sure you have help at home for the first week. It makes such a difference in your recovery! \n\nAMA about the experience so far! 💪",
                "procedure_id": procedures[2].id if len(procedures) > 2 else None,
                "upvotes": 31,
                "downvotes": 0,
                "view_count": 127,
                "reply_count": 9,
                "is_pinned": False
            },
            {
                "title": "Consultation Questions - What Should I Ask?",
                "content": "I have my first consultation for a facelift next week and want to make sure I ask all the right questions. \n\nSo far I have:\n✓ Your experience with this procedure\n✓ Realistic expectations for results\n✓ Recovery timeline\n✓ Potential risks and complications\n✓ Cost breakdown\n✓ Before/after photos\n\nWhat other important questions should I add to my list? I want to make sure I'm fully informed before making any decisions.\n\nThanks in advance for your help! This community has been such a valuable resource. ❤️",
                "upvotes": 28,
                "downvotes": 1,
                "view_count": 103,
                "reply_count": 14,
                "is_pinned": False
            },
            {
                "title": "Cost Considerations - Financing Your Procedure",
                "content": "Let's talk about the financial aspect of cosmetic procedures - something that's often overlooked but super important!\n\nI saved for 2 years for my procedure and here's what I learned:\n\n💰 Get detailed quotes from multiple surgeons\n💰 Factor in time off work\n💰 Budget for aftercare products\n💰 Consider payment plans if offered\n💰 Don't compromise quality for cost\n\nSome practices offer financing options, but make sure you understand the terms. Your health and safety should always come first.\n\nHow did you budget for your procedure? Any tips for others?",
                "upvotes": 19,
                "downvotes": 3,
                "view_count": 78,
                "reply_count": 7,
                "is_pinned": False
            }
        ]
        
        # Create the posts
        for i, post_data in enumerate(sample_posts):
            # Use different users for variety
            user = users[i % len(users)]
            
            # Create post with some variation in timing
            days_ago = random.randint(1, 30)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            post = Community(
                title=post_data["title"],
                content=post_data["content"],
                user_id=user.id,
                procedure_id=post_data.get("procedure_id"),
                category_id=post_data.get("category_id"),
                upvotes=post_data.get("upvotes", 0),
                downvotes=post_data.get("downvotes", 0),
                view_count=post_data.get("view_count", 0),
                reply_count=post_data.get("reply_count", 0),
                is_pinned=post_data.get("is_pinned", False),
                created_at=created_at,
                trending_score=post_data.get("upvotes", 0) * 1.5  # Simple trending score
            )
            
            db.session.add(post)
            print(f"✅ Created post: {post_data['title']}")
        
        db.session.commit()
        print(f"🎉 Successfully created {len(sample_posts)} sample community posts!")
        print("The enhanced community platform is now ready to showcase!")

if __name__ == "__main__":
    create_sample_posts()