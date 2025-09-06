#!/usr/bin/env python3
"""
Debug application to isolate and fix issues with the main application.
"""
import os
from flask import Flask, jsonify

# Create a simple app for debugging
app = Flask(__name__)

@app.route('/')
def index():
    """Simple index route for debugging."""
    return jsonify({"status": "ok", "message": "Debug application is running"})

@app.route('/test')
def test():
    """Test database connection."""
    import psycopg2
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM doctors")
        doctor_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({"status": "ok", "doctor_count": doctor_count})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)