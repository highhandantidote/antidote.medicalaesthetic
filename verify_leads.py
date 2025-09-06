"""
Verify leads in the database.
"""
from main import app
from app import db
from sqlalchemy import text
from models import Lead

def verify_leads():
    """Verify leads in the database."""
    with app.app_context():
        leads = db.session.execute(text("SELECT * FROM leads")).fetchall()
        print(f"Found {len(leads)} leads in the database:")
        for lead in leads:
            print(f"Lead ID: {lead.id}, Patient: {lead.patient_name}, Procedure: {lead.procedure_name}, Source: {lead.source}")
            
        # Alternative approach using the ORM
        print("\nVerifying leads using ORM:")
        orm_leads = db.session.query(Lead).all()
        for lead in orm_leads:
            print(f"Lead ID: {lead.id}, Patient: {lead.patient_name}, Doctor ID: {lead.doctor_id}")

if __name__ == "__main__":
    verify_leads()