#!/usr/bin/env python
"""
Procedure import summary
"""
import os
import psycopg2

def get_db_connection():
    """Get a connection to the database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    return conn

def show_import_summary():
    """Show a summary of the procedure import."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Count body parts
            cursor.execute("SELECT COUNT(*) FROM body_parts")
            body_part_count = cursor.fetchone()[0]
            print(f"Body Parts: {body_part_count}")
            
            # Count categories
            cursor.execute("SELECT COUNT(*) FROM categories")
            category_count = cursor.fetchone()[0]
            print(f"Categories: {category_count}")
            
            # Count procedures
            cursor.execute("SELECT COUNT(*) FROM procedures")
            procedure_count = cursor.fetchone()[0]
            print(f"Procedures: {procedure_count}")
            
            # Sample of procedures
            cursor.execute("SELECT procedure_name FROM procedures ORDER BY id DESC LIMIT 5")
            recent_procedures = [row[0] for row in cursor.fetchall()]
            print(f"Recent procedures: {', '.join(recent_procedures)}")
            
            # Count procedures by body part
            cursor.execute("""
                SELECT body_part, COUNT(*) 
                FROM procedures 
                GROUP BY body_part 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            """)
            procedures_by_body_part = cursor.fetchall()
            print("\nProcedures by Body Part (Top 10):")
            for body_part, count in procedures_by_body_part:
                print(f"  - {body_part}: {count}")
            
            print("\nImport Summary Complete!")

if __name__ == "__main__":
    show_import_summary()