-- Advanced Database Security Enhancements for Antidote Platform
-- Run these commands to implement additional security layers

-- 1. Create database roles with specific permissions
CREATE ROLE antidote_readonly;
CREATE ROLE antidote_app_user;
CREATE ROLE antidote_admin;

-- 2. Grant appropriate permissions to roles
-- Read-only role for reporting/analytics
GRANT CONNECT ON DATABASE postgres TO antidote_readonly;
GRANT USAGE ON SCHEMA public TO antidote_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO antidote_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO antidote_readonly;

-- Application user role with controlled access
GRANT CONNECT ON DATABASE postgres TO antidote_app_user;
GRANT USAGE ON SCHEMA public TO antidote_app_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO antidote_app_user;
GRANT DELETE ON public.otp_verifications TO antidote_app_user;
GRANT DELETE ON public.notifications TO antidote_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO antidote_app_user;

-- Admin role with full access
GRANT ALL PRIVILEGES ON DATABASE postgres TO antidote_admin;
GRANT ALL ON SCHEMA public TO antidote_admin;
GRANT ALL ON ALL TABLES IN SCHEMA public TO antidote_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO antidote_admin;

-- 3. Enable additional security features
-- Enable SSL connections only (uncomment when SSL is configured)
-- ALTER SYSTEM SET ssl = on;
-- ALTER SYSTEM SET ssl_cert_file = '/path/to/certificate.crt';
-- ALTER SYSTEM SET ssl_key_file = '/path/to/private.key';

-- 4. Configure connection limits
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';

-- 5. Enable query logging for security monitoring
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_checkpoints = on;

-- 6. Create audit table for sensitive operations
CREATE TABLE IF NOT EXISTS public.security_audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    severity VARCHAR(20) DEFAULT 'INFO'
);

-- Enable RLS on audit table
ALTER TABLE public.security_audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Audit log - admin only" ON public.security_audit_log FOR ALL USING (false);

-- 7. Create indexes for performance and security
CREATE INDEX IF NOT EXISTS idx_security_audit_timestamp ON public.security_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_audit_user_id ON public.security_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_security_audit_action ON public.security_audit_log(action);

-- 8. Data encryption at rest (add encryption for sensitive fields)
-- Note: This requires application-level implementation
-- Consider encrypting: phone numbers, email addresses, personal data

-- 9. Create function to log security events
CREATE OR REPLACE FUNCTION log_security_event(
    p_user_id INTEGER,
    p_action VARCHAR(100),
    p_table_name VARCHAR(100) DEFAULT NULL,
    p_record_id INTEGER DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_details JSONB DEFAULT NULL,
    p_severity VARCHAR(20) DEFAULT 'INFO'
) RETURNS VOID AS $$
BEGIN
    INSERT INTO public.security_audit_log (
        user_id, action, table_name, record_id, 
        ip_address, user_agent, details, severity
    ) VALUES (
        p_user_id, p_action, p_table_name, p_record_id,
        p_ip_address, p_user_agent, p_details, p_severity
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 10. Create triggers for sensitive table monitoring
CREATE OR REPLACE FUNCTION audit_sensitive_changes() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM log_security_event(
            OLD.user_id,
            TG_OP || '_' || TG_TABLE_NAME,
            TG_TABLE_NAME,
            OLD.id,
            NULL,
            NULL,
            row_to_json(OLD)::jsonb,
            'WARNING'
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        PERFORM log_security_event(
            NEW.user_id,
            TG_OP || '_' || TG_TABLE_NAME,
            TG_TABLE_NAME,
            NEW.id,
            NULL,
            NULL,
            jsonb_build_object('old', row_to_json(OLD), 'new', row_to_json(NEW)),
            'INFO'
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        PERFORM log_security_event(
            NEW.user_id,
            TG_OP || '_' || TG_TABLE_NAME,
            TG_TABLE_NAME,
            NEW.id,
            NULL,
            NULL,
            row_to_json(NEW)::jsonb,
            'INFO'
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to sensitive tables
DROP TRIGGER IF EXISTS audit_users_changes ON public.users;
CREATE TRIGGER audit_users_changes
    AFTER INSERT OR UPDATE OR DELETE ON public.users
    FOR EACH ROW EXECUTE FUNCTION audit_sensitive_changes();

DROP TRIGGER IF EXISTS audit_clinic_billing_changes ON public.clinic_billing;
CREATE TRIGGER audit_clinic_billing_changes
    AFTER INSERT OR UPDATE OR DELETE ON public.clinic_billing
    FOR EACH ROW EXECUTE FUNCTION audit_sensitive_changes();

DROP TRIGGER IF EXISTS audit_leads_changes ON public.leads;
CREATE TRIGGER audit_leads_changes
    AFTER INSERT OR UPDATE OR DELETE ON public.leads
    FOR EACH ROW EXECUTE FUNCTION audit_sensitive_changes();