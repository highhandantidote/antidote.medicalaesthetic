"""Utility functions for database operations."""
import logging
from sqlalchemy import text
from app import db
from models import (
    BodyPart, Category, Procedure, User, Doctor, DoctorCategory,
    DoctorProcedure, Review, Community, CommunityReply,
    CommunityTagging, UserPreference, Notification, Interaction,
    DoctorPhoto, DoctorAvailability, Lead
)

logger = logging.getLogger(__name__)

def check_database_connection():
    """Check if the database connection is working."""
    try:
        result = db.session.execute(text("SELECT version()"))
        version = result.scalar()
        logger.info(f"Database connection successful. PostgreSQL version: {version}")
        return True, version
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False, str(e)

def get_table_counts():
    """Get the number of records in each table."""
    try:
        tables = [
            BodyPart, Category, Procedure, User, Doctor, DoctorCategory,
            DoctorProcedure, Review, Community, CommunityReply,
            CommunityTagging, UserPreference, Notification, Interaction,
            DoctorPhoto, DoctorAvailability, Lead
        ]
        
        counts = {}
        for table in tables:
            count = db.session.query(table).count()
            counts[table.__tablename__] = count
        
        return counts
    except Exception as e:
        logger.error(f"Error getting table counts: {str(e)}")
        return {"error": str(e)}

def list_tables():
    """List all tables in the database."""
    try:
        result = db.session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        return tables
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        return []

def describe_table(table_name):
    """Describe the columns of a table."""
    try:
        result = db.session.execute(text(f"""
            SELECT 
                column_name, 
                data_type, 
                is_nullable, 
                column_default
            FROM 
                information_schema.columns
            WHERE 
                table_name = '{table_name}'
            ORDER BY 
                ordinal_position
        """))
        
        columns = [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2],
                "default": row[3]
            }
            for row in result
        ]
        
        return columns
    except Exception as e:
        logger.error(f"Error describing table {table_name}: {str(e)}")
        return []

def check_foreign_keys():
    """Check if all foreign keys are valid."""
    try:
        result = db.session.execute(text("""
            SELECT
                tc.table_schema, 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
        """))
        
        foreign_keys = [
            {
                "table": row[1],
                "column": row[2],
                "references_table": row[4],
                "references_column": row[5]
            }
            for row in result
        ]
        
        return foreign_keys
    except Exception as e:
        logger.error(f"Error checking foreign keys: {str(e)}")
        return []

def check_indexes():
    """List all indexes in the database."""
    try:
        result = db.session.execute(text("""
            SELECT
                tablename,
                indexname,
                indexdef
            FROM
                pg_indexes
            WHERE
                schemaname = 'public'
            ORDER BY
                tablename,
                indexname
        """))
        
        indexes = [
            {
                "table": row[0],
                "index": row[1],
                "definition": row[2]
            }
            for row in result
        ]
        
        return indexes
    except Exception as e:
        logger.error(f"Error checking indexes: {str(e)}")
        return []
