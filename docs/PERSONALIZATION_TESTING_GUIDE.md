# Personalization System Testing Guide

## Overview
This guide explains how to test the personalization features to verify they're working correctly.

## Testing Strategy

### 1. Database Verification
First, verify the personalization tables exist and are functioning:

```sql
-- Check if tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('user_interactions', 'user_category_affinity');

-- Check table structure
\d user_interactions
\d user_category_affinity
```

### 2. Interaction Tracking Test

#### Manual Testing Steps:

1. **Clear Browser Data**: Start with a clean slate
   - Clear cookies, localStorage, and cache
   - Use incognito/private browsing mode

2. **Visit Homepage**: Navigate to the main page
   - This should create your first interaction record

3. **Browse Categories**: Click on different procedure categories
   - Breast Surgery, Rhinoplasty, etc.
   - Each click should be tracked

4. **View Procedures**: Click on individual procedures
   - This builds your preference profile

5. **View Doctor Profiles**: Browse different doctors
   - Helps establish your interests

#### Verification Queries:

```sql
-- Check if interactions are being tracked
SELECT * FROM user_interactions 
ORDER BY timestamp DESC 
LIMIT 10;

-- Check affinity scores being calculated
SELECT * FROM user_category_affinity 
ORDER BY affinity_score DESC;

-- Count interactions by type
SELECT interaction_type, COUNT(*) 
FROM user_interactions 
GROUP BY interaction_type;
```

### 3. Personalization Effect Test

#### Testing Personalized Content:

1. **First Visit** (New User):
   - Homepage should show popular/default content
   - No personalization yet

2. **Build Profile**: Interact with specific categories
   - Focus on 2-3 categories (e.g., Breast Surgery, Rhinoplasty)
   - View multiple procedures in these categories
   - Visit doctor profiles who specialize in these areas

3. **Return Visit**: 
   - Clear session but keep the same browser
   - Revisit homepage
   - Should now see personalized content based on your interactions

#### Expected Behavior:

- **Categories**: Your preferred categories should appear first
- **Procedures**: Procedures from your preferred categories should be prioritized
- **Doctors**: Doctors specializing in your areas of interest should be featured

### 4. Browser Fingerprinting Test

#### Multi-Browser Testing:

1. **Same Device, Different Browsers**:
   - Chrome: Build one profile (focus on facial procedures)
   - Firefox: Build different profile (focus on body procedures)
   - Each should maintain separate personalization

2. **Incognito vs Normal**:
   - Normal browsing: Should maintain personalization
   - Incognito: Should start fresh each time

#### Verification:

```sql
-- Check unique fingerprints
SELECT user_id, COUNT(*) as interaction_count 
FROM user_interactions 
GROUP BY user_id 
ORDER BY interaction_count DESC;

-- See different user profiles
SELECT ui.user_id, ui.interaction_type, ui.target_type, ui.timestamp
FROM user_interactions ui
WHERE ui.user_id IN (
    SELECT DISTINCT user_id FROM user_interactions LIMIT 3
)
ORDER BY ui.user_id, ui.timestamp;
```

## Automated Testing

### API Endpoint Testing

#### 1. Track Interaction Endpoint

```bash
# Test interaction tracking
curl -X POST http://localhost:5000/personalization/track-interaction \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_type": "click",
    "target_type": "procedure", 
    "target_id": 1,
    "metadata": {"test": "api_test"}
  }'
```

#### 2. Recommendations Endpoint

```bash
# Test personalized recommendations
curl "http://localhost:5000/personalization/recommendations/categories?fingerprint=test_fingerprint"
```

### JavaScript Console Testing

Open browser console and run:

```javascript
// Test interaction tracking
fetch('/personalization/track-interaction', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        interaction_type: 'test',
        target_type: 'procedure',
        target_id: 1,
        metadata: {test: 'console_test'}
    })
}).then(response => response.json())
  .then(data => console.log('Success:', data));

// Check if tracking script is loaded
console.log('Personalization loaded:', typeof trackInteraction !== 'undefined');
```

## Expected Test Results

### 1. Database Growth
- `user_interactions` table should gain new records with each action
- `user_category_affinity` table should show increasing scores for preferred categories

### 2. Homepage Changes
- First visit: Generic popular content
- After interactions: Content shifts to match your browsing patterns
- Categories you clicked should appear higher in the list
- Procedures from your preferred categories should be featured

### 3. Affinity Score Development
```sql
-- Monitor affinity score changes
SELECT 
    uca.user_id,
    c.name as category_name,
    uca.affinity_score,
    uca.last_updated
FROM user_category_affinity uca
JOIN categories c ON uca.category_id = c.id
WHERE uca.user_id = 'YOUR_FINGERPRINT'
ORDER BY uca.affinity_score DESC;
```

## Performance Testing

### Load Testing
1. Simulate multiple users browsing simultaneously
2. Monitor database performance during high interaction volume
3. Check response times for personalized content delivery

### Memory Testing
1. Monitor server memory usage during personalization
2. Check for memory leaks in long-running sessions

## Troubleshooting Common Issues

### No Interactions Being Tracked
1. Check browser console for JavaScript errors
2. Verify CSRF token configuration
3. Check database connection

### Personalization Not Working
1. Verify sufficient interaction data exists
2. Check affinity score calculations
3. Ensure fallback content is working

### Performance Issues
1. Check database indexes are created
2. Monitor query execution times
3. Verify caching is working properly

## Testing Checklist

- [ ] Database tables created correctly
- [ ] Interaction tracking works on homepage
- [ ] Category clicks are recorded
- [ ] Procedure views are tracked
- [ ] Doctor profile visits are logged
- [ ] Affinity scores are calculated
- [ ] Homepage content personalizes after interactions
- [ ] Different browsers maintain separate profiles
- [ ] API endpoints respond correctly
- [ ] JavaScript tracking functions work
- [ ] Performance is acceptable under load
- [ ] Error handling works properly
- [ ] Privacy compliance is maintained

## Success Metrics

1. **Interaction Capture Rate**: >95% of user actions tracked
2. **Personalization Effectiveness**: Content relevance improves after 5+ interactions
3. **Performance**: Homepage loads in <2 seconds with personalization
4. **Accuracy**: Personalized content matches user behavior patterns
5. **Privacy**: No personally identifiable information stored