"""
Phase 1 Template Helpers
Provides objects that work with both cached dictionaries and SQLAlchemy objects
"""

class SimpleCategory:
    """Simple category object that works with templates"""
    def __init__(self, data):
        if isinstance(data, dict):
            self.id = data.get('id')
            self.name = data.get('name', '')
            self.description = data.get('description', '')
            self.image_url = data.get('image_url', '')
            self.slug = data.get('slug', '')
        else:
            # SQLAlchemy object
            self.id = data.id
            self.name = data.name
            self.description = getattr(data, 'description', '')
            self.image_url = getattr(data, 'image_url', '')
            self.slug = getattr(data, 'slug', '')

class SimpleProcedure:
    """Simple procedure object that works with templates"""
    def __init__(self, data):
        if isinstance(data, dict):
            self.id = data.get('id')
            self.procedure_name = data.get('procedure_name', '')
            self.description = data.get('description', '')
            self.image_url = data.get('image_url', '')
            self.category_id = data.get('category_id')
        else:
            # SQLAlchemy object
            self.id = data.id
            self.procedure_name = data.procedure_name
            self.description = getattr(data, 'description', '')
            self.image_url = getattr(data, 'image_url', '')
            self.category_id = getattr(data, 'category_id', None)

class SimpleDoctor:
    """Simple doctor object that works with templates"""
    def __init__(self, data):
        if isinstance(data, dict):
            self.id = data.get('id')
            self.name = data.get('name', '')
            self.specialization = data.get('specialization', '')
            self.specialty = data.get('specialty', '')
            self.qualification = data.get('qualification', '')
            self.experience = data.get('experience', 0)
            self.rating = data.get('rating', 0)
            self.profile_image = data.get('profile_image', '')
            self.profile_picture = data.get('profile_picture', '') or data.get('profile_image', '')
            self.city = data.get('city', '')
            self.bio = data.get('bio', '')
            self.is_verified = data.get('is_verified', False)
        else:
            # SQLAlchemy object
            self.id = data.id
            self.name = data.name
            self.specialization = getattr(data, 'specialization', '')
            self.specialty = getattr(data, 'specialty', '')
            self.qualification = getattr(data, 'qualification', '')
            self.experience = getattr(data, 'experience', 0)
            self.rating = getattr(data, 'rating', 0)
            self.profile_image = getattr(data, 'profile_image', '')
            self.profile_picture = getattr(data, 'profile_image', '')
            self.city = getattr(data, 'city', '')
            self.bio = getattr(data, 'bio', '')
            self.is_verified = getattr(data, 'is_verified', False)

class SimpleCommunityThread:
    """Simple community thread object that works with templates"""
    def __init__(self, data):
        if isinstance(data, dict):
            self.id = data.get('id')
            self.title = data.get('title', '')
            self.content = data.get('content', '')
            self.user_id = data.get('user_id')
            self.author_name = data.get('author_name', 'Anonymous User')
            self.is_anonymous = data.get('is_anonymous', False)
            self.created_at = data.get('created_at')
            self.view_count = data.get('view_count', 0)
            self.upvotes = data.get('upvotes', 0)
            self.reply_count = data.get('reply_count', 0)
            # Create a mock user object for template compatibility
            self.user = type('User', (), {'username': self.author_name})()
        else:
            # SQLAlchemy object
            self.id = data.id
            self.title = getattr(data, 'title', '')
            self.content = getattr(data, 'content', '')
            self.user_id = data.user_id
            self.author_name = getattr(data, 'author_name', 'Anonymous User')
            self.is_anonymous = getattr(data, 'is_anonymous', False)
            self.created_at = data.created_at
            self.view_count = getattr(data, 'view_count', 0)
            self.upvotes = getattr(data, 'upvotes', 0)
            self.reply_count = getattr(data, 'reply_count', 0)
            self.user = getattr(data, 'user', None)

def convert_cached_data_to_objects(cached_data, object_type):
    """Convert cached dictionary data to simple objects for template compatibility"""
    if not cached_data:
        return []
    
    object_map = {
        'category': SimpleCategory,
        'procedure': SimpleProcedure,  
        'doctor': SimpleDoctor,
        'community_thread': SimpleCommunityThread
    }
    
    ObjectClass = object_map.get(object_type)
    if not ObjectClass:
        return cached_data
    
    return [ObjectClass(item) for item in cached_data]