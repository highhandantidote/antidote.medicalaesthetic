# Clinic Details Extractor Documentation

## Overview
This document explains the complete process of extracting clinic data from Google My Business URLs and importing it into the Antidote platform database. The system maintains data integrity by using existing database structures and authentic Google Business data.

## Database Tables Used

### Primary Tables
1. **clinics** - Main clinic information
2. **google_reviews** - External Google Business reviews  
3. **users** - User accounts for clinic owners
4. **clinic_doctors** - Association between clinics and doctors
5. **doctors** - Doctor profiles

### Supporting Tables
- **clinic_reviews** - Internal platform reviews (separate from Google reviews)
- **packages** - Treatment packages offered by clinics
- **leads** - Lead generation and tracking

## Extraction Process

### Step 1: Google Business URL Processing

#### Required URL Format
```
https://www.google.com/maps/place/[CLINIC_NAME]/[COORDINATES]/[PLACE_ID]
```

#### Data Extraction Points
- **Basic Information**: Name, address, phone, website, hours
- **Reviews**: Authentic Google Business reviews with ratings
- **Photos**: Profile images and gallery photos
- **Services**: Listed specialties and services
- **Contact Details**: Phone numbers, email, website links

### Step 2: Database Schema Integration

#### Clinics Table Structure
```sql
clinics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    contact_number VARCHAR(20),
    whatsapp_number VARCHAR(20),
    email VARCHAR(255),
    website_url VARCHAR(500),
    google_business_url VARCHAR(500),
    working_hours TEXT,
    description TEXT,
    specialties TEXT,
    popular_procedures TEXT,
    highlights TEXT,
    profile_image VARCHAR(500),
    promotional_banner_url VARCHAR(500),
    rating DECIMAL(3,2),
    total_reviews INTEGER,
    is_verified BOOLEAN DEFAULT false,
    owner_user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### Google Reviews Table Structure
```sql
google_reviews (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER REFERENCES clinics(id),
    reviewer_name VARCHAR(255),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    review_date DATE,
    profile_photo_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Step 3: Implementation Scripts

#### Core Extraction Script
**File**: `production_clinic_extractor.py`
- Handles Google Maps URL parsing
- Extracts clinic information using BeautifulSoup
- Processes contact details and business hours
- Downloads and stores profile images

#### Review Extraction Script  
**File**: `google_reviews_proper_extractor.py`
- Extracts authentic Google Business reviews
- Maintains reviewer anonymity while preserving authenticity
- Stores review dates and ratings
- Links reviews to clinic records

#### Admin Assignment Script
**File**: `admin_clinic_assignment.py` (from unified_clinic_dashboard.py)
- Creates clinic owner accounts
- Assigns clinic ownership to users
- Sets proper role permissions (role: 'clinic_owner')

### Step 4: Data Processing Workflow

#### Phase 1: Basic Clinic Information
1. **Extract URL Components**
   ```python
   place_id = extract_place_id(google_business_url)
   clinic_data = scrape_business_details(place_id)
   ```

2. **Store Clinic Record**
   ```sql
   INSERT INTO clinics (name, address, city, state, contact_number, 
                       google_business_url, rating, total_reviews)
   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
   ```

#### Phase 2: Review Integration
1. **Extract Reviews**
   ```python
   reviews = extract_google_reviews(place_id)
   for review in reviews:
       store_google_review(clinic_id, review)
   ```

2. **Store Reviews**
   ```sql
   INSERT INTO google_reviews (clinic_id, reviewer_name, rating, 
                              review_text, review_date)
   VALUES (%s, %s, %s, %s, %s)
   ```

#### Phase 3: Owner Assignment
1. **Create User Account**
   ```sql
   INSERT INTO users (email, username, password_hash, role)
   VALUES (%s, %s, %s, 'clinic_owner')
   ```

2. **Assign Ownership**
   ```sql
   UPDATE clinics SET owner_user_id = %s WHERE id = %s
   ```

### Step 5: Error Prevention Guidelines

#### Common Pitfalls and Solutions

1. **CSRF Token Errors**
   - **Problem**: Forms missing security tokens
   - **Solution**: Add `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>` to all forms

2. **Duplicate Clinic Entries**
   - **Problem**: Multiple imports of same clinic
   - **Solution**: Check for existing `google_business_url` before insertion

3. **Invalid User Roles**
   - **Problem**: Users cannot access clinic dashboard
   - **Solution**: Ensure role is set to `'clinic_owner'` not `'clinic'`

4. **Missing Foreign Key Relationships**
   - **Problem**: Orphaned records
   - **Solution**: Always verify parent records exist before creating relationships

#### Database Constraints
```sql
-- Ensure unique Google Business URLs
ALTER TABLE clinics ADD CONSTRAINT unique_google_url 
UNIQUE (google_business_url);

-- Ensure clinic owners exist
ALTER TABLE clinics ADD CONSTRAINT fk_clinic_owner 
FOREIGN KEY (owner_user_id) REFERENCES users(id);

-- Ensure reviews link to valid clinics
ALTER TABLE google_reviews ADD CONSTRAINT fk_review_clinic 
FOREIGN KEY (clinic_id) REFERENCES clinics(id);
```

### Step 6: Verification Process

#### Data Integrity Checks
1. **Clinic Profile Completeness**
   ```sql
   SELECT name, address, contact_number, rating 
   FROM clinics 
   WHERE google_business_url IS NOT NULL;
   ```

2. **Review Association Verification**
   ```sql
   SELECT c.name, COUNT(gr.id) as review_count
   FROM clinics c
   LEFT JOIN google_reviews gr ON c.id = gr.clinic_id
   GROUP BY c.id, c.name;
   ```

3. **Owner Assignment Check**
   ```sql
   SELECT c.name, u.email, u.role
   FROM clinics c
   JOIN users u ON c.owner_user_id = u.id
   WHERE u.role = 'clinic_owner';
   ```

### Step 7: Dashboard Access Setup

#### Required Components
1. **User Authentication**: Clinic owner must be logged in
2. **Role Verification**: User role must be `'clinic_owner'`
3. **Clinic Association**: User must be linked to clinic via `owner_user_id`
4. **CSRF Protection**: All forms must include CSRF tokens

#### Access Flow
```
User Login → Role Check → Clinic Lookup → Dashboard Access
```

### Step 8: Troubleshooting Guide

#### Error Scenarios

1. **"No clinic profile found"**
   - Check `owner_user_id` is set correctly
   - Verify user role is `'clinic_owner'`
   - Confirm clinic record exists

2. **"CSRF token missing"**
   - Add `{{ csrf_token() }}` to form templates
   - Include hidden CSRF input in all forms

3. **"Access denied"**
   - Update user role: `UPDATE users SET role = 'clinic_owner' WHERE email = ?`
   - Verify clinic ownership assignment

4. **Review display issues**
   - Check `google_reviews` table has data
   - Verify `clinic_id` foreign key relationships
   - Confirm review template includes Google reviews section

### Step 9: Future Enhancements

#### Planned Features
- Bulk clinic import from CSV
- Automated review synchronization
- Multi-location clinic support
- Enhanced image gallery management

#### Scalability Considerations
- Implement rate limiting for Google scraping
- Add caching for frequently accessed clinic data
- Consider API integration for real-time updates

## Example Implementation

### Complete Import Process
```python
# 1. Extract clinic data
clinic_data = extract_google_business_data(google_url)

# 2. Store clinic record
clinic_id = create_clinic_record(clinic_data)

# 3. Extract and store reviews
reviews = extract_google_reviews(google_url)
store_reviews(clinic_id, reviews)

# 4. Create owner account
user_id = create_clinic_owner(email, clinic_data['name'])

# 5. Assign ownership
assign_clinic_ownership(clinic_id, user_id)

# 6. Verify setup
verify_clinic_setup(clinic_id, user_id)
```

This process ensures authentic data integration while maintaining database integrity and providing secure clinic management capabilities.