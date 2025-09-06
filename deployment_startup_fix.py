"""
Deployment startup optimization module.
Addresses specific deployment issues for fast startup and health checks.
"""
import os
import time
import threading
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from sqlalchemy import text
import json

logger = logging.getLogger(__name__)

class DeploymentStartupOptimizer:
    """Optimizes application startup for deployment environments."""
    
    def __init__(self):
        self.startup_time = time.time()
        self.initialization_complete = False
        self.health_status = 'starting'
        self.database_ready = False
        self.services_ready = False
        self.startup_errors = []
        
    def init_app(self, app, db):
        """Initialize the deployment optimizer with the Flask app."""
        self.app = app
        self.db = db
        
        # Register immediate health check endpoints
        self._register_health_endpoints(app)
        
        # Start background initialization
        self._start_background_initialization(app, db)
        
        # Configure gunicorn-friendly settings
        self._configure_deployment_settings(app)
        
    def _register_health_endpoints(self, app):
        """Register health check endpoints that respond immediately."""
        
        @app.route('/health')
        @app.route('/health/')
        def health_check():
            """Primary health check endpoint for deployment monitoring."""
            uptime = time.time() - self.startup_time
            
            status_code = 200
            status = {
                'status': self.health_status,
                'service': 'antidote',
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': round(uptime, 2),
                'database_ready': self.database_ready,
                'services_ready': self.services_ready,
                'initialization_complete': self.initialization_complete
            }
            
            # Include any startup errors for debugging
            if self.startup_errors:
                status['startup_errors'] = self.startup_errors[-5:]  # Last 5 errors only
                
            # Return 503 only if critical services failed to start
            if self.health_status == 'error' and not self.database_ready:
                status_code = 503
                
            return jsonify(status), status_code
        
        @app.route('/ready')
        @app.route('/ready/')
        def readiness_check():
            """Kubernetes-style readiness probe."""
            if self.initialization_complete and self.database_ready:
                return jsonify({
                    'status': 'ready',
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            else:
                return jsonify({
                    'status': 'not_ready',
                    'database_ready': self.database_ready,
                    'initialization_complete': self.initialization_complete,
                    'timestamp': datetime.utcnow().isoformat()
                }), 503
        
        @app.route('/alive')
        @app.route('/alive/')
        def liveness_check():
            """Kubernetes-style liveness probe - always returns 200."""
            return jsonify({
                'status': 'alive',
                'service': 'antidote',
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': round(time.time() - self.startup_time, 2)
            }), 200
            
        logger.info("✅ Health check endpoints registered")
    
    def _start_background_initialization(self, app, db):
        """Start database and service initialization in background."""
        def background_init():
            try:
                logger.info("🚀 Starting background initialization...")
                self.health_status = 'initializing'
                
                with app.app_context():
                    # Phase 1: Basic database connection and table creation
                    self._initialize_database_fast(db)
                    
                    # Phase 2: Initialize core services
                    self._initialize_core_services(app, db)
                    
                    # Phase 3: Initialize performance optimizations
                    self._initialize_performance_systems(app)
                    
                    # Mark as complete
                    self.initialization_complete = True
                    self.services_ready = True
                    self.health_status = 'healthy'
                    
                    total_time = time.time() - self.startup_time
                    logger.info(f"✅ Background initialization completed in {total_time:.2f}s")
                    
            except Exception as e:
                self.health_status = 'error'
                self.startup_errors.append({
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat(),
                    'phase': 'background_initialization'
                })
                logger.error(f"❌ Background initialization failed: {e}")
                # Don't crash the app, just mark as error
        
        # Start in daemon thread so it doesn't block shutdown
        init_thread = threading.Thread(target=background_init, daemon=True)
        init_thread.start()
        logger.info("🔄 Background initialization thread started")
    
    def _initialize_database_fast(self, db):
        """Fast database initialization with optimized queries."""
        try:
            logger.info("⚡ Starting fast database initialization...")
            
            # Test database connection first
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("✅ Database connection verified")
            except Exception as e:
                self.startup_errors.append({
                    'error': f"Database connection failed: {str(e)}",
                    'timestamp': datetime.utcnow().isoformat(),
                    'phase': 'database_connection'
                })
                raise e
            
            # Import models to register them
            import models
            
            # Create tables with IF NOT EXISTS optimization
            start_time = time.time()
            
            # Use SQLAlchemy's built-in create_all which is optimized
            db.create_all()
            
            creation_time = time.time() - start_time
            logger.info(f"✅ Database tables created in {creation_time:.3f}s")
            
            # Verify critical tables exist
            critical_tables = ['users', 'procedures', 'categories', 'body_parts']
            missing_tables = []
            
            with db.engine.connect() as conn:
                for table in critical_tables:
                    try:
                        result = conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                        result.close()
                    except Exception:
                        missing_tables.append(table)
            
            if missing_tables:
                error_msg = f"Critical tables missing: {missing_tables}"
                self.startup_errors.append({
                    'error': error_msg,
                    'timestamp': datetime.utcnow().isoformat(),
                    'phase': 'table_verification'
                })
                raise Exception(error_msg)
            
            self.database_ready = True
            logger.info("✅ Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            self.database_ready = False
            raise e
    
    def _initialize_core_services(self, app, db):
        """Initialize core application services."""
        try:
            logger.info("🔧 Initializing core services...")
            
            # Initialize personalization service (if available)
            try:
                from personalization_service import PersonalizationService
                PersonalizationService.initialize_cache()
                logger.info("✅ Personalization service initialized")
            except ImportError:
                logger.info("ℹ️ Personalization service not available")
            except Exception as e:
                logger.warning(f"⚠️ Personalization service initialization failed: {e}")
            
            # Initialize search indexing (if available)
            try:
                from search_optimization import SearchOptimizer
                search_optimizer = SearchOptimizer()
                search_optimizer.warm_cache()
                logger.info("✅ Search optimizer initialized")
            except ImportError:
                logger.info("ℹ️ Search optimizer not available")
            except Exception as e:
                logger.warning(f"⚠️ Search optimizer initialization failed: {e}")
            
            logger.info("✅ Core services initialization completed")
            
        except Exception as e:
            logger.error(f"❌ Core services initialization failed: {e}")
            # Don't fail startup for service initialization issues
            self.startup_errors.append({
                'error': f"Core services failed: {str(e)}",
                'timestamp': datetime.utcnow().isoformat(),
                'phase': 'core_services'
            })
    
    def _initialize_performance_systems(self, app):
        """Initialize performance optimization systems."""
        try:
            logger.info("⚡ Initializing performance systems...")
            
            # List of performance modules to load (non-critical)
            performance_modules = [
                'server_response_optimization',
                'compression_middleware',
                'static_asset_optimizer',
                'css_optimizer',
                'image_optimizer'
            ]
            
            for module_name in performance_modules:
                try:
                    module = __import__(module_name)
                    if hasattr(module, 'initialize'):
                        module.initialize(app)
                    logger.info(f"✅ {module_name} initialized")
                except ImportError:
                    logger.info(f"ℹ️ {module_name} not available")
                except Exception as e:
                    logger.warning(f"⚠️ {module_name} initialization failed: {e}")
            
            logger.info("✅ Performance systems initialization completed")
            
        except Exception as e:
            logger.error(f"❌ Performance systems initialization failed: {e}")
            # Don't fail startup for performance optimization issues
            self.startup_errors.append({
                'error': f"Performance systems failed: {str(e)}",
                'timestamp': datetime.utcnow().isoformat(),
                'phase': 'performance_systems'
            })
    
    def _configure_deployment_settings(self, app):
        """Configure Flask app for deployment environments."""
        try:
            # Ensure proper host binding
            app.config['SERVER_NAME'] = None  # Allow any host
            
            # Optimize session settings for deployment
            app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
            app.config['SESSION_COOKIE_HTTPONLY'] = True
            app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
            
            # Database connection optimization for deployment
            if 'SQLALCHEMY_ENGINE_OPTIONS' not in app.config:
                app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
            
            # Update engine options for better deployment performance
            app.config['SQLALCHEMY_ENGINE_OPTIONS'].update({
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 30,
                'pool_recycle': 300,
                'pool_pre_ping': True,
                'connect_args': {
                    'connect_timeout': 10,
                    'application_name': 'antidote_app'
                }
            })
            
            # Configure logging for deployment
            if not app.debug:
                logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            
            logger.info("✅ Deployment settings configured")
            
        except Exception as e:
            logger.error(f"❌ Deployment configuration failed: {e}")
            self.startup_errors.append({
                'error': f"Deployment config failed: {str(e)}",
                'timestamp': datetime.utcnow().isoformat(),
                'phase': 'deployment_config'
            })

# Global instance
deployment_optimizer = DeploymentStartupOptimizer()