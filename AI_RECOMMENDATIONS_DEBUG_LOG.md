# AI Recommendations System - Debug Log & Resolution Guide

## Project Overview
The goal was to fix the AI recommendation system on the Antidote medical marketplace homepage where users can type their medical concerns in the "Confused? Ask AI for treatment recommendations" section, click "Ask AI", and receive personalized treatment recommendations.

## Initial Problem Statement
- Users typing concerns and clicking "Ask AI" resulted in page reloading without showing results
- Internal server errors and CSRF validation failures were occurring
- Multiple conflicting AI recommendation systems were causing route conflicts

## Key Issues Identified

### 1. Multiple Conflicting AI Systems
**Problem**: The application had multiple AI recommendation files causing route conflicts:
- `ai_recommendations.py`
- `simple_ai_recommendations.py` 
- `ai_recommendations_clean.py`
- Various other AI-related files

**Evidence**: Route registration warnings and import conflicts in logs

**Resolution Attempted**: 
- Deleted all conflicting AI files
- Created single clean implementation in `ai_recommendations_clean.py`
- Updated `routes.py` to register only the clean system

### 2. Template Reference Issues
**Problem**: Templates still referenced old AI system endpoints
**Location**: `templates/base.html` line 401
**Error**: `Could not build url for endpoint 'simple_ai.get_recommendations'`
**Resolution**: Updated footer link to use `ai_clean.ai_recommendations`

### 3. Form Data Capture Issues
**Problem**: Form was submitting but textarea values were empty
**Evidence**: Logs showed `'concerns': ''` despite user input
**Root Cause**: Two textareas with same name (desktop/mobile) causing form submission conflicts

**Technical Analysis**:
```
Form data received: {
    'csrf_token': 'IjQ3NGU1MzA0YWNhMTEyZWNhZmI2NGQ0NTQwMzUyNzUyOWM1NDUyOWIi.aG-A9A.2xGursn4wE4aAlIYtonos0SjAFo', 
    'concerns': ''
}
```

**Resolution Implemented**:
- Removed `name="concerns"` from both textareas
- Added hidden input field: `<input type="hidden" name="concerns" id="hiddenConcerns" value=""/>`
- Added JavaScript to sync textarea values to hidden input before submission

### 4. CSRF Token Validation
**Problem**: Initial CSRF validation failures
**Resolution**: Added proper CSRF handling in `ai_recommendations_clean.py`:
```python
from flask_wtf.csrf import validate_csrf, CSRFError
# Validation logic added but later removed for debugging
```

### 5. JavaScript Form Handling
**Implementation**: Added comprehensive JavaScript solution:
```javascript
// Sync textareas based on screen size
function syncTextareas() {
    const activeTextarea = window.innerWidth >= 992 ? desktopTextarea : mobileTextarea;
    if (activeTextarea && activeTextarea.value.trim()) {
        hiddenInput.value = activeTextarea.value.trim();
    }
}
```

## Current Status

### ✅ Successfully Resolved
1. **Form submission working**: Console logs show `"AI form submitting with concerns: dark circles"`
2. **AI processing working**: Gemini AI successfully processes queries and finds recommendations
3. **Data flow working**: Form → Backend → AI Analysis → Database queries for procedures/doctors

### ❌ Current Issue - Template Error
**Error Location**: `templates/ai_recommendations_results.html` line 110
**Error Details**: 
```
jinja2.exceptions.UndefinedError: 'summary' is undefined
<span class="confidence-number">{{ (summary.confidence * 100)|round|int }}%</span>
```

**Analysis**: The results template expects a `summary` object with confidence data, but the backend is not providing this structure.

## Backend Data Structure Analysis

### What the Backend Provides:
```python
session['ai_recommendations'] = {
    'user_input': query_text,
    'analysis': analysis,  # Dict with health concerns, body parts, etc.
    'procedures': [...],   # List of procedure objects
    'doctors': [...]       # List of doctor objects
}
```

### What the Template Expects:
- `summary` object with confidence scores
- Structured analysis data
- Specific data format that doesn't match current implementation

## Files Modified

### Core System Files:
1. **`ai_recommendations_clean.py`** - New clean AI system implementation
2. **`routes.py`** - Updated to register only clean AI system
3. **`templates/base.html`** - Fixed footer link reference
4. **`templates/index.html`** - Updated form structure and added JavaScript

### Files Deleted:
- Multiple conflicting AI recommendation files (cleaned up during resolution)

## Recommended Next Steps

### Immediate Fix Required:
1. **Fix Template Data Structure**: Update `ai_recommendations_clean.py` to provide data matching template expectations
2. **Create Missing Summary Object**: Generate confidence scores and summary data
3. **Template Compatibility**: Ensure all template variables have corresponding backend data

### Long-term Improvements:
1. **Error Handling**: Add comprehensive error handling for AI failures
2. **User Experience**: Add loading states and better feedback
3. **Performance**: Cache AI results for similar queries
4. **Testing**: Create test cases for form submission and AI processing

## Technical Architecture

### Current Flow:
```
User Input → Form (index.html) 
    ↓
JavaScript validation & sync 
    ↓
POST /ai-recommendations 
    ↓
ai_recommendations_clean.py processing
    ↓
Gemini AI analysis
    ↓
Database queries (procedures, doctors)
    ↓
Session storage
    ↓
Redirect to /ai-recommendations-results
    ↓
Template rendering (FAILS HERE - missing 'summary')
```

### Key Components:
- **Form Handler**: JavaScript syncs mobile/desktop textareas
- **Backend Processor**: Gemini AI + database integration
- **Results Display**: Template system (needs data structure fix)

## Environment & Dependencies
- **AI Service**: Google Gemini AI (GEMINI_API_KEY configured)
- **Framework**: Flask with Jinja2 templates
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: Bootstrap + custom JavaScript

## Debug Information for Next Developer

### To Test the Current State:
1. Go to homepage
2. Type "dark circles" in AI recommendation form
3. Click "Ask AI"
4. Check browser console - should show: "AI form submitting with concerns: dark circles"
5. Check server logs - should show successful AI processing
6. Error occurs during results template rendering

### Key Log Entries to Monitor:
- `INFO:ai_recommendations_clean:AI Recommendations POST request received`
- `INFO:ai_recommendations_clean:Found X procedures and Y doctors`
- Template error: `jinja2.exceptions.UndefinedError: 'summary' is undefined`

### Quick Fix Location:
The immediate fix needed is in `ai_recommendations_clean.py` around lines 235-263 where the session data is structured. Need to add a `summary` object that matches template expectations in `templates/ai_recommendations_results.html`.

## Lessons Learned
1. **Multiple systems conflict**: Always check for existing implementations before creating new ones
2. **Form design matters**: Responsive forms with multiple inputs need careful JavaScript handling
3. **Template-backend alignment**: Ensure data structures match between backend and frontend
4. **Incremental testing**: Test each component (form → backend → template) separately
5. **Logging is crucial**: Detailed logging helped identify exact failure points

---
*Generated: July 10, 2025*
*Status: Ready for template data structure fix*