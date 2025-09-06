# Indian Clinic Data Processing - CSV Format Documentation

## Overview

This document outlines the standardized CSV format and data processing methodology for importing clinic data from Google Places API across major Indian cities into the medical aesthetics marketplace database.

## Processed Cities Dataset

The following cities have been processed and standardized:

| City | Filename | Records | File Size | State |
|------|----------|---------|-----------|-------|
| Hyderabad | `hyderabad_clinics.csv` | 1,243 | 1.3MB | Telangana |
| Bengaluru | `bengaluru_clinics.csv` | 1,247 | 1.4MB | Karnataka |
| Mumbai | `mumbai_clinics.csv` | 1,245 | 1.3MB | Maharashtra |
| Delhi | `delhi_clinics.csv` | 1,246 | 1.3MB | Delhi |
| Gurugram | `gurugram_clinics.csv` | 392 | 415KB | Haryana |
| Kolkata | `kolkata_clinics.csv` | 437 | 430KB | West Bengal |
| Chennai | `chennai_clinics.csv` | 281 | 287KB | Tamil Nadu |
| Ahmedabad | `ahmedabad_clinics.csv` | 240 | 244KB | Gujarat |
| Jaipur | `jaipur_clinics.csv` | 107 | 105KB | Rajasthan |
| Visakhapatnam | `visakhapatnam_clinics.csv` | 97 | 99KB | Andhra Pradesh |

**Total: 6,535 authentic clinic profiles**

## CSV Structure

### Column Definitions (25 columns)

```csv
name,slug,description,address,city,state,country,pincode,latitude,longitude,contact_number,email,website_url,specialties,operating_hours,google_rating,google_review_count,google_place_id,google_maps_url,profile_image,amenities,owner_email,is_approved,verification_status,claim_status
```

### Field Specifications

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `name` | String | Yes | Clinic/business name from Google Places | "Chennai Plastic Surgery" |
| `slug` | String | Yes | URL-friendly identifier | "chennai-plastic-surgery" |
| `description` | String | No | Business description (often empty) | "" |
| `address` | String | Yes | Complete address with pincode | "New No. 12, Old, 10, Mc Nichols Road..." |
| `city` | String | Yes | Standardized city name | "Chennai" |
| `state` | String | Yes | Indian state name | "Tamil Nadu" |
| `country` | String | Yes | Always "India" | "India" |
| `pincode` | String | No | 6-digit postal code extracted from address | "600031" |
| `latitude` | Float | No | Geographic coordinate | "13.0709521" |
| `longitude` | Float | No | Geographic coordinate | "80.2406935" |
| `contact_number` | String | No | Phone in +91 format | "+919600058899" |
| `email` | String | No | Currently empty (for future use) | "" |
| `website_url` | String | No | Clinic website URL | "http://www.thecosmeticsurgery.org/" |
| `specialties` | String | No | Comma-separated service categories | "Plastic surgeon, Dermatologist, Hair removal service" |
| `operating_hours` | JSON | No | Hours in JSON format | `{"Monday": "6 AM to 7 PM", "Tuesday": "6 AM to 7 PM"}` |
| `google_rating` | Float | No | Rating out of 5 | "4.9" |
| `google_review_count` | Integer | No | Number of reviews | "1322" |
| `google_place_id` | String | Yes | Unique Google Places identifier | "ChIJV3xs3XpmUjoR3xUXFHKsvg4" |
| `google_maps_url` | String | No | Google Maps search URL | "https://www.google.com/maps/search/..." |
| `profile_image` | String | No | Google business photo URL | "https://lh3.googleusercontent.com/..." |
| `amenities` | String | No | Comma-separated facility features | "Wheelchair Accessible, Digital Payments" |
| `owner_email` | String | Yes | Temporary email for claiming | "che.chennaiplasticsurger.1@antidote-temp.com" |
| `is_approved` | Boolean | Yes | Always "false" initially | "false" |
| `verification_status` | String | Yes | Always "pending" initially | "pending" |
| `claim_status` | String | Yes | Always "unclaimed" initially | "unclaimed" |

## Data Cleaning & Standardization Process

### 1. Phone Number Standardization

```python
def clean_phone_number(phone: str) -> str:
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # If it starts with +91, keep it
    if cleaned.startswith('+91'):
        return cleaned
    
    # If it's a 10-digit number, add +91
    if len(cleaned) == 10 and cleaned.isdigit():
        return f"+91{cleaned}"
    
    return cleaned
```

### 2. City Name Standardization

Each city processor includes specific variants mapping:
- **Chennai**: ['chennai', 'madras', 'tamil nadu, chennai'] → "Chennai"
- **Mumbai**: ['mumbai', 'bombay'] → "Mumbai"
- **Bengaluru**: ['bengaluru', 'bangalore'] → "Bengaluru"
- **Kolkata**: ['kolkata', 'calcutta'] → "Kolkata"
- **Ahmedabad**: ['ahmedabad', 'amdavad', 'ahmadabad'] → "Ahmedabad"

### 3. Operating Hours Processing

Google Places hours are converted to JSON format:

```python
def process_opening_hours(row: Dict) -> str:
    hours_data = {}
    for i in range(7):
        day_key = f"openingHours/{i}/day"
        hours_key = f"openingHours/{i}/hours"
        
        if day_key in row and hours_key in row and row[day_key] and row[hours_key]:
            hours_data[row[day_key]] = row[hours_key]
    
    return json.dumps(hours_data) if hours_data else ""
```

### 4. Specialty Extraction

Categories are extracted from multiple Google Places category fields:

```python
def extract_categories(row: Dict) -> str:
    categories = []
    for i in range(10):  # Check categories/0 through categories/9
        cat_key = f"categories/{i}"
        if cat_key in row and row[cat_key]:
            categories.append(row[cat_key].strip())
    
    return ", ".join(list(dict.fromkeys(categories)))  # Remove duplicates
```

### 5. URL Slug Generation

```python
def generate_slug(name: str) -> str:
    # Convert to lowercase, replace spaces and special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')
```

### 6. Owner Email Generation

Temporary emails are created for clinic claiming process:

```python
def generate_owner_email(name: str, index: int, city_prefix: str) -> str:
    base_name = re.sub(r'[^\w\s]', '', name.lower())
    base_name = re.sub(r'\s+', '', base_name)[:20]  # Max 20 chars
    
    return f"{city_prefix}.{base_name}.{index}@antidote-temp.com"
```

**City Prefixes:**
- Chennai: `che`
- Mumbai: `mum`
- Bengaluru: `blr`
- Delhi: `del`
- Hyderabad: `hyd`
- Kolkata: `kol`
- Gurugram: `ggn`
- Ahmedabad: `ahd`
- Jaipur: `jai`
- Visakhapatnam: `vzg`

### 7. Amenities Extraction

```python
def extract_amenities(row: Dict) -> List[str]:
    amenities = []
    
    # Accessibility
    if row.get("additionalInfo/Accessibility/0/Wheelchair accessible entrance") == "true":
        amenities.append("Wheelchair Accessible")
    
    # Parking
    if row.get("additionalInfo/Parking/0/Free parking lot") == "true":
        amenities.append("Free Parking")
    elif row.get("additionalInfo/Parking/0/Paid parking lot") == "true":
        amenities.append("Parking Available")
    
    # Payments
    if row.get("additionalInfo/Payments/0/Credit cards") == "true":
        amenities.append("Credit Cards Accepted")
    if row.get("additionalInfo/Payments/0/Google Pay") == "true":
        amenities.append("Digital Payments")
    
    # Appointments
    if row.get("additionalInfo/Planning/0/Appointment required") == "true":
        amenities.append("Appointment Required")
    elif row.get("additionalInfo/Planning/0/Accepts walk-ins") == "true":
        amenities.append("Walk-ins Welcome")
    
    return amenities
```

## Data Quality Metrics

### Overall Statistics

| Metric | Percentage Range | Description |
|--------|------------------|-------------|
| Phone Numbers | 85-95% | Clinics with contact numbers |
| Websites | 60-75% | Clinics with website URLs |
| Google Ratings | 95%+ | Clinics with verified ratings |
| Operating Hours | 70-85% | Clinics with hours data |
| Profile Images | 90%+ | Clinics with business photos |

### City-Specific Quality

| City | Phone % | Website % | Rating % |
|------|---------|-----------|----------|
| Hyderabad | 92% | 68% | 97% |
| Bengaluru | 91% | 72% | 96% |
| Mumbai | 93% | 71% | 95% |
| Delhi | 90% | 69% | 96% |
| Gurugram | 88% | 65% | 94% |
| Kolkata | 90% | 63% | 96% |
| Chennai | 89% | 62% | 95% |
| Ahmedabad | 89% | 60% | 94% |
| Jaipur | 88% | 61% | 96% |
| Visakhapatnam | 93% | 74% | 91% |

## Implementation Guidelines

### 1. Database Import Process

```sql
-- Example table structure
CREATE TABLE clinics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    country VARCHAR(50) DEFAULT 'India',
    pincode VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    contact_number VARCHAR(20),
    email VARCHAR(255),
    website_url TEXT,
    specialties TEXT,
    operating_hours JSONB,
    google_rating DECIMAL(2,1),
    google_review_count INTEGER,
    google_place_id VARCHAR(255) UNIQUE,
    google_maps_url TEXT,
    profile_image TEXT,
    amenities TEXT,
    owner_email VARCHAR(255) NOT NULL,
    is_approved BOOLEAN DEFAULT FALSE,
    verification_status VARCHAR(50) DEFAULT 'pending',
    claim_status VARCHAR(50) DEFAULT 'unclaimed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Bulk Import Script

```python
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

def import_clinic_csv(csv_file, db_connection):
    df = pd.read_csv(csv_file)
    
    # Convert empty strings to None for database
    df = df.replace('', None)
    
    # Prepare data for insertion
    data = [tuple(row) for row in df.values]
    
    with db_connection.cursor() as cursor:
        execute_values(
            cursor,
            "INSERT INTO clinics (...columns...) VALUES %s",
            data,
            template=None,
            page_size=100
        )
    
    db_connection.commit()
```

### 3. Post-Import Verification

```sql
-- Verify import counts
SELECT city, COUNT(*) as clinic_count 
FROM clinics 
GROUP BY city 
ORDER BY clinic_count DESC;

-- Check data quality
SELECT 
    COUNT(*) as total_clinics,
    COUNT(contact_number) as with_phone,
    COUNT(website_url) as with_website,
    COUNT(google_rating) as with_rating,
    AVG(google_rating) as avg_rating
FROM clinics;
```

## Owner Claiming Workflow

### 1. Clinic Discovery
- Business owners search for their clinic using name, address, or phone
- System matches using fuzzy search on multiple fields

### 2. Claim Initiation
- Owner provides business verification documents
- Temporary email is replaced with owner's actual email
- Status changes from 'unclaimed' to 'pending_verification'

### 3. Verification Process
- Document review (business license, GST certificate, etc.)
- Phone verification using stored contact_number
- Status changes to 'verified' upon approval

### 4. Profile Management
- Owner gains access to edit clinic details
- Can update services, photos, operating hours
- Manage patient inquiries and bookings

## Error Handling & Edge Cases

### 1. Duplicate Detection
```python
# Check for potential duplicates based on:
# - Google Place ID (primary)
# - Name + Address similarity
# - Phone number matches
```

### 2. Data Validation
```python
# Validate required fields
# Check phone number format
# Verify pincode format (6 digits)
# Validate coordinate ranges for India
```

### 3. Missing Data Handling
```python
# Skip records missing essential data (name, address)
# Set default values for optional fields
# Log missing data statistics for monitoring
```

## Maintenance & Updates

### 1. Regular Data Refresh
- Re-scrape Google Places data quarterly
- Update ratings and review counts monthly
- Refresh operating hours during holiday seasons

### 2. Data Quality Monitoring
- Track completion rates for key fields
- Monitor claim success rates by city
- Alert on significant data quality drops

### 3. Schema Evolution
- Version control for CSV format changes
- Backward compatibility for existing imports
- Migration scripts for schema updates

---

**Last Updated:** June 2025  
**Version:** 1.1  
**Total Records:** 6,535 clinics across 10 cities