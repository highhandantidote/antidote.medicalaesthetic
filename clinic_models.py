from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, ARRAY, Numeric
from sqlalchemy.orm import relationship
from app import db

class Clinic(db.Model):
    """Comprehensive clinic management model"""
    __tablename__ = 'clinics'
    
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    established_year = Column(Integer)
    
    # Location Information
    address = Column(Text, nullable=False)
    city = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    pincode = Column(String(10), nullable=False)
    country = Column(Text, default='India')
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Contact Information
    phone_primary = Column(String(15), nullable=False)
    phone_secondary = Column(String(15))
    email = Column(String(120), nullable=False)
    website = Column(Text)
    
    # Business Information
    registration_number = Column(Text, unique=True)
    license_number = Column(Text, unique=True)
    accreditation = Column(ARRAY(Text))  # Multiple accreditations
    insurance_accepted = Column(ARRAY(Text))  # Insurance providers accepted
    
    # Operational Details
    operating_hours = Column(JSON)  # Store operating hours for each day
    emergency_services = Column(Boolean, default=False)
    appointment_booking_available = Column(Boolean, default=True)
    online_consultation_available = Column(Boolean, default=False)
    
    # Facility Information
    total_beds = Column(Integer)
    operation_theaters = Column(Integer)
    icu_available = Column(Boolean, default=False)
    parking_available = Column(Boolean, default=True)
    wheelchair_accessible = Column(Boolean, default=True)
    
    # Media & Branding
    logo_url = Column(Text)
    cover_image_url = Column(Text)
    gallery_images = Column(ARRAY(Text))  # Multiple clinic images
    virtual_tour_url = Column(Text)
    video_introduction_url = Column(Text)
    
    # Ratings & Reviews
    avg_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    total_patients_treated = Column(Integer, default=0)
    
    # Status & Verification
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    featured = Column(Boolean, default=False)
    
    # SEO & Marketing
    seo_keywords = Column(ARRAY(Text))
    social_media_links = Column(JSON)  # Facebook, Instagram, etc.
    promotional_text = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    doctors = relationship("ClinicDoctor", back_populates="clinic", cascade="all, delete-orphan")
    packages = relationship("ClinicPackage", back_populates="clinic", cascade="all, delete-orphan")
    appointments = relationship("ClinicAppointment", back_populates="clinic", cascade="all, delete-orphan")
    reviews = relationship("ClinicReview", back_populates="clinic", cascade="all, delete-orphan")
    facilities = relationship("ClinicFacility", back_populates="clinic", cascade="all, delete-orphan")
    specializations = relationship("ClinicSpecialization", back_populates="clinic", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Clinic {self.name}>"

class ClinicDoctor(db.Model):
    """Association between clinics and doctors"""
    __tablename__ = 'clinic_doctors'
    
    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey('clinics.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    
    # Employment Details
    position = Column(Text)  # Head Doctor, Consultant, etc.
    department = Column(Text)
    is_head_doctor = Column(Boolean, default=False)
    is_available_for_consultation = Column(Boolean, default=True)
    consultation_fee_at_clinic = Column(Numeric(10, 2))
    
    # Schedule Information
    available_days = Column(ARRAY(String(10)))  # Monday, Tuesday, etc.
    available_time_slots = Column(JSON)  # Time slots for each day
    
    # Status
    is_active = Column(Boolean, default=True)
    joined_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="doctors")
    doctor = relationship("Doctor")
    
    def __repr__(self):
        return f"<ClinicDoctor clinic_id={self.clinic_id} doctor_id={self.doctor_id}>"

class ClinicPackage(db.Model):
    """Procedure packages offered by clinics with real pricing"""
    __tablename__ = 'clinic_packages'
    
    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey('clinics.id'), nullable=False)
    procedure_id = Column(Integer, ForeignKey('procedures.id'), nullable=False)
    
    # Package Information
    package_name = Column(Text, nullable=False)
    package_description = Column(Text)
    package_type = Column(Text)  # Basic, Standard, Premium
    
    # Pricing Information
    base_price = Column(Numeric(10, 2), nullable=False)
    consultation_fee = Column(Numeric(10, 2))
    anesthesia_cost = Column(Numeric(10, 2))
    facility_charges = Column(Numeric(10, 2))
    post_care_cost = Column(Numeric(10, 2))
    total_package_price = Column(Numeric(10, 2), nullable=False)
    
    # Inclusions & Exclusions
    inclusions = Column(ARRAY(Text))  # What's included in the package
    exclusions = Column(ARRAY(Text))  # What's not included
    
    # Package Details
    duration_days = Column(Integer)  # Treatment duration
    follow_up_visits = Column(Integer)
    warranty_months = Column(Integer)  # Warranty on results
    revision_policy = Column(Text)
    
    # Financing Options
    emi_available = Column(Boolean, default=False)
    emi_min_amount = Column(Numeric(10, 2))
    emi_max_tenure_months = Column(Integer)
    discount_percentage = Column(Float, default=0)
    seasonal_offer = Column(Text)
    
    # Availability
    is_active = Column(Boolean, default=True)
    limited_time_offer = Column(Boolean, default=False)
    offer_valid_until = Column(DateTime)
    slots_available = Column(Integer)
    
    # Media
    package_images = Column(ARRAY(Text))
    before_after_gallery = Column(ARRAY(Text))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="packages")
    procedure = relationship("Procedure")
    bookings = relationship("PackageBooking", back_populates="package", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ClinicPackage {self.package_name}>"

class ClinicSpecialization(db.Model):
    """Clinic specializations and expertise areas"""
    __tablename__ = 'clinic_specializations'
    
    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey('clinics.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    
    # Specialization Details
    expertise_level = Column(Text)  # Beginner, Intermediate, Expert
    years_of_experience = Column(Integer)
    cases_completed = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Certification
    certification_details = Column(Text)
    certification_date = Column(DateTime)
    
    # Status
    is_primary_specialization = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="specializations")
    category = relationship("Category")
    
    def __repr__(self):
        return f"<ClinicSpecialization clinic_id={self.clinic_id} category_id={self.category_id}>"

class ClinicFacility(db.Model):
    """Clinic facilities and amenities"""
    __tablename__ = 'clinic_facilities'
    
    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey('clinics.id'), nullable=False)
    
    # Facility Information
    facility_name = Column(Text, nullable=False)
    facility_type = Column(Text)  # Equipment, Amenity, Service
    description = Column(Text)
    
    # Equipment Details (if applicable)
    brand = Column(Text)
    model = Column(Text)
    year_acquired = Column(Integer)
    certification = Column(Text)
    
    # Availability
    is_available = Column(Boolean, default=True)
    maintenance_schedule = Column(Text)
    
    # Media
    facility_images = Column(ARRAY(Text))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="facilities")
    
    def __repr__(self):
        return f"<ClinicFacility {self.facility_name}>"

class ClinicAppointment(db.Model):
    """Appointment booking system for clinics"""
    __tablename__ = 'clinic_appointments'
    
    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey('clinics.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    package_id = Column(Integer, ForeignKey('clinic_packages.id'))
    
    # Appointment Details
    appointment_type = Column(Text, nullable=False)  # Consultation, Procedure, Follow-up
    appointment_date = Column(DateTime, nullable=False)
    appointment_time = Column(Text, nullable=False)
    duration_minutes = Column(Integer, default=30)
    
    # Patient Information
    patient_name = Column(Text, nullable=False)
    patient_phone = Column(String(15), nullable=False)
    patient_email = Column(String(120))
    patient_age = Column(Integer)
    patient_gender = Column(String(10))
    
    # Medical Information
    chief_complaint = Column(Text)
    medical_history = Column(Text)
    current_medications = Column(Text)
    allergies = Column(Text)
    previous_surgeries = Column(Text)
    
    # Appointment Status
    status = Column(Text, default='scheduled')  # scheduled, confirmed, completed, cancelled, no-show
    confirmation_sent = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    
    # Payment Information
    consultation_fee_paid = Column(Boolean, default=False)
    payment_method = Column(Text)
    payment_status = Column(Text, default='pending')
    payment_amount = Column(Numeric(10, 2))
    
    # Notes
    doctor_notes = Column(Text)
    clinic_notes = Column(Text)
    patient_feedback = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="appointments")
    user = relationship("User", back_populates="appointments")
    doctor = relationship("Doctor")
    package = relationship("ClinicPackage")
    
    def __repr__(self):
        return f"<ClinicAppointment {self.id} - {self.patient_name}>"

class PackageBooking(db.Model):
    """Package booking and purchase tracking"""
    __tablename__ = 'package_bookings'
    
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey('clinic_packages.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    clinic_id = Column(Integer, ForeignKey('clinics.id'), nullable=False)
    
    # Booking Information
    booking_date = Column(DateTime, default=datetime.utcnow)
    preferred_schedule = Column(Text)
    special_requests = Column(Text)
    
    # Payment Information
    total_amount = Column(Numeric(10, 2), nullable=False)
    advance_paid = Column(Numeric(10, 2), default=0)
    balance_amount = Column(Numeric(10, 2))
    payment_plan = Column(Text)  # Full, Installment, EMI
    emi_tenure = Column(Integer)
    
    # Status Tracking
    booking_status = Column(Text, default='pending')  # pending, confirmed, in-progress, completed, cancelled
    payment_status = Column(Text, default='pending')  # pending, partial, paid, refunded
    
    # Treatment Tracking
    treatment_start_date = Column(DateTime)
    treatment_completion_date = Column(DateTime)
    follow_up_scheduled = Column(Boolean, default=False)
    
    # Documentation
    consent_forms_signed = Column(Boolean, default=False)
    medical_clearance_obtained = Column(Boolean, default=False)
    insurance_claimed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    package = relationship("ClinicPackage", back_populates="bookings")
    user = relationship("User")
    clinic = relationship("Clinic")
    
    def __repr__(self):
        return f"<PackageBooking {self.id}>"

class ClinicReview(db.Model):
    """Reviews and ratings for clinics"""
    __tablename__ = 'clinic_reviews'
    
    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey('clinics.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    package_id = Column(Integer, ForeignKey('clinic_packages.id'))
    
    # Review Information
    overall_rating = Column(Float, nullable=False)
    facility_rating = Column(Float)
    staff_rating = Column(Float)
    cleanliness_rating = Column(Float)
    value_for_money_rating = Column(Float)
    doctor_rating = Column(Float)
    
    # Review Content
    review_title = Column(Text)
    review_content = Column(Text, nullable=False)
    pros = Column(ARRAY(Text))
    cons = Column(ARRAY(Text))
    
    # Treatment Information
    procedure_name = Column(Text)
    treatment_date = Column(DateTime)
    would_recommend = Column(Boolean)
    
    # Verification
    is_verified_patient = Column(Boolean, default=False)
    verification_method = Column(Text)
    
    # Media
    review_images = Column(ARRAY(Text))
    before_after_images = Column(ARRAY(Text))
    
    # Engagement
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    
    # Status
    is_published = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="reviews")
    user = relationship("User")
    package = relationship("ClinicPackage")
    
    def __repr__(self):
        return f"<ClinicReview {self.id} - Rating: {self.overall_rating}>"