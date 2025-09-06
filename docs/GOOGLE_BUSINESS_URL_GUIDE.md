
# Google Business URL Format Guide

## Working URL Formats ✅

### 1. Google Maps Place URLs
```
https://www.google.com/maps/place/[Business+Name]/@[lat],[lng],[zoom]/data=[encoded_data]
https://maps.google.com/maps/place/[Business+Name]/@[lat],[lng],[zoom]/data=[encoded_data]
```

### 2. Google Maps CID URLs  
```
https://maps.google.com/maps?cid=[BUSINESS_ID]
https://www.google.com/maps?cid=[BUSINESS_ID]
```

### 3. Short Google Maps URLs
```
https://goo.gl/maps/[unique_identifier]
https://maps.app.goo.gl/[unique_identifier]
```

### 4. Direct Place ID URLs
```
https://www.google.com/maps/place/?q=place_id:[PLACE_ID]
```

## Problematic URL Formats ❌

### 1. Knowledge Graph URLs (like your example)
```
https://g.co/kgs/[identifier] → Redirects to search results
```

### 2. Search Result URLs
```
https://www.google.com/search?kgmid=[identifier] → Search page, not business profile
```

## How to Get the Right URL

1. **Search for the business on Google Maps**
2. **Click on the business listing**
3. **Copy the URL from the address bar** (this will be in the correct format)
4. **Alternatively, click "Share" and copy the link**

## For Bulk Collection

When collecting URLs for bulk processing:
- Use direct Google Maps URLs only
- Test a few URLs first to ensure they work
- Avoid Knowledge Graph and search result URLs
- Consider using Google Places API for systematic data collection
