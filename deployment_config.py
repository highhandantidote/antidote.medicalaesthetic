"""
Deployment configuration for better startup performance and compatibility.
"""
import os
import logging

logger = logging.getLogger(__name__)

class DeploymentConfig:
    """Configuration optimized for deployment environments."""
    
    # Database configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 5,  # Reduced pool size for faster startup
        "max_overflow": 10,
        "pool_timeout": 30,
        "echo": False,  # Disable SQL logging in production
    }
    
    # Session configuration
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Performance settings
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year cache for static files
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Deployment specific settings
    SERVER_NAME = None  # Allow any host
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'https'
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def configure_app(app):
        """Apply deployment configuration to Flask app."""
        logger.info("Applying deployment configuration...")
        
        # Apply database configuration
        app.config.update(DeploymentConfig.SQLALCHEMY_ENGINE_OPTIONS)
        
        # Configure session settings
        app.config['SESSION_COOKIE_SECURE'] = DeploymentConfig.SESSION_COOKIE_SECURE
        app.config['SESSION_COOKIE_HTTPONLY'] = DeploymentConfig.SESSION_COOKIE_HTTPONLY
        app.config['SESSION_COOKIE_SAMESITE'] = DeploymentConfig.SESSION_COOKIE_SAMESITE
        
        # Configure performance settings
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = DeploymentConfig.SEND_FILE_MAX_AGE_DEFAULT
        app.config['MAX_CONTENT_LENGTH'] = DeploymentConfig.MAX_CONTENT_LENGTH
        
        # Configure deployment settings
        app.config['SERVER_NAME'] = DeploymentConfig.SERVER_NAME
        app.config['APPLICATION_ROOT'] = DeploymentConfig.APPLICATION_ROOT
        app.config['PREFERRED_URL_SCHEME'] = DeploymentConfig.PREFERRED_URL_SCHEME
        
        # Set up logging level
        logging.getLogger().setLevel(getattr(logging, DeploymentConfig.LOG_LEVEL))
        
        # Ensure the app can bind to any host
        if not hasattr(app, '_deployment_configured'):
            app.config['SERVER_NAME'] = None
            app._deployment_configured = True
        
        logger.info("✅ Deployment configuration applied successfully")
        return app