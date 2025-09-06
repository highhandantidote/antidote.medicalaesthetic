#!/usr/bin/env python3
"""
Simulate user behavior to test personalization system.
This creates realistic interaction data for testing homepage personalization.
"""

import requests
import time
import json

def simulate_breast_surgery_interest():
    """Simulate a user interested in breast surgery procedures."""
    
    base_url = "http://localhost:5000"
    user_fingerprint = f"real_user_breast_interest_{int(time.time())}"
    
    print(f"Simulating breast surgery interest for fingerprint: {user_fingerprint}")
    
    # Simulate the exact sequence: search -> category browse -> procedure views
    interactions = [
        # Initial search for breast implants
        {
            "fingerprint": user_fingerprint,
            "interaction_type": "search",
            "content_type": "procedure",
            "content_id": "0",
            "content_name": "breast implants",
            "page_url": "/search?q=breast+implants",
            "session_id": "breast_session_real"
        },
        # Browse breast surgery category  
        {
            "fingerprint": user_fingerprint,
            "interaction_type": "view",
            "content_type": "category",
            "content_id": "17",
            "content_name": "Breast Surgery",
            "page_url": "/categories/17",
            "session_id": "breast_session_real"
        },
        # Click on breast surgery category
        {
            "fingerprint": user_fingerprint,
            "interaction_type": "click",
            "content_type": "category",
            "content_id": "17",
            "content_name": "Breast Surgery",
            "page_url": "/categories/17",
            "session_id": "breast_session_real"
        },
        # Search for breast augmentation specifically
        {
            "fingerprint": user_fingerprint,
            "interaction_type": "search",
            "content_type": "procedure",
            "content_id": "0",
            "content_name": "breast augmentation",
            "page_url": "/search?q=breast+augmentation",
            "session_id": "breast_session_real"
        },
        # View body contouring (related interest)
        {
            "fingerprint": user_fingerprint,
            "interaction_type": "view",
            "content_type": "category",
            "content_id": "18",
            "content_name": "Body Contouring",
            "page_url": "/categories/18",
            "session_id": "breast_session_real"
        }
    ]
    
    success_count = 0
    for i, interaction in enumerate(interactions, 1):
        try:
            response = requests.post(f"{base_url}/api/track-interaction", json=interaction)
            if response.status_code == 200:
                success_count += 1
                print(f"  ✓ {i}. {interaction['interaction_type']}: {interaction['content_name']}")
            else:
                print(f"  ✗ {i}. Failed: {interaction['content_name']} - {response.status_code}")
        except Exception as e:
            print(f"  ✗ {i}. Error: {interaction['content_name']} - {e}")
        
        # Small delay to simulate real browsing
        time.sleep(0.5)
    
    print(f"\nSimulation complete: {success_count}/{len(interactions)} interactions tracked")
    print(f"User fingerprint: {user_fingerprint}")
    
    return user_fingerprint

def test_personalization_data(fingerprint):
    """Test that the personalization data was stored correctly."""
    
    print(f"\nTesting personalization data for: {fingerprint}")
    
    # You can check the database or make a request to see personalized content
    # For now, we'll just provide instructions for testing
    
    print("\nTo test the personalization:")
    print("1. Open your browser developer tools (F12)")
    print("2. Go to Console tab")
    print(f"3. Set your fingerprint: localStorage.setItem('userFingerprint', '{fingerprint}')")
    print("4. Set preferences: localStorage.setItem('antidote_preferences', JSON.stringify({")
    print("     categories: {'17': 5, '18': 2},")
    print("     keywords: {'breast': 8, 'implants': 5, 'augmentation': 4, 'surgery': 3}")
    print("   }))")
    print("5. Refresh the homepage")
    print("6. You should see breast surgery related procedures prominently displayed")

if __name__ == "__main__":
    fingerprint = simulate_breast_surgery_interest()
    test_personalization_data(fingerprint)