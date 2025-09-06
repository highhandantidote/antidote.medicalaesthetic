"""
Add helpful_count and reported fields to the Review model.
"""
from app import create_app, db
from models import Review
from sqlalchemy import text

# Create the Flask application
app = create_app()

def add_review_fields():
    """Add helpful_count and reported fields to the reviews table."""
    with app.app_context():
        # Create a connection to the database
        with db.engine.connect() as conn:
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")
            
            # Check if the helpful_count column already exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'reviews'
                AND column_name = 'helpful_count'
            """))
            
            # If the column doesn't exist, add it
            helpful_exists = bool(result.fetchone())
            if not helpful_exists:
                print("Adding helpful_count field to reviews table...")
                conn.execute(text("""
                    ALTER TABLE reviews
                    ADD COLUMN helpful_count INTEGER DEFAULT 0
                """))
            else:
                print("helpful_count field already exists in reviews table.")
            
            # Check if the reported column already exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'reviews'
                AND column_name = 'reported'
            """))
            
            # If the column doesn't exist, add it
            reported_exists = bool(result.fetchone())
            if not reported_exists:
                print("Adding reported field to reviews table...")
                conn.execute(text("""
                    ALTER TABLE reviews
                    ADD COLUMN reported BOOLEAN DEFAULT FALSE
                """))
            else:
                print("reported field already exists in reviews table.")
            
        print("Database migration completed successfully.")
        
        # Verify that the model and database are in sync
        if helpful_exists and reported_exists:
            print("Database already contains both fields.")
        elif helpful_exists or reported_exists:
            print("Database partially migrated, new fields added successfully.")
        else:
            print("Database successfully migrated with new fields.")

if __name__ == "__main__":
    add_review_fields()