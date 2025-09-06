#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Face Analysis Routes

This module provides routes for the new face analysis feature.
It handles facial image uploads, analysis using Google's Gemini Vision API,
and displaying comprehensive results to users.
"""

import os
import uuid
import base64
import logging
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, TextAreaField, IntegerField
from wtforms.validators import Optional, NumberRange
from werkzeug.utils import secure_filename

from app import db
from models import FaceAnalysis, FaceAnalysisRecommendation
from utils.gemini_analysis import analyze_face_image, analyze_face_image_enhanced
from utils.image_validation import validate_face_image
from utils.image_compression import optimize_face_analysis_image

# Configure logging
logger = logging.getLogger(__name__)

# Create the blueprint
face_analysis = Blueprint('face_analysis', __name__, url_prefix='/face-analysis')

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads/face_analysis'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Define the face analysis form class
class FaceAnalysisForm(FlaskForm):
    """Form for uploading a face analysis image."""
    face_image = FileField('Face Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG, JPEG, and PNG images are allowed')
    ])
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=1, max=120)])
    gender = SelectField('Gender', choices=[
        ('', 'Select'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('non-binary', 'Non-binary'),
        ('prefer-not-to-say', 'Prefer not to say')
    ], validators=[Optional()])
    concerns = TextAreaField('Primary Concerns', validators=[Optional()])
    treatment_history = TextAreaField('Treatment History', validators=[Optional()])

def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@face_analysis.route('/')
def index():
    """Render the face analysis upload page."""
    form = FaceAnalysisForm()
    return render_template('face_analysis/index.html', form=form)

@face_analysis.route('/upload', methods=['POST'])
def upload():
    """Handle face image upload and start analysis."""
    form = FaceAnalysisForm()
    
    # Check if we have either an image file or base64 data
    image_data = request.form.get('image_data')
    has_image_data = image_data and image_data.startswith('data:image')
    
    # If we have base64 image data, we can bypass form validation
    # because FileRequired validator would fail without an actual file
    if not has_image_data and not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")
        return redirect(url_for('face_analysis.index'))
    
    try:
        # Get form data
        face_image = form.face_image.data
        age = form.age.data
        gender = form.gender.data
        concerns = form.concerns.data
        treatment_history = form.treatment_history.data
        
        file_path = None
        
        # Handle base64 image data (from drag-and-drop or camera)
        if has_image_data:
            try:
                # Extract the base64 data
                file_format = 'jpeg'
                if image_data and 'data:image/png' in image_data:
                    file_format = 'png'
                
                # Safely split to get content after comma
                if image_data and ',' in image_data:
                    base64_content = image_data.split(',')[1]
                    
                    # Check file size before processing (approximate size from base64)
                    estimated_size = len(base64_content) * 3 / 4  # base64 is ~4/3 the original size
                    max_size = 20 * 1024 * 1024  # 20MB limit for face analysis
                    
                    if estimated_size > max_size:
                        flash(f'Image file is too large ({estimated_size/1024/1024:.1f}MB). Please use an image smaller than 20MB or compress the image.', 'error')
                        return redirect(url_for('face_analysis.index'))
                    
                    # Create a unique filename
                    unique_id = uuid.uuid4().hex
                    filename = f"{unique_id}.{file_format}"
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    
                    # Decode and save the image
                    with open(file_path, 'wb') as f:
                        f.write(base64.b64decode(base64_content))
                    logger.info(f"Base64 image saved at {file_path} (size: {estimated_size/1024/1024:.1f}MB)")
                else:
                    raise ValueError("Invalid base64 image format")
            except Exception as e:
                logger.error(f"Error saving base64 image: {e}")
                flash('Error processing the image. Please try uploading a file instead or use a smaller image.', 'error')
                return redirect(url_for('face_analysis.index'))
        
        # If image is from file upload
        elif face_image:
            # Check if the file is allowed
            if not face_image or not allowed_file(face_image.filename):
                flash('Invalid file format. Please upload a JPG, JPEG, or PNG image.', 'error')
                return redirect(url_for('face_analysis.index'))
            
            # Check file size
            face_image.seek(0, 2)  # Seek to end of file
            file_size = face_image.tell()
            face_image.seek(0)  # Reset to beginning
            
            max_size = 20 * 1024 * 1024  # 20MB limit
            if file_size > max_size:
                flash(f'Image file is too large ({file_size/1024/1024:.1f}MB). Please use an image smaller than 20MB.', 'error')
                return redirect(url_for('face_analysis.index'))
            
            # Generate unique filename and save the image
            filename = secure_filename(face_image.filename)
            unique_id = uuid.uuid4().hex
            filename = f"{unique_id}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            face_image.save(file_path)
            logger.info(f"Face image saved at {file_path} (size: {file_size/1024/1024:.1f}MB)")
        
        # If no image was provided
        if not file_path:
            flash('Please upload an image or take a photo with the camera.', 'error')
            return redirect(url_for('face_analysis.index'))
        
        # Validate image positioning and quality
        logger.info(f"Validating image positioning for {file_path}")
        validation_result = validate_face_image(file_path)
        
        # Check if image passes validation
        if not validation_result['is_valid']:
            logger.warning(f"Image failed validation: {validation_result['issues']}")
            
            # Create detailed error message with recommendations
            error_message = "Image quality issues detected:\n"
            for issue in validation_result['issues']:
                error_message += f"• {issue}\n"
            
            error_message += "\nRecommendations for better results:\n"
            for recommendation in validation_result['recommendations']:
                error_message += f"• {recommendation}\n"
            
            flash(error_message, 'warning')
            
            # If validation score is very low, reject the image
            if validation_result['validation_score'] < 0.5:
                flash('Image quality is too poor for accurate analysis. Please retake the photo following the guidelines.', 'error')
                return redirect(url_for('face_analysis.index'))
            
            # For moderate scores, warn but proceed
            flash('Proceeding with analysis, but results may be less accurate due to image quality issues.', 'info')
        
        # Optimize image for face analysis (compress if needed)
        try:
            logger.info(f"Optimizing image for face analysis: {file_path}")
            optimized_file_path = optimize_face_analysis_image(file_path)
            
            # Update file path if image was optimized
            if optimized_file_path != file_path:
                file_path = optimized_file_path
                logger.info(f"Image optimized and saved to: {file_path}")
        except Exception as e:
            logger.warning(f"Image optimization failed, proceeding with original: {e}")
            # Continue with original image if optimization fails
        
        # Create anonymous analysis record first
        user_id = current_user.id if current_user.is_authenticated else None
        is_anonymous = not current_user.is_authenticated
        
        # Create an empty analysis record
        analysis = FaceAnalysis()
        analysis.user_id = user_id
        analysis.image_path = file_path
        analysis.analysis_data = {}
        analysis.is_anonymous = is_anonymous
        db.session.add(analysis)
        db.session.commit()
        
        # Prepare user info for analysis
        user_info = {
            'age': age,
            'gender': gender,
            'concerns': concerns,
            'history': treatment_history
        }
        
        # Analyze the face using enhanced analysis (Gemini + Geometric)
        logger.info(f"Calling analyze_face_image_enhanced with file_path={file_path}")
        analysis_result = analyze_face_image_enhanced(file_path, user_info)
        
        # Check for errors in the analysis result
        if 'error' in analysis_result:
            error_message = analysis_result['error']
            logger.error(f"Analysis returned error: {error_message}")
            # Update error info in the analysis data
            analysis.analysis_data = {
                'error': error_message,
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                db.session.commit()
            except Exception as db_error:
                logger.error(f"Error commit failed: {db_error}")
                db.session.rollback()
            
            if "API key" in error_message:
                flash('API configuration error. Please contact the administrator.', 'error')
            else:
                flash(f'Analysis error: {error_message}', 'error')
            return redirect(url_for('face_analysis.index'))
        
        # Update the analysis record with the results
        logger.info("Updating database with analysis results")
        analysis.analysis_data = analysis_result
        
        # Store geometric analysis data if available
        if analysis_result.get('has_geometric_analysis'):
            analysis.geometric_analysis_data = analysis_result.get('geometric_analysis')
            analysis.mathematical_scores = analysis_result.get('mathematical_scores')
            analysis.has_geometric_analysis = True
            logger.info("Geometric analysis data stored successfully")
        else:
            analysis.has_geometric_analysis = False
            logger.warning("Geometric analysis was not available")
        
        # Store skin analysis recommendations
        logger.info(f"Processing {len(analysis_result.get('skin_analysis', []))} skin analysis recommendations")
        for skin_item in analysis_result.get('skin_analysis', []):
            try:
                recommendation = FaceAnalysisRecommendation()
                recommendation.analysis_id = analysis.id
                recommendation.recommendation_type = 'skin'
                recommendation.feature_name = skin_item.get('name', '')
                recommendation.severity_score = skin_item.get('severity', 0.0)
                recommendation.recommendation_details = skin_item.get('details', '')
                recommendation.treatment_options = skin_item.get('treatments', '')
                db.session.add(recommendation)
            except Exception as e:
                logger.error(f"Error adding skin recommendation: {e}")
        
        # Store facial structure recommendations
        logger.info(f"Processing {len(analysis_result.get('facial_structure', []))} facial structure recommendations")
        for structure_item in analysis_result.get('facial_structure', []):
            try:
                recommendation = FaceAnalysisRecommendation()
                recommendation.analysis_id = analysis.id
                recommendation.recommendation_type = 'structure'
                recommendation.feature_name = structure_item.get('name', '')
                recommendation.severity_score = structure_item.get('prominence', 0.0)
                recommendation.recommendation_details = structure_item.get('details', '')
                recommendation.treatment_options = structure_item.get('treatments', '')
                recommendation.needs_surgery = structure_item.get('needs_surgery', False)
                db.session.add(recommendation)
            except Exception as e:
                logger.error(f"Error adding structure recommendation: {e}")
        
        # Store surgical recommendations
        logger.info(f"Processing {len(analysis_result.get('surgical_recommendations', []))} surgical recommendations")
        for surgery_item in analysis_result.get('surgical_recommendations', []):
            try:
                recommendation = FaceAnalysisRecommendation()
                recommendation.analysis_id = analysis.id
                recommendation.recommendation_type = 'surgical'
                recommendation.feature_name = surgery_item.get('procedure_name', '')
                recommendation.severity_score = surgery_item.get('urgency', 0.8)  # Default high urgency for surgical procedures
                recommendation.recommendation_details = f"For: {surgery_item.get('target_condition', '')}\n\n{surgery_item.get('description', '')}"
                recommendation.treatment_options = surgery_item.get('expected_outcomes', '')
                recommendation.needs_surgery = True
                db.session.add(recommendation)
            except Exception as e:
                logger.error(f"Error adding surgical recommendation: {e}")
        
        try:
            db.session.commit()
            logger.info(f"Face analysis completed for ID {analysis.id}")
        except Exception as db_error:
            logger.error(f"Database commit error: {db_error}")
            db.session.rollback()
            flash('Analysis completed but could not save to database. Please try again.', 'warning')
            return redirect(url_for('face_analysis.index'))
        
        # Redirect to results page
        return redirect(url_for('face_analysis.results', analysis_id=analysis.id))
    except Exception as e:
        logger.error(f"Error processing face analysis: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Create a minimal analysis entry to record the error
        try:
            if 'analysis' not in locals() or analysis is None:
                # Create a new analysis object for error recording
                analysis = FaceAnalysis()
                analysis.user_id = current_user.id if current_user.is_authenticated else None
                analysis.image_path = file_path if 'file_path' in locals() and file_path else "error_no_file"
                analysis.analysis_data = {
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                analysis.is_anonymous = not current_user.is_authenticated
                db.session.add(analysis)
            else:
                # Update existing analysis object with error info
                analysis.analysis_data = {
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as creation_error:
            logger.error(f"Failed to create error analysis record: {creation_error}")
            # Set analysis to None to prevent further issues
            analysis = None
        
        try:
            db.session.commit()
        except Exception as db_error:
            logger.error(f"Error commit failed: {db_error}")
            db.session.rollback()
        
        flash('Failed to analyze the image. Please try again with a clearer facial photo.', 'error')
        return redirect(url_for('face_analysis.index'))

@face_analysis.route('/results/<int:analysis_id>')
def results(analysis_id):
    """Display the face analysis results."""
    # Get the analysis record
    analysis = FaceAnalysis.query.get_or_404(analysis_id)
    
    # Check if the user can access this analysis
    if analysis.user_id and current_user.is_authenticated and (analysis.user_id != current_user.id) and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        flash('You do not have permission to view this analysis.', 'error')
        return redirect(url_for('face_analysis.index'))
    
    # Ensure analysis_data is properly formatted
    if not analysis.analysis_data or analysis.analysis_data is None:
        analysis.analysis_data = {
            'error': 'Analysis data not available',
            'mathematical_scores': {
                'golden_ratio_score': 0,
                'symmetry_score': 0,
                'facial_thirds_score': 0,
                'facial_fifths_score': 0,
                'ogee_curve_score': 0,
                'neoclassical_score': 0,
                'facial_harmony_score': 0
            }
        }
    
    # Get the recommendations
    skin_recs = FaceAnalysisRecommendation.query.filter_by(
        analysis_id=analysis_id, recommendation_type='skin'
    ).all()
    
    structure_recs = FaceAnalysisRecommendation.query.filter_by(
        analysis_id=analysis_id, recommendation_type='structure'
    ).all()
    
    surgical_recs = FaceAnalysisRecommendation.query.filter_by(
        analysis_id=analysis_id, recommendation_type='surgical'
    ).all()
    
    # Serialize recommendations to a format that can be JSON encoded
    skin_recommendations = [
        {
            'id': rec.id,
            'title': rec.feature_name,
            'description': rec.recommendation_details,
            'confidence': rec.severity_score,
            'treatment_options': rec.treatment_options,
            'recommendation_type': rec.recommendation_type,
            'needs_surgery': getattr(rec, 'needs_surgery', False)
        } for rec in skin_recs
    ]
    
    structure_recommendations = [
        {
            'id': rec.id,
            'title': rec.feature_name,
            'description': rec.recommendation_details,
            'confidence': rec.severity_score,
            'treatment_options': rec.treatment_options,
            'recommendation_type': rec.recommendation_type,
            'needs_surgery': getattr(rec, 'needs_surgery', False)
        } for rec in structure_recs
    ]
    
    surgical_recommendations = [
        {
            'id': rec.id,
            'title': rec.feature_name,
            'description': rec.recommendation_details,
            'confidence': rec.severity_score,
            'treatment_options': rec.treatment_options,
            'recommendation_type': rec.recommendation_type,
            'needs_surgery': True
        } for rec in surgical_recs
    ]
    
    # Convert analysis data for template - ensure analysis_data is JSON serializable
    safe_analysis_data = {}
    if hasattr(analysis, 'analysis_data') and analysis.analysis_data:
        if isinstance(analysis.analysis_data, dict):
            safe_analysis_data = analysis.analysis_data
        else:
            safe_analysis_data = {}
    
    analysis_data = {
        'id': analysis.id,
        'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'image_path': analysis.image_path,
        'skin_analysis': safe_analysis_data.get('skin_analysis', ''),
        'structural_analysis': safe_analysis_data.get('structural_analysis', ''),
        'overall_summary': safe_analysis_data.get('summary', ''),
        'analysis_data': safe_analysis_data  # Include the raw analysis data for template
    }
    
    # Render the results template
    return render_template(
        'face_analysis/results.html',
        analysis=analysis_data,
        skin_recommendations=skin_recommendations,
        structure_recommendations=structure_recommendations,
        surgical_recommendations=surgical_recommendations
    )

@face_analysis.route('/history')
@login_required
def history():
    """Display the user's face analysis history."""
    analyses = FaceAnalysis.query.filter_by(user_id=current_user.id).order_by(FaceAnalysis.created_at.desc()).all()
    return render_template('face_analysis/history.html', analyses=analyses)