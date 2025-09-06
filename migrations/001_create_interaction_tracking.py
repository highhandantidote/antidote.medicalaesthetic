"""
Migration 001: Create User Interaction Tracking System
Creates the foundation for comprehensive lead capture
"""

import os
import psycopg2
from datetime import datetime

def get_db_connection():
    """Get database connection using environment variable."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def create_user_interactions_table():
    """Create the user_interactions table for comprehensive tracking."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create user_interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_interactions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255),
                user_id INTEGER,
                interaction_type VARCHAR(50) NOT NULL,
                source_page VARCHAR(200),
                data TEXT,
                converted_to_lead BOOLEAN DEFAULT FALSE,
                lead_id INTEGER,
                ip_address VARCHAR(45),
                user_agent TEXT,
                referrer_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes for performance (separately to handle any failures gracefully)
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_interactions_session_id ON user_interactions(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_interactions_user_id ON user_interactions(user_id);", 
            "CREATE INDEX IF NOT EXISTS idx_user_interactions_type ON user_interactions(interaction_type);",
            "CREATE INDEX IF NOT EXISTS idx_user_interactions_created_at ON user_interactions(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_user_interactions_converted ON user_interactions(converted_to_lead);"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as index_error:
                print(f"Warning: Could not create index: {index_error}")
                continue
        
        print("✓ Created user_interactions table with indexes")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating user_interactions table: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def enhance_leads_table():
    """Add new columns to leads table for enhanced tracking."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Add new columns to leads table
        new_columns = [
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS interaction_id INTEGER;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_score INTEGER DEFAULT 50;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS engagement_level VARCHAR(20) DEFAULT 'medium';",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS conversion_probability DECIMAL(5,2) DEFAULT 0.50;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_interaction_at TIMESTAMP;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS interaction_count INTEGER DEFAULT 1;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS source_campaign VARCHAR(100);",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_source VARCHAR(100);",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_medium VARCHAR(100);",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_campaign VARCHAR(100);"
        ]
        
        for column_sql in new_columns:
            try:
                cursor.execute(column_sql)
            except Exception as col_error:
                print(f"Warning: Could not add column: {col_error}")
                continue
        
        # Create indexes for new columns
        lead_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_leads_interaction_id ON leads(interaction_id);",
            "CREATE INDEX IF NOT EXISTS idx_leads_lead_score ON leads(lead_score);",
            "CREATE INDEX IF NOT EXISTS idx_leads_engagement_level ON leads(engagement_level);",
            "CREATE INDEX IF NOT EXISTS idx_leads_source_campaign ON leads(source_campaign);"
        ]
        
        for index_sql in lead_indexes:
            try:
                cursor.execute(index_sql)
            except Exception as index_error:
                print(f"Warning: Could not create lead index: {index_error}")
                continue
        
        print("✓ Enhanced leads table with new tracking columns")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"Error enhancing leads table: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_lead_scoring_rules_table():
    """Create table for configurable lead scoring rules."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_scoring_rules (
                id SERIAL PRIMARY KEY,
                interaction_type VARCHAR(50) NOT NULL,
                condition_field VARCHAR(100),
                condition_operator VARCHAR(20),
                condition_value TEXT,
                points INTEGER NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Insert default scoring rules
        default_rules = [
            ('ai_recommendation', 'base', 'equals', 'true', 60, 'AI recommendation form submission'),
            ('face_analysis', 'base', 'equals', 'true', 80, 'Face analysis submission'),
            ('cost_calculator', 'base', 'equals', 'true', 70, 'Cost calculator usage'),
            ('appointment_booking', 'base', 'equals', 'true', 90, 'Direct appointment booking'),
            ('package_inquiry', 'base', 'equals', 'true', 75, 'Package inquiry submission'),
            ('search_behavior', 'search_count', 'greater_than', '3', 15, 'Multiple searches indicating high intent'),
            ('engagement', 'page_time', 'greater_than', '300', 10, 'High engagement (5+ minutes on page)'),
            ('urgency', 'preferred_date', 'within_days', '7', 25, 'Wants consultation within a week'),
            ('budget', 'budget_range', 'equals', 'high', 20, 'High budget range indicated'),
            ('multiple_procedures', 'procedure_count', 'greater_than', '1', 15, 'Interest in multiple procedures')
        ]
        
        cursor.execute("SELECT COUNT(*) FROM lead_scoring_rules")
        existing_count = cursor.fetchone()[0]
        
        if existing_count == 0:
            for rule in default_rules:
                cursor.execute("""
                    INSERT INTO lead_scoring_rules 
                    (interaction_type, condition_field, condition_operator, condition_value, points, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, rule)
            
            print("✓ Created lead_scoring_rules table with default rules")
        else:
            print("✓ Lead scoring rules table already exists")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating lead_scoring_rules table: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_session_tracking_table():
    """Create table for anonymous session tracking."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                user_id INTEGER,
                ip_address VARCHAR(45),
                user_agent TEXT,
                referrer_url TEXT,
                utm_source VARCHAR(100),
                utm_medium VARCHAR(100),
                utm_campaign VARCHAR(100),
                first_page VARCHAR(200),
                last_page VARCHAR(200),
                page_count INTEGER DEFAULT 1,
                total_time_seconds INTEGER DEFAULT 0,
                converted_to_lead BOOLEAN DEFAULT FALSE,
                lead_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_sessions_converted ON user_sessions(converted_to_lead);
            CREATE INDEX IF NOT EXISTS idx_user_sessions_created_at ON user_sessions(created_at);
        """)
        
        print("✓ Created user_sessions table for anonymous tracking")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating user_sessions table: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Run all migration steps."""
    print("Starting Phase 1: Database Schema Enhancement")
    print("=" * 50)
    
    try:
        create_user_interactions_table()
        enhance_leads_table()
        create_lead_scoring_rules_table()
        create_session_tracking_table()
        
        print("\n" + "=" * 50)
        print("✅ Phase 1 Migration Completed Successfully!")
        print("\nNew tables created:")
        print("  - user_interactions (comprehensive interaction tracking)")
        print("  - lead_scoring_rules (configurable scoring system)")
        print("  - user_sessions (anonymous session tracking)")
        print("\nEnhanced tables:")
        print("  - leads (added scoring and tracking columns)")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()