"""
Phase 1 Database Connection Optimizer
Optimizes database connections and queries for <200ms response times
"""

import logging
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
import time

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database connection and query optimizer for Phase 1"""
    
    def __init__(self, app=None):
        self.app = app
        self.query_count = 0
        self.slow_query_threshold = 0.1  # 100ms
        
    def init_app(self, app):
        """Initialize database optimizations with the Flask app"""
        self.app = app
        
        # Update database configuration for better performance
        app.config['SQLALCHEMY_ENGINE_OPTIONS'].update({
            'pool_size': 15,          # Increased from 10
            'max_overflow': 25,       # Increased from 20  
            'pool_recycle': 1800,     # 30 minutes instead of 5 minutes
            'pool_pre_ping': True,    # Keep enabled for connection health
            'pool_timeout': 20,       # Reduced from 30 for faster failures
            'echo': False,            # Disable SQL logging in production
            'connect_args': {
                'sslmode': 'prefer',
                'connect_timeout': 20,
                'application_name': 'antidote_optimized',
                'options': '-c statement_timeout=30000'  # 30 second query timeout
            }
        })
        
        # Register database event listeners for monitoring
        self.register_query_monitoring()
        
        logger.info("✅ Phase 1 database optimizations applied")
    
    def register_query_monitoring(self):
        """Register database event listeners for query monitoring"""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Start query timing"""
            context._query_start_time = time.time()
            self.query_count += 1
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log slow queries"""
            if hasattr(context, '_query_start_time'):
                query_time = time.time() - context._query_start_time
                
                if query_time > self.slow_query_threshold:
                    # Log slow queries for optimization
                    query_preview = statement[:100] + '...' if len(statement) > 100 else statement
                    logger.warning(f"Slow query ({query_time*1000:.2f}ms): {query_preview}")
    
    def optimize_database_session(self, db):
        """Apply session-level optimizations"""
        try:
            # Set optimized PostgreSQL parameters for this session
            db.session.execute(text("SET work_mem = '32MB'"))
            db.session.execute(text("SET shared_buffers = '256MB'"))
            db.session.execute(text("SET effective_cache_size = '1GB'"))
            db.session.execute(text("SET random_page_cost = 1.1"))
            db.session.execute(text("SET seq_page_cost = 1.0"))
            db.session.commit()
            
            logger.debug("Database session optimizations applied")
        except Exception as e:
            logger.error(f"Error applying database session optimizations: {e}")
            db.session.rollback()

def register_database_optimizations(app, db):
    """Register all Phase 1 database optimizations"""
    optimizer = DatabaseOptimizer()
    optimizer.init_app(app)
    
    # Apply session optimizations on app startup
    with app.app_context():
        try:
            optimizer.optimize_database_session(db)
        except Exception as e:
            logger.warning(f"Could not apply session optimizations: {e}")
    
    return optimizer