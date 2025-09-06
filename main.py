from app import create_app
import os

# Create the Flask application
app = create_app()

# Configure for deployment
if __name__ == "__main__":
    # For deployment, let gunicorn handle the server
    # This is only for local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
