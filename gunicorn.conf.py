# Production-optimized Gunicorn configuration for antidote.fit
# Optimized for handling high traffic and database-heavy operations

# Worker configuration - optimized for production load
workers = 6  # 8 cores detected, using optimal worker count
threads = 4
worker_class = 'sync'
worker_connections = 1000
max_requests = 2000
max_requests_jitter = 200

# Timeout configuration - optimized for database queries
timeout = 120  # Increased timeout for complex queries
keepalive = 5
graceful_timeout = 60

# Server socket
bind = '0.0.0.0:5000'
backlog = 2048

# Performance optimizations
preload_app = True  # Enable preload for better memory usage
worker_tmp_dir = '/dev/shm'

# Memory management
max_worker_memory = 314572800  # 300MB max per worker

# Logging (minimal for performance)
accesslog = '-'
errorlog = '-'
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)s'
loglevel = 'warning'

# Security limits - optimized for medical platform
limit_request_line = 8192
limit_request_fields = 200
limit_request_field_size = 8192

# Production startup hook
def on_starting(server):
    server.log.info("🚀 Starting antidote.fit production server")
    server.log.info("Workers: 6, Threads: 4")

def on_reload(server):
    server.log.info("🔄 Reloading antidote.fit production server")

def worker_int(worker):
    worker.log.info("🔄 Worker received INT or QUIT signal")