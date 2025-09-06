# Google Places API Setup Guide

## Quick Setup (Recommended)

### Step 1: Create New Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it "Antidote Clinics" or similar
4. Click "Create"

### Step 2: Enable Required APIs
1. Go to [APIs & Services](https://console.cloud.google.com/apis/dashboard)
2. Click "Enable APIs and Services"
3. Search and enable these APIs:
   - **Places API (New)** - Essential for clinic imports
   - **Places API** - Legacy fallback
   - **Maps JavaScript API** - For map display

### Step 3: Create API Key
1. Go to [Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" → "API Key"
3. Copy the API key
4. Click "Restrict Key"
5. Under "API restrictions" select "Restrict key"
6. Choose the APIs you enabled above
7. Save

### Step 4: Set up Billing
1. Go to [Billing](https://console.cloud.google.com/billing)
2. Link a billing account (required for Places API)
3. Google provides $200 free credits monthly

### Step 5: Test the API Key
Provide the new API key to the system and we'll test it immediately.

## Expected Costs for 400+ Clinics
- Places API (New): ~$17-34 per 1000 requests
- For 400 clinics: ~$7-14 total
- Well within free tier limits

## Current Issue
Your current API key is from project 219853954654 where you don't have permissions to enable new APIs. Creating your own project gives you full control.