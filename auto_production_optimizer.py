"""
Auto Production Optimizer
Automatically detects production environment and activates optimizations
without requiring manual environment variable configuration.
"""

import os
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def is_production_environment():
    """
    Automatically detect if we're in production based on various indicators.
    """
    # Check common production indicators
    indicators = [
        # Domain-based detection
        'antidote.fit' in os.environ.get('REPL_SLUG', ''),
        'antidote.fit' in os.environ.get('REPLIT_DOMAIN', ''),
        
        # Replit deployment indicators
        os.environ.get('REPL_DEPLOYMENT') == 'true',
        os.environ.get('REPL_ENVIRONMENT') == 'production',
        
        # Manual override
        os.environ.get('PRODUCTION_MODE', '').lower() == 'true',
        
        # Domain detection from server name
        'antidote.fit' in os.environ.get('SERVER_NAME', ''),
        
        # Check if we're not in development
        not os.environ.get('FLASK_ENV') == 'development',
        not os.environ.get('FLASK_DEBUG') == '1'
    ]
    
    return any(indicators)

def auto_configure_production(app):
    """
    Automatically configure production optimizations without manual setup.
    """
    if is_production_environment():
        logger.info("🚀 Production environment detected - auto-configuring optimizations")
        
        # Set production configuration automatically
        app.config.update({
            'PRODUCTION_MODE': True,
            'CACHE_TYPE': 'simple',
            'CACHE_DEFAULT_TIMEOUT': 600,
            'SEND_FILE_MAX_AGE_DEFAULT': 31536000,  # 1 year for static files
        })
        
        # Optimize database for production
        if 'SQLALCHEMY_ENGINE_OPTIONS' not in app.config:
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
        
        app.config['SQLALCHEMY_ENGINE_OPTIONS'].update({
            'pool_size': 20,
            'max_overflow': 30,
            'pool_recycle': 300,
            'pool_pre_ping': True,
            'pool_timeout': 30,
        })
        
        logger.info("✅ Production optimizations auto-configured")
        return True
    else:
        logger.info("🔧 Development environment detected - using development settings")
        return False

def register_auto_production_optimizer(app):
    """
    Register automatic production optimization that works without manual configuration.
    """
    
    # Auto-configure based on environment detection
    is_prod = auto_configure_production(app)
    
    if is_prod:
        # Add production-specific routes
        @app.route('/deployment-status')
        def deployment_status():
            """Check if production optimizations are active."""
            return {
                'production_mode': True,
                'auto_configured': True,
                'cache_enabled': app.config.get('CACHE_TYPE') == 'simple',
                'db_pool_size': app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_size', 'default'),
                'domain_detected': 'antidote.fit'
            }, 200
        
        # Add warmup endpoint for production
        @app.route('/auto-warmup')
        def auto_warmup():
            """Auto warmup for production."""
            try:
                from models import Category, Procedure
                categories = Category.query.limit(5).all()
                procedures = Procedure.query.limit(10).all()
                
                return {
                    'status': 'warmed',
                    'production_auto': True,
                    'categories_loaded': len(categories),
                    'procedures_loaded': len(procedures)
                }, 200
            except Exception as e:
                return {'status': 'warmup_failed', 'error': str(e)}, 500
    
    logger.info(f"🎯 Auto production optimizer registered (Production: {is_prod})")