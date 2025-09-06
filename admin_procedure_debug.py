#!/usr/bin/env python3
"""
Debug script to specifically check procedure objects in the admin dashboard.

This script focuses on analyzing the procedure model fields and their structure
to determine why procedures aren't displaying properly in the admin dashboard.
"""

import os
import sys
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a direct connection to the database."""
    import psycopg2
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL not found in environment")
        sys.exit(1)
    
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        logger.info("Database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

def check_procedure_model_attributes():
    """Check all available attributes in the Procedure model."""
    try:
        from models import Procedure
        logger.info("Successfully imported Procedure model")
    except ImportError as e:
        logger.error(f"Failed to import Procedure model: {e}")
        return
    
    logger.info("Checking Procedure model attributes...")
    procedure_attrs = [attr for attr in dir(Procedure) 
                      if not attr.startswith('_') and attr != 'metadata']
    
    logger.info(f"Found {len(procedure_attrs)} attributes in Procedure model:")
    for attr in procedure_attrs:
        logger.info(f"  - {attr}")
    
    # Check table name
    logger.info(f"Procedure model __tablename__: {getattr(Procedure, '__tablename__', 'Not defined')}")
    
    # Check column names through SQLAlchemy
    table_columns = []
    try:
        for column in Procedure.__table__.columns:
            table_columns.append(f"{column.name} ({column.type})")
        
        logger.info(f"Found {len(table_columns)} columns in Procedure model:")
        for col in table_columns:
            logger.info(f"  - {col}")
    except Exception as e:
        logger.error(f"Error checking table columns: {e}")

def check_procedure_table():
    """Check the procedure table structure in the database directly."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    logger.info("Checking procedure table structure...")
    try:
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'procedure'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            logger.info("Table 'procedure' exists in database")
        else:
            logger.warning("Table 'procedure' does NOT exist in database")
            
            # Check if there's a procedures table (plural)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'procedures'
                );
            """)
            exists_plural = cursor.fetchone()[0]
            
            if exists_plural:
                logger.info("Table 'procedures' exists in database (note the plural name)")
            else:
                logger.warning("Neither 'procedure' nor 'procedures' table found")
        
        # Get table columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'procedure';
        """)
        
        columns = cursor.fetchall()
        logger.info(f"Found {len(columns)} columns in table 'procedure':")
        for col_name, data_type in columns:
            logger.info(f"  - {col_name} ({data_type})")
            
        # Get procedure records
        cursor.execute("SELECT * FROM procedure LIMIT 5;")
        records = cursor.fetchall()
        
        logger.info(f"Found {len(records)} records in table 'procedure'")
        
        # Pretty print column names and first 2 records with values
        if records:
            col_names = [desc[0] for desc in cursor.description]
            logger.info("Column names: " + ", ".join(col_names))
            
            for i, record in enumerate(records[:2]):
                logger.info(f"Record {i+1}:")
                for j, value in enumerate(record):
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    logger.info(f"  - {col_names[j]}: {value}")
    except Exception as e:
        logger.error(f"Error checking procedure table: {e}")
    finally:
        cursor.close()
        conn.close()

def check_relationships():
    """Check relationships between Procedure and other models."""
    try:
        from sqlalchemy import inspect
        from models import Procedure, Category, Review
        logger.info("Successfully imported models for relationship check")
    except ImportError as e:
        logger.error(f"Failed to import models for relationship check: {e}")
        return
    
    logger.info("Checking Procedure model relationships...")
    
    try:
        # Check relationship with Category
        inspector = inspect(Procedure)
        relationships = inspector.relationships
        
        logger.info(f"Found {len(relationships)} relationships in Procedure model:")
        for name, rel in relationships.items():
            target_cls = rel.mapper.class_.__name__
            logger.info(f"  - {name}: related to {target_cls}")
            
        # Check if categories are accessible
        procedures = Procedure.query.limit(2).all()
        if procedures:
            for i, proc in enumerate(procedures):
                logger.info(f"Procedure {i+1} ({proc.id}): {proc.procedure_name}")
                
                if hasattr(proc, 'category'):
                    category = proc.category
                    if category:
                        logger.info(f"  - Category: {category.name} (ID: {category.id})")
                    else:
                        logger.warning(f"  - Category is None for procedure {proc.id}")
                else:
                    logger.warning(f"  - No 'category' attribute in procedure {proc.id}")
                    
                # Check category_id
                if hasattr(proc, 'category_id'):
                    logger.info(f"  - category_id: {proc.category_id}")
                else:
                    logger.warning(f"  - No 'category_id' attribute in procedure {proc.id}")
    except Exception as e:
        logger.error(f"Error checking relationships: {e}")

def check_admin_dashboard_context():
    """Simulate admin dashboard context preparation to debug issues."""
    try:
        from models import Procedure
        logger.info("Successfully imported Procedure model for dashboard context")
    except ImportError as e:
        logger.error(f"Failed to import Procedure model for dashboard context: {e}")
        return
    
    logger.info("Simulating admin dashboard context preparation...")
    try:
        # Get all procedures for procedure management
        procedures = Procedure.query.all()
        logger.info(f"Retrieved {len(procedures)} procedures for admin dashboard")
        
        # Check each procedure for required template attributes
        for i, proc in enumerate(procedures):
            logger.info(f"Procedure {i+1}:")
            logger.info(f"  - id: {proc.id}")
            logger.info(f"  - procedure_name: {getattr(proc, 'procedure_name', 'MISSING')}")
            
            # Check category relationship
            if hasattr(proc, 'category') and proc.category:
                logger.info(f"  - category: {proc.category.name}")
            else:
                logger.warning(f"  - category: MISSING (could cause template error)")
            
            # Check min/max cost attributes
            logger.info(f"  - min_cost: {getattr(proc, 'min_cost', 'MISSING')}")
            logger.info(f"  - max_cost: {getattr(proc, 'max_cost', 'MISSING')}")
            
            # Check popularity score
            logger.info(f"  - popularity_score: {getattr(proc, 'popularity_score', 'MISSING')}")
            
            # Check avg_rating and review_count
            logger.info(f"  - avg_rating: {getattr(proc, 'avg_rating', 'MISSING')}")
            logger.info(f"  - review_count: {getattr(proc, 'review_count', 'MISSING')}")
            
    except Exception as e:
        logger.error(f"Error simulating admin dashboard context: {e}")

def main():
    """Main execution function."""
    from main import app
    
    with app.app_context():
        logger.info("Starting admin procedures debug...")
        
        try:
            logger.info("Checking for procedures directly in database...")
            check_procedure_table()
            
            logger.info("Getting model attributes...")
            check_procedure_model_attributes()
            
            logger.info("Checking relationships...")
            check_relationships()
            
            logger.info("Simulating admin dashboard context...")
            check_admin_dashboard_context()
            
            logger.info("Admin procedures debug completed.")
        except Exception as e:
            logger.error(f"Error during debugging: {e}")

if __name__ == "__main__":
    main()