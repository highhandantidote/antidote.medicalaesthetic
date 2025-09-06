-- Enhanced Lead Generation Schema Updates
-- Add new columns to leads table for Firebase OTP verification and enhanced tracking

-- Add new columns to leads table
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS source_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS source_id INTEGER,
ADD COLUMN IF NOT EXISTS contact_intent VARCHAR(20) DEFAULT 'inquiry',
ADD COLUMN IF NOT EXISTS lead_cost INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS payment_status VARCHAR(30) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS firebase_uid VARCHAR(255),
ADD COLUMN IF NOT EXISTS verification_timestamp TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_contacted TIMESTAMP;

-- Add comments for new columns
COMMENT ON COLUMN leads.source_type IS 'Type of source: package or clinic';
COMMENT ON COLUMN leads.source_id IS 'ID of the package or clinic that generated this lead';
COMMENT ON COLUMN leads.contact_intent IS 'User intent: whatsapp, call, or inquiry';
COMMENT ON COLUMN leads.lead_cost IS 'Cost charged to clinic for this lead';
COMMENT ON COLUMN leads.payment_status IS 'Payment status: paid, insufficient_credits, pending';
COMMENT ON COLUMN leads.is_verified IS 'Whether phone number was verified via OTP';
COMMENT ON COLUMN leads.firebase_uid IS 'Firebase authentication UID for verification';
COMMENT ON COLUMN leads.verification_timestamp IS 'When phone verification was completed';
COMMENT ON COLUMN leads.last_contacted IS 'Last time clinic contacted this lead';

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_leads_source_type_id ON leads(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_leads_is_verified ON leads(is_verified);
CREATE INDEX IF NOT EXISTS idx_leads_payment_status ON leads(payment_status);
CREATE INDEX IF NOT EXISTS idx_leads_created_date ON leads(DATE(created_at));
CREATE INDEX IF NOT EXISTS idx_leads_clinic_verified ON leads(clinic_id, is_verified);

-- Add constraints
ALTER TABLE leads 
ADD CONSTRAINT chk_source_type CHECK (source_type IN ('package', 'clinic')),
ADD CONSTRAINT chk_contact_intent CHECK (contact_intent IN ('whatsapp', 'call', 'inquiry')),
ADD CONSTRAINT chk_payment_status CHECK (payment_status IN ('paid', 'insufficient_credits', 'pending', 'refunded'));

-- Update existing leads to have default values
UPDATE leads 
SET source_type = 'clinic', 
    contact_intent = 'inquiry',
    is_verified = FALSE,
    payment_status = 'pending',
    lead_cost = 75
WHERE source_type IS NULL;

-- Create a view for verified leads statistics
CREATE OR REPLACE VIEW verified_leads_stats AS
SELECT 
    DATE(created_at) as lead_date,
    source_type,
    contact_intent,
    COUNT(*) as total_leads,
    COUNT(CASE WHEN is_verified = TRUE THEN 1 END) as verified_leads,
    COUNT(CASE WHEN payment_status = 'paid' THEN 1 END) as paid_leads,
    SUM(CASE WHEN payment_status = 'paid' THEN lead_cost ELSE 0 END) as revenue_generated,
    AVG(lead_cost) as avg_lead_cost
FROM leads 
GROUP BY DATE(created_at), source_type, contact_intent
ORDER BY lead_date DESC;

-- Create a function to calculate lead conversion rates
CREATE OR REPLACE FUNCTION get_lead_conversion_rate(clinic_id_param INTEGER, days_back INTEGER DEFAULT 30)
RETURNS TABLE(
    total_leads BIGINT,
    verified_leads BIGINT,
    conversion_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_leads,
        COUNT(CASE WHEN is_verified = TRUE THEN 1 END) as verified_leads,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                ROUND((COUNT(CASE WHEN is_verified = TRUE THEN 1 END) * 100.0 / COUNT(*)), 2)
            ELSE 0
        END as conversion_rate
    FROM leads 
    WHERE clinic_id = clinic_id_param 
    AND created_at >= CURRENT_DATE - INTERVAL '%s days' LIMIT 1;
END;
$$ LANGUAGE plpgsql;