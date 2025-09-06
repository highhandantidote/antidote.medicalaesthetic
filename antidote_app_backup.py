#!/usr/bin/env python3
"""
Antidote Medical Platform - Complete Application Backup
Created: June 10, 2025
Description: A comprehensive medical aesthetic marketplace platform with clinic management,
lead tracking, package management, and credit processing system.

Key Features:
- Flask-based web application with PostgreSQL database
- Clinic dashboard with credit management and lead analytics
- Enhanced package management system
- Authentication with Flask-Login
- Admin dashboard with transaction history
- Lead capture and processing with credit deduction
- Community features and AI recommendations
- Mobile-responsive design with Bootstrap 5

Database Schema:
- Users (authentication and profiles)
- Clinics (clinic information and ownership)
- Packages (treatment packages with pricing)
- Leads (patient inquiries and bookings)
- Credit Transactions (billing and payment tracking)
- Reviews, Appointments, Procedures, Categories, etc.
"""

import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import pytz
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)

# Initialize Flask extensions
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "antidote_secret_key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config['TIMEZONE'] = pytz.timezone('Asia/Kolkata')
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour in seconds
    
    # Email configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'antidote.platform@gmail.com')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'antidote.platform@gmail.com')
    
    # Use ProxyFix middleware for proper URL generation
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            user = db.session.get(User, int(user_id))
            if user:
                db.session.expunge(user)  # Detach from session to avoid conflicts
            return user
        except Exception as e:
            try:
                db.session.rollback()
                result = db.session.execute(text("SELECT * FROM users WHERE id = :user_id"), {"user_id": int(user_id)}).fetchone()
                if result:
                    user_data = dict(result._mapping)
                    user = User()
                    user.id = user_data['id']
                    user.email = user_data['email']
                    user.role = user_data['role']
                    user.name = user_data['name']
                    return user
            except Exception as e2:
                app.logger.error(f"Error loading user {user_id} with fallback: {e2}")
                db.session.rollback()
            return None
    
    return app

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    clinics_owned = relationship('Clinic', foreign_keys='Clinic.owner_user_id', back_populates='owner')
    reviews = relationship('Review', back_populates='user')
    appointments = relationship('Appointment', back_populates='user')
    leads = relationship('Lead', back_populates='user')

class Clinic(db.Model):
    __tablename__ = 'clinics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    credit_balance = db.Column(db.Numeric(10, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship('User', foreign_keys=[owner_user_id], back_populates='clinics_owned')
    packages = relationship('Package', back_populates='clinic')
    leads = relationship('Lead', back_populates='clinic')
    credit_transactions = relationship('CreditTransaction', back_populates='clinic')

class Package(db.Model):
    __tablename__ = 'packages'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price_actual = db.Column(db.Numeric(10, 2), nullable=False)
    price_discounted = db.Column(db.Numeric(10, 2))
    discount_percentage = db.Column(db.Integer)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    procedure_id = db.Column(db.Integer, db.ForeignKey('procedures.id'))
    about_procedure = db.Column(db.Text)
    anesthetic_type = db.Column(db.String(100))
    aftercare_kit = db.Column(db.String(200))
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clinic = relationship('Clinic', back_populates='packages')
    category = relationship('Category', back_populates='packages')
    procedure = relationship('Procedure', back_populates='packages')

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100))
    preferred_date = db.Column(db.DateTime)
    procedure_name = db.Column(db.String(200))
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'))
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='new')  # new, contacted, converted, closed
    notes = db.Column(db.Text)
    source = db.Column(db.String(50), default='website')
    lead_cost = db.Column(db.Numeric(10, 2), default=100)  # Cost deducted from clinic credits
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    clinic = relationship('Clinic', back_populates='leads')
    user = relationship('User', back_populates='leads')
    package = relationship('Package')

class CreditTransaction(db.Model):
    __tablename__ = 'credit_transactions'
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'))
    transaction_type = db.Column(db.String(50), nullable=False)  # topup, lead_deduction, refund, adjustment
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(200))
    reference_id = db.Column(db.String(100))  # Payment gateway reference or lead ID
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed, refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    clinic = relationship('Clinic', back_populates='credit_transactions')

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    body_part_id = db.Column(db.Integer, db.ForeignKey('body_parts.id'))
    image_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    body_part = relationship('BodyPart', back_populates='categories')
    procedures = relationship('Procedure', back_populates='category')
    packages = relationship('Package', back_populates='category')

class BodyPart(db.Model):
    __tablename__ = 'body_parts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    categories = relationship('Category', back_populates='body_part')

class Procedure(db.Model):
    __tablename__ = 'procedures'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    avg_price = db.Column(db.Numeric(10, 2))
    duration = db.Column(db.String(50))
    recovery_time = db.Column(db.String(50))
    image_url = db.Column(db.String(200))
    is_featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    category = relationship('Category', back_populates='procedures')
    packages = relationship('Package', back_populates='procedure')

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(200))
    qualifications = db.Column(db.Text)
    experience_years = db.Column(db.Integer)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'))
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(200))
    consultation_fee = db.Column(db.Numeric(10, 2))
    rating = db.Column(db.Numeric(3, 2))
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = relationship('Review', back_populates='doctor')
    appointments = relationship('Appointment', back_populates='doctor')

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'))
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='reviews')
    doctor = relationship('Doctor', back_populates='reviews')

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'))
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, confirmed, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='appointments')
    doctor = relationship('Doctor', back_populates='appointments')

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class SignupForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=10)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Sign Up')

class PackageForm(FlaskForm):
    title = StringField('Package Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price_actual = FloatField('Actual Price (₹)', validators=[DataRequired()])
    price_discounted = FloatField('Discounted Price (₹)')
    category_id = SelectField('Category', coerce=int)
    procedure_id = SelectField('Procedure', coerce=int)
    about_procedure = TextAreaField('About Procedure')
    anesthetic_type = StringField('Anesthetic Type')
    aftercare_kit = StringField('Aftercare Kit')
    is_featured = BooleanField('Featured Package')
    submit = SubmitField('Save Package')

# Helper Functions
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def clinic_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        # Check if user owns a clinic
        clinic = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {'user_id': current_user.id}).fetchone()
        if not clinic:
            flash('You need to be a clinic owner to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def send_email(subject, recipients, template):
    """Send an email using Flask-Mail."""
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=template
        )
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def calculate_growth_percentage(current, previous):
    """Calculate growth percentage between two periods."""
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 1)

# Create Flask app instance
app = create_app()

# Routes
@app.route('/')
def index():
    """Render the home page."""
    try:
        # Get featured packages
        featured_packages = db.session.execute(text("""
            SELECT p.*, c.name as clinic_name, cat.name as category_name
            FROM packages p
            JOIN clinics c ON p.clinic_id = c.id
            LEFT JOIN categories cat ON p.category_id = cat.id
            WHERE p.is_featured = true AND p.is_active = true
            ORDER BY p.created_at DESC
            LIMIT 6
        """)).fetchall()
        
        # Get popular procedures
        popular_procedures = db.session.execute(text("""
            SELECT * FROM procedures 
            WHERE is_featured = true 
            ORDER BY view_count DESC 
            LIMIT 8
        """)).fetchall()
        
        # Get top-rated doctors
        top_doctors = db.session.execute(text("""
            SELECT * FROM doctors 
            WHERE is_verified = true AND is_active = true 
            ORDER BY rating DESC NULLS LAST
            LIMIT 6
        """)).fetchall()
        
        return render_template('index.html',
                             featured_packages=featured_packages,
                             popular_procedures=popular_procedures,
                             top_doctors=top_doctors)
    except Exception as e:
        logger.error(f"Error loading homepage: {e}")
        return render_template('index.html',
                             featured_packages=[],
                             popular_procedures=[],
                             top_doctors=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(text("""
            SELECT * FROM users 
            WHERE email = :email AND is_active = true
        """), {'email': form.email.data}).fetchone()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            user_obj = User()
            user_obj.id = user.id
            user_obj.email = user.email
            user_obj.username = user.username
            user_obj.name = user.name
            user_obj.role = user.role
            
            login_user(user_obj, remember=form.remember_me.data)
            flash('Logged in successfully!', 'success')
            
            # Redirect to clinic dashboard if user owns a clinic
            clinic = db.session.execute(text("""
                SELECT id FROM clinics WHERE owner_user_id = :user_id
            """), {'user_id': user.id}).fetchone()
            
            if clinic:
                return redirect(url_for('clinic_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = SignupForm()
    if form.validate_on_submit():
        try:
            # Check if user already exists
            existing_user = db.session.execute(text("""
                SELECT id FROM users 
                WHERE email = :email OR username = :username
            """), {
                'email': form.email.data,
                'username': form.username.data
            }).fetchone()
            
            if existing_user:
                flash('User with this email or username already exists.', 'error')
                return render_template('auth/signup.html', form=form)
            
            # Create new user
            password_hash = generate_password_hash(form.password.data)
            db.session.execute(text("""
                INSERT INTO users (username, email, name, phone_number, password_hash, role)
                VALUES (:username, :email, :name, :phone, :password_hash, 'user')
            """), {
                'username': form.username.data,
                'email': form.email.data,
                'name': form.name.data,
                'phone': form.phone_number.data,
                'password_hash': password_hash
            })
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during signup: {e}")
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('auth/signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/clinic/dashboard')
@login_required
@clinic_required
def clinic_dashboard():
    """Comprehensive clinic dashboard with credit management and lead tracking."""
    try:
        # Get clinic for current user
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics 
            WHERE owner_user_id = :user_id 
        """), {'user_id': current_user.id}).fetchone()
        
        if not clinic_result:
            flash('No clinic found for your account.', 'error')
            return redirect(url_for('index'))
        
        clinic = dict(clinic_result._mapping)
        
        # Get lead statistics
        total_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads WHERE clinic_id = :clinic_id
        """), {'clinic_id': clinic['id']}).scalar() or 0
        
        pending_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE clinic_id = :clinic_id AND status = 'new'
        """), {'clinic_id': clinic['id']}).scalar() or 0
        
        this_month_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE clinic_id = :clinic_id 
            AND created_at >= date_trunc('month', CURRENT_DATE)
        """), {'clinic_id': clinic['id']}).scalar() or 0
        
        # Get credit spending this month
        monthly_spending = db.session.execute(text("""
            SELECT COALESCE(ABS(SUM(amount)), 0) 
            FROM credit_transactions 
            WHERE clinic_id = :clinic_id 
            AND transaction_type = 'lead_deduction'
            AND created_at >= date_trunc('month', CURRENT_DATE)
        """), {'clinic_id': clinic['id']}).scalar() or 0
        
        # Get recent packages
        recent_packages = db.session.execute(text("""
            SELECT id, title, description, price_actual, is_featured, is_active, created_at
            FROM packages 
            WHERE clinic_id = :clinic_id 
            ORDER BY created_at DESC 
            LIMIT 5
        """), {'clinic_id': clinic['id']}).fetchall()
        
        # Convert packages to objects for template compatibility
        packages_list = []
        for row in recent_packages:
            package_dict = dict(row._mapping)
            class PackageObj:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)
                    if not hasattr(self, 'description'):
                        self.description = ''
                    if not hasattr(self, 'price'):
                        self.price = self.price_actual if hasattr(self, 'price_actual') else 0
            packages_list.append(PackageObj(package_dict))
        
        clinic['packages'] = packages_list
        
        # Get recent credit transactions
        recent_transactions = db.session.execute(text("""
            SELECT transaction_type, amount, description, status, created_at 
            FROM credit_transactions 
            WHERE clinic_id = :clinic_id 
            ORDER BY created_at DESC 
            LIMIT 10
        """), {'clinic_id': clinic['id']}).fetchall()
        
        return render_template('clinic/dashboard.html',
                             clinic=clinic,
                             total_leads=total_leads,
                             pending_leads=pending_leads,
                             this_month_leads=this_month_leads,
                             monthly_spending=monthly_spending,
                             recent_transactions=recent_transactions)
                             
    except Exception as e:
        logger.error(f"Error loading clinic dashboard: {e}")
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/clinic/packages/add', methods=['GET', 'POST'])
@login_required
@clinic_required
def add_package():
    """Add a new treatment package."""
    form = PackageForm()
    
    # Populate form choices
    categories = db.session.execute(text("SELECT id, name FROM categories WHERE is_active = true ORDER BY name")).fetchall()
    procedures = db.session.execute(text("SELECT id, name FROM procedures ORDER BY name")).fetchall()
    
    form.category_id.choices = [(0, 'Select Category')] + [(c.id, c.name) for c in categories]
    form.procedure_id.choices = [(0, 'Select Procedure')] + [(p.id, p.name) for p in procedures]
    
    if form.validate_on_submit():
        try:
            # Get clinic ID
            clinic = db.session.execute(text("""
                SELECT id FROM clinics WHERE owner_user_id = :user_id
            """), {'user_id': current_user.id}).fetchone()
            
            if not clinic:
                flash('Clinic not found.', 'error')
                return redirect(url_for('clinic_dashboard'))
            
            # Create new package
            db.session.execute(text("""
                INSERT INTO packages (
                    title, description, price_actual, price_discounted,
                    clinic_id, category_id, procedure_id, about_procedure,
                    anesthetic_type, aftercare_kit, is_featured
                ) VALUES (
                    :title, :description, :price_actual, :price_discounted,
                    :clinic_id, :category_id, :procedure_id, :about_procedure,
                    :anesthetic_type, :aftercare_kit, :is_featured
                )
            """), {
                'title': form.title.data,
                'description': form.description.data,
                'price_actual': form.price_actual.data,
                'price_discounted': form.price_discounted.data,
                'clinic_id': clinic.id,
                'category_id': form.category_id.data if form.category_id.data > 0 else None,
                'procedure_id': form.procedure_id.data if form.procedure_id.data > 0 else None,
                'about_procedure': form.about_procedure.data,
                'anesthetic_type': form.anesthetic_type.data,
                'aftercare_kit': form.aftercare_kit.data,
                'is_featured': form.is_featured.data
            })
            db.session.commit()
            
            flash('Package created successfully!', 'success')
            return redirect(url_for('clinic_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating package: {e}")
            flash('Error creating package. Please try again.', 'error')
    
    return render_template('clinic/add_package_enhanced.html', form=form)

@app.route('/submit_lead', methods=['POST'])
def submit_lead():
    """Process lead submission for clinic leads."""
    try:
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        city = request.form.get('city')
        preferred_date = request.form.get('preferred_date')
        procedure_name = request.form.get('procedure_name')
        package_id = request.form.get('package_id')
        clinic_id = request.form.get('clinic_id')
        
        # Validate required fields
        if not all([name, email, phone, procedure_name, clinic_id]):
            flash('Please fill in all required fields.', 'error')
            return redirect(request.referrer or url_for('index'))
        
        # Get clinic credit balance
        clinic = db.session.execute(text("""
            SELECT id, name, credit_balance FROM clinics WHERE id = :clinic_id
        """), {'clinic_id': clinic_id}).fetchone()
        
        if not clinic:
            flash('Clinic not found.', 'error')
            return redirect(request.referrer or url_for('index'))
        
        # Check if clinic has sufficient credits
        lead_cost = Decimal('100.00')  # Default lead cost
        if clinic.credit_balance < lead_cost:
            flash('Clinic has insufficient credits to receive this lead.', 'error')
            return redirect(request.referrer or url_for('index'))
        
        # Create lead
        lead_id = db.session.execute(text("""
            INSERT INTO leads (
                name, email, phone, city, preferred_date, procedure_name,
                package_id, clinic_id, status, lead_cost, source
            ) VALUES (
                :name, :email, :phone, :city, :preferred_date, :procedure_name,
                :package_id, :clinic_id, 'new', :lead_cost, 'website'
            ) RETURNING id
        """), {
            'name': name,
            'email': email,
            'phone': phone,
            'city': city,
            'preferred_date': preferred_date if preferred_date else None,
            'procedure_name': procedure_name,
            'package_id': package_id if package_id else None,
            'clinic_id': clinic_id,
            'lead_cost': lead_cost
        }).scalar()
        
        # Deduct credits from clinic
        db.session.execute(text("""
            UPDATE clinics 
            SET credit_balance = credit_balance - :lead_cost 
            WHERE id = :clinic_id
        """), {
            'lead_cost': lead_cost,
            'clinic_id': clinic_id
        })
        
        # Record credit transaction
        db.session.execute(text("""
            INSERT INTO credit_transactions (
                clinic_id, transaction_type, amount, description, reference_id, status
            ) VALUES (
                :clinic_id, 'lead_deduction', :amount, :description, :reference_id, 'completed'
            )
        """), {
            'clinic_id': clinic_id,
            'amount': -lead_cost,
            'description': f'Lead deduction for {procedure_name}',
            'reference_id': f'LEAD_{lead_id}'
        })
        
        db.session.commit()
        
        flash('Your inquiry has been submitted successfully! The clinic will contact you soon.', 'success')
        return redirect(url_for('lead_confirmation', lead_id=lead_id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting lead: {e}")
        flash('An error occurred while submitting your inquiry. Please try again.', 'error')
        return redirect(request.referrer or url_for('index'))

@app.route('/lead_confirmation/<int:lead_id>')
def lead_confirmation(lead_id):
    """Show confirmation page after successful lead submission."""
    try:
        lead = db.session.execute(text("""
            SELECT l.*, c.name as clinic_name, c.phone as clinic_phone, c.email as clinic_email
            FROM leads l
            JOIN clinics c ON l.clinic_id = c.id
            WHERE l.id = :lead_id
        """), {'lead_id': lead_id}).fetchone()
        
        if not lead:
            flash('Lead not found.', 'error')
            return redirect(url_for('index'))
        
        return render_template('lead_confirmation.html', lead=lead)
        
    except Exception as e:
        logger.error(f"Error loading lead confirmation: {e}")
        flash('Error loading confirmation page.', 'error')
        return redirect(url_for('index'))

@app.route('/mock_login')
def mock_login():
    """Mock login route for testing purposes."""
    try:
        # Get user 339 from database (Ashok Advanced Aesthetics clinic owner)
        user = db.session.get(User, 339)
        if user:
            login_user(user)
            flash('You are now logged in as Ashok Advanced Aesthetics clinic user', 'success')
            return redirect(url_for('clinic_dashboard'))
        else:
            flash('Test user not found', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in mock login: {e}")
        flash('Login error occurred', 'error')
        return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with platform overview."""
    try:
        # Get platform statistics
        total_clinics = db.session.execute(text("SELECT COUNT(*) FROM clinics")).scalar()
        total_users = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        total_packages = db.session.execute(text("SELECT COUNT(*) FROM packages")).scalar()
        total_leads = db.session.execute(text("SELECT COUNT(*) FROM leads")).scalar()
        
        # Get recent activity
        recent_leads = db.session.execute(text("""
            SELECT l.*, c.name as clinic_name
            FROM leads l
            JOIN clinics c ON l.clinic_id = c.id
            ORDER BY l.created_at DESC
            LIMIT 10
        """)).fetchall()
        
        recent_transactions = db.session.execute(text("""
            SELECT ct.*, c.name as clinic_name
            FROM credit_transactions ct
            JOIN clinics c ON ct.clinic_id = c.id
            ORDER BY ct.created_at DESC
            LIMIT 10
        """)).fetchall()
        
        return render_template('admin/dashboard.html',
                             total_clinics=total_clinics,
                             total_users=total_users,
                             total_packages=total_packages,
                             total_leads=total_leads,
                             recent_leads=recent_leads,
                             recent_transactions=recent_transactions)
                             
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        flash('Error loading admin dashboard.', 'error')
        return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Database initialization
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

"""
DEPLOYMENT INSTRUCTIONS:
========================

1. Environment Variables Required:
   - DATABASE_URL: PostgreSQL connection string
   - SESSION_SECRET: Flask session secret key
   - MAIL_USERNAME: Email username for notifications
   - MAIL_PASSWORD: Email password
   - MAIL_DEFAULT_SENDER: Default email sender

2. Database Setup:
   - Create PostgreSQL database
   - Run: flask db init (if using migrations)
   - Run: flask db migrate
   - Run: flask db upgrade

3. Sample Data:
   - Create admin user: INSERT INTO users (username, email, name, password_hash, role) VALUES ('admin', 'admin@antidote.com', 'Admin', '<hashed_password>', 'admin');
   - Create test clinic and packages for testing

4. Production Considerations:
   - Set DEBUG=False
   - Use proper SSL certificates
   - Configure reverse proxy (nginx)
   - Set up proper logging and monitoring
   - Configure backup strategy for database
   - Implement rate limiting for API endpoints

5. File Structure:
   - templates/ (HTML templates)
   - static/ (CSS, JS, images)
   - uploads/ (user uploaded files)
   - migrations/ (database migrations)

This backup contains the core functionality of the Antidote medical platform
with clinic management, lead processing, package management, and credit system.
"""