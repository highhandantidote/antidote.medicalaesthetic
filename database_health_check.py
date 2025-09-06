"""
Database health check module for deployment monitoring.
Provides fast database connectivity and table verification.
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import time

logger = logging.getLogger(__name__)

class DatabaseHealthChecker:
    """Fast database health verification for deployment."""
    
    def __init__(self):
        self.engine = None
        self.last_check_time = 0
        self.last_check_result = False
        self.cache_duration = 5  # Cache health check for 5 seconds
        
    def get_engine(self):
        """Get or create database engine with optimized settings."""
        if self.engine is None:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise Exception("DATABASE_URL environment variable not set")
            
            # Create engine with minimal connection settings for health checks
            self.engine = create_engine(
                database_url,
                pool_size=1,
                max_overflow=0,
                pool_timeout=5,
                pool_recycle=300,
                pool_pre_ping=True,
                connect_args={
                    'connect_timeout': 5,
                    'application_name': 'health_check'
                }
            )
        return self.engine
    
    def check_connection(self):
        """Fast database connection check with caching."""
        current_time = time.time()
        
        # Return cached result if recent
        if current_time - self.last_check_time < self.cache_duration:
            return self.last_check_result
        
        try:
            engine = self.get_engine()
            
            # Simple connectivity test
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.close()
            
            self.last_check_result = True
            self.last_check_time = current_time
            return True
            
        except SQLAlchemyError as e:
            logger.warning(f"Database connection check failed: {e}")
            self.last_check_result = False
            self.last_check_time = current_time
            return False
        except Exception as e:
            logger.error(f"Database health check error: {e}")
            self.last_check_result = False
            self.last_check_time = current_time
            return False
    
    def check_critical_tables(self):
        """Verify critical tables exist."""
        try:
            engine = self.get_engine()
            critical_tables = ['users', 'procedures', 'categories', 'body_parts']
            
            with engine.connect() as conn:
                for table in critical_tables:
                    try:
                        result = conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                        result.close()
                    except SQLAlchemyError:
                        logger.warning(f"Critical table '{table}' not accessible")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Critical tables check failed: {e}")
            return False
    
    def get_table_count(self):
        """Get total number of tables in database."""
        try:
            engine = self.get_engine()
            
            with engine.connect() as conn:
                # PostgreSQL specific query
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                count = result.scalar()
                result.close()
                return count
                
        except Exception as e:
            logger.error(f"Table count check failed: {e}")
            return 0
    
    def get_health_status(self):
        """Get comprehensive database health status."""
        start_time = time.time()
        
        status = {
            'connected': False,
            'tables_accessible': False,
            'table_count': 0,
            'response_time_ms': 0,
            'timestamp': time.time()
        }
        
        try:
            # Check basic connectivity
            status['connected'] = self.check_connection()
            
            if status['connected']:
                # Check critical tables
                status['tables_accessible'] = self.check_critical_tables()
                
                # Get table count
                status['table_count'] = self.get_table_count()
            
        except Exception as e:
            logger.error(f"Database health status check failed: {e}")
        
        # Calculate response time
        status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        return status

# Global instance
db_health_checker = DatabaseHealthChecker()

def check_database_health():
    """Quick function to check database health."""
    return db_health_checker.check_connection()

def get_database_status():
    """Get detailed database status."""
    return db_health_checker.get_health_status()