# Antidote - Medical Aesthetic Marketplace Platform

## Overview
Antidote is a comprehensive medical aesthetic marketplace platform connecting patients with aesthetic clinics and doctors. It features a credit-based billing system, lead generation, and clinic management capabilities, adopting a Korean-style marketplace approach with premium features for all users. The platform aims to be a leading resource for medical aesthetic procedures, focusing on a robust business vision, market potential, and ambitious growth targets.

## User Preferences
Preferred communication style: Simple, everyday language.
Design preferences: Prefers original doctor card design over modern compact cards.
Navigation preferences: Clean navigation menu with 13px font size, no blinking or animation effects.
Performance priorities: Fast page loads and navigation menu response times are critical for user experience.
Production Focus: antidote.fit domain requires specialized optimization vs development environment.

## Recent Changes - 2025-08-27

### Treatment Package Data Standards Update
- **Issue**: Duration and downtime information was generic across all treatment packages (all showing "30-60 minutes" and "minimal downtime")
- **Solution Applied**: 
  - Updated treatment packages with accurate, procedure-specific duration and downtime information
  - Established medical accuracy standards for all future packages
- **Examples of Updated Data**:
  - Botox treatments: 10-20 minutes, no downtime
  - Lip fillers: 20-30 minutes, 2-4 days swelling
  - Thread lifts: 60-90 minutes, 5-7 days recovery
  - Scar removal: 45-90 minutes, 3-7 days per session
- **Standard for Future Packages**: All new treatment packages must include realistic, treatment-specific duration and downtime based on actual medical procedures

## Recent Changes - 2025-08-26

### Firebase OTP Authentication Fix
- **Issue**: Firebase OTP verification failing with "auth/internal-error" preventing WhatsApp contact requests
- **Root Cause**: Malformed Content Security Policy headers blocking Firebase authentication services
- **Solution Applied**: 
  - Removed conflicting CSP headers from HTML templates (base_optimized_complete.html, base_optimized.html, base_phase2_optimized.html)
  - Fixed database SSL configuration (changed from 'allow' to 'require' for Supabase)
  - Temporarily disabled problematic CSP to allow Firebase communication
- **Result**: ✅ Firebase OTP now working - users can successfully verify phone numbers for WhatsApp contact requests

## Recent Changes - 2025-08-20

### Production Performance Crisis Resolution
- **Issue**: antidote.fit experiencing 5+ second page load times (20-50x slower than development)
- **Root Causes Identified**:
  - Database connection pool too small (5 connections vs 50+ needed)
  - Insufficient caching for production workload  
  - Multiple conflicting performance optimization modules
  - Suboptimal Gunicorn configuration for production traffic

### Emergency Fixes Applied
- **Database Optimization**: Increased pool_size to 50, max_overflow to 100
- **Connection Management**: Optimized timeouts and pre-ping settings
- **Caching Strategy**: Implemented aggressive caching with 5-minute TTL
- **Server Configuration**: Updated Gunicorn to 6 workers with 4 threads each
- **Performance Monitoring**: Added comprehensive health endpoints and request tracking

### Performance Results
- **Homepage**: Improved from 5+ seconds to ~1-2 seconds (still optimizing)
- **Database Queries**: Reduced server response time from 988ms to ~250ms
- **Cache Implementation**: Active with 5-minute TTL for frequently accessed data

### Monitoring Endpoints Added
- `/final-production-status`: Check optimization status
- `/performance-test`: Quick health and performance check
- `/quick-warmup`: Pre-load critical data for faster responses

## System Architecture

### Backend
- **Framework**: Flask (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Session-based, multi-role (patients, clinics, doctors, admin)
- **Deployment**: Gunicorn WSGI server, autoscale deployment target
- **Security**: Row Level Security (RLS) across all tables, targeted Content Security Policy (CSP), robust security headers, CSRF token handling, and optimized database indexing.

### Frontend
- **Templates**: Jinja2
- **Styling**: Custom CSS with Antidote's teal theme (#00A0B0), responsive design
- **JavaScript**: Vanilla JS for interactivity

### Core Features
- **User Management**: Multi-role system with comprehensive profile management.
- **Clinic Application Workflow**: Streamlined application, admin review, and automatic account creation.
- **Credit-Based Billing**: Prepaid, 6-tier dynamic pricing, Razorpay integration, transaction history, and automatic lead deduction.
- **Lead Generation & Management**: Lead capture, dispute resolution, and quality control.
- **Procedure & Doctor Management**: Extensive procedure database (490+), doctor profiles, categorized procedures, and body part hierarchy.
- **Admin Dashboard**: Clinic application management, dispute resolution, user/content moderation, and analytics.
- **Computer Vision Integration**: Facial analysis using MediaPipe for geometric measurements (golden ratio, symmetry, proportions), integrated with Google Gemini AI for comprehensive insights, with intelligent image validation for frontal positioning.
- **SEO & PWA**: Dynamic XML sitemap, robots.txt, OpenSearch XML, canonical URLs, comprehensive meta tags, and Progressive Web App (PWA) functionality.
- **Performance Optimization**: Single-query database optimization, CSS render-blocking fixes, response caching, middleware conflict resolution, and comprehensive navigation loading system for improved user experience during page transitions.

### Design Decisions
- **UI/UX**: Clean, professional appearance with a consistent teal color scheme and responsive design.
- **User Flow**: Clear, intuitive paths for clinic onboarding, credit purchasing, and lead generation.
- **Data Integrity**: Focus on accurate medical information from authenticated sources. All treatment packages must include realistic, procedure-specific duration and downtime information based on actual medical practices.
- **Performance Strategy**: Single-query database optimization, response caching, critical CSS inlining, and middleware conflict resolution for sub-500ms navigation response times.
- **Smart Face Positioning System**: Intelligent positioning validation using MediaPipe for accurate geometric analysis, providing real-time feedback and intelligent capture control.

## External Dependencies
- **Payment Gateway**: Razorpay
- **Email Service**: SMTP
- **Database**: PostgreSQL (Supabase)
- **Computer Vision**: MediaPipe
- **AI**: Google Gemini Vision
- **Phone Verification**: Firebase OTP
- **Mapping/Geocoding**: OpenStreetMap with Nominatim