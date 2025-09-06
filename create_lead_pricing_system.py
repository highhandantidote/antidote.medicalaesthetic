#!/usr/bin/env python3
"""
Create lead pricing system with admin-configurable tiers.
This script creates the database table and inserts initial pricing data.
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    engine = create_engine(database_url)
    return engine.connect()

def create_lead_pricing_table():
    """Create the lead pricing tiers table."""
    try:
        conn = get_db_connection()
        
        # Create lead_pricing_tiers table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lead_pricing_tiers (
                id SERIAL PRIMARY KEY,
                tier_name VARCHAR(100) NOT NULL,
                min_package_value INTEGER NOT NULL,
                max_package_value INTEGER,
                credit_cost INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                created_by INTEGER REFERENCES users(id),
                UNIQUE(min_package_value, max_package_value)
            )
        """))
        
        # Add index for efficient lookups
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pricing_tiers_package_value 
            ON lead_pricing_tiers(min_package_value, max_package_value, is_active)
        """))
        
        # Insert initial pricing tiers based on current hardcoded values
        initial_tiers = [
            ('Basic Tier', 0, 5000, 100),
            ('Standard Tier', 5001, 10000, 150),
            ('Premium Tier', 10001, 20000, 200),
            ('Luxury Tier', 20001, 50000, 300),
            ('Ultra Premium Tier', 50001, None, 400)
        ]
        
        for tier_name, min_val, max_val, credit_cost in initial_tiers:
            conn.execute(text("""
                INSERT INTO lead_pricing_tiers (tier_name, min_package_value, max_package_value, credit_cost)
                VALUES (:tier_name, :min_val, :max_val, :credit_cost)
                ON CONFLICT (min_package_value, max_package_value) DO NOTHING
            """), {
                "tier_name": tier_name,
                "min_val": min_val,
                "max_val": max_val,
                "credit_cost": credit_cost
            })
        
        # Add audit log table for pricing changes
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lead_pricing_audit (
                id SERIAL PRIMARY KEY,
                tier_id INTEGER REFERENCES lead_pricing_tiers(id),
                action VARCHAR(50) NOT NULL,
                old_values JSONB,
                new_values JSONB,
                changed_by INTEGER REFERENCES users(id),
                changed_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        conn.commit()
        logger.info("Lead pricing tiers table created successfully with initial data")
        
    except Exception as e:
        logger.error(f"Error creating lead pricing table: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    try:
        create_lead_pricing_table()
        print("Lead pricing system setup completed successfully!")
    except Exception as e:
        print(f"Failed to setup lead pricing system: {e}")
        sys.exit(1)