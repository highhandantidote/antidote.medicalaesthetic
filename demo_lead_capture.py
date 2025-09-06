"""
Demo Script: Test Enhanced Lead Capture System
Demonstrates the complete flow from CTA interaction to lead conversion
"""

import os
import sys
import json
from datetime import datetime
from interaction_tracker import track_user_interaction, should_show_contact_form, create_lead_from_form
from app import app, db
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ai_recommendation_flow():
    """Test AI recommendation lead capture flow."""
    print("\n🧠 Testing AI Recommendation Lead Capture...")
    
    with app.app_context():
        # Simulate AI recommendation interaction
        interaction_data = {
            'query_text': 'I want to improve my nose shape and reduce wrinkles',
            'has_audio': False,
            'has_image': True,
            'recommendations_count': 3,
            'primary_procedure': 'Rhinoplasty',
            'urgency_level': 'high',
            'complexity_score': 75
        }
        
        # Track interaction
        interaction_id = track_user_interaction(
            interaction_type='ai_recommendation',
            data=interaction_data,
            source_page='/ai-recommendation'
        )
        
        print(f"  ✓ AI recommendation interaction tracked (ID: {interaction_id})")
        
        # Check if should show contact form
        from flask import session
        session['session_id'] = 'demo_session_ai_123'
        should_prompt = should_show_contact_form('demo_session_ai_123', 'ai_recommendation', interaction_data)
        print(f"  ✓ Should prompt for contact: {should_prompt}")
        
        # Create lead from interaction
        contact_data = {
            'name': 'Sarah Chen',
            'phone': '9876543210',
            'email': 'sarah.chen@example.com',
            'city': 'Mumbai'
        }
        
        lead_id = create_lead_from_form(interaction_id, contact_data)
        print(f"  ✓ Lead created successfully (ID: {lead_id})")
        
        return interaction_id, lead_id

def test_face_analysis_flow():
    """Test face analysis lead capture flow."""
    print("\n📸 Testing Face Analysis Lead Capture...")
    
    with app.app_context():
        # Simulate face analysis interaction
        interaction_data = {
            'has_image': True,
            'age': '28',
            'gender': 'female',
            'skin_concerns': ['wrinkles', 'pigmentation'],
            'treatment_history': True,
            'budget_range': 'high',
            'recommendations_count': 2,
            'top_recommendation': 'Anti-Aging Treatment',
            'confidence_score': 88,
            'urgency_level': 'medium'
        }
        
        # Track interaction
        interaction_id = track_user_interaction(
            interaction_type='face_analysis',
            data=interaction_data,
            source_page='/face-analysis'
        )
        
        print(f"  ✓ Face analysis interaction tracked (ID: {interaction_id})")
        
        # Create lead (face analysis is always high-intent)
        contact_data = {
            'name': 'Priya Sharma',
            'phone': '9876543211',
            'email': 'priya.sharma@example.com',
            'city': 'Delhi'
        }
        
        lead_id = create_lead_from_form(interaction_id, contact_data)
        print(f"  ✓ High-intent lead created successfully (ID: {lead_id})")
        
        return interaction_id, lead_id

def test_cost_calculator_flow():
    """Test cost calculator lead capture flow."""
    print("\n💰 Testing Cost Calculator Lead Capture...")
    
    with app.app_context():
        # Simulate cost calculator interaction
        interaction_data = {
            'selected_procedure': 'Breast Augmentation',
            'city': 'Bangalore',
            'budget_range': '100000_200000',
            'urgency': 'within_month',
            'additional_procedures': ['Liposuction'],
            'total_procedures': 2,
            'estimated_cost': 180000,
            'cost_range': '₹1,50,000 - ₹2,20,000',
            'wants_detailed_quote': True,
            'price_intent_score': 85
        }
        
        # Track interaction
        interaction_id = track_user_interaction(
            interaction_type='cost_calculator',
            data=interaction_data,
            source_page='/cost-calculator'
        )
        
        print(f"  ✓ Cost calculator interaction tracked (ID: {interaction_id})")
        
        # Create lead from quote request
        contact_data = {
            'name': 'Anita Reddy',
            'phone': '9876543212',
            'email': 'anita.reddy@example.com',
            'city': 'Bangalore'
        }
        
        lead_id = create_lead_from_form(interaction_id, contact_data)
        print(f"  ✓ Cost inquiry lead created successfully (ID: {lead_id})")
        
        return interaction_id, lead_id

def test_anonymous_session_tracking():
    """Test anonymous session tracking and progressive profiling."""
    print("\n👤 Testing Anonymous Session Tracking...")
    
    with app.app_context():
        session_id = 'demo_anonymous_session_456'
        
        # Track multiple anonymous interactions
        interactions = []
        
        # First interaction - browsing
        int1 = track_user_interaction(
            interaction_type='page_view',
            data={'page': 'procedures', 'time_spent': 120},
            source_page='/procedures'
        )
        interactions.append(int1)
        
        # Second interaction - searching
        int2 = track_user_interaction(
            interaction_type='search_behavior',
            data={'query': 'rhinoplasty cost', 'results_viewed': 5},
            source_page='/search'
        )
        interactions.append(int2)
        
        # Third interaction - cost calculator (high intent)
        int3 = track_user_interaction(
            interaction_type='cost_calculator',
            data={'selected_procedure': 'Rhinoplasty', 'urgency': 'immediate'},
            source_page='/cost-calculator'
        )
        interactions.append(int3)
        
        print(f"  ✓ Tracked {len(interactions)} anonymous interactions")
        
        # Check if session qualifies for lead conversion
        should_convert = should_show_contact_form(session_id, 'cost_calculator', 
                                                {'urgency': 'immediate'})
        print(f"  ✓ Anonymous session qualifies for conversion: {should_convert}")
        
        return interactions

def display_analytics_summary():
    """Display comprehensive analytics summary."""
    print("\n📊 Analytics Summary:")
    print("=" * 50)
    
    with app.app_context():
        # Get interaction counts by type
        result = db.session.execute(text("""
            SELECT 
                interaction_type,
                COUNT(*) as total_count,
                COUNT(CASE WHEN converted_to_lead = true THEN 1 END) as converted_count
            FROM user_interactions 
            WHERE created_at >= NOW() - INTERVAL '1 hour'
            GROUP BY interaction_type
            ORDER BY total_count DESC
        """)).fetchall()
        
        print("Recent Interactions (Last Hour):")
        for row in result:
            conversion_rate = (row[2] * 100.0 / row[1]) if row[1] > 0 else 0
            print(f"  {row[0]}: {row[1]} interactions, {row[2]} leads ({conversion_rate:.1f}% conversion)")
        
        # Get lead scores
        lead_scores = db.session.execute(text("""
            SELECT lead_score, COUNT(*) as count
            FROM leads 
            WHERE created_at >= NOW() - INTERVAL '1 hour'
            GROUP BY lead_score
            ORDER BY lead_score DESC
        """)).fetchall()
        
        print("\nLead Score Distribution:")
        for score, count in lead_scores:
            print(f"  Score {score}: {count} leads")
        
        # Get total stats
        total_stats = db.session.execute(text("""
            SELECT 
                COUNT(DISTINCT ui.id) as total_interactions,
                COUNT(DISTINCT l.id) as total_leads,
                AVG(l.lead_score) as avg_score
            FROM user_interactions ui
            LEFT JOIN leads l ON ui.lead_id = l.id
            WHERE ui.created_at >= NOW() - INTERVAL '1 hour'
        """)).fetchone()
        
        if total_stats:
            conversion_rate = (total_stats[1] * 100.0 / total_stats[0]) if total_stats[0] > 0 else 0
            print(f"\nOverall Performance:")
            print(f"  Total Interactions: {total_stats[0]}")
            print(f"  Total Leads: {total_stats[1]}")
            print(f"  Conversion Rate: {conversion_rate:.1f}%")
            print(f"  Average Lead Score: {total_stats[2]:.1f}" if total_stats[2] else "  Average Lead Score: N/A")

def main():
    """Run comprehensive lead capture demo."""
    print("🚀 Enhanced Lead Capture System Demo")
    print("=" * 50)
    
    try:
        # Test individual flows
        ai_interaction, ai_lead = test_ai_recommendation_flow()
        face_interaction, face_lead = test_face_analysis_flow()
        cost_interaction, cost_lead = test_cost_calculator_flow()
        
        # Test anonymous tracking
        anonymous_interactions = test_anonymous_session_tracking()
        
        # Display comprehensive analytics
        display_analytics_summary()
        
        print("\n✅ Demo completed successfully!")
        print(f"   - Created {3} high-quality leads")
        print(f"   - Tracked {3 + len(anonymous_interactions)} total interactions")
        print(f"   - Demonstrated end-to-end lead capture flow")
        
        print("\n📈 Next Steps:")
        print("   1. Visit /admin/comprehensive/dashboard to view analytics")
        print("   2. Check /admin/comprehensive/interactions for detailed data")
        print("   3. Review /admin/comprehensive/lead-scoring for scoring performance")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")

if __name__ == "__main__":
    main()