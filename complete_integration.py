"""
Complete integration of all new features into the main application.
This script adds missing database tables and integrates all new components.
"""
from flask import Flask
from models import db
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def create_missing_tables():
    """Create any missing tables required for the new features."""
    try:
        # Create refund_requests table for dispute resolution
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS refund_requests (
                id SERIAL PRIMARY KEY,
                clinic_id INTEGER REFERENCES clinics(id),
                lead_id INTEGER REFERENCES leads(id),
                refund_amount INTEGER NOT NULL,
                reason TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                processed_by INTEGER REFERENCES users(id),
                processed_at TIMESTAMP,
                admin_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Add missing fields to clinics table
        db.session.execute(text("""
            ALTER TABLE clinics 
            ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP,
            ADD COLUMN IF NOT EXISTS approved_by INTEGER REFERENCES users(id),
            ADD COLUMN IF NOT EXISTS rejection_reason TEXT,
            ADD COLUMN IF NOT EXISTS rejection_date TIMESTAMP,
            ADD COLUMN IF NOT EXISTS rejected_by INTEGER REFERENCES users(id),
            ADD COLUMN IF NOT EXISTS email VARCHAR(255),
            ADD COLUMN IF NOT EXISTS description TEXT;
        """))
        
        # Add missing fields to leads table for better tracking
        db.session.execute(text("""
            ALTER TABLE leads 
            ADD COLUMN IF NOT EXISTS procedure_id INTEGER REFERENCES procedures(id),
            ADD COLUMN IF NOT EXISTS doctor_id INTEGER REFERENCES doctors(id),
            ADD COLUMN IF NOT EXISTS contact_info TEXT,
            ADD COLUMN IF NOT EXISTS notes TEXT,
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'new';
        """))
        
        # Create email_logs table for tracking notifications
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id SERIAL PRIMARY KEY,
                recipient_email VARCHAR(255) NOT NULL,
                subject VARCHAR(500) NOT NULL,
                email_type VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'sent',
                error_message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                clinic_id INTEGER REFERENCES clinics(id),
                lead_id INTEGER REFERENCES leads(id)
            );
        """))
        
        # Create search_analytics table for tracking searches
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS search_analytics (
                id SERIAL PRIMARY KEY,
                search_query VARCHAR(500),
                search_type VARCHAR(50),
                results_count INTEGER,
                user_id INTEGER REFERENCES users(id),
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create seo_pages table for managing meta data
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS seo_pages (
                id SERIAL PRIMARY KEY,
                page_type VARCHAR(50) NOT NULL,
                entity_id INTEGER,
                title VARCHAR(500),
                description TEXT,
                keywords TEXT,
                canonical_url VARCHAR(500),
                schema_markup JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        db.session.commit()
        logger.info("Successfully created missing database tables")
        return True
        
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        db.session.rollback()
        return False

def integrate_billing_automation():
    """Add automated billing triggers to the database."""
    try:
        # Create function to automatically deduct credits when leads are created
        db.session.execute(text("""
            CREATE OR REPLACE FUNCTION deduct_credits_for_lead()
            RETURNS TRIGGER AS $$
            DECLARE
                credits_required INTEGER := 300; -- Default chat credits
                clinic_balance INTEGER;
            BEGIN
                -- Determine credits required based on action type
                IF NEW.action_type = 'call' THEN
                    credits_required := 500;
                ELSIF NEW.action_type = 'consultation' THEN
                    credits_required := 800;
                END IF;
                
                -- Check clinic credit balance
                SELECT COALESCE(
                    (SELECT SUM(amount) FROM credit_transactions 
                     WHERE clinic_id = NEW.clinic_id AND transaction_type = 'credit') -
                    (SELECT SUM(amount) FROM credit_transactions 
                     WHERE clinic_id = NEW.clinic_id AND transaction_type = 'deduction'), 
                    0
                ) INTO clinic_balance;
                
                -- Only create lead if clinic has sufficient credits
                IF clinic_balance >= credits_required THEN
                    -- Deduct credits
                    INSERT INTO credit_transactions (
                        clinic_id, amount, transaction_type, description, 
                        lead_id, created_at
                    ) VALUES (
                        NEW.clinic_id, credits_required, 'deduction',
                        'Lead generation - ' || NEW.action_type || ' request',
                        NEW.id, CURRENT_TIMESTAMP
                    );
                ELSE
                    -- Prevent lead creation if insufficient credits
                    RAISE EXCEPTION 'Insufficient credits. Required: %, Available: %', 
                        credits_required, clinic_balance;
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))
        
        # Create trigger for automatic credit deduction
        db.session.execute(text("""
            DROP TRIGGER IF EXISTS trigger_deduct_credits ON leads;
            CREATE TRIGGER trigger_deduct_credits
                AFTER INSERT ON leads
                FOR EACH ROW
                EXECUTE FUNCTION deduct_credits_for_lead();
        """))
        
        db.session.commit()
        logger.info("Successfully integrated billing automation")
        return True
        
    except Exception as e:
        logger.error(f"Error integrating billing automation: {e}")
        db.session.rollback()
        return False

def setup_email_notifications():
    """Set up email notification triggers."""
    try:
        # Create function to send email notifications for new leads
        db.session.execute(text("""
            CREATE OR REPLACE FUNCTION notify_clinic_new_lead()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Insert into a notification queue table that will be processed by background job
                INSERT INTO notification_queue (
                    type, clinic_id, lead_id, priority, created_at
                ) VALUES (
                    'lead_notification', NEW.clinic_id, NEW.id, 'high', CURRENT_TIMESTAMP
                );
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))
        
        # Create notification queue table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS notification_queue (
                id SERIAL PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                clinic_id INTEGER REFERENCES clinics(id),
                lead_id INTEGER REFERENCES leads(id),
                priority VARCHAR(20) DEFAULT 'normal',
                status VARCHAR(20) DEFAULT 'pending',
                processed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create trigger for email notifications
        db.session.execute(text("""
            DROP TRIGGER IF EXISTS trigger_notify_clinic ON leads;
            CREATE TRIGGER trigger_notify_clinic
                AFTER INSERT ON leads
                FOR EACH ROW
                EXECUTE FUNCTION notify_clinic_new_lead();
        """))
        
        db.session.commit()
        logger.info("Successfully set up email notification system")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up email notifications: {e}")
        db.session.rollback()
        return False

def populate_seo_data():
    """Populate SEO data for existing entities."""
    try:
        # Update clinic SEO data
        db.session.execute(text("""
            INSERT INTO seo_pages (page_type, entity_id, title, description, canonical_url)
            SELECT 
                'clinic',
                id,
                name || ' - Best Cosmetic Surgery Clinic in ' || city || ' | Antidote',
                'Book consultation at ' || name || ' in ' || city || '. Professional cosmetic surgery services with expert doctors and modern facilities.',
                'https://antidote.com/clinics/' || id
            FROM clinics 
            WHERE is_approved = true
            ON CONFLICT DO NOTHING;
        """))
        
        # Update doctor SEO data
        db.session.execute(text("""
            INSERT INTO seo_pages (page_type, entity_id, title, description, canonical_url)
            SELECT 
                'doctor',
                id,
                'Dr. ' || name || ' - ' || specialty || ' Specialist in ' || city || ' | Antidote',
                'Consult Dr. ' || name || ', ' || specialty || ' specialist with ' || experience || ' years experience. Book consultation for ₹' || COALESCE(consultation_fee::text, '1000') || '.',
                'https://antidote.com/doctors/' || id
            FROM doctors 
            WHERE verification_status = 'approved'
            ON CONFLICT DO NOTHING;
        """))
        
        # Update procedure SEO data
        db.session.execute(text("""
            INSERT INTO seo_pages (page_type, entity_id, title, description, canonical_url)
            SELECT 
                'procedure',
                id,
                procedure_name || ' Cost, Benefits & Best Doctors in India | Antidote',
                'Complete guide to ' || procedure_name || '. Cost range: ₹' || min_cost || '-₹' || max_cost || '. Benefits, risks, recovery time and best doctors in India.',
                'https://antidote.com/procedures/' || id
            FROM procedures
            ON CONFLICT DO NOTHING;
        """))
        
        db.session.commit()
        logger.info("Successfully populated SEO data")
        return True
        
    except Exception as e:
        logger.error(f"Error populating SEO data: {e}")
        db.session.rollback()
        return False

def add_analytics_indexes():
    """Add database indexes for better performance."""
    try:
        # Add indexes for common queries
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_clinics_city ON clinics(city);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_clinics_rating ON clinics(rating DESC);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_doctors_city ON doctors(city);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_doctors_specialty ON doctors(specialty);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_procedures_body_part ON procedures(body_part);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_procedures_cost ON procedures(min_cost, max_cost);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_credit_transactions_clinic ON credit_transactions(clinic_id, created_at DESC);"))
        
        db.session.commit()
        logger.info("Successfully added analytics indexes")
        return True
        
    except Exception as e:
        logger.error(f"Error adding indexes: {e}")
        db.session.rollback()
        return False

def main():
    """Run complete integration setup."""
    from app import app
    
    with app.app_context():
        logger.info("Starting complete integration process...")
        
        # Step 1: Create missing tables
        if not create_missing_tables():
            logger.error("Failed to create missing tables")
            return False
        
        # Step 2: Integrate billing automation
        if not integrate_billing_automation():
            logger.error("Failed to integrate billing automation")
            return False
        
        # Step 3: Setup email notifications
        if not setup_email_notifications():
            logger.error("Failed to setup email notifications")
            return False
        
        # Step 4: Populate SEO data
        if not populate_seo_data():
            logger.error("Failed to populate SEO data")
            return False
        
        # Step 5: Add performance indexes
        if not add_analytics_indexes():
            logger.error("Failed to add analytics indexes")
            return False
        
        logger.info("Complete integration process finished successfully!")
        return True

if __name__ == "__main__":
    main()