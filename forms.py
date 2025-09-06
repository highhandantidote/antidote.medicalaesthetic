from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, IntegerField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class PackageEditForm(FlaskForm):
    title = StringField('Package Title', validators=[
        DataRequired(), 
        Length(min=5, max=200, message="Title must be between 5 and 200 characters")
    ])
    
    category = SelectField('Category', choices=[
        ('facial_treatment', 'Facial Treatment'),
        ('body_contouring', 'Body Contouring'),
        ('skin_care', 'Skin Care'),
        ('hair_treatment', 'Hair Treatment'),
        ('dental_aesthetic', 'Dental Aesthetic'),
        ('surgical_procedure', 'Surgical Procedure'),
        ('non_surgical', 'Non-Surgical'),
        ('wellness', 'Wellness'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=20, max=2000, message="Description must be between 20 and 2000 characters")
    ])
    
    price_actual = DecimalField('Actual Price (₹)', validators=[
        DataRequired(),
        NumberRange(min=1, max=1000000, message="Price must be between ₹1 and ₹10,00,000")
    ])
    
    price_discounted = DecimalField('Discounted Price (₹)', validators=[
        Optional(),
        NumberRange(min=1, max=1000000, message="Discounted price must be between ₹1 and ₹10,00,000")
    ])
    
    discount_percentage = IntegerField('Discount Percentage', validators=[
        Optional(),
        NumberRange(min=0, max=90, message="Discount must be between 0% and 90%")
    ])
    
    duration = StringField('Treatment Duration', validators=[
        Optional(),
        Length(max=100, message="Duration must be less than 100 characters")
    ])
    
    downtime = StringField('Recovery Downtime', validators=[
        Optional(),
        Length(max=100, message="Downtime must be less than 100 characters")
    ])
    
    procedure_info = TextAreaField('Procedure Information', validators=[
        Optional(),
        Length(max=2000, message="Procedure info must be less than 2000 characters")
    ])
    
    side_effects = TextAreaField('Side Effects', validators=[
        Optional(),
        Length(max=1000, message="Side effects must be less than 1000 characters")
    ])
    
    recommended_for = TextAreaField('Recommended For', validators=[
        Optional(),
        Length(max=500, message="Recommended for must be less than 500 characters")
    ])
    
    is_active = BooleanField('Active Package')
    is_featured = BooleanField('Featured Package')
    
    featured_image = FileField('Featured Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    
    gallery_images = FileField('Gallery Images', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])