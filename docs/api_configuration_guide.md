# Google API Configuration Guide for Clinic Data Extraction

## Current Issue
Your Google API key exists but has "REQUEST_DENIED" errors because specific API services need to be enabled.

## Required API Services

### 1. Places API (Legacy) - For basic business data
- **Service**: Places API
- **Endpoint**: `maps.googleapis.com/maps/api/place/textsearch/json`
- **Usage**: Business search and basic details

### 2. Places API (New) - For enhanced features  
- **Service**: Places API (New)
- **Endpoint**: `places.googleapis.com/v1/places:searchText`
- **Usage**: Reviews, photos, comprehensive business data

### 3. Geocoding API - For address coordinates
- **Service**: Geocoding API  
- **Endpoint**: `maps.googleapis.com/maps/api/geocode/json`
- **Usage**: Convert addresses to lat/lng coordinates

### 4. Photos API - For business images
- **Service**: Places API Photos
- **Endpoint**: `maps.googleapis.com/maps/api/place/photo`
- **Usage**: Download business photos

## API Configuration Steps

### Step 1: Access Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (ID: 219853954654)
3. Navigate to "APIs & Services" > "Library"

### Step 2: Enable Required APIs
Enable these APIs in order:
1. **Places API** (Legacy)
2. **Places API (New)**  
3. **Geocoding API**
4. **Maps JavaScript API** (for frontend maps)

### Step 3: Update API Key Restrictions
1. Go to "APIs & Services" > "Credentials"
2. Click on your API key
3. Under "API restrictions", select "Restrict key"
4. Choose the APIs you enabled above

### Step 4: Test Configuration
The extractor will test each API service and report which ones work.

## Pricing Estimates for 500+ Clinics

### Places API (New) - Most comprehensive
- **Text Search**: $32 per 1000 requests
- **Place Details**: $17 per 1000 requests  
- **Cost for 500 clinics**: ~$25

### Places API (Legacy) - Basic data
- **Text Search**: $17 per 1000 requests
- **Place Details**: $17 per 1000 requests
- **Cost for 500 clinics**: ~$17

### Geocoding API
- **Geocoding**: $5 per 1000 requests
- **Cost for 500 clinics**: ~$3

## Fallback Options

### Option 1: Web Scraping (Current Implementation)
- **Cost**: Free
- **Data Quality**: Good for basic info
- **Limitations**: No reviews/photos, rate-limited

### Option 2: Manual CSV Upload
- **Cost**: Free  
- **Data Quality**: Depends on source
- **Scalability**: Not suitable for 500+ clinics

### Option 3: Hybrid Approach (Recommended)
- Use web scraping for basic data
- Enable Places API for high-priority clinics
- Manual verification for critical information

## Implementation Status

✅ **Web Scraping Extractor**: Ready for 500+ clinics
✅ **Database Schema**: Reviews and photos tables created
✅ **Bulk Processing**: Handles rate limiting and error handling
⚠️ **Google API**: Needs service activation
⚠️ **Reviews/Photos**: Requires Places API (New)

## Next Steps

1. **Immediate**: Use web scraping extractor for bulk processing
2. **Short-term**: Enable required Google APIs for enhanced data
3. **Long-term**: Implement automated review and photo extraction

## Production Usage

```python
from production_clinic_extractor import ClinicDataExtractor

# Initialize extractor
extractor = ClinicDataExtractor()

# Process single URL
clinic_id = extractor.process_single_url("https://g.co/kgs/...")

# Process bulk URLs (500+)
urls = [...]  # List of Google Business URLs
results = extractor.process_bulk_urls(urls, delay=1)

print(f"Processed: {results['successful']}/{results['total']} clinics")
```

The system is ready for production use with current web scraping capabilities, and can be enhanced with full Google API integration when services are enabled.