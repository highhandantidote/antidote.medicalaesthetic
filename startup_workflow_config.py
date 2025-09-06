"""
Startup workflow configuration for optimized deployment.
Configures Gunicorn and worker settings for fast startup.
"""
import os
import multiprocessing

# Gunicorn configuration for deployment optimization
def configure_gunicorn_for_deployment():
    """Configure environment variables for optimized Gunicorn startup."""
    
    # Worker configuration
    os.environ.setdefault('GUNICORN_WORKERS', str(min(4, multiprocessing.cpu_count() * 2 + 1)))
    os.environ.setdefault('GUNICORN_TIMEOUT', '30')
    os.environ.setdefault('GUNICORN_KEEPALIVE', '2')
    os.environ.setdefault('GUNICORN_MAX_REQUESTS', '1000')
    os.environ.setdefault('GUNICORN_MAX_REQUESTS_JITTER', '50')
    
    # Performance settings
    os.environ.setdefault('GUNICORN_PRELOAD', 'true')
    os.environ.setdefault('GUNICORN_WORKER_CLASS', 'sync')
    os.environ.setdefault('GUNICORN_WORKER_CONNECTIONS', '1000')
    
    # Deployment-specific settings
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('PYTHONUNBUFFERED', '1')
    os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
    
    # Database connection settings for faster startup
    if 'DATABASE_URL' in os.environ:
        # Ensure connection string has optimal parameters
        db_url = os.environ['DATABASE_URL']
        if '?' not in db_url:
            os.environ['DATABASE_URL'] = f"{db_url}?sslmode=require&connect_timeout=10"
    
    return {
        'bind': '0.0.0.0:5000',
        'workers': int(os.environ.get('GUNICORN_WORKERS', 4)),
        'timeout': int(os.environ.get('GUNICORN_TIMEOUT', 30)),
        'keepalive': int(os.environ.get('GUNICORN_KEEPALIVE', 2)),
        'max_requests': int(os.environ.get('GUNICORN_MAX_REQUESTS', 1000)),
        'max_requests_jitter': int(os.environ.get('GUNICORN_MAX_REQUESTS_JITTER', 50)),
        'preload_app': os.environ.get('GUNICORN_PRELOAD', 'true').lower() == 'true',
        'worker_class': os.environ.get('GUNICORN_WORKER_CLASS', 'sync'),
        'worker_connections': int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000)),
    }

def get_startup_command():
    """Get the optimized Gunicorn startup command."""
    config = configure_gunicorn_for_deployment()
    
    command_parts = [
        'gunicorn',
        '--bind', config['bind'],
        '--workers', str(config['workers']),
        '--timeout', str(config['timeout']),
        '--keepalive', str(config['keepalive']),
        '--max-requests', str(config['max_requests']),
        '--max-requests-jitter', str(config['max_requests_jitter']),
        '--worker-class', config['worker_class'],
        '--worker-connections', str(config['worker_connections']),
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info',
        '--reuse-port',
        '--reload' if os.environ.get('FLASK_ENV') == 'development' else '--no-reload',
    ]
    
    if config['preload_app']:
        command_parts.append('--preload')
    
    command_parts.append('main:app')
    
    return ' '.join(command_parts)

def optimize_environment_for_startup():
    """Optimize environment variables for fast startup."""
    
    # Python optimization
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['PYTHONHASHSEED'] = 'random'
    
    # Flask optimization
    os.environ.setdefault('FLASK_SKIP_DOTENV', '1')  # Skip .env loading in production
    
    # Database optimization
    os.environ.setdefault('SQLALCHEMY_POOL_SIZE', '5')
    os.environ.setdefault('SQLALCHEMY_MAX_OVERFLOW', '10')
    os.environ.setdefault('SQLALCHEMY_POOL_TIMEOUT', '30')
    os.environ.setdefault('SQLALCHEMY_POOL_RECYCLE', '300')
    
    # Performance optimization
    os.environ.setdefault('WTF_CSRF_TIME_LIMIT', '3600')  # 1 hour
    os.environ.setdefault('PERMANENT_SESSION_LIFETIME', '86400')  # 24 hours
    
    return True

if __name__ == "__main__":
    # Configure for deployment
    configure_gunicorn_for_deployment()
    optimize_environment_for_startup()
    
    print("Startup configuration:")
    print(f"Command: {get_startup_command()}")
    print("Environment optimized for deployment")