"""
Optimize Gunicorn configuration for production deployment
This addresses the slow server response times in production.
"""

import os
import multiprocessing

# Production-optimized Gunicorn configuration
def configure_production_gunicorn():
    """Generate optimized gunicorn configuration for production"""
    
    # Detect available CPU cores
    cores = multiprocessing.cpu_count()
    workers = max(2, min(cores * 2 + 1, 8))  # Cap at 8 workers max
    
    config = {
        # Worker configuration
        'workers': workers,
        'threads': 4,  # 4 threads per worker
        'worker_class': 'sync',
        'worker_connections': 1000,
        'max_requests': 2000,  # Restart workers after 2000 requests
        'max_requests_jitter': 200,
        
        # Timeout configuration
        'timeout': 120,  # Increased timeout for slow queries
        'keepalive': 5,
        'graceful_timeout': 60,
        
        # Performance optimizations
        'preload_app': True,  # Preload for better memory usage
        'worker_tmp_dir': '/dev/shm',  # Use shared memory
        
        # Connection settings
        'bind': '0.0.0.0:5000',
        'backlog': 2048,
        
        # Memory management
        'max_worker_memory': 300 * 1024 * 1024,  # 300MB max per worker
        
        # Logging (minimal in production)
        'accesslog': '-',
        'errorlog': '-',
        'access_log_format': '%(h)s "%(r)s" %(s)s %(b)s %(D)s',
        'log_level': 'warning',  # Reduce log verbosity
        
        # Security
        'limit_request_line': 8192,
        'limit_request_fields': 200,
        'limit_request_field_size': 8192,
    }
    
    return config

# Write optimized gunicorn.conf.py
def update_gunicorn_config():
    """Update gunicorn.conf.py with production optimizations"""
    
    config = configure_production_gunicorn()
    
    config_content = f"""# Optimized Gunicorn configuration for production deployment
# Auto-generated for antidote.fit performance optimization

# Worker configuration - optimized for production load
workers = {config['workers']}  # {multiprocessing.cpu_count()} cores detected
threads = {config['threads']}
worker_class = '{config['worker_class']}'
worker_connections = {config['worker_connections']}
max_requests = {config['max_requests']}
max_requests_jitter = {config['max_requests_jitter']}

# Timeout configuration - optimized for database queries
timeout = {config['timeout']}
keepalive = {config['keepalive']}
graceful_timeout = {config['graceful_timeout']}

# Server socket
bind = '{config['bind']}'
backlog = {config['backlog']}

# Performance optimizations
preload_app = {config['preload_app']}
worker_tmp_dir = '{config['worker_tmp_dir']}'

# Memory management
max_worker_memory = {config['max_worker_memory']}

# Logging (minimal for performance)
accesslog = '{config['accesslog']}'
errorlog = '{config['errorlog']}'
access_log_format = '{config['access_log_format']}'
loglevel = '{config['log_level']}'

# Security limits
limit_request_line = {config['limit_request_line']}
limit_request_fields = {config['limit_request_fields']}
limit_request_field_size = {config['limit_request_field_size']}

# Production startup hook
def on_starting(server):
    server.log.info("🚀 Starting antidote.fit production server")
    server.log.info(f"Workers: {config['workers']}, Threads: {config['threads']}")

def on_reload(server):
    server.log.info("🔄 Reloading antidote.fit production server")

def worker_int(worker):
    worker.log.info("🔄 Worker received INT or QUIT signal")

# Performance monitoring
def pre_request(worker, req):
    worker.log.debug(f"Processing: {{req.method}} {{req.path}}")

def post_request(worker, req, environ, resp):
    # Log slow requests only
    if hasattr(req, '_start_time'):
        duration = time.time() - req._start_time
        if duration > 2.0:  # Log requests taking more than 2 seconds
            worker.log.warning(f"SLOW: {{req.method}} {{req.path}} took {{duration:.2f}}s")
"""
    
    return config_content

if __name__ == "__main__":
    # Generate and display optimized configuration
    content = update_gunicorn_config()
    print("Optimized Gunicorn Configuration:")
    print("=" * 50)
    print(content)