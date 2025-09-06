"""
Fix key highlights processing for package creation
"""
import json
from sqlalchemy import text
from app import db

def process_key_highlights_from_form(form_data):
    """Process key highlights from form data"""
    highlights = []
    count = 1
    
    while True:
        title = form_data.get(f'highlight_title_{count}', '').strip()
        value = form_data.get(f'highlight_value_{count}', '').strip()
        explanation = form_data.get(f'highlight_explanation_{count}', '').strip()
        
        if not title or not value:
            break
            
        highlights.append({
            'title': title,
            'value': value,
            'explanation': explanation
        })
        count += 1
    
    return highlights

def update_package_key_highlights(package_id, highlights):
    """Update package with enhanced key highlights"""
    try:
        highlights_json = json.dumps(highlights) if highlights else None
        
        db.session.execute(text("""
            UPDATE packages 
            SET key_highlights = :highlights 
            WHERE id = :package_id
        """), {
            'highlights': highlights_json,
            'package_id': package_id
        })
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error updating key highlights: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    # Test with package 33
    test_highlights = [
        {
            'title': 'Advanced Technology',
            'value': 'Latest Laser Technology',
            'explanation': 'Using state-of-the-art laser technology for better results and minimal discomfort'
        },
        {
            'title': 'Recovery Time',
            'value': '1-2 days',
            'explanation': 'Minimal downtime with quick recovery due to advanced techniques'
        },
        {
            'title': 'Results Duration',
            'value': 'Long-lasting',
            'explanation': 'Results can last for several years with proper maintenance'
        }
    ]
    
    success = update_package_key_highlights(33, test_highlights)
    print(f"Update successful: {success}")