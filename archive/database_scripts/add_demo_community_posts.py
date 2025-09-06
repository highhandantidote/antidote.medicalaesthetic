"""
Add demo community posts for the Reddit-style community platform.
Creates realistic cosmetic surgery discussion posts to showcase the new features.
"""

import os
import sys
from datetime import datetime, timedelta
import random

# Add the project root to the path
sys.path.append('/home/runner/workspace')

from main import app
from app import db
from models import Community, User, Category, Procedure

def create_demo_user():
    """Create a demo user for posts."""
    with app.app_context():
        # Check if demo user already exists
        demo_user = User.query.filter_by(username='demo_user').first()
        if not demo_user:
            demo_user = User(
                username='demo_user',
                name='Demo User',
                email='demo@antidote.com',
                role='user',
                created_at=datetime.utcnow()
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.commit()
            print(f"Created demo user: {demo_user.username}")
        return demo_user

def get_random_category_and_procedure():
    """Get random category and procedure for posts."""
    categories = Category.query.all()
    procedures = Procedure.query.all()
    
    category = random.choice(categories) if categories else None
    procedure = random.choice(procedures) if procedures else None
    
    return category, procedure

def create_demo_posts():
    """Create a variety of demo community posts."""
    with app.app_context():
        demo_user = create_demo_user()
        
        # Sample posts with realistic cosmetic surgery content
        demo_posts = [
            {
                'title': 'My rhinoplasty journey - 3 months post-op results!',
                'content': 'I wanted to share my experience with rhinoplasty for anyone considering the procedure. I had my surgery 3 months ago with Dr. Smith in Mumbai. The recovery was easier than expected, and I\'m really happy with the natural-looking results. The swelling took about 6 weeks to fully go down. AMA!',
                'upvotes': 45,
                'downvotes': 2,
                'reply_count': 12,
                'view_count': 156,
                'source_type': 'native',
                'is_professional_verified': False,
                'created_at': datetime.utcnow() - timedelta(hours=6)
            },
            {
                'title': 'Hair transplant vs. medications - What worked for you?',
                'content': 'I\'m 28 and dealing with male pattern baldness. I\'ve been using minoxidil for 8 months with minimal results. Considering FUE hair transplant but it\'s a big investment. For those who\'ve tried both approaches, what would you recommend? Looking for honest experiences.',
                'upvotes': 32,
                'downvotes': 1,
                'reply_count': 18,
                'view_count': 203,
                'source_type': 'native',
                'is_professional_verified': False,
                'created_at': datetime.utcnow() - timedelta(hours=12)
            },
            {
                'title': 'Breast augmentation cost in major Indian cities - 2024 update',
                'content': 'After consulting with multiple surgeons across Delhi, Mumbai, and Bangalore, here\'s what I found for breast augmentation costs:\n\nDelhi: ₹2.5-4.5L\nMumbai: ₹3-5L\nBangalore: ₹2.8-4.2L\n\nPrices vary based on surgeon experience, implant type, and hospital facilities. Always prioritize safety over cost!',
                'upvotes': 67,
                'downvotes': 3,
                'reply_count': 24,
                'view_count': 312,
                'source_type': 'native',
                'is_professional_verified': False,
                'created_at': datetime.utcnow() - timedelta(hours=18)
            },
            {
                'title': '[Expert Insight] Choosing the right surgeon - Red flags to avoid',
                'content': 'As a plastic surgeon with 15 years of experience, I want to share some red flags to watch out for when choosing a cosmetic surgeon:\n\n1. No board certification in plastic surgery\n2. Pressure to decide immediately\n3. Unrealistic promises or guarantees\n4. Operating in non-accredited facilities\n5. Unwillingness to show before/after photos\n\nAlways verify credentials and take time to make informed decisions.',
                'upvotes': 89,
                'downvotes': 1,
                'reply_count': 15,
                'view_count': 445,
                'source_type': 'native',
                'is_professional_verified': True,
                'created_at': datetime.utcnow() - timedelta(days=1)
            },
            {
                'title': 'Liposuction recovery tips that actually work',
                'content': 'Just finished my 8-week recovery from abdominal liposuction. Here are the tips that made the biggest difference:\n\n• Compression garments 24/7 for first 4 weeks\n• Lymphatic drainage massage after week 2\n• Walking daily but no heavy lifting for 6 weeks\n• Protein-rich diet to support healing\n• Stay hydrated!\n\nHappy to answer questions about the process.',
                'upvotes': 41,
                'downvotes': 0,
                'reply_count': 9,
                'view_count': 178,
                'source_type': 'native',
                'is_professional_verified': False,
                'created_at': datetime.utcnow() - timedelta(days=2)
            },
            {
                'title': 'Non-surgical alternatives - Botox vs. fillers for facial rejuvenation',
                'content': 'For those considering facial treatments but not ready for surgery, here\'s my experience with both:\n\nBotox (for forehead lines): ₹15,000, lasts 4-6 months, minimal downtime\nFillers (for cheeks): ₹25,000, lasts 12-18 months, slight swelling for 2 days\n\nBoth gave natural results when done by experienced practitioners. Key is finding someone who understands facial anatomy.',
                'upvotes': 28,
                'downvotes': 2,
                'reply_count': 14,
                'view_count': 167,
                'source_type': 'native',
                'is_professional_verified': False,
                'created_at': datetime.utcnow() - timedelta(days=3)
            },
            {
                'title': '[From Reddit] Realistic expectations for tummy tuck surgery',
                'content': 'I see a lot of unrealistic expectations about tummy tucks, so here\'s the reality:\n\n• Surgery takes 2-4 hours under general anesthesia\n• 2-3 weeks off work minimum\n• 6-8 weeks before normal exercise\n• Permanent scar (though it fades significantly)\n• Results continue improving for 6-12 months\n\nIt\'s major surgery but life-changing for the right candidates. Do your research!',
                'upvotes': 52,
                'downvotes': 1,
                'reply_count': 11,
                'view_count': 234,
                'source_type': 'reddit',
                'source_url': 'https://reddit.com/r/PlasticSurgery/comments/example',
                'reddit_author': 'PlasticSurgeryMom',
                'is_professional_verified': False,
                'created_at': datetime.utcnow() - timedelta(days=4)
            },
            {
                'title': 'Blepharoplasty before and after - 6 month update',
                'content': 'Sharing my upper eyelid surgery results after 6 months. The procedure took about 90 minutes under local anesthesia. Bruising lasted 10 days, but the results have been amazing. My eyes look more youthful and alert. Cost was ₹1.8L in Chennai. Would definitely recommend to anyone considering it.',
                'upvotes': 38,
                'downvotes': 0,
                'reply_count': 8,
                'view_count': 192,
                'source_type': 'native',
                'is_professional_verified': False,
                'created_at': datetime.utcnow() - timedelta(days=5)
            }
        ]
        
        # Create posts
        for post_data in demo_posts:
            # Check if post already exists
            existing_post = Community.query.filter_by(title=post_data['title']).first()
            if existing_post:
                print(f"Post already exists: {post_data['title']}")
                continue
            
            category, procedure = get_random_category_and_procedure()
            
            # Calculate engagement score
            upvotes = post_data['upvotes']
            downvotes = post_data['downvotes']
            replies = post_data['reply_count']
            hours_old = (datetime.utcnow() - post_data['created_at']).total_seconds() / 3600
            
            # Reddit-style engagement scoring
            score = upvotes - downvotes
            time_decay = max(0.1, 1 / (1 + hours_old / 6))
            comment_bonus = replies * 0.5
            professional_bonus = 2 if post_data.get('is_professional_verified') else 0
            engagement_score = (score + comment_bonus + professional_bonus) * time_decay
            
            post = Community(
                user_id=demo_user.id,
                title=post_data['title'],
                content=post_data['content'],
                upvotes=upvotes,
                downvotes=downvotes,
                total_votes=upvotes - downvotes,
                reply_count=replies,
                view_count=post_data['view_count'],
                source_type=post_data['source_type'],
                source_url=post_data.get('source_url'),
                reddit_author=post_data.get('reddit_author'),
                is_professional_verified=post_data['is_professional_verified'],
                engagement_score=engagement_score,
                category_id=category.id if category else None,
                procedure_id=procedure.id if procedure else None,
                created_at=post_data['created_at'],
                is_anonymous=False
            )
            
            db.session.add(post)
            print(f"Created post: {post_data['title']}")
        
        db.session.commit()
        print(f"\nSuccessfully created {len(demo_posts)} demo community posts!")
        print("Your Reddit-style community platform now has engaging content to showcase!")

if __name__ == "__main__":
    create_demo_posts()