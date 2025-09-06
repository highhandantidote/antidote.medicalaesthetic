"""
Simple Flask application for testing the database and doctor display.
This is a minimalist version to isolate problems.
"""
import os
import logging
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a simple app
app = Flask(__name__)

@app.route('/')
def index():
    """Simple index route."""
    return jsonify({"status": "ok", "message": "Simple app is running"})

@app.route('/doctors')
def doctors():
    """Get a simple list of doctors."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    try:
        # Connect to the database
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get a very limited set of doctor data
        cursor.execute("""
            SELECT id, name, city, specialty 
            FROM doctors 
            ORDER BY rating DESC NULLS LAST
            LIMIT 10
        """)
        
        doctors_data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert to a list of dictionaries for JSON
        doctors_list = [dict(doctor) for doctor in doctors_data]
        
        return jsonify({
            "status": "ok", 
            "count": len(doctors_list), 
            "doctors": doctors_list
        })
        
    except Exception as e:
        logger.error(f"Error fetching doctors: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)