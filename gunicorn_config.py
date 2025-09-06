"""
Gunicorn configuration optimized for deployment performance.
Addresses startup timeout and worker configuration issues.
"""
import os
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes (optimized for deployment)
workers = min(4, multiprocessing.cpu_count() * 2 + 1)
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after processing this many requests
max_requests = 1000
max_requests_jitter = 50

# Timeout for graceful workers restart
graceful_timeout = 30

# The maximum time a worker can take to process a request
worker_timeout = 30

# Workers silent for more than this many seconds are killed and restarted
worker_silent_timeout = 60

# Restart workers gracefully after this many seconds - CRITICAL for deployment
preload_app = True

# Enable port reuse for faster startup
reuse_port = True

# Application module
module = "main:app"

# Process naming
proc_name = "antidote_app"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance optimizations
def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info("Worker received SIGINT or SIGQUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info(f"Worker initialized (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info(f"Worker received SIGABRT signal (pid: {worker.pid})")