"""
Patch to fix key highlights processing in unified clinic dashboard
"""
import json

def process_dynamic_key_highlights(request_form):
    """Process the dynamic key highlights from the form"""
    key_highlights = []
    highlight_count = 1
    
    while True:
        title_field = f'highlight_title_{highlight_count}'
        value_field = f'highlight_value_{highlight_count}'
        explanation_field = f'highlight_explanation_{highlight_count}'
        
        title = request_form.get(title_field, '').strip()
        value = request_form.get(value_field, '').strip()
        explanation = request_form.get(explanation_field, '').strip()
        
        if not title or not value:
            break
            
        key_highlights.append({
            'title': title,
            'value': value,
            'explanation': explanation
        })
        highlight_count += 1
    
    return key_highlights