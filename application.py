#!/usr/bin/env python3
"""
AWS Elastic Beanstalk WSGI Entry Point for Antidote Platform

This file serves as the main entry point for AWS Elastic Beanstalk deployment.
Elastic Beanstalk looks for 'application' variable in application.py.
"""

import os
import sys
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging for AWS deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

try:
    # Import the Flask app from your existing structure
    from app import create_app
    
    # Create the application instance
    application = create_app()
    
    # AWS Elastic Beanstalk expects the variable to be named 'application'
    app = application
    
    logger.info("✅ Antidote Flask application successfully initialized for AWS Elastic Beanstalk")
    
    # Health check endpoint for AWS Load Balancer
    @application.route('/health')
    def health_check():
        """AWS Load Balancer health check endpoint"""
        return {'status': 'healthy', 'service': 'antidote-platform'}, 200
    
    # Application info endpoint
    @application.route('/info')
    def app_info():
        """Application information for monitoring"""
        return {
            'service': 'antidote-platform',
            'version': '1.0.0',
            'environment': os.environ.get('FLASK_ENV', 'production'),
            'status': 'running'
        }, 200

except Exception as e:
    logger.error(f"❌ Failed to initialize Flask application: {e}")
    raise

if __name__ == "__main__":
    # For local testing and DigitalOcean App Platform
    port = int(os.environ.get('PORT', 8080))
    application.run(host='0.0.0.0', port=port, debug=False)