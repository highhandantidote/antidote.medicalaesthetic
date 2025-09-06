#!/usr/bin/env python3
"""
Custom entry point for Gunicorn with larger request size limits.
This file serves as a wrapper around the main Flask application to
configure Gunicorn with settings optimized for handling larger uploads.
"""

import os
import sys
import subprocess

def run_with_large_request_limit():
    """
    Run the Gunicorn server with increased request size limits.
    """
    # Gunicorn command with parameters to allow larger request sizes
    cmd = [
        "gunicorn",
        "--bind", "0.0.0.0:5000",
        "--reuse-port",
        "--reload",
        "--limit-request-line", "0",     # No limit on request line size
        "--limit-request-fields", "0",   # No limit on number of header fields
        "--limit-request-field-size", "0", # No limit on header field size
        "main:app"
    ]
    
    # Execute the command
    process = subprocess.Popen(cmd)
    
    try:
        # Wait for the process to complete
        process.wait()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        process.terminate()
        process.wait()
        print("Server stopped")
        
if __name__ == "__main__":
    run_with_large_request_limit()