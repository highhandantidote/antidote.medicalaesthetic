#!/usr/bin/env python3
"""
Simple HTTP server to serve the CSV file for download.
"""

from flask import Flask, send_file, jsonify
import os

app = Flask(__name__)

@app.route('/download-csv')
def download_csv():
    """Serve the CSV file for download."""
    csv_path = 'clinics_import_ready.csv'
    
    if os.path.exists(csv_path):
        return send_file(
            csv_path,
            as_attachment=True,
            download_name='clinics_import_ready.csv',
            mimetype='text/csv'
        )
    else:
        return jsonify({"error": "CSV file not found"}), 404

@app.route('/csv-info')
def csv_info():
    """Show CSV file information."""
    csv_path = 'clinics_import_ready.csv'
    
    if os.path.exists(csv_path):
        file_size = os.path.getsize(csv_path)
        with open(csv_path, 'r') as f:
            line_count = sum(1 for _ in f)
        
        return jsonify({
            "file_exists": True,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "line_count": line_count,
            "clinic_count": line_count - 1,  # Subtract header row
            "download_url": "/download-csv"
        })
    else:
        return jsonify({"error": "CSV file not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)