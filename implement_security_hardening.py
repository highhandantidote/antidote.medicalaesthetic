#!/usr/bin/env python3
"""
Database Security Hardening Implementation for Antidote Platform

This script implements advanced security measures beyond basic RLS policies.
Focuses on real-world security hardening for production environments.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """Get database connection using environment variables."""
    try:
        conn = psycopg2.connect(
            host=os.environ.get('PGHOST', 'localhost'),
            database=os.environ.get('PGDATABASE', 'postgres'),
            user=os.environ.get('PGUSER', 'postgres'),
            password=os.environ.get('PGPASSWORD', ''),
            port=os.environ.get('PGPORT', '5432')
        )
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None

def create_data_validation_constraints():
    """Add data validation constraints to critical tables."""
    constraints = [
        # User data validation
        "ALTER TABLE public.users ADD CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$');",
        "ALTER TABLE public.users ADD CONSTRAINT valid_phone CHECK (phone_number IS NULL OR phone_number ~ '^[+]?[0-9\\s\\-\\(\\)]{10,20}$');",
        
        # Doctor data validation
        "ALTER TABLE public.doctors ADD CONSTRAINT valid_years_experience CHECK (years_of_experience >= 0 AND years_of_experience <= 70);",
        "ALTER TABLE public.doctors ADD CONSTRAINT valid_rating CHECK (rating >= 0 AND rating <= 5);",
        
        # Procedure pricing validation
        "ALTER TABLE public.procedures ADD CONSTRAINT valid_min_cost CHECK (min_cost > 0);",
        "ALTER TABLE public.procedures ADD CONSTRAINT valid_max_cost CHECK (max_cost > min_cost);",
        "ALTER TABLE public.procedures ADD CONSTRAINT reasonable_cost_range CHECK (max_cost <= min_cost * 10);",
        
        # Review validation
        "ALTER TABLE public.reviews ADD CONSTRAINT valid_review_rating CHECK (rating >= 1 AND rating <= 5);",
        "ALTER TABLE public.reviews ADD CONSTRAINT review_content_length CHECK (char_length(trim(review_text)) >= 10);",
        
        # Appointment validation
        "ALTER TABLE public.appointments ADD CONSTRAINT future_appointment CHECK (appointment_date > CURRENT_DATE);",
        
        # Lead validation
        "ALTER TABLE public.leads ADD CONSTRAINT valid_lead_budget CHECK (budget > 0);",
        
        # Billing validation
        "ALTER TABLE public.clinic_billing ADD CONSTRAINT valid_amount CHECK (amount > 0);",
        "ALTER TABLE public.credit_transactions ADD CONSTRAINT valid_credit_amount CHECK (amount != 0);"
    ]
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        for constraint_sql in constraints:
            try:
                cur.execute(constraint_sql)
                logging.info(f"Applied constraint: {constraint_sql[:50]}...")
            except psycopg2.Error as e:
                if "already exists" in str(e) or "duplicate key" in str(e):
                    logging.info(f"Constraint already exists, skipping")
                else:
                    logging.warning(f"Failed to apply constraint: {e}")
        
        conn.commit()
        logging.info("Data validation constraints applied successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error applying constraints: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_security_indexes():
    """Create indexes for security and performance optimization."""
    security_indexes = [
        # Security monitoring indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login ON public.users(last_login_at) WHERE last_login_at IS NOT NULL;",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON public.users(created_at);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_failed_logins ON public.security_audit_log(timestamp, action) WHERE action LIKE '%LOGIN_FAILED%';",
        
        # Performance and security for sensitive operations
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_user_date ON public.appointments(user_id, appointment_date);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_created_at ON public.leads(created_at);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clinic_billing_date ON public.clinic_billing(created_at);",
        
        # Email and phone lookup optimization
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower ON public.users(LOWER(email));",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_phone ON public.users(phone_number) WHERE phone_number IS NOT NULL;",
        
        # Audit trail optimization
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_user_action ON public.security_audit_log(user_id, action, timestamp);",
        
        # Rate limiting support
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_otp_verifications_recent ON public.otp_verifications(phone_number, created_at) WHERE created_at > NOW() - INTERVAL '1 hour';"
    ]
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        for index_sql in security_indexes:
            try:
                cur.execute(index_sql)
                logging.info(f"Created index: {index_sql[:60]}...")
            except psycopg2.Error as e:
                if "already exists" in str(e):
                    logging.info("Index already exists, skipping")
                else:
                    logging.warning(f"Failed to create index: {e}")
        
        conn.commit()
        logging.info("Security indexes created successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error creating indexes: {e}")
        return False
    finally:
        conn.close()

def implement_rate_limiting_tables():
    """Create tables for rate limiting and abuse prevention."""
    rate_limiting_tables = [
        """
        CREATE TABLE IF NOT EXISTS public.rate_limits (
            id SERIAL PRIMARY KEY,
            identifier VARCHAR(100) NOT NULL, -- IP address, user_id, email, etc.
            action VARCHAR(50) NOT NULL,       -- login_attempt, otp_request, etc.
            attempt_count INTEGER DEFAULT 1,
            window_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            blocked_until TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(identifier, action)
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS public.suspicious_activities (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            ip_address INET,
            user_agent TEXT,
            activity_type VARCHAR(100) NOT NULL,
            details JSONB,
            risk_score INTEGER DEFAULT 1, -- 1-10 scale
            is_blocked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS public.ip_blacklist (
            id SERIAL PRIMARY KEY,
            ip_address INET NOT NULL UNIQUE,
            reason TEXT,
            blocked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            blocked_until TIMESTAMP WITH TIME ZONE,
            is_permanent BOOLEAN DEFAULT FALSE
        );
        """
    ]
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        for table_sql in rate_limiting_tables:
            cur.execute(table_sql)
            logging.info("Created rate limiting table")
        
        # Enable RLS on new security tables
        security_rls_commands = [
            "ALTER TABLE public.rate_limits ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE public.suspicious_activities ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE public.ip_blacklist ENABLE ROW LEVEL SECURITY;",
            
            # Create restrictive policies
            "CREATE POLICY 'Rate limits - admin only' ON public.rate_limits FOR ALL USING (false);",
            "CREATE POLICY 'Suspicious activities - admin only' ON public.suspicious_activities FOR ALL USING (false);",
            "CREATE POLICY 'IP blacklist - admin only' ON public.ip_blacklist FOR ALL USING (false);"
        ]
        
        for rls_sql in security_rls_commands:
            try:
                cur.execute(rls_sql)
            except psycopg2.Error as e:
                if "already exists" in str(e):
                    continue
                else:
                    logging.warning(f"RLS command failed: {e}")
        
        conn.commit()
        logging.info("Rate limiting and security tables created successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error creating security tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_security_functions():
    """Create utility functions for security operations."""
    security_functions = [
        """
        CREATE OR REPLACE FUNCTION is_suspicious_login(
            p_user_id INTEGER,
            p_ip_address INET,
            p_user_agent TEXT
        ) RETURNS BOOLEAN AS $$
        DECLARE
            recent_logins INTEGER;
            different_ips INTEGER;
            is_suspicious BOOLEAN DEFAULT FALSE;
        BEGIN
            -- Check for multiple login attempts from different IPs
            SELECT COUNT(DISTINCT ip_address) INTO different_ips
            FROM public.security_audit_log 
            WHERE user_id = p_user_id 
                AND action = 'LOGIN_SUCCESS'
                AND timestamp > NOW() - INTERVAL '1 hour';
            
            -- Check for rapid login attempts
            SELECT COUNT(*) INTO recent_logins
            FROM public.security_audit_log 
            WHERE user_id = p_user_id 
                AND action LIKE '%LOGIN%'
                AND timestamp > NOW() - INTERVAL '10 minutes';
            
            -- Flag as suspicious if multiple IPs or rapid attempts
            IF different_ips > 3 OR recent_logins > 10 THEN
                is_suspicious := TRUE;
                
                -- Log suspicious activity
                INSERT INTO public.suspicious_activities (
                    user_id, ip_address, user_agent, activity_type, 
                    details, risk_score
                ) VALUES (
                    p_user_id, p_ip_address, p_user_agent, 'SUSPICIOUS_LOGIN',
                    jsonb_build_object(
                        'different_ips', different_ips,
                        'recent_attempts', recent_logins
                    ),
                    CASE WHEN different_ips > 5 OR recent_logins > 20 THEN 9 ELSE 6 END
                );
            END IF;
            
            RETURN is_suspicious;
        END;
        $$ LANGUAGE plpgsql;
        """,
        
        """
        CREATE OR REPLACE FUNCTION cleanup_old_audit_logs() RETURNS VOID AS $$
        BEGIN
            -- Keep only last 6 months of audit logs for performance
            DELETE FROM public.security_audit_log 
            WHERE timestamp < NOW() - INTERVAL '6 months';
            
            -- Keep only last 3 months of rate limiting data
            DELETE FROM public.rate_limits 
            WHERE created_at < NOW() - INTERVAL '3 months';
            
            -- Clean up old OTP verifications (keep only last 24 hours)
            DELETE FROM public.otp_verifications 
            WHERE created_at < NOW() - INTERVAL '24 hours';
        END;
        $$ LANGUAGE plpgsql;
        """,
        
        """
        CREATE OR REPLACE FUNCTION validate_user_permissions(
            p_user_id INTEGER,
            p_action VARCHAR(100),
            p_resource_type VARCHAR(100),
            p_resource_id INTEGER DEFAULT NULL
        ) RETURNS BOOLEAN AS $$
        DECLARE
            user_role VARCHAR(50);
            is_authorized BOOLEAN DEFAULT FALSE;
        BEGIN
            -- Get user role
            SELECT role INTO user_role FROM public.users WHERE id = p_user_id;
            
            -- Basic role-based authorization
            CASE 
                WHEN user_role = 'admin' THEN
                    is_authorized := TRUE;
                WHEN user_role = 'doctor' AND p_resource_type IN ('appointments', 'reviews', 'professional_responses') THEN
                    is_authorized := TRUE;
                WHEN user_role = 'clinic_owner' AND p_resource_type IN ('clinic_leads', 'clinic_billing', 'clinic_packages') THEN
                    is_authorized := TRUE;
                WHEN user_role = 'user' AND p_resource_type IN ('appointments', 'reviews', 'favorites') THEN
                    is_authorized := TRUE;
                ELSE
                    is_authorized := FALSE;
            END CASE;
            
            -- Log authorization attempt
            PERFORM log_security_event(
                p_user_id, 
                'AUTHORIZATION_CHECK',
                p_resource_type,
                p_resource_id,
                NULL,
                NULL,
                jsonb_build_object(
                    'action', p_action,
                    'authorized', is_authorized,
                    'user_role', user_role
                )
            );
            
            RETURN is_authorized;
        END;
        $$ LANGUAGE plpgsql;
        """
    ]
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        for func_sql in security_functions:
            cur.execute(func_sql)
            logging.info("Created security function")
        
        conn.commit()
        logging.info("Security functions created successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error creating security functions: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def implement_data_masking_views():
    """Create views with data masking for sensitive information."""
    masking_views = [
        """
        CREATE OR REPLACE VIEW public.users_public AS 
        SELECT 
            id,
            username,
            CASE 
                WHEN email IS NOT NULL THEN 
                    CONCAT(LEFT(email, 2), '****@', SPLIT_PART(email, '@', 2))
                ELSE NULL 
            END as email_masked,
            first_name,
            last_name,
            role,
            is_verified,
            created_at,
            last_login_at
        FROM public.users;
        """,
        
        """
        CREATE OR REPLACE VIEW public.doctors_public AS
        SELECT 
            id,
            name,
            specialization,
            years_of_experience,
            rating,
            location,
            about,
            profile_image_url,
            is_verified,
            CASE 
                WHEN phone_number IS NOT NULL THEN 
                    CONCAT('****', RIGHT(phone_number, 4))
                ELSE NULL 
            END as phone_masked
        FROM public.doctors;
        """,
        
        """
        CREATE OR REPLACE VIEW public.clinic_analytics AS
        SELECT 
            c.id,
            c.name,
            c.location,
            COUNT(cl.id) as total_leads,
            COUNT(CASE WHEN cl.status = 'converted' THEN 1 END) as converted_leads,
            AVG(cr.rating) as average_rating,
            COUNT(cr.id) as total_reviews
        FROM public.clinics c
        LEFT JOIN public.clinic_leads cl ON c.id = cl.clinic_id
        LEFT JOIN public.clinic_reviews cr ON c.id = cr.clinic_id
        GROUP BY c.id, c.name, c.location;
        """
    ]
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        for view_sql in masking_views:
            cur.execute(view_sql)
            logging.info("Created data masking view")
        
        conn.commit()
        logging.info("Data masking views created successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error creating masking views: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function to execute all security hardening measures."""
    logging.info("Starting database security hardening process...")
    
    security_measures = [
        ("Data Validation Constraints", create_data_validation_constraints),
        ("Security Indexes", create_security_indexes),
        ("Rate Limiting Tables", implement_rate_limiting_tables),
        ("Security Functions", create_security_functions),
        ("Data Masking Views", implement_data_masking_views)
    ]
    
    results = {}
    for measure_name, measure_func in security_measures:
        logging.info(f"Implementing {measure_name}...")
        try:
            success = measure_func()
            results[measure_name] = "SUCCESS" if success else "FAILED"
            logging.info(f"{measure_name}: {'SUCCESS' if success else 'FAILED'}")
        except Exception as e:
            results[measure_name] = f"ERROR: {str(e)}"
            logging.error(f"{measure_name} failed with error: {e}")
    
    # Print summary
    logging.info("\n" + "="*50)
    logging.info("SECURITY HARDENING SUMMARY")
    logging.info("="*50)
    for measure, status in results.items():
        logging.info(f"{measure}: {status}")
    
    # Count successes
    successes = sum(1 for status in results.values() if status == "SUCCESS")
    total = len(results)
    
    logging.info(f"\nCompleted {successes}/{total} security measures successfully")
    
    if successes == total:
        logging.info("✅ All security hardening measures implemented successfully!")
    else:
        logging.warning(f"⚠️  {total - successes} security measures need attention")

if __name__ == "__main__":
    main()