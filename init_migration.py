#!/usr/bin/env python3
"""
Initialize Flask-Migrate for the application.
"""
from flask_migrate import Migrate, init
from app import create_app, db

def main():
    """Initialize the migration repository."""
    app = create_app()
    migrate = Migrate(app, db)
    
    with app.app_context():
        init()
    
    print("Migration repository initialized successfully.")

if __name__ == "__main__":
    main()