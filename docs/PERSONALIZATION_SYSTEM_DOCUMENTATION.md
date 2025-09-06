# Antidote Personalization System - Technical Documentation

## Overview

The Antidote personalization system implements anonymous user tracking and content personalization for the medical aesthetic marketplace. It uses browser fingerprinting to track user interactions without requiring login, enabling personalized content recommendations based on user behavior patterns.

## System Architecture

### Core Components

1. **PersonalizationEngine** - Main class handling all personalization logic
2. **UserInteraction** - Database model tracking user actions
3. **UserCategoryAffinity** - Database model storing user preferences for categories
4. **Browser Fingerprinting** - Anonymous user identification system
5. **Content Recommendation Engine** - Personalized content delivery system

## Database Schema

### UserInteraction Table
```sql
CREATE TABLE user_interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL,           -- Browser fingerprint
    session_id VARCHAR(64) NOT NULL,        -- Session identifier
    interaction_type VARCHAR(50) NOT NULL,  -- 'view', 'search', 'click', 'form_submit'
    target_type VARCHAR(50),                -- 'procedure', 'category', 'doctor', 'package'
    target_id INTEGER,                      -- ID of the target object
    extra_data TEXT,                        -- JSON metadata
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX idx_user_interactions_timestamp ON user_interactions(timestamp);
CREATE INDEX idx_user_interactions_type ON user_interactions(interaction_type);
```

### UserCategoryAffinity Table
```sql
CREATE TABLE user_category_affinity (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL,           -- Browser fingerprint
    category_id INTEGER NOT NULL,           -- Foreign key to categories table
    affinity_score FLOAT DEFAULT 0.0,      -- Score 0.0-1.0
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Indexes and constraints
CREATE INDEX idx_user_category_affinity_user_id ON user_category_affinity(user_id);
CREATE INDEX idx_user_category_affinity_category_id ON user_category_affinity(category_id);
CREATE UNIQUE INDEX idx_user_category_affinity_unique ON user_category_affinity(user_id, category_id);
```

## PersonalizationEngine Implementation

### File: `personalization_system.py`

```python
class PersonalizationEngine:
    """
    Core personalization engine that tracks anonymous users and personalizes content.
    Uses browser fingerprinting for anonymous tracking without requiring login.
    """
    
    @staticmethod
    def create_browser_fingerprint(user_agent, ip_address, accept_language):
        """Create a unique browser fingerprint for anonymous user tracking."""
        # Implementation uses MD5 hash of browser characteristics
        
    @staticmethod
    def track_user_interaction(fingerprint, interaction_type, target_type=None, target_id=None, metadata=None):
        """Track user interactions for personalization."""
        # Stores interaction data in user_interactions table
        
    @staticmethod
    def update_category_affinity(fingerprint, category_id, interaction_type):
        """Update user's affinity score for a category based on interaction."""
        # Implements weighted scoring system for category preferences
        
    @staticmethod
    def get_personalized_categories(fingerprint, limit=6):
        """Get personalized categories based on user's interaction history."""
        # Returns categories ordered by user affinity scores
        
    @staticmethod
    def get_personalized_procedures(fingerprint, limit=6):
        """Get personalized procedures based on user's category preferences."""
        # Returns procedures from user's preferred categories
        
    @staticmethod
    def get_personalized_doctors(fingerprint, limit=9):
        """Get personalized doctors based on user's procedure interests."""
        # Returns doctors specializing in user's preferred procedures
```

## Browser Fingerprinting System

### How It Works

1. **Data Collection**: Combines User-Agent, IP address, and Accept-Language headers
2. **Hash Generation**: Creates MD5 hash for unique identification
3. **Anonymous Tracking**: No personal data stored, only behavioral patterns
4. **Session Management**: Links interactions across page visits

### Implementation Details

```python
def create_browser_fingerprint(user_agent, ip_address, accept_language):
    """
    Creates a unique fingerprint from browser characteristics.
    
    Args:
        user_agent: Browser user agent string
        ip_address: Client IP address
        accept_language: Browser language preferences
        
    Returns:
        32-character MD5 hash as fingerprint
    """
    combined_data = f"{user_agent}|{ip_address}|{accept_language}"
    return hashlib.md5(combined_data.encode()).hexdigest()
```

## Interaction Tracking System

### Tracked Interactions

1. **Page Views**: Homepage, category pages, procedure pages, doctor profiles
2. **Search Activities**: Search queries and result interactions
3. **Click Events**: Procedure clicks, doctor profile visits, category selections
4. **Form Submissions**: Lead forms, consultation requests

### Affinity Scoring Algorithm

```python
def update_category_affinity(fingerprint, category_id, interaction_type):
    """
    Updates user affinity scores based on interaction weights:
    
    - view: +0.1 points
    - click: +0.3 points  
    - search: +0.2 points
    - form_submit: +0.5 points
    
    Maximum score: 1.0 (capped using min function)
    """
```

## Content Personalization Logic

### Homepage Personalization

The homepage (`routes.py` - `index()` function) implements the following personalization flow:

1. **Fingerprint Creation**: Generate browser fingerprint from request headers
2. **Interaction Tracking**: Log homepage view
3. **Content Retrieval**: Get personalized content based on user history
4. **Fallback System**: Use popular content for new users

### Implementation in Homepage Route

```python
@web.route('/')
def index():
    """Render the personalized home page based on user behavior."""
    try:
        from personalization_system import PersonalizationEngine
        
        # Create browser fingerprint for anonymous user tracking
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', '')
        accept_language = request.headers.get('Accept-Language', '')
        
        fingerprint = PersonalizationEngine.create_browser_fingerprint(
            user_agent, ip_address, accept_language
        )
        
        # Track homepage view for personalization
        PersonalizationEngine.track_user_interaction(
            fingerprint,
            'view',
            'page',
            None,
            {'page': 'homepage', 'url': request.path, 'session_id': session.get('session_id', '')}
        )
        
        # Get personalized content based on user's interaction history
        personalized_categories = PersonalizationEngine.get_personalized_categories(fingerprint, limit=6)
        personalized_procedures = PersonalizationEngine.get_personalized_procedures(fingerprint, limit=6)
        personalized_doctors = PersonalizationEngine.get_personalized_doctors(fingerprint, limit=9)
        
        # Use personalized content or fallback to popular content
        popular_categories = personalized_categories if personalized_categories else PersonalizationEngine.get_popular_categories(6)
        popular_procedures = personalized_procedures if personalized_procedures else PersonalizationEngine.get_popular_procedures(6)
```

## API Endpoints

### Interaction Tracking API

```python
@web.route('/personalization/track-interaction', methods=['POST'])
def track_interaction():
    """Track user interactions for personalization."""
    # Endpoint for AJAX interaction tracking from frontend
```

### Personalized Recommendations API

```python
@web.route('/personalization/recommendations/<content_type>')
def get_personalized_recommendations(content_type):
    """Get personalized content recommendations."""
    # Returns JSON with personalized content based on content_type
    # Supported types: 'categories', 'procedures', 'doctors'
```

## Frontend Integration

### JavaScript Tracking

The system includes client-side JavaScript for tracking user interactions:

1. **Automatic Tracking**: Page views, clicks on procedures/doctors
2. **Manual Tracking**: Custom events via AJAX calls
3. **Performance Optimization**: Debounced tracking to prevent spam

### Implementation Example

```javascript
// Track user interaction via AJAX
function trackInteraction(interactionType, targetType, targetId, metadata) {
    fetch('/personalization/track-interaction', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            interaction_type: interactionType,
            target_type: targetType,
            target_id: targetId,
            metadata: metadata
        })
    });
}
```

## Performance Considerations

### Database Optimization

1. **Indexes**: Strategic indexing on user_id, timestamp, and interaction_type
2. **Data Retention**: Automatic cleanup of old interaction data (>90 days)
3. **Query Optimization**: Efficient queries for personalized content retrieval

### Caching Strategy

1. **Popular Content Caching**: Cache fallback content for new users
2. **Affinity Score Caching**: Cache user affinity calculations
3. **Session-based Caching**: Reduce database queries within sessions

## Privacy and Compliance

### Data Protection

1. **Anonymous Tracking**: No personally identifiable information stored
2. **Browser Fingerprinting**: Only technical browser characteristics used
3. **Data Retention**: Configurable retention periods for compliance
4. **User Control**: Ability to opt-out of tracking

### GDPR Compliance

1. **Lawful Basis**: Legitimate interest for website optimization
2. **Data Minimization**: Only necessary data collected
3. **Transparency**: Clear privacy policy documentation
4. **User Rights**: Right to erasure and data portability

## Monitoring and Analytics

### Key Metrics

1. **Engagement Metrics**: Click-through rates, time on page
2. **Personalization Effectiveness**: Conversion rate improvements
3. **User Journey Analysis**: Path analysis through personalized content
4. **A/B Testing**: Personalized vs non-personalized content performance

### Database Monitoring

```sql
-- Monitor interaction volume
SELECT 
    DATE(timestamp) as date,
    interaction_type,
    COUNT(*) as interaction_count
FROM user_interactions 
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp), interaction_type
ORDER BY date DESC;

-- Monitor user engagement
SELECT 
    user_id,
    COUNT(*) as total_interactions,
    COUNT(DISTINCT target_type) as unique_targets,
    MAX(timestamp) as last_activity
FROM user_interactions
GROUP BY user_id
HAVING COUNT(*) > 5
ORDER BY total_interactions DESC;
```

## Deployment and Configuration

### Environment Variables

```bash
# Database configuration
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Personalization settings
PERSONALIZATION_ENABLED=true
INTERACTION_RETENTION_DAYS=90
AFFINITY_DECAY_RATE=0.95
```

### Installation Steps

1. **Database Migration**: Create personalization tables
2. **Code Deployment**: Deploy PersonalizationEngine module
3. **Frontend Integration**: Add tracking JavaScript
4. **Configuration**: Set environment variables
5. **Testing**: Verify tracking and personalization functionality

## Troubleshooting

### Common Issues

1. **Database Connection Errors**: Check DATABASE_URL configuration
2. **Tracking Not Working**: Verify JavaScript inclusion and CSRF tokens
3. **Performance Issues**: Check database indexes and query optimization
4. **Privacy Concerns**: Review data collection and retention policies

### Debug Logging

```python
import logging

# Enable debug logging for personalization
logging.getLogger('personalization').setLevel(logging.DEBUG)

# Log interaction tracking
logger.debug(f"Tracked interaction: {interaction_type} for user {fingerprint}")

# Log personalization results
logger.debug(f"Returned {len(results)} personalized items for user {fingerprint}")
```

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**: Advanced recommendation algorithms
2. **Real-time Personalization**: Live content adaptation
3. **Cross-device Tracking**: Link user sessions across devices
4. **Advanced Segmentation**: User behavior clustering
5. **Predictive Analytics**: Anticipate user needs and preferences

### Technical Roadmap

1. **Phase 1**: Basic interaction tracking and simple personalization (✓ Complete)
2. **Phase 2**: Advanced scoring algorithms and content filtering
3. **Phase 3**: Machine learning recommendation engine
4. **Phase 4**: Real-time personalization and predictive analytics

## Conclusion

The Antidote personalization system provides a comprehensive, privacy-compliant solution for anonymous user tracking and content personalization. The system enhances user experience by delivering relevant content based on behavior patterns while maintaining strong privacy protections and performance optimization.

The implementation follows modern web development best practices, includes comprehensive error handling, and provides extensive monitoring capabilities for ongoing optimization and compliance management.