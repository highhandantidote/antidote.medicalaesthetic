"""
Startup optimization module to reduce application boot time.
Moves database initialization to background and provides instant health checks.
"""
import os
import logging
import threading
import time
from flask import Flask, jsonify
from datetime import datetime

logger = logging.getLogger(__name__)

class StartupOptimizer:
    def __init__(self):
        self.initialization_complete = False
        self.initialization_start_time = None
        self.initialization_end_time = None
        self.initialization_error = None
        
    def init_app(self, app: Flask, db):
        """Initialize startup optimization for the Flask app."""
        self.app = app
        self.db = db
        
        # Add immediate health check endpoint
        @app.route('/health')
        @app.route('/health/')
        def health_check():
            """Immediate health check that responds during startup."""
            status = {
                'status': 'healthy',
                'service': 'antidote',
                'startup_complete': self.initialization_complete,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if self.initialization_start_time:
                elapsed = time.time() - self.initialization_start_time
                status['startup_elapsed'] = f"{elapsed:.2f}s"
            
            if self.initialization_error:
                status['initialization_error'] = str(self.initialization_error)
                return jsonify(status), 503
                
            return jsonify(status), 200
        
        # Add readiness probe for deployment
        @app.route('/ready')
        @app.route('/ready/')
        def readiness_check():
            """Readiness check for deployment health monitoring."""
            if self.initialization_complete:
                return jsonify({
                    'status': 'ready',
                    'service': 'antidote',
                    'database': 'connected'
                }), 200
            else:
                return jsonify({
                    'status': 'initializing',
                    'service': 'antidote',
                    'database': 'connecting'
                }), 503
        
        # Add deployment status endpoint
        @app.route('/status')
        @app.route('/status/')
        def deployment_status():
            """Comprehensive deployment status for monitoring."""
            status = {
                'service': 'antidote',
                'status': 'healthy' if self.initialization_complete else 'initializing',
                'timestamp': datetime.utcnow().isoformat(),
                'initialization_complete': self.initialization_complete
            }
            
            if self.initialization_start_time:
                elapsed = time.time() - self.initialization_start_time
                status['startup_time'] = f"{elapsed:.2f}s"
                
            if self.initialization_end_time:
                total_time = self.initialization_end_time - self.initialization_start_time
                status['total_initialization_time'] = f"{total_time:.2f}s"
            
            if self.initialization_error:
                status['error'] = str(self.initialization_error)
                return jsonify(status), 503
                
            return jsonify(status), 200
        
        # Add liveness probe
        @app.route('/alive')
        @app.route('/alive/')
        def liveness_check():
            """Simple liveness check that always responds."""
            return jsonify({
                'status': 'alive',
                'service': 'antidote',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
            
        logger.info("✅ Startup optimization endpoints registered")
    
    def start_background_initialization(self, app, db):
        """Start database initialization in background thread."""
        def background_init():
            try:
                self.initialization_start_time = time.time()
                logger.info("🚀 Starting background database initialization...")
                
                with app.app_context():
                    # Import models to ensure they're registered
                    import models
                    
                    # Optimized database table creation with IF NOT EXISTS logic
                    self._create_tables_optimized(db)
                    
                    # Initialize performance optimizations in background
                    self._initialize_performance_systems(app, db)
                    
                    self.initialization_end_time = time.time()
                    elapsed = self.initialization_end_time - self.initialization_start_time
                    logger.info(f"✅ Background initialization completed in {elapsed:.2f}s")
                    self.initialization_complete = True
                    
            except Exception as e:
                self.initialization_error = e
                logger.error(f"❌ Background initialization failed: {e}")
                # Don't let initialization failure crash the app
                self.initialization_complete = True  # Mark as complete to prevent hanging
        
        # Start initialization in background thread
        init_thread = threading.Thread(target=background_init, daemon=True)
        init_thread.start()
        logger.info("🔄 Background database initialization started")
    
    def _create_tables_optimized(self, db):
        """Create database tables with optimized queries."""
        try:
            logger.info("Creating database tables with optimization...")
            
            # Use the database optimizer for efficient table creation
            from database_optimizer import DatabaseOptimizer
            db_optimizer = DatabaseOptimizer(db)
            
            # Verify connection first
            if not db_optimizer.verify_database_connection():
                logger.error("Database connection verification failed")
                return
            
            # Create tables with optimization
            if db_optimizer.optimize_table_creation():
                logger.info("✅ Database tables created successfully")
                
                # Create optimized indexes
                if db_optimizer.optimize_indexes():
                    logger.info("✅ Database indexes optimized successfully")
                
                # Log database stats
                stats = db_optimizer.get_database_stats()
                logger.info(f"📊 Database stats: {stats.get('table_count', 0)} tables")
            else:
                logger.error("Failed to create database tables")
            
        except Exception as e:
            logger.error(f"Error in optimized table creation: {e}")
            # Try fallback approach
            try:
                db.session.rollback()
                db.create_all()
                logger.info("Database tables created with fallback method")
            except Exception as e2:
                logger.error(f"Fallback table creation also failed: {e2}")
                raise e2
    
    def _initialize_performance_systems(self, app, db):
        """Initialize performance systems in background."""
        try:
            # Initialize performance optimizations without blocking startup
            performance_modules = [
                'performance_cache',
                'phase1_performance_cache',
                'phase1_database_optimizer',
                'server_response_optimizer',
                'mobile_css_optimization',
                'mobile_performance_complete',
                'phase1_4_performance_optimizer'
            ]
            
            for module_name in performance_modules:
                try:
                    if module_name == 'phase1_performance_cache':
                        from phase1_performance_cache import optimize_homepage_queries
                        optimize_homepage_queries()
                    elif module_name == 'phase1_database_optimizer':
                        from phase1_database_optimizer import register_database_optimizations
                        register_database_optimizations(app, db)
                    elif module_name == 'server_response_optimizer':
                        from server_response_optimizer import register_server_optimizations
                        register_server_optimizations(app, db)
                    elif module_name == 'mobile_css_optimization':
                        from mobile_css_optimization import optimize_mobile_css_loading
                        optimize_mobile_css_loading(app)
                    elif module_name == 'mobile_performance_complete':
                        from mobile_performance_complete import initialize_mobile_performance_system
                        initialize_mobile_performance_system(app, db)
                    elif module_name == 'phase1_4_performance_optimizer':
                        from phase1_4_performance_optimizer import register_phase1_4_optimizations
                        register_phase1_4_optimizations(app, db)
                    elif module_name == 'performance_cache':
                        from performance_cache import initialize_performance_optimizations
                        initialize_performance_optimizations()
                        
                    logger.info(f"✅ {module_name} initialized")
                except ImportError:
                    logger.warning(f"⚠️ {module_name} not available")
                except Exception as e:
                    logger.warning(f"⚠️ Error initializing {module_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error initializing performance systems: {e}")

# Global instance
startup_optimizer = StartupOptimizer()