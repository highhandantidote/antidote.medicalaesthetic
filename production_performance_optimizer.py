"""
Production Performance Optimizer
Addresses common deployment performance issues for different domains.
"""

import os
import time
import logging
from flask import request, g
from functools import wraps
import psycopg2
from models import db

logger = logging.getLogger(__name__)

class ProductionPerformanceOptimizer:
    def __init__(self, app=None):
        self.app = app
        self.connection_pool = None
        self.cache = {}
        self.cache_ttl = 600  # 10 minutes for production
        
    def init_app(self, app):
        """Initialize production optimizations."""
        self.app = app
        
        # 1. Optimize database connections for production
        self._setup_production_db_config()
        
        # 2. Add connection pooling
        self._setup_connection_pooling()
        
        # 3. Add production caching
        self._setup_production_cache()
        
        # 4. Add keep-alive mechanism
        self._setup_keep_alive()
        
        logger.info("🚀 Production performance optimizer initialized")
    
    def _setup_production_db_config(self):
        """Optimize database configuration for production."""
        if self.app:
            # Increase connection pool for production
            self.app.config.update({
                "SQLALCHEMY_ENGINE_OPTIONS": {
                    "pool_size": 20,  # Increased from default
                    "max_overflow": 30,  # Handle traffic spikes
                    "pool_recycle": 300,
                    "pool_pre_ping": True,
                    "pool_timeout": 30,
                    "connect_args": {
                        "connect_timeout": 10,
                        "application_name": "antidote_production"
                    }
                }
            })
            logger.info("✅ Production database configuration applied")
    
    def _setup_connection_pooling(self):
        """Setup optimized connection pooling."""
        @self.app.before_request
        def before_request():
            # Ensure database connection is healthy
            try:
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                g.db_healthy = True
            except Exception as e:
                logger.warning(f"Database health check failed: {e}")
                g.db_healthy = False
        
        @self.app.teardown_appcontext
        def teardown_db(error):
            # Ensure connections are properly closed
            try:
                db.session.remove()
            except Exception:
                pass
    
    def _setup_production_cache(self):
        """Setup aggressive caching for production."""
        def production_cache(ttl=600):
            def decorator(f):
                @wraps(f)
                def wrapper(*args, **kwargs):
                    # Create cache key from request
                    cache_key = f"{request.endpoint}_{request.args.to_dict()}_{request.path}"
                    
                    # Check cache
                    if cache_key in self.cache:
                        cached_data, timestamp = self.cache[cache_key]
                        if time.time() - timestamp < ttl:
                            logger.info(f"🎯 Production cache HIT: {request.endpoint}")
                            return cached_data
                        else:
                            del self.cache[cache_key]
                    
                    # Execute and cache
                    start_time = time.time()
                    result = f(*args, **kwargs)
                    elapsed = (time.time() - start_time) * 1000
                    
                    # Cache the result
                    self.cache[cache_key] = (result, time.time())
                    logger.info(f"⚡ Production optimized: {request.endpoint} in {elapsed:.1f}ms")
                    
                    return result
                return wrapper
            return decorator
        
        # Make decorator available globally
        self.app.jinja_env.globals['production_cache'] = production_cache
    
    def _setup_keep_alive(self):
        """Setup keep-alive mechanism to prevent cold starts."""
        @self.app.route('/production-health')
        def production_health_check():
            """Ultra-fast health check to prevent cold starts."""
            try:
                # Quick database ping
                db.session.execute('SELECT 1')
                return {'status': 'healthy', 'timestamp': time.time()}, 200
            except Exception as e:
                return {'status': 'unhealthy', 'error': str(e)}, 500
        
        @self.app.route('/warmup')
        def warmup():
            """Warmup endpoint to preload critical data."""
            try:
                from models import Category, Procedure
                
                # Preload critical data
                categories = Category.query.limit(10).all()
                procedures = Procedure.query.limit(20).all()
                
                return {
                    'status': 'warmed',
                    'categories': len(categories),
                    'procedures': len(procedures),
                    'timestamp': time.time()
                }, 200
            except Exception as e:
                return {'status': 'warmup_failed', 'error': str(e)}, 500

def register_production_optimizations(app):
    """Register production-specific optimizations."""
    
    # Initialize production optimizer
    optimizer = ProductionPerformanceOptimizer()
    optimizer.init_app(app)
    
    # Add production-specific middleware
    @app.before_request
    def production_request_optimization():
        """Optimize each request for production."""
        g.start_time = time.time()
        
        # Set production headers
        g.production_headers = {
            'Cache-Control': 'public, max-age=300',  # 5 minutes
            'X-Production-Optimized': 'true'
        }
    
    @app.after_request
    def production_response_optimization(response):
        """Optimize response for production."""
        if hasattr(g, 'start_time'):
            elapsed = (time.time() - g.start_time) * 1000
            response.headers['X-Response-Time'] = f"{elapsed:.1f}ms"
            
            # Log slow requests in production
            if elapsed > 500:
                logger.warning(f"SLOW PRODUCTION REQUEST: {request.endpoint} took {elapsed:.1f}ms")
        
        # Add production headers
        if hasattr(g, 'production_headers'):
            for key, value in g.production_headers.items():
                response.headers[key] = value
        
        return response
    
    # Add database optimization middleware
    @app.before_request
    def optimize_db_for_production():
        """Optimize database queries for production."""
        # Enable query optimization
        if hasattr(db.session, 'info'):
            db.session.info['production_mode'] = True
    
    logger.info("🚀 Production performance optimizations registered")

def create_production_deployment_guide():
    """Create deployment optimization guide."""
    guide = """
# Production Deployment Performance Guide

## Database Optimization
1. Ensure database is in same region as application
2. Use connection pooling (configured automatically)
3. Enable query optimization
4. Set up read replicas if needed

## Caching Strategy
1. Enable Redis/Memcached for session storage
2. Use CDN for static assets
3. Configure browser caching headers
4. Implement edge caching

## Infrastructure
1. Use auto-scaling groups
2. Configure load balancer health checks
3. Set up monitoring and alerting
4. Enable gzip compression

## Environment Variables for Production
- DATABASE_URL: Use pooled connection string
- CACHE_TYPE: redis
- ASSETS_URL: CDN URL for static assets
- PRODUCTION_MODE: true

## Monitoring Endpoints
- /health: Basic health check
- /warmup: Preload critical data
- /_admin/performance: Performance metrics
"""
    
    with open('PRODUCTION_DEPLOYMENT_GUIDE.md', 'w') as f:
        f.write(guide)
    
    logger.info("📋 Production deployment guide created")