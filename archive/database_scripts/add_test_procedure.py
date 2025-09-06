from app import create_app, db
from models import BodyPart, Category, Procedure
from datetime import datetime

def add_test_procedure():
    """Add a test procedure (Rhinoplasty) to the database."""
    app = create_app()
    with app.app_context():
        # Check if the procedure already exists
        existing = Procedure.query.filter_by(procedure_name="Rhinoplasty").first()
        if existing:
            print("Test procedure 'Rhinoplasty' already exists with ID:", existing.id)
            return existing.id
        
        # Create body part if it doesn't exist
        body_part = BodyPart.query.filter_by(name="Face").first()
        if not body_part:
            body_part = BodyPart(
                name="Face",
                description="Facial procedures including nose, eyes, and facial contouring",
                created_at=datetime.utcnow()
            )
            db.session.add(body_part)
            db.session.flush()  # Get the ID without committing
            print("Created body part 'Face' with ID:", body_part.id)
        
        # Create category if it doesn't exist
        category = Category.query.filter_by(name="Nose").first()
        if not category:
            category = Category(
                name="Nose",
                description="Procedures involving nasal reconstruction and reshaping",
                body_part_id=body_part.id,
                created_at=datetime.utcnow()
            )
            db.session.add(category)
            db.session.flush()  # Get the ID without committing
            print("Created category 'Nose' with ID:", category.id)
        
        # Create the test procedure
        procedure = Procedure(
            procedure_name="Rhinoplasty",
            short_description="Reshapes the nose for improved appearance and function",
            overview="Rhinoplasty is a surgical procedure that changes the shape or size of the nose, or improves its function.",
            procedure_details="During rhinoplasty, the surgeon makes incisions to access the bones and cartilage that support the nose.",
            ideal_candidates="Good candidates include those with breathing problems, those unhappy with the appearance of their nose, and those with realistic expectations.",
            recovery_process="Recovery from rhinoplasty typically involves swelling, bruising, and discomfort that gradually subsides.",
            recovery_time="1-2 weeks",
            results_duration="Permanent",
            min_cost=350000,
            max_cost=1050000,
            benefits="Improved appearance, better breathing, enhanced self-confidence",
            benefits_detailed=["Improved nasal appearance", "Corrected breathing difficulties", "Enhanced facial harmony", "Boosted self-confidence"],
            risks="Bleeding, infection, adverse reaction to anesthesia, unsatisfactory results requiring revision",
            procedure_types="Open Rhinoplasty, Closed Rhinoplasty, Revision Rhinoplasty",
            alternative_procedures="Non-surgical rhinoplasty using fillers",
            category_id=category.id,
            created_at=datetime.utcnow()
        )
        db.session.add(procedure)
        db.session.commit()
        print("Added test procedure 'Rhinoplasty' with ID:", procedure.id)
        return procedure.id

if __name__ == "__main__":
    add_test_procedure()