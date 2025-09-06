# Lead Submission Flow for Antidote India Launch

This document provides instructions for setting up and testing the lead submission flow for Antidote's India launch.

## Features

- Guest users can submit consultation requests via popup forms
- Forms are available on both procedure and doctor detail pages
- DPDP Act 2023 compliant consent checkbox
- Email notifications to doctors
- Confirmation page with account creation prompts
- Mock authentication for testing purposes

## Setup Instructions

### 1. Environment Variables

Copy the `.env.example` file to create a `.env` file:

```bash
cp .env.example .env
```

Then edit the `.env` file to add your email credentials:

```
# Mail configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-actual-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@antidote.com
```

### 2. Using Gmail for Sending Emails

If you're using Gmail, you need to create an App Password:

1. Go to your Google Account.
2. Select Security.
3. Under "Signing in to Google," select 2-Step Verification.
4. At the bottom of the page, select App passwords.
5. Enter a name for the app password (e.g., "Antidote Flask App").
6. Click "Create".
7. Copy the 16-character password.
8. Paste this password in your `.env` file as `MAIL_PASSWORD`.

### 3. Testing the Flow

1. Start the application:
   ```
   flask run
   ```

2. Visit `/mock_login` to simulate being logged in (sets `session['user_id'] = 1`).
3. Navigate to a procedure or doctor detail page.
4. Click "Book Consultation" button.
5. Fill out the form (including checking the DPDP Act consent checkbox).
6. Submit the form.
7. Verify that:
   - The lead is saved in the database
   - An email notification is sent to the doctor (if a doctor was selected)
   - You are redirected to the confirmation page

## Data Model

The Lead model has been updated with India-specific fields:

- `patient_name`: Full name of the patient
- `mobile_number`: 10-digit mobile number
- `city`: Patient's city
- `procedure_name`: Selected procedure
- `preferred_date`: Preferred consultation date
- `consent_given`: DPDP Act consent checkbox status
- `doctor_id`: ID of the selected doctor (if applicable)
- `message`: Optional additional information

## Troubleshooting

If emails are not sending:

1. Check that your SMTP settings are correct in `.env`.
2. For Gmail, ensure you're using an App Password, not your regular password.
3. Verify that the doctor has a valid email in the database.
4. Check the application logs for any errors related to email sending.

## Security Considerations

- Real authentication should be implemented for production.
- Form validation could be enhanced for production.
- Consider encrypting sensitive patient data in production.