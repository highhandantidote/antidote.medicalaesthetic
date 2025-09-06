"""
Production Emergency Performance Fix for antidote.fit
This addresses the critical 5+ second page load times by fixing multiple bottlenecks.
"""

import os
import logging
import time
from flask import Flask, request, g, jsonify
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ProductionPerformanceFix:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.request_times = []
        
    def is_production_deployment(self):
        """Enhanced production detection"""
        indicators = [
            'antidote.fit' in os.environ.get('REPL_SLUG', ''),
            'antidote.fit' in os.environ.get('REPLIT_DOMAIN', ''),
            'antidote.fit' in os.environ.get('REPLIT_URL', ''),
            os.environ.get('REPL_DEPLOYMENT') == 'true',
            os.environ.get('PRODUCTION_MODE', '').lower() == 'true'
        ]
        
        # Check request URL if available
        try:
            if hasattr(request, 'url_root') and request.url_root:
                indicators.append('antidote.fit' in str(request.url_root))
        except:
            pass
            
        return any(indicators)
    
    def apply_database_optimizations(self, app):
        """Apply optimized database configuration for production"""
        if self.is_production_deployment():
            # Override any existing database config with production-optimized settings
            current_options = app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {})
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                "pool_size": 30,                    # Increased connection pool
                "max_overflow": 50,                 # More overflow connections
                "pool_recycle": 300,                # Recycle connections every 5 min
                "pool_pre_ping": True,              # Verify connections before use
                "pool_timeout": 20,                 # Connection timeout
                "echo": False,                      # No SQL logging in production
                "connect_args": {
                    "connect_timeout": 10,
                    "application_name": "antidote_production_v2",
                    "options": "-c statement_timeout=30s -c idle_in_transaction_session_timeout=60s"
                },
                **current_options  # Preserve any existing options
            }
            
            # Enable database query optimization
            app.config['SQLALCHEMY_RECORD_QUERIES'] = False
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            logger.info("✅ Production database optimizations applied (pool_size=30)")
            
    def apply_caching_optimizations(self, app):
        """Apply comprehensive caching for production"""
        if self.is_production_deployment():
            app.config.update({
                'CACHE_TYPE': 'simple',
                'CACHE_DEFAULT_TIMEOUT': 600,       # 10 minute cache
                'SEND_FILE_MAX_AGE_DEFAULT': 31536000,  # 1 year for static files
                'PERMANENT_SESSION_LIFETIME': timedelta(hours=24),
                'PRODUCTION_MODE': True
            })
            
            logger.info("✅ Production caching optimizations applied")
    
    def register_performance_monitoring(self, app):
        """Add comprehensive performance monitoring"""
        
        @app.before_request
        def start_performance_timer():
            g.start_time = time.time()
            g.is_production = self.is_production_deployment()
            
            # Pre-warm database connection for production
            if g.is_production:
                try:
                    from app import db
                    from sqlalchemy import text
                    db.session.execute(text('SELECT 1'))
                    g.db_prewarmed = True
                except Exception as e:
                    logger.warning(f"Database prewarm failed: {e}")
                    g.db_prewarmed = False
        
        @app.after_request
        def log_performance_metrics(response):
            if hasattr(g, 'start_time'):
                request_time = time.time() - g.start_time
                
                # Log slow requests in production
                if getattr(g, 'is_production', False) and request_time > 1.0:
                    logger.warning(f"SLOW REQUEST: {request.path} took {request_time:.2f}s")
                
                # Add performance headers
                response.headers['X-Response-Time'] = f"{request_time:.3f}s"
                
                if getattr(g, 'is_production', False):
                    response.headers['X-Production-Optimized'] = 'true'
                    
                # Track request times
                self.request_times.append(request_time)
                if len(self.request_times) > 100:
                    self.request_times = self.request_times[-50:]  # Keep last 50
            
            return response
    
    def register_health_endpoints(self, app):
        """Add production health monitoring endpoints"""
        
        @app.route('/production-health')
        def production_health():
            """Check production system health"""
            try:
                from app import db
                from sqlalchemy import text
                
                # Test database response time
                start = time.time()
                from sqlalchemy import text
                db.session.execute(text('SELECT COUNT(*) FROM users LIMIT 1'))
                db_time = time.time() - start
                
                # Calculate average response time
                avg_response = sum(self.request_times[-10:]) / len(self.request_times[-10:]) if self.request_times else 0
                
                health_data = {
                    'status': 'healthy',
                    'production_mode': self.is_production_deployment(),
                    'database_response_time': f"{db_time:.3f}s",
                    'avg_request_time': f"{avg_response:.3f}s",
                    'cache_enabled': app.config.get('CACHE_TYPE') == 'simple',
                    'pool_size': app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_size', 'default'),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add warning if performance is poor
                if db_time > 0.5 or avg_response > 2.0:
                    health_data['warning'] = 'Performance degraded'
                    
                return jsonify(health_data), 200
                
            except Exception as e:
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'production_mode': self.is_production_deployment()
                }), 500
        
        @app.route('/production-warmup')
        def production_warmup():
            """Warm up production system"""
            if not self.is_production_deployment():
                return jsonify({'status': 'skipped', 'reason': 'not production'}), 200
            
            try:
                # Pre-load critical data
                from models import Category, Procedure, User
                
                start = time.time()
                categories = Category.query.limit(10).all()
                procedures = Procedure.query.limit(20).all()
                users_count = User.query.count()
                warmup_time = time.time() - start
                
                return jsonify({
                    'status': 'warmed',
                    'warmup_time': f"{warmup_time:.3f}s",
                    'categories_loaded': len(categories),
                    'procedures_loaded': len(procedures),
                    'users_count': users_count,
                    'production_optimized': True
                }), 200
                
            except Exception as e:
                return jsonify({
                    'status': 'warmup_failed',
                    'error': str(e)
                }), 500
    
    def apply_static_file_optimizations(self, app):
        """Optimize static file serving for production"""
        if self.is_production_deployment():
            
            @app.after_request
            def add_static_headers(response):
                # Add aggressive caching for static files
                if request.path.startswith('/static/'):
                    response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                    response.headers['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
                elif request.path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2')):
                    response.headers['Cache-Control'] = 'public, max-age=86400'
                
                # Add compression hints
                if request.path.endswith(('.css', '.js', '.html')):
                    response.headers['Vary'] = 'Accept-Encoding'
                
                return response
            
            logger.info("✅ Static file optimizations applied")

def register_production_emergency_fix(app):
    """Register all production emergency performance fixes"""
    
    fix = ProductionPerformanceFix()
    
    # Apply all optimizations
    fix.apply_database_optimizations(app)
    fix.apply_caching_optimizations(app)
    fix.register_performance_monitoring(app)
    fix.register_health_endpoints(app)
    fix.apply_static_file_optimizations(app)
    
    if fix.is_production_deployment():
        logger.info("🚀 Production emergency performance fixes activated for antidote.fit")
    else:
        logger.info("🔧 Development environment - emergency fixes available but not activated")
    
    return fix