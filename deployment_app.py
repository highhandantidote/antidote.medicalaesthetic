import os
import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

def create_app():
    """Create a deployment-safe Flask application."""
    app = Flask(__name__)
    
    # Essential configuration only
    app.secret_key = os.environ.get("SESSION_SECRET", "deployment_secret_key")
    
    # Database configuration
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20
        }
    
    # Disable debug mode for production
    app.config["DEBUG"] = False
    app.config["TESTING"] = False
    
    # Use ProxyFix for proper URL generation behind proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize database
    db.init_app(app)
    
    # Health check endpoint for readiness probe
    @app.route('/health')
    def health_check():
        """Health check endpoint for deployment readiness probe."""
        return jsonify({
            "status": "healthy",
            "message": "Antidote app is running"
        }), 200
    
    # Basic root endpoint
    @app.route('/')
    def home():
        """Basic home endpoint."""
        return jsonify({
            "message": "Antidote Medical Aesthetic Marketplace",
            "status": "running"
        })
    
    # Try to import and register main routes safely
    try:
        import routes
        logger.info("✅ Main routes imported successfully")
    except ImportError as e:
        logger.warning(f"Main routes not available: {e}")
        
        # Fallback route if main routes fail
        @app.route('/api/status')
        def api_status():
            return jsonify({"status": "API available", "mode": "minimal"})
    
    # Create database tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Database tables created/verified")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    logger.info("✅ Deployment-safe Flask app created successfully")
    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    # For local development only
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=False)