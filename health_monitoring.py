"""
Health monitoring endpoints for deployment and production monitoring.
Provides comprehensive health checks, metrics, and status information.
"""
import os
import sys
import time
from datetime import datetime
from flask import Blueprint, jsonify, request, Response
import logging

# Try to import psutil, but don't fail if it's not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)

# Create blueprint for health monitoring
health_bp = Blueprint('health_monitoring', __name__)

class HealthMonitor:
    def __init__(self):
        self.start_time = time.time()
        
    def get_system_metrics(self):
        """Get system resource metrics."""
        if not PSUTIL_AVAILABLE:
            return {
                'cpu_percent': 'unavailable',
                'memory_percent': 'unavailable',
                'disk_percent': 'unavailable',
            }
        try:
            if psutil is not None:
                return {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                }
            else:
                return {
                    'cpu_percent': 'unavailable',
                    'memory_percent': 'unavailable',
                    'disk_percent': 'unavailable',
                }
        except Exception:
            return {
                'cpu_percent': 'error',
                'memory_percent': 'error',
                'disk_percent': 'error',
            }
    
    def get_uptime(self):
        """Get application uptime in seconds."""
        return time.time() - self.start_time
        
    def get_environment_info(self):
        """Get deployment environment information."""
        return {
            'python_version': sys.version,
            'flask_env': os.environ.get('FLASK_ENV', 'development'),
            'debug_mode': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
            'port': os.environ.get('PORT', '5000'),
        }

# Global health monitor instance
monitor = HealthMonitor()

@health_bp.route('/health/detailed')
def detailed_health():
    """Detailed health check with system metrics."""
    try:
        health_data = {
            'status': 'healthy',
            'service': 'antidote',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': monitor.get_uptime(),
            'system_metrics': monitor.get_system_metrics(),
            'environment': monitor.get_environment_info(),
        }
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/health/quick')
def quick_health():
    """Quick health check for load balancers."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@health_bp.route('/metrics')
def metrics():
    """Prometheus-style metrics endpoint."""
    try:
        uptime = monitor.get_uptime()
        metrics_data = monitor.get_system_metrics()
        
        metrics_text = f"""# HELP antidote_uptime_seconds Application uptime in seconds
# TYPE antidote_uptime_seconds counter
antidote_uptime_seconds {uptime}

# HELP antidote_cpu_percent CPU usage percentage
# TYPE antidote_cpu_percent gauge
antidote_cpu_percent {metrics_data['cpu_percent']}

# HELP antidote_memory_percent Memory usage percentage
# TYPE antidote_memory_percent gauge
antidote_memory_percent {metrics_data['memory_percent']}

# HELP antidote_disk_percent Disk usage percentage
# TYPE antidote_disk_percent gauge
antidote_disk_percent {metrics_data['disk_percent']}
"""
        
        return Response(metrics_text, mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return f"# Error: {str(e)}", 503

def register_health_monitoring(app):
    """Register health monitoring blueprint with the app."""
    app.register_blueprint(health_bp)
    logger.info("✅ Health monitoring endpoints registered")
    return health_bp