"""
API routes without CSRF protection for personalization tracking.
"""
from flask import Blueprint, request, jsonify

# Create a separate blueprint for API routes without CSRF
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/track-interaction', methods=['POST'])
def track_interaction():
    """Track user interactions for personalization - no CSRF protection."""
    try:
        from personalization_service import PersonalizationService
        
        # Get data from either JSON or form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        fingerprint = data.get('fingerprint')
        interaction_type = data.get('interaction_type')
        content_type = data.get('content_type')
        content_id = data.get('content_id', 0)
        content_name = data.get('content_name', '')
        page_url = data.get('page_url', '')
        session_id = data.get('session_id', '')
        
        if not fingerprint or not interaction_type or not content_type:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Track the interaction
        PersonalizationService.track_interaction(
            fingerprint, interaction_type, content_type, content_id, 
            content_name, page_url, session_id
        )
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error tracking interaction: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/recommendations/<content_type>')
def get_personalized_recommendations(content_type):
    """Get personalized content recommendations."""
    try:
        from personalization_service import PersonalizationService
        
        fingerprint = request.args.get('fingerprint')
        limit = int(request.args.get('limit', 6))
        
        if not fingerprint:
            return jsonify({'success': False, 'error': 'Fingerprint required'}), 400
        
        recommendations = PersonalizationService.get_personalized_content(
            fingerprint, content_type, limit
        )
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500