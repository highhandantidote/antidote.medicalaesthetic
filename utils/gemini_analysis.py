#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Analysis API Utility Module

This module provides utilities for facial analysis using Google's Gemini Pro Vision model.
It handles image processing, API integration, and result formatting for the face analysis feature.
"""

import os
import base64
import json
import logging
from datetime import datetime

# Import Google Generative AI package
import google.generativeai as genai
from flask import current_app

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the Gemini API with the API key from environment variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Set the API key
if GOOGLE_API_KEY:
    try:
        # Configure the API
        genai.configure(api_key=GOOGLE_API_KEY)
        logger.info("Gemini API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {e}")
else:
    logger.warning("GOOGLE_API_KEY environment variable not set")
    
# Define the model to use
GEMINI_MODEL = "gemini-1.5-flash"

def encode_image_to_base64(image_path):
    """
    Encode an image file to base64 for API transmission.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string of the image
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image: {e}")
        return None

def analyze_face_image(image_path, user_info=None):
    """
    Analyze a facial image using Google's Gemini Pro Vision model.
    
    Args:
        image_path: Path to the facial image
        user_info: Optional dictionary containing user information like age, concerns, etc.
        
    Returns:
        Dictionary containing analysis results and recommendations
    """
    logger.info(f"Starting facial analysis for image at {image_path}")
    logger.info(f"User info: {user_info}")
    
    try:
        # Check if the API key is available
        if not GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY is not set")
            return {"error": "API key not configured. Contact the administrator."}
            
        # Check if the image file exists
        if not os.path.exists(image_path):
            logger.error(f"Image file does not exist: {image_path}")
            return {"error": "Image file not found"}
            
        # Encode the image to base64
        logger.info("Encoding image to base64")
        encoded_image = encode_image_to_base64(image_path)
        if not encoded_image:
            logger.error("Failed to encode image to base64")
            return {"error": "Failed to encode image"}
        
        # Create the model
        logger.info(f"Creating Gemini model: {GEMINI_MODEL}")
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Extract user info for prompt context
        age = user_info.get('age', None) if user_info else None
        gender = user_info.get('gender', '') if user_info else ''
        concerns = user_info.get('concerns', '') if user_info else ''
        history = user_info.get('history', '') if user_info else ''
        
        # Define the prompt for skin analysis
        skin_analysis_prompt = """
        I want you to act as an expert dermatologist and cosmetic surgeon. Analyze this face photo with the following objectives:
        
        1. SKIN ANALYSIS:
        - Identify visible skin conditions (acne, rosacea, hyperpigmentation, texture issues, scarring, etc.)
        - Rate each condition's severity on a scale of 0.1-1.0
        - Carefully assess any visible scars, burn marks, or keloid formations
        - For severe conditions (severity > 0.7), always include surgical treatment options
        - Identify signs of aging (fine lines, wrinkles, volume loss) if present
        
        2. FACIAL STRUCTURE ANALYSIS:
        - Evaluate facial symmetry and proportions
        - Identify any structural features that could be enhanced
        - Note facial shape and characteristics
        - Assess need for reconstructive procedures if applicable
        
        3. SURGICAL INTERVENTION ASSESSMENT:
        - For any severe condition (scarring, burn marks, asymmetry) with severity > 0.7, explicitly assess if surgical intervention is advisable
        - Provide specific surgical procedure recommendations when appropriate
        - Consider both reconstructive and cosmetic surgical approaches
        
        Format your response as structured JSON with these sections:
        {
          "timestamp": "current_time",
          "skin_analysis": [
            {
              "name": "condition_name",
              "severity": 0.x,
              "details": "brief description",
              "treatments": "possible treatments including non-surgical and surgical options",
              "needs_surgery": true/false
            }
          ],
          "facial_structure": [
            {
              "name": "feature_name",
              "prominence": 0.x,
              "details": "description of feature",
              "treatments": "possible enhancements including surgical options if appropriate",
              "needs_surgery": true/false
            }
          ],
          "surgical_recommendations": [
            {
              "procedure_name": "name of surgical procedure",
              "target_condition": "condition being addressed",
              "urgency": 0.x,
              "description": "description of procedure",
              "expected_outcomes": "expected benefits"
            }
          ],
          "overall_summary": "brief overall assessment including mention of surgical needs if present"
        }
        
        IMPORTANT GUIDELINES:
        - Focus ONLY on visible features in the image
        - Remain objective and clinical
        - DO NOT include disclaimers or caveats in your JSON
        - DO NOT hesitate to recommend surgical procedures for severe conditions
        - For severe scarring, burns, or facial deformities, ALWAYS include appropriate surgical options
        - If something is unclear from the image, do not include it rather than guessing
        - Present results suitable for a cosmetic surgery and medical procedure marketplace
        """
        
        # Add user-specific context to the prompt if available
        context_prompt = ""
        if age or gender or concerns or history:
            context_prompt = "User-provided context:\n"
            if age:
                context_prompt += f"- Age: {age}\n"
            if gender:
                context_prompt += f"- Gender: {gender}\n"
            if concerns:
                context_prompt += f"- Stated concerns: {concerns}\n"
            if history:
                context_prompt += f"- Treatment history: {history}\n"
            context_prompt += "\nPlease consider this information in your analysis.\n"
            
        full_prompt = skin_analysis_prompt
        if context_prompt:
            full_prompt = context_prompt + "\n" + skin_analysis_prompt
        
        # Call the Gemini API with the image and prompt
        try:
            logger.info("Calling Gemini API with image and prompt")
            
            # Create a model instance
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            # Create the content with the prompt and image
            contents = [
                full_prompt,
                {"mime_type": "image/jpeg", "data": encoded_image}
            ]
            
            # Generate content with the model
            response = model.generate_content(contents)
            
            logger.info("Successfully received response from Gemini API")
        except Exception as api_error:
            logger.error(f"Error in API call: {api_error}")
            return {"error": f"API call failed: {str(api_error)}"}
        
        # Process the API response
        response_text = response.text
        
        # Convert response to structured data
        # First, try to extract JSON directly
        try:
            # Look for JSON structure in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                structured_result = json.loads(json_str)
                logger.info(f"Successfully parsed JSON response from Gemini API")
            else:
                # If no JSON is found, create a structured result with the response text
                logger.warning("No JSON found in response, creating structured result manually")
                structured_result = {
                    "timestamp": datetime.now().isoformat(),
                    "skin_analysis": [],
                    "facial_structure": [],
                    "overall_summary": "Analysis completed but response format was not as expected."
                }
                
                # Add the raw text for debugging
                structured_result["raw_response"] = response_text
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            structured_result = {
                "timestamp": datetime.now().isoformat(),
                "skin_analysis": [],
                "facial_structure": [],
                "overall_summary": "Analysis completed but couldn't parse structured data.",
                "raw_response": response_text
            }
        
        # Add image path to the result
        structured_result["image_path"] = image_path
        
        # Return the structured result
        return structured_result
    
    except Exception as e:
        logger.error(f"Error analyzing face: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Face analysis failed: {str(e)}"}

def extract_recommendations(analysis_result):
    """
    Extract recommendations from analysis result.
    
    Args:
        analysis_result: The analysis result from analyze_face_image
        
    Returns:
        Dictionary containing extracted recommendations including surgical options
    """
    recommendations = {
        "skin": [],
        "structure": [],
        "surgical": []
    }
    
    # Extract skin recommendations
    for item in analysis_result.get("skin_analysis", []):
        if "name" in item and "severity" in item:
            recommendations["skin"].append({
                "name": item["name"],
                "severity": item["severity"],
                "details": item.get("details", ""),
                "treatments": item.get("treatments", ""),
                "needs_surgery": item.get("needs_surgery", False)
            })
    
    # Extract structure recommendations
    for item in analysis_result.get("facial_structure", []):
        if "name" in item and "prominence" in item:
            recommendations["structure"].append({
                "name": item["name"],
                "prominence": item["prominence"],
                "details": item.get("details", ""),
                "treatments": item.get("treatments", ""),
                "needs_surgery": item.get("needs_surgery", False)
            })
    
    # Extract surgical recommendations
    for item in analysis_result.get("surgical_recommendations", []):
        if "procedure_name" in item and "target_condition" in item:
            recommendations["surgical"].append({
                "procedure_name": item["procedure_name"],
                "target_condition": item["target_condition"],
                "urgency": item.get("urgency", 0.5),
                "description": item.get("description", ""),
                "expected_outcomes": item.get("expected_outcomes", "")
            })
    
    return recommendations

def analyze_face_image_enhanced(image_path, user_info=None):
    """
    Enhanced facial image analysis combining Gemini AI with geometric analysis.
    
    Args:
        image_path: Path to the facial image
        user_info: Optional dictionary containing user information
        
    Returns:
        Dictionary containing comprehensive analysis results
    """
    try:
        # Perform Gemini AI analysis
        gemini_result = analyze_face_image(image_path, user_info)
        
        # Import geometric analyzer (avoid circular imports)
        try:
            from utils.geometric_analysis import FacialGeometricAnalyzer
            from utils.visualization import FacialVisualizationGenerator
            
            # Perform geometric analysis
            geometric_analyzer = FacialGeometricAnalyzer()
            geometric_result = geometric_analyzer.analyze_face(image_path)
            
            # Generate visualization data
            viz_generator = FacialVisualizationGenerator()
            
            if 'error' not in geometric_result and geometric_result.get('landmarks_data'):
                landmarks_data = geometric_result['landmarks_data']
                
                # Generate overlays for different analysis types
                golden_ratio_overlay = viz_generator.generate_golden_ratio_overlay(landmarks_data, geometric_result)
                symmetry_overlay = viz_generator.generate_symmetry_overlay(landmarks_data, geometric_result)
                thirds_overlay = viz_generator.generate_facial_thirds_overlay(landmarks_data, geometric_result)
                fifths_overlay = viz_generator.generate_facial_fifths_overlay(landmarks_data, geometric_result)
                neoclassical_overlay = viz_generator.generate_neoclassical_overlay(landmarks_data, geometric_result)
                
                # Generate measurement annotations
                annotations = viz_generator.generate_measurement_annotations(geometric_result)
                
                # Combine results
                enhanced_result = {
                    **gemini_result,
                    'geometric_analysis': geometric_result,
                    'visualizations': {
                        'golden_ratio': golden_ratio_overlay,
                        'symmetry': symmetry_overlay,
                        'facial_thirds': thirds_overlay,
                        'facial_fifths': fifths_overlay,
                        'neoclassical': neoclassical_overlay
                    },
                    'annotations': annotations,
                    'mathematical_scores': {
                        'golden_ratio_score': geometric_result.get('golden_ratio_analysis', {}).get('overall_score', 0),
                        'symmetry_score': geometric_result.get('symmetry_analysis', {}).get('overall_score', 0),
                        'facial_thirds_score': 100 - geometric_result.get('facial_thirds_analysis', {}).get('deviation_score', 100),
                        'facial_fifths_score': 100 - geometric_result.get('facial_fifths_analysis', {}).get('deviation_score', 100),
                        'neoclassical_score': geometric_result.get('neoclassical_canons', {}).get('overall_score', 0),
                        'ogee_curve_score': geometric_result.get('ogee_curve_analysis', {}).get('overall_score', 0),
                        'facial_harmony_score': geometric_result.get('facial_harmony_score', {}).get('overall_score', 0)
                    },
                    'has_geometric_analysis': True
                }
                
                logger.info("Enhanced face analysis with geometric measurements completed successfully")
                return enhanced_result
            else:
                # Geometric analysis failed, return Gemini results with error note
                logger.warning("Geometric analysis failed, returning Gemini analysis only")
                return {
                    **gemini_result,
                    'geometric_analysis': {'error': 'Geometric analysis unavailable'},
                    'mathematical_scores': {
                        'golden_ratio_score': 0,
                        'symmetry_score': 0,
                        'facial_thirds_score': 0,
                        'facial_fifths_score': 0,
                        'neoclassical_score': 0,
                        'ogee_curve_score': 0,
                        'facial_harmony_score': 0
                    },
                    'has_geometric_analysis': False
                }
                
        except ImportError as e:
            logger.error(f"Could not import geometric analysis modules: {e}")
            return {
                **gemini_result,
                'geometric_analysis': {'error': 'Geometric analysis modules unavailable'},
                'has_geometric_analysis': False
            }
            
    except Exception as e:
        logger.error(f"Error in enhanced face analysis: {e}")
        return {
            'error': f'Enhanced analysis failed: {str(e)}',
            'success': False,
            'has_geometric_analysis': False
        }

if __name__ == "__main__":
    # Test the face analysis
    image_path = "test_image.jpg"
    user_info = {
        "age": 30,
        "gender": "female",
        "concerns": "Wrinkles around eyes, uneven skin tone",
        "history": "Regular use of retinol cream"
    }
    
    print(f"Testing face analysis with image: {image_path}")
    result = analyze_face_image_enhanced(image_path, user_info)
    print(json.dumps(result, indent=2))