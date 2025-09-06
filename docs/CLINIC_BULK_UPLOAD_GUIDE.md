# Clinic Bulk Upload Guide

## Overview
This guide explains how to bulk upload clinic data to the Antidote platform using CSV files. The system can create both user accounts and clinic profiles automatically.

## Available Fields for Clinic Profiles

### Required Fields
- `clinic_name` - Name of the clinic
- `contact_person` - Primary contact person name
- `email` - Clinic email address (used for login)
- `phone` - Primary contact number
- `address` - Full clinic address
- `city` - City name
- `state` - State name

### Optional Fields
- `pincode` - Postal/PIN code
- `website` - Clinic website URL
- `specialties` - Comma-separated list of specialties
- `description` - Clinic description
- `password` - Login password (defaults to "clinic123" if not provided)

### Additional Profile Fields (can be updated later via dashboard)
- `profile_image` - Clinic logo/image
- `banner_image` - Top banner image
- `working_hours` - Operating hours
- `highlights` - Key features array
- `services_offered` - Detailed services list
- `whatsapp_number` - WhatsApp contact
- `google_business_url` - Google Business profile
- `area` - Local area (e.g., Bandra, Koramangala)

## CSV Upload Methods

### Method 1: Direct Bulk Upload Script (Recommended)
Creates clinics directly with user accounts.

**Usage:**
```bash
python bulk_clinic_upload.py clinics.csv
```

**Create Sample CSV:**
```bash
python bulk_clinic_upload.py --create-sample
```

### Method 2: Admin Panel Upload (Existing Feature)
1. Access admin panel at `/admin/clinic-applications`
2. Upload CSV file via bulk import
3. Review and approve applications manually
4. System creates clinic accounts upon approval

## CSV Format Requirements

### Sample CSV Structure:
```csv
clinic_name,contact_person,email,phone,address,city,state,pincode,website,specialties,description,password
Elite Cosmetic Center,Dr. Priya Sharma,info@elitecosmetic.com,+919876543210,123 MG Road,Bangalore,Karnataka,560001,https://elitecosmetic.com,"Rhinoplasty, Breast Augmentation, Liposuction",Premier cosmetic surgery clinic,secure123
Mumbai Aesthetic Clinic,Dr. Rajesh Khanna,contact@mumbaiaesthetic.com,+919876543211,456 Linking Road,Mumbai,Maharashtra,400050,https://mumbaiaesthetic.com,"Botox, Fillers, Laser Treatment",Modern aesthetic treatments,clinic456
```

### Data Validation Rules
- Email addresses must be unique
- Phone numbers should include country code
- Specialties should be comma-separated
- All required fields must have values
- Duplicate emails will be skipped with warnings

## Features of Bulk Upload System

### Automatic Account Creation
- Creates user accounts for clinic owners
- Generates secure password hashes
- Assigns 'clinic' role to users
- Links clinics to user accounts

### Smart Data Processing
- Generates unique URL slugs for clinics
- Parses specialty lists automatically
- Validates email format and uniqueness
- Handles missing optional fields gracefully

### Error Handling
- Comprehensive validation and error reporting
- Continues processing despite individual failures
- Detailed summary of success/failure counts
- Rollback capability for database consistency

### Auto-Approval
- Bulk uploaded clinics are auto-approved
- Starting credit balance of 100 credits
- Verification status set to 'approved'
- Ready for immediate use

## Post-Upload Clinic Management

### Dashboard Access
Clinics can access their dashboard at:
- URL: `/clinic/dashboard`
- Login: Use email and password from CSV

### Profile Completion
After upload, clinics should complete:
1. Upload profile and banner images
2. Set detailed working hours
3. Add service highlights
4. Configure Google Business integration
5. Set up payment methods for credits

### Additional Features Available
- Lead management and notifications
- Credit billing system integration
- Package creation and management
- Google Reviews synchronization
- Analytics and performance tracking

## Troubleshooting

### Common Issues
1. **Duplicate Email Error**: Check CSV for duplicate email addresses
2. **Missing Required Fields**: Ensure all required columns have values
3. **Invalid Phone Format**: Use international format (+91XXXXXXXXXX)
4. **Database Connection**: Verify DATABASE_URL environment variable

### Error Messages
The system provides detailed error reporting including:
- Row numbers with issues
- Specific validation failures
- Success/failure summary
- Rollback information if needed

## Security Considerations

### Default Passwords
- Change default passwords immediately after upload
- Use strong, unique passwords for each clinic
- Consider implementing password reset functionality

### Data Privacy
- CSV files contain sensitive information
- Delete CSV files after successful upload
- Ensure secure transmission of CSV files
- Validate data before upload

## Integration with Existing Systems

### Credit Billing
- New clinics start with 100 credits
- Integrated with lead generation billing
- Automatic credit deduction for leads
- Credit purchase workflow available

### Lead Management
- Automatic lead routing to clinics
- Email notifications for new leads
- Dispute resolution system available
- Analytics and conversion tracking

### Google Integration
- Optional Google Business profile linking
- Automatic review synchronization
- Enhanced local SEO capabilities
- Real-time rating updates