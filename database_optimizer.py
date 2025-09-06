"""
Database optimization module to reduce startup time.
Implements IF NOT EXISTS checks and optimized index creation.
"""
import logging
from sqlalchemy import text, inspect
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    def __init__(self, db):
        self.db = db
        
    def optimize_table_creation(self):
        """Create tables with optimized queries using IF NOT EXISTS logic."""
        try:
            logger.info("Starting optimized database table creation...")
            
            # Check existing tables first
            inspector = inspect(self.db.engine)
            existing_tables = set(inspector.get_table_names())
            
            # Get all defined model tables
            metadata_tables = set(self.db.metadata.tables.keys())
            
            # Only create missing tables
            missing_tables = metadata_tables - existing_tables
            
            if len(missing_tables) == 0:
                logger.info(f"All {len(metadata_tables)} tables already exist, skipping creation")
                return True
            
            logger.info(f"Creating {len(missing_tables)} missing tables: {missing_tables}")
            
            # Create only missing tables using SQLAlchemy's create_all
            # This is more efficient than checking each table individually
            self.db.create_all()
            
            logger.info("✅ Database tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in optimized table creation: {e}")
            return False
    
    def optimize_indexes(self):
        """Create database indexes with optimization checks."""
        try:
            logger.info("Optimizing database indexes...")
            
            # Common indexes that improve query performance
            index_queries = [
                # Users table indexes
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
                
                # Procedures table indexes
                "CREATE INDEX IF NOT EXISTS idx_procedures_category ON procedures(category_id)",
                "CREATE INDEX IF NOT EXISTS idx_procedures_cost ON procedures(min_cost, max_cost)",
                
                # Reviews table indexes
                "CREATE INDEX IF NOT EXISTS idx_reviews_procedure ON reviews(procedure_id)",
                "CREATE INDEX IF NOT EXISTS idx_reviews_doctor ON reviews(doctor_id)",
                "CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating)",
                
                # Community table indexes
                "CREATE INDEX IF NOT EXISTS idx_community_procedure ON community(procedure_id)",
                "CREATE INDEX IF NOT EXISTS idx_community_category ON community(category_id)",
                "CREATE INDEX IF NOT EXISTS idx_community_created ON community(created_at)",
                
                # Clinics table indexes
                "CREATE INDEX IF NOT EXISTS idx_clinics_location ON clinics(city, state)",
                "CREATE INDEX IF NOT EXISTS idx_clinics_verification ON clinics(is_verified)",
                
                # Doctors table indexes
                "CREATE INDEX IF NOT EXISTS idx_doctors_clinic ON doctors(clinic_id)",
                "CREATE INDEX IF NOT EXISTS idx_doctors_verification ON doctors(is_verified)",
            ]
            
            created_count = 0
            for query in index_queries:
                try:
                    self.db.session.execute(text(query))
                    created_count += 1
                except Exception as e:
                    # Index might already exist, which is fine
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Could not create index: {query} - {e}")
            
            self.db.session.commit()
            logger.info(f"✅ Created/verified {created_count} database indexes")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing indexes: {e}")
            self.db.session.rollback()
            return False
    
    def verify_database_connection(self):
        """Verify database connection with minimal query."""
        try:
            # Simple connection test
            result = self.db.session.execute(text("SELECT 1")).fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Database connection verification failed: {e}")
            return False
        finally:
            try:
                self.db.session.close()
            except:
                pass
    
    def get_database_stats(self):
        """Get basic database statistics for monitoring."""
        try:
            stats = {}
            
            # Get table counts
            inspector = inspect(self.db.engine)
            tables = inspector.get_table_names()
            stats['table_count'] = len(tables)
            stats['tables'] = tables
            
            # Get basic row counts for main tables
            main_tables = ['users', 'procedures', 'clinics', 'doctors', 'reviews', 'community']
            for table in main_tables:
                try:
                    if table in tables:
                        result = self.db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                        stats[f'{table}_count'] = result[0] if result else 0
                except Exception as e:
                    logger.warning(f"Could not get count for {table}: {e}")
                    stats[f'{table}_count'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}
        finally:
            try:
                self.db.session.close()
            except:
                pass