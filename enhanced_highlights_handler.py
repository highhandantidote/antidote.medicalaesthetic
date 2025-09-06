"""
Enhanced Key Highlights Handler
Processes the new key highlights structure with titles, values, and explanations.
"""
import json
import logging

logger = logging.getLogger(__name__)

def process_key_highlights(request_form):
    """
    Process key highlights from the form data with enhanced structure.
    
    Args:
        request_form: Flask request.form object
        
    Returns:
        list: List of validated highlight objects with title, value, and explanation
    """
    try:
        key_highlights_raw = request_form.get('key_highlights', '[]')
        key_highlights = json.loads(key_highlights_raw) if key_highlights_raw else []
        
        # Validate the key highlights structure
        if isinstance(key_highlights, list):
            validated_highlights = []
            for highlight in key_highlights:
                if isinstance(highlight, dict) and 'title' in highlight and 'value' in highlight:
                    validated_highlights.append({
                        'title': highlight.get('title', '').strip(),
                        'value': highlight.get('value', '').strip(),
                        'explanation': highlight.get('explanation', '').strip()
                    })
            return validated_highlights
        else:
            # Handle legacy format (convert to new format)
            if isinstance(key_highlights, dict):
                legacy_highlights = []
                for title, value in key_highlights.items():
                    legacy_highlights.append({
                        'title': title,
                        'value': value,
                        'explanation': ''
                    })
                return legacy_highlights
            else:
                return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing key highlights JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error processing key highlights: {e}")
        return []

def format_highlights_for_display(highlights_json):
    """
    Format highlights for display in templates.
    
    Args:
        highlights_json: JSON string or list of highlights
        
    Returns:
        list: Formatted highlights for template display
    """
    try:
        if isinstance(highlights_json, str):
            highlights = json.loads(highlights_json)
        else:
            highlights = highlights_json
            
        if not isinstance(highlights, list):
            return []
            
        formatted_highlights = []
        for highlight in highlights:
            if isinstance(highlight, dict):
                formatted_highlights.append({
                    'title': highlight.get('title', ''),
                    'value': highlight.get('value', ''),
                    'explanation': highlight.get('explanation', ''),
                    'has_explanation': bool(highlight.get('explanation', '').strip())
                })
            
        return formatted_highlights
    except Exception as e:
        logger.error(f"Error formatting highlights for display: {e}")
        return []