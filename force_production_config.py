"""
Force Production Configuration
This ensures that production optimizations are applied regardless of detection issues.
"""

import os
import logging
from flask import Flask

logger = logging.getLogger(__name__)

def force_production_optimizations(app):
    """Force production optimizations for antidote.fit deployment"""
    
    logger.info("🔧 Forcing production optimizations for antidote.fit")
    
    # Force production mode
    app.config['PRODUCTION_MODE'] = True
    
    # Force optimized database configuration
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_size": 30,
        "max_overflow": 50,
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 20,
        "echo": False,
        "connect_args": {
            "connect_timeout": 10,
            "application_name": "antidote_production_forced",
            "options": "-c statement_timeout=30s -c idle_in_transaction_session_timeout=60s"
        }
    }
    
    # Force caching configuration
    app.config.update({
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 600,
        'SEND_FILE_MAX_AGE_DEFAULT': 31536000,
    })
    
    # Add forced health endpoint
    @app.route('/forced-production-status')
    def forced_production_status():
        """Check forced production configuration"""
        return {
            'forced_production': True,
            'pool_size': app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_size'),
            'cache_type': app.config.get('CACHE_TYPE'),
            'production_mode': app.config.get('PRODUCTION_MODE'),
            'engine_options': app.config.get('SQLALCHEMY_ENGINE_OPTIONS')
        }
    
    logger.info("✅ Production optimizations forced - pool_size=30, cache=simple")
    
    return app

def register_forced_production_config(app):
    """Register forced production configuration"""
    force_production_optimizations(app)
    return app