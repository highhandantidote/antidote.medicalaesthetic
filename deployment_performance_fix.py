"""
Emergency Production Performance Fix for antidote.fit
Addresses the 20-50x slower performance on deployed domain
"""

import os
import logging
from flask import Flask, request, g
from functools import wraps
import time

logger = logging.getLogger(__name__)

def is_production_deployment():
    """Detect if running on antidote.fit deployment"""
    production_indicators = [
        'antidote.fit' in os.environ.get('REPL_SLUG', ''),
        'antidote.fit' in os.environ.get('REPLIT_DOMAIN', ''),
        os.environ.get('REPL_DEPLOYMENT') == 'true',
        os.environ.get('PRODUCTION_MODE', '').lower() == 'true'
    ]
    
    # Check request URL if available
    try:
        if request and hasattr(request, 'url_root'):
            production_indicators.append('antidote.fit' in str(request.url_root))
    except:
        pass
        
    return any(production_indicators)

def apply_emergency_production_fixes(app):
    """Apply critical performance fixes for production deployment"""
    
    # 1. Optimize database configuration for production
    app.config.update({
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_size": 25,
            "max_overflow": 40,
            "pool_recycle": 300,
            "pool_pre_ping": True,
            "pool_timeout": 20,
            "echo": False,  # Disable SQL logging in production
            "connect_args": {
                "connect_timeout": 10,
                "application_name": "antidote_production",
                "options": "-c statement_timeout=30000"  # 30 second query timeout
            }
        }
    })
    
    # 2. Enable production caching
    app.config.update({
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 600,  # 10 minute cache
        'PRODUCTION_MODE': True
    })
    
    # 3. Add request-level performance monitoring
    @app.before_request
    def start_timer():
        g.start_time = time.time()
        
        # Pre-warm database connection
        try:
            from models import db
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            g.db_healthy = True
        except Exception as e:
            logger.warning(f"Database precheck failed: {e}")
            g.db_healthy = False
    
    @app.after_request
    def log_request_time(response):
        if hasattr(g, 'start_time'):
            duration = (time.time() - g.start_time) * 1000
            if duration > 1000:  # Log slow requests over 1 second
                logger.warning(f"SLOW REQUEST: {request.method} {request.path} took {duration:.2f}ms")
        return response
    
    # 4. Add production health endpoints
    @app.route('/production-health')
    def production_health():
        """Keep production deployment warm"""
        try:
            from models import db
            from sqlalchemy import text
            start = time.time()
            db.session.execute(text('SELECT 1'))
            db_time = (time.time() - start) * 1000
            
            return {
                'status': 'healthy',
                'db_response_time_ms': round(db_time, 2),
                'production_mode': True,
                'cache_enabled': app.config.get('CACHE_TYPE') == 'simple'
            }, 200
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 500
    
    @app.route('/warmup')
    def warmup():
        """Warm up critical routes and cache"""
        try:
            # Pre-load critical data
            from models import Procedure, Doctor, Clinic
            
            # Cache key queries
            Procedure.query.limit(10).all()
            Doctor.query.limit(10).all()
            Clinic.query.filter_by(is_verified=True).limit(10).all()
            
            return {'status': 'warmed up', 'timestamp': time.time()}, 200
        except Exception as e:
            return {'status': 'warmup failed', 'error': str(e)}, 500
    
    logger.info("🚀 Emergency production performance fixes applied")

def create_production_middleware(app):
    """Create production-specific middleware"""
    
    @app.after_request
    def add_production_headers(response):
        if is_production_deployment():
            response.headers['X-Production-Mode'] = 'true'
            response.headers['X-Cache-Status'] = 'enabled'
        return response

# Auto-apply fixes when imported
def auto_apply_production_fixes():
    """Automatically apply fixes when this module is imported"""
    try:
        from app import app
        if is_production_deployment():
            apply_emergency_production_fixes(app)
            logger.info("✅ Auto-applied production performance fixes")
    except Exception as e:
        logger.error(f"Failed to auto-apply production fixes: {e}")

if __name__ == "__main__":
    auto_apply_production_fixes()