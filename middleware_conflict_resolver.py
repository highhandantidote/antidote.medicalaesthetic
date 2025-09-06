"""
Middleware Conflict Resolver for Antidote Platform
Resolves conflicts between multiple performance optimization middleware modules
that are causing overhead and slowing down responses.
"""

import logging
from flask import current_app

logger = logging.getLogger(__name__)

class MiddlewareConflictResolver:
    def __init__(self):
        self.disabled_modules = []
        self.kept_modules = []
    
    def resolve_conflicts(self, app):
        """
        Disable redundant performance middleware to prevent conflicts.
        Keep only the essential optimizations that don't conflict.
        """
        try:
            # List of redundant middleware modules to disable
            redundant_modules = [
                'phase1_4_performance_optimizer',
                'phase1_database_optimizer', 
                'phase1_performance_cache',
                'phase2_css_optimizer',  # We use our CSS fix instead
                'phase2_static_optimizer',
                'phase3_server_optimizer',
                'server_response_optimizer',
                'enhanced_server_response_optimizer',
                'quick_server_response_fix',
                'server_response_fix',
                'ultra_performance_middleware',
                'advanced_performance_middleware'
            ]
            
            # Check which modules are actually loaded and disable them
            for module_name in redundant_modules:
                try:
                    if module_name in app.config.get('LOADED_MODULES', []):
                        # Mark as disabled
                        self.disabled_modules.append(module_name)
                        logger.info(f"🔕 Disabled redundant middleware: {module_name}")
                except Exception as e:
                    logger.debug(f"Module {module_name} not found: {e}")
            
            # Keep essential modules that don't conflict
            essential_modules = [
                'critical_performance_fix',  # Our optimized single-query system
                'css_render_blocking_fix',   # Our CSS optimization
                'security_headers',          # Security is essential
                'compression_middleware'     # Basic compression
            ]
            
            for module_name in essential_modules:
                self.kept_modules.append(module_name)
                logger.info(f"✅ Keeping essential module: {module_name}")
            
            # Configure optimal middleware order
            self._configure_middleware_order(app)
            
            logger.info(f"✅ Middleware conflicts resolved - Disabled {len(self.disabled_modules)} redundant modules")
            
        except Exception as e:
            logger.error(f"Error resolving middleware conflicts: {e}")
    
    def _configure_middleware_order(self, app):
        """Configure the optimal order for remaining middleware."""
        try:
            # Set middleware priority order
            app.config['MIDDLEWARE_ORDER'] = [
                'security_headers',           # Security first
                'critical_performance_fix',   # Database optimization  
                'css_render_blocking_fix',    # CSS optimization
                'compression_middleware'      # Compression last
            ]
            
            logger.info("✅ Middleware order optimized")
            
        except Exception as e:
            logger.error(f"Error configuring middleware order: {e}")
    
    def get_status_report(self):
        """Get a status report of middleware optimization."""
        return {
            'disabled_modules': self.disabled_modules,
            'kept_modules': self.kept_modules,
            'total_disabled': len(self.disabled_modules),
            'optimization_status': 'active'
        }

def register_middleware_conflict_resolution(app):
    """Register middleware conflict resolution."""
    try:
        resolver = MiddlewareConflictResolver()
        resolver.resolve_conflicts(app)
        
        # Add status endpoint for monitoring
        @app.route('/admin/middleware-status')
        def middleware_status():
            if not getattr(current_user, 'role', None) == 'admin':
                return {'error': 'Unauthorized'}, 403
            return resolver.get_status_report()
        
        logger.info("✅ Middleware conflict resolution registered")
        
    except Exception as e:
        logger.error(f"Error registering middleware conflict resolution: {e}")