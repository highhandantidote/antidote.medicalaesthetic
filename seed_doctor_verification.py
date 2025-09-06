#!/usr/bin/env python3
"""
Script to add sample data for doctor verification workflow testing
"""
import os
import sys
import random
import string
from datetime import datetime

# Add the current directory to path so Python can find the modules
sys.path.append('.')  

from app import create_app, db
from models import User, Doctor, Community

def generate_random_name():
    """Generate a random doctor name"""
    first_names = [
        "Anil", "Priya", "Rahul", "Sneha", "Vikram", "Ananya", "Amit", "Divya", 
        "Rajesh", "Kavita", "Sanjay", "Meena", "Deepak", "Neha", "Sanjay", "Pooja",
        "Vivek", "Ritu", "Nitin", "Swati", "Rakesh", "Anjali", "Sunil", "Kiran"
    ]
    last_names = [
        "Sharma", "Patel", "Singh", "Reddy", "Kumar", "Gupta", "Joshi", "Verma",
        "Agarwal", "Chakraborty", "Mehta", "Bhat", "Nair", "Rao", "Malik", "Das",
        "Khanna", "Shah", "Kapoor", "Jain", "Chopra", "Iyer", "Bose", "Banerjee"
    ]
    return f"Dr. {random.choice(first_names)} {random.choice(last_names)}"

def generate_indian_city():
    """Generate a random Indian city for practice location"""
    cities = [
        "Mumbai, Maharashtra", "Delhi, Delhi", "Bangalore, Karnataka", "Chennai, Tamil Nadu",
        "Hyderabad, Telangana", "Kolkata, West Bengal", "Pune, Maharashtra", "Ahmedabad, Gujarat",
        "Jaipur, Rajasthan", "Lucknow, Uttar Pradesh", "Chandigarh, Punjab", "Kochi, Kerala",
        "Indore, Madhya Pradesh", "Bhubaneswar, Odisha", "Guwahati, Assam", "Nagpur, Maharashtra",
        "Surat, Gujarat", "Patna, Bihar", "Coimbatore, Tamil Nadu", "Visakhapatnam, Andhra Pradesh"
    ]
    return random.choice(cities)

def generate_qualification():
    """Generate random medical qualifications"""
    degrees = ["MBBS", "MS", "MD", "DNB", "FRCS", "MCh"]
    specialties = ["General Surgery", "Plastic Surgery", "Dermatology", "ENT", "Ophthalmology"]
    years = list(range(2000, 2020))
    
    qualification = random.choice(degrees)
    if random.random() > 0.5:
        qualification += f" {random.choice(specialties)}"
    qualification += f" ({random.choice(years)})"
    
    # Add additional qualification (30% chance)
    if random.random() < 0.3:
        additional = random.choice(degrees)
        while additional == qualification.split()[0]:
            additional = random.choice(degrees)
        qualification += f", {additional} ({random.choice(years)})"
    
    return qualification

def generate_doctor():
    """Generate a doctor with verification data"""
    # Generate license number in MCI-XXXXX-YYYY format
    license_number = f"MCI-{random.randint(10000, 99999)}-{random.randint(2020, 2027)}"
    
    # Generate Aadhaar number (50% chance to have one)
    aadhaar_number = None
    if random.random() > 0.5:
        aadhaar_number = f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
    
    # Generate verification status (50% pending, 30% approved, 20% rejected)
    status_options = ["pending", "approved", "rejected"]
    status_weights = [0.5, 0.3, 0.2]
    verification_status = random.choices(status_options, status_weights, k=1)[0]
    
    # Generate credentials file path (80% chance to have one)
    credentials_url = None
    if random.random() > 0.2:
        file_number = random.randint(1, 100)
        file_ext = random.choice(["pdf", "jpg", "png"])
        credentials_url = f"doc{file_number}_credentials.{file_ext}"
    
    # Other fields
    name = generate_random_name()
    practice_location = generate_indian_city()
    qualification = generate_qualification()
    specialty = random.choice([
        "Plastic Surgery", "Dermatology", "Cosmetic Surgery", 
        "Aesthetic Medicine", "Hair Transplant", "Facial Cosmetic Surgery",
        "Reconstructive Surgery", "Oculoplastic Surgery", "Dental Surgery"
    ])
    experience = random.randint(5, 25)
    
    # Create the doctor object
    return Doctor(
        user_id=random.randint(1, 50),  # Assuming 50 users exist
        name=name,
        medical_license_number=license_number,
        qualification=qualification,
        practice_location=practice_location,
        verification_status=verification_status,
        credentials_url=credentials_url,
        aadhaar_number=aadhaar_number,
        specialty=specialty,
        experience=experience,
        city=practice_location.split(',')[0],
        state=practice_location.split(',')[1].strip() if ',' in practice_location else "",
        created_at=datetime.utcnow(),
        is_verified=verification_status == "approved"
    )

def generate_community_thread():
    """Generate a community thread for testing"""
    title_prefixes = ["Question about", "Looking for advice on", "Experiences with", "Should I get"]
    title_procedures = ["Rhinoplasty", "Lip Fillers", "Botox", "Face Lift", "Breast Augmentation", 
                        "Hair Transplant", "Liposuction", "Tummy Tuck", "Eyelid Surgery"]
    title_suffixes = ["in India", "cost", "recovery", "doctors", "clinics", "results", "side effects"]
    
    # Generate random content
    content_length = random.randint(50, 200)
    content = ''.join(random.choices(string.ascii_letters + ' ' + '.' + ',' + '?' + '!', k=content_length))
    
    # Generate title
    title = f"{random.choice(title_prefixes)} {random.choice(title_procedures)} {random.choice(title_suffixes)}"
    
    # Photo URL (30% chance)
    photo_url = None
    if random.random() <= 0.3:
        photo_num = random.randint(1, 50)
        photo_url = f"static/media/thread{photo_num}.jpg"
    
    return Community(
        title=title,
        content=content,
        category_id=random.randint(1, 5),  # Assuming 5 categories exist
        author_id=random.randint(1, 50),  # Assuming 50 users exist
        photo_url=photo_url,
        created_at=datetime.utcnow(),
        view_count=random.randint(0, 200),
        reply_count=random.randint(0, 20),
        featured=random.random() < 0.1  # 10% chance to be featured
    )

def create_doctor_credentials_directory():
    """Create the directory for doctor credentials if it doesn't exist"""
    credentials_dir = os.path.join('static', 'doctor_credentials')
    if not os.path.exists(credentials_dir):
        os.makedirs(credentials_dir, exist_ok=True)
        print(f"Created directory: {credentials_dir}")

    # Create a sample credential file for testing
    sample_file_path = os.path.join(credentials_dir, 'doc1_credentials.pdf')
    if not os.path.exists(sample_file_path):
        with open(sample_file_path, 'w') as f:
            f.write("This is a sample credential document for testing purposes.")
        print(f"Created sample credential file: {sample_file_path}")

def generate_users(num_users=50):
    """Generate test users for doctor relationships"""
    print(f"Creating {num_users} test users...")
    users = []
    
    roles = ["user", "doctor"]
    role_weights = [0.3, 0.7]  # 70% doctors for our verification testing
    
    for i in range(1, num_users + 1):
        role = random.choices(roles, role_weights, k=1)[0]
        role_type = role
        username = f"testuser{i}"
        
        user = User(
            name=f"Test User {i}",
            username=username,
            email=f"{username}@example.com",
            phone_number=f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            role=role,
            role_type=role_type,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        users.append(user)
    
    db.session.add_all(users)
    db.session.commit()
    print(f"Created {len(users)} test users successfully.")
    return users

def main():
    """Seed the database with sample data"""
    app = create_app()
    
    with app.app_context():
        print("Starting database seeding...")
        
        # Create the doctor credentials directory
        create_doctor_credentials_directory()
        
        # First create users
        users = generate_users(50)
        
        # Get user IDs for doctors
        doctor_user_ids = [user.id for user in users if user.role == 'doctor']
        
        if not doctor_user_ids:
            print("No doctor users created. Creating at least one...")
            admin_user = User(
                name="Admin User",
                username="admin",
                email="admin@example.com",
                phone_number="555-000-0000",
                role="admin",
                role_type="admin",
                is_verified=True,
                created_at=datetime.utcnow()
            )
            db.session.add(admin_user)
            
            doctor_user = User(
                name="Test Doctor",
                username="testdoctor",
                email="testdoctor@example.com",
                phone_number="555-111-1111",
                role="doctor",
                role_type="doctor",
                is_verified=True,
                created_at=datetime.utcnow()
            )
            db.session.add(doctor_user)
            db.session.commit()
            doctor_user_ids = [doctor_user.id]
        
        # Create 100 doctor profiles using the real user IDs
        print("Creating 100 doctor profiles...")
        doctors = []
        for _ in range(100):
            doc = generate_doctor()
            # Assign a real user ID
            doc.user_id = random.choice(doctor_user_ids)
            doctors.append(doc)
        
        db.session.add_all(doctors)
        db.session.commit()
        print("Doctor profiles created successfully.")
        
        # Create 500 community threads with valid user IDs
        print("Creating 500 community threads...")
        # Get all valid user IDs
        all_user_ids = [user.id for user in users]
        
        threads = []
        for _ in range(500):
            thread = generate_community_thread()
            # Assign a real user ID
            thread.author_id = random.choice(all_user_ids)
            threads.append(thread)
        
        db.session.add_all(threads)
        db.session.commit()
        print("Community threads created successfully.")
        
        print("\nSample data added successfully!")
        print("\nTest cases:")
        print("1. Navigate to /dashboard/doctor/verify to test doctor verification")
        print("2. Submit MCI-12345-2025, 'MBBS', 'Delhi, India' to test valid submission")
        print("3. Submit MCI-123 to test invalid license format")
        print("4. Navigate to /dashboard/admin/doctor-verifications as admin to approve/reject doctors")
        print("5. Navigate to /community to view the community threads")

if __name__ == "__main__":
    main()