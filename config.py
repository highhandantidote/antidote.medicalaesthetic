import os

class Config:
    """Base configuration for the application."""
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev_key')
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('SMTP_EMAIL', os.environ.get('MAIL_USERNAME', 'your-email@gmail.com'))
    MAIL_PASSWORD = os.environ.get('SMTP_PASSWORD', os.environ.get('MAIL_PASSWORD', 'your-password'))
    MAIL_DEFAULT_SENDER = os.environ.get('SMTP_EMAIL', os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@antidote.com'))
    
    # File Upload Configuration
    # Set maximum content length to 50MB for face analysis images (50 * 1024 * 1024 bytes)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    
    # SQLAlchemy database configuration - Using Supabase
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Optimized configuration for Supabase connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 600,          # 10 minutes - longer for Supabase pooler
        'pool_pre_ping': True,        # Test connections before use
        'pool_timeout': 60,           # 60 seconds - more time for Supabase pooler
        'pool_size': 10,              # Larger pool for concurrent requests
        'max_overflow': 15,           # Higher overflow for traffic spikes
        'connect_args': {
            'sslmode': 'require',     # Require SSL for Supabase connections
            'sslcert': None,          # Disable client certificates
            'sslkey': None,           # Disable client keys
            'sslrootcert': None,      # Use system CA certificates
            'connect_timeout': 30,    # 30 seconds for initial connection
            'application_name': 'antidote_flask_app',  # Connection tracking
            'keepalives_idle': 600,   # Keep connections alive
            'keepalives_interval': 30,
            'keepalives_count': 3
        }
    }
    
    # Debug configuration
    DEBUG = True
