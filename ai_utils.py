#!/usr/bin/env python3
"""
AI utilities for the medical marketplace platform.

This module provides AI-related functionality using Google's Gemini AI and Anthropic Claude.
"""
import os
import json
import logging
import base64

# Import AI services with error handling
try:
    import google.generativeai as genai
except ImportError:
    logging.error("Google Generative AI library not installed. Install with: pip install google-generativeai")
    genai = None

try:
    import anthropic
    from anthropic import Anthropic
except ImportError:
    logging.error("Anthropic library not installed. Install with: pip install anthropic")
    anthropic = None
    Anthropic = None

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ai_utils")

# Initialize Gemini AI client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if genai:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("Google Generative AI client not available - some AI features will be limited")

# Initialize Anthropic client for audio transcription
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if Anthropic and ANTHROPIC_API_KEY:
    try:
        anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("Anthropic client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {str(e)}")
        anthropic_client = None
else:
    logger.warning("Anthropic client not available - audio transcription will be limited")
    anthropic_client = None

# Set up the model configuration
generation_config = {
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

def analyze_health_query(text, image_base64=None, additional_concerns=None):
    """
    Analyze a health-related query using Google's Gemini model.
    
    Args:
        text (str): The user's query text (can be in any Indian language)
        image_base64 (str, optional): Base64-encoded image for analysis
        additional_concerns (list, optional): List of additional health concerns to analyze
        
    Returns:
        dict: Analysis results including detected concerns, recommended procedures,
              and any additional insights
    """
    try:
        # Check if Gemini module is available
        if not genai:
            logger.error("Google Generative AI module not available")
            return {
                "error": "Google Generative AI service unavailable",
                "primary_concern": text[:30] + "..." if len(text) > 30 else text,
                "body_part": "Not detected",
                "symptoms": [],
                "potential_procedures": ["Hair Transplant", "Rhinoplasty"] if "hair" in text.lower() or "nose" in text.lower() else [],
                "severity": "medium",
                "language_detected": "Not detected"
            }
            
        # Create the system prompt with support for multiple conditions
        system_prompt = """You are an AI assistant for a medical marketplace platform in India. 
        Your job is to analyze the user's health concerns (which could be in any Indian language) 
        and/or analyze medical images they provide.
        
        CRITICALLY IMPORTANT FOR IMAGES: If an image is provided, it contains critical medical information!
        Carefully analyze the image for:
        - Facial scars, marks, or irregularities
        - Skin conditions or discoloration
        - Hair loss patterns or hairline issues
        - Facial asymmetry or structural abnormalities
        - Any other visible medical condition
        
        NEW FEATURE: The user may describe multiple health concerns. If they do, identify each distinct concern.
        
        You must extract the following information:
        1. The primary health concern (be specific about what you see in the image if provided)
        2. Body part or area affected (be specific, e.g., "right cheek", "forehead", "hairline")
        3. Any symptoms mentioned or visibly apparent in the image
        4. Potential medical or cosmetic procedures that might address these concerns
        5. The severity level (low, medium, high)
        6. Additional concerns if multiple conditions are described
        
        IMPORTANT: You MUST respond ONLY with a valid JSON object containing these exact fields:
        {
            "primary_concern": "string",
            "body_part": "string",
            "symptoms": ["string"],
            "potential_procedures": ["string"],
            "severity": "string",
            "language_detected": "string",
            "additional_concerns": [
                {
                    "concern": "string",
                    "body_part": "string",
                    "symptoms": ["string"],
                    "potential_procedures": ["string"],
                    "severity": "string"
                }
            ]
        }
        
        For the "potential_procedures" field, prioritize these procedures if they match the concern:
        - Hair Transplant
        - PRP Therapy for Hair Loss
        - Rhinoplasty
        - Facelift
        - Scar Revision
        - Skin Resurfacing
        
        If you see a facial scar in the image, always include "Scar Revision" as a procedure.
        If you see skin texture issues, always include "Skin Resurfacing" as a procedure.
        
        If the user has "Additional Health Concerns:" followed by numbered items, each of these should be included as a separate entry in the "additional_concerns" array.
        
        DO NOT include any explanatory text outside the JSON. Return only a single valid JSON object."""
        
        try:
            # Initialize Gemini model - using the fully qualified model name
            # Using the latest Gemini 1.5-flash model which is faster and more efficient
            model = genai.GenerativeModel('models/gemini-1.5-flash')
            
            # Prepare the content
            prompt = f"{system_prompt}\n\nUser's health concern: {text}"
            
            # Add additional concerns if provided
            if additional_concerns and isinstance(additional_concerns, list) and len(additional_concerns) > 0:
                prompt += "\n\nAdditional Health Concerns:\n"
                for i, concern in enumerate(additional_concerns, 1):
                    prompt += f"{i}. {concern}\n"
            
            # Handle image if provided
            if image_base64:
                # Log image processing attempt
                logger.info("Processing image for health query analysis")
                
                try:
                    # Enhance prompt to ensure image is considered in analysis
                    image_specific_prompt = prompt + "\n\nIMPORTANT: The image provided shows a medical condition. Please analyze it carefully. If you see a facial scar, skin issue, hair loss, or other visible condition, include it in your analysis."
                    
                    # Use the newer Gemini 1.5 model for multimodal analysis
                    # Note: gemini-1.5-flash is the updated version for gemini-pro-vision which was deprecated on July 12, 2024
                    vision_model = genai.GenerativeModel('models/gemini-1.5-flash')
                    
                    try:
                        # Decode the base64 image to binary
                        decoded_image = base64.b64decode(image_base64)
                        logger.info(f"Decoded image size: {len(decoded_image)} bytes")
                    except Exception as decode_error:
                        logger.error(f"Error decoding base64 image: {str(decode_error)}")
                        raise ValueError("Invalid image data")
                    
                    # Create image part
                    image_part = {
                        "mime_type": "image/jpeg",
                        "data": decoded_image
                    }
                    
                    logger.info("Sending multimodal request to Gemini API")
                    # Get appropriate MIME type based on image data signature
                    mime_type = "image/jpeg"  # Default
                    
                    # Check for image signatures to determine the correct MIME type
                    if decoded_image[:2] == b'\xff\xd8':
                        mime_type = "image/jpeg"
                    elif decoded_image[:8] == b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A':
                        mime_type = "image/png"
                    elif decoded_image[:6] in (b'GIF87a', b'GIF89a'):
                        mime_type = "image/gif" 
                    elif decoded_image[:4] == b'RIFF' and decoded_image[8:12] == b'WEBP':
                        mime_type = "image/webp"
                    elif decoded_image[:2] in (b'MM', b'II'):
                        mime_type = "image/tiff"
                    
                    logger.info(f"Detected image MIME type: {mime_type}")
                    
                    # Create content parts in the correct format for Gemini API
                    content_parts = [
                        {"text": image_specific_prompt},
                        {"inline_data": {
                            "mime_type": mime_type,
                            "data": image_base64
                        }}
                    ]
                    
                    # Generate content with both text and image
                    try:
                        logger.info("Attempting to send request with correct format")
                        response = vision_model.generate_content(
                            content_parts,
                            generation_config=generation_config
                        )
                    except Exception as format_error:
                        logger.error(f"Error with new format: {str(format_error)}")
                        # Try alternative format
                        logger.info("Trying alternative format for Gemini API")
                        response = vision_model.generate_content(
                            [image_specific_prompt, decoded_image],
                            generation_config=generation_config
                        )
                    logger.info("Received response from Gemini for multimodal request")
                except Exception as img_error:
                    logger.error(f"Error processing image: {str(img_error)}")
                    # Fall back to text-only analysis if image processing fails
                    logger.info("Falling back to text-only analysis")
                    response = model.generate_content(
                        prompt + "\n(Note: Image analysis failed, proceeding with text-only analysis)",
                        generation_config=generation_config
                    )
            else:
                # Text-only analysis with standard model
                logger.info("Performing text-only analysis")
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
        except Exception as model_error:
            logger.error(f"Error with Gemini model: {str(model_error)}")
            raise ValueError(f"Failed to process with Google Gemini: {str(model_error)}")
        
        # Parse the JSON response
        try:
            analysis = json.loads(response.text)
        except json.JSONDecodeError:
            # Handle case where response might not be valid JSON
            logger.warning(f"Response not in JSON format: {response.text}")
            # Try to extract JSON from the text (Gemini sometimes wraps JSON in markdown code blocks)
            import re
            
            # Check for markdown code blocks with JSON
            json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', response.text, re.DOTALL)
            if json_match:
                try:
                    analysis = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    # If still can't parse, try fixing common JSON issues
                    json_str = json_match.group(1)
                    # Fix unquoted keys
                    fixed_json = re.sub(r'(\s*)(\w+)(\s*):', r'\1"\2"\3:', json_str)
                    # Fix trailing commas
                    fixed_json = re.sub(r',\s*}', '}', fixed_json)
                    fixed_json = re.sub(r',\s*]', ']', fixed_json)
                    try:
                        analysis = json.loads(fixed_json)
                    except json.JSONDecodeError:
                        raise ValueError("Could not parse JSON from markdown code block")
            else:
                # Try to extract JSON object directly with regex
                json_match = re.search(r'({[\s\S]*?})', response.text, re.DOTALL)
                if json_match:
                    try:
                        analysis = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        raise ValueError("Could not parse JSON from response")
                else:
                    raise ValueError("Could not find JSON in response")
        
        logger.debug(f"Analysis results: {analysis}")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing health query: {str(e)}")
        return {
            "error": str(e),
            "primary_concern": None,
            "body_part": None,
            "symptoms": [],
            "potential_procedures": [],
            "severity": None,
            "language_detected": None
        }

def transcribe_audio(audio_file_path):
    """
    Attempt to transcribe audio from a file using available AI services.
    
    This function will try different transcription methods based on available API keys
    and provide a friendly fallback message if transcription fails.
    
    Args:
        audio_file_path (str): Path to the audio file
        
    Returns:
        str: Transcribed text or friendly fallback message
    """
    try:
        # Read audio file as binary data
        with open(audio_file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        # Check if audio file is empty
        if len(audio_data) == 0:
            logger.warning("Audio file is empty")
            return "We couldn't process your audio. Please try speaking more clearly or type your health concern."
        
        # Try Anthropic Claude API if available and has credit
        if anthropic_client and ANTHROPIC_API_KEY:
            try:
                # Encode audio to base64
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                # Determine MIME type based on file extension
                mime_type = "audio/mpeg"  # default
                if audio_file_path.lower().endswith('.wav'):
                    mime_type = "audio/wav"
                elif audio_file_path.lower().endswith('.mp3'):
                    mime_type = "audio/mpeg"
                elif audio_file_path.lower().endswith('.m4a'):
                    mime_type = "audio/mp4"
                elif audio_file_path.lower().endswith('.webm'):
                    mime_type = "audio/webm"
                
                # Log attempt to use Anthropic
                logger.info(f"Attempting to transcribe audio using Anthropic Claude with mime type: {mime_type}")
                
                try:
                    # Create message for Claude
                    message = anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1024,
                        temperature=0.0,
                        system="You are a medical transcription assistant that accurately transcribes audio related to health concerns. Focus only on transcribing the content exactly as spoken. Do not analyze or add commentary.",
                        messages=[
                            {
                                "role": "user", 
                                "content": [
                                    {
                                        "type": "text", 
                                        "text": "Please transcribe this audio recording of a health concern. Only transcribe what was said, don't add any analysis."
                                    },
                                    {
                                        "type": "image", 
                                        "source": {
                                            "type": "base64",
                                            "media_type": mime_type,
                                            "data": audio_base64
                                        }
                                    }
                                ]
                            }
                        ]
                    )
                    
                    # Extract transcription from response
                    transcription = message.content[0].text.strip()
                    
                    # Log successful transcription
                    logger.info(f"Successfully transcribed audio: {transcription[:50]}...")
                    
                    return transcription
                except Exception as api_error:
                    logger.error(f"Anthropic API error: {str(api_error)}")
                    # Fall through to fallback mechanism
            except Exception as anthropic_error:
                logger.warning(f"Anthropic transcription failed: {str(anthropic_error)}")
                # Continue to fallback options
        
        # Provide a friendly fallback message
        logger.info("Using friendly fallback message for audio transcription")
        return "We heard your audio recording. Please also type your health concern in the text box for better results."
        
    except Exception as e:
        logger.error(f"Error in audio transcription process: {str(e)}")
        return "We couldn't process your audio. Please type your health concern instead."

def get_doctor_recommendations(analysis, limit=3):
    """
    Get doctor recommendations based on the analysis results.
    
    Args:
        analysis (dict): The analysis results from analyze_health_query
        limit (int, optional): Maximum number of doctors to recommend
        
    Returns:
        list: Recommended doctor objects
    """
    from models import Doctor, DoctorProcedure, Procedure
    from app import db
    from sqlalchemy import or_
    
    try:
        recommended_doctors = []
        
        # Extract the body part and potential procedures from the analysis
        body_part = analysis.get("body_part", "").lower() if analysis.get("body_part") else ""
        primary_concern = analysis.get("primary_concern", "").lower()
        potential_procedures = analysis.get("potential_procedures", [])
        
        # Map body parts to doctor specialties
        specialty_map = {
            "hair": ["hair transplant", "hair restoration", "dermatology"],
            "face": ["facial plastic surgery", "plastic surgery", "cosmetic surgery"],
            "nose": ["rhinoplasty", "ent", "facial plastic surgery"],
            "skin": ["dermatology", "cosmetic dermatology"],
            "eye": ["oculoplasty", "ophthalmology"],
            "neck": ["neck surgery", "plastic surgery"]
        }
        
        # Determine relevant specialties based on body part
        target_specialties = []
        for body_area, specialties in specialty_map.items():
            if body_area in body_part or body_area in primary_concern:
                target_specialties.extend(specialties)
        
        # First try: Find procedures that match the potential procedures
        if potential_procedures:
            try:
                # Get all procedures that match the names in potential_procedures
                # Use ilike for each name instead of 'in_' operator
                procedure_filters = []
                for proc_name in potential_procedures:
                    procedure_filters.append(Procedure.procedure_name.ilike(f"%{proc_name}%"))
                
                procedures = Procedure.query.filter(or_(*procedure_filters)).all()
                
                # If no exact matches, try to find procedures by body part
                if not procedures and body_part:
                    procedures = Procedure.query.filter(
                        Procedure.body_part.ilike(f"%{body_part}%")
                    ).all()
                
                # Get the IDs of the matching procedures
                procedure_ids = [p.id for p in procedures]
                
                if procedure_ids:
                    # Find doctors who perform these procedures using individual queries
                    # to avoid JOIN issues with JSON fields
                    for proc_id in procedure_ids:
                        doctor_procs = DoctorProcedure.query.filter(
                            DoctorProcedure.procedure_id == proc_id
                        ).limit(limit).all()
                        
                        doctor_ids = [dp.doctor_id for dp in doctor_procs]
                        if doctor_ids:
                            doctors = Doctor.query.filter(Doctor.id.in_(doctor_ids)).all()
                            for doc in doctors:
                                if doc not in recommended_doctors:
                                    recommended_doctors.append(doc)
                                    if len(recommended_doctors) >= limit:
                                        break
                            
                            if len(recommended_doctors) >= limit:
                                break
            except Exception as e:
                logger.warning(f"Error finding doctors by procedures: {str(e)}")
        
        # If no doctors found through procedures, find by specialty
        if len(recommended_doctors) < limit and target_specialties:
            try:
                # Build filters for specialties
                specialty_filters = []
                for specialty in target_specialties:
                    specialty_filters.append(Doctor.specialty.ilike(f"%{specialty}%"))
                
                # Query doctors with matching specialties
                doctors = Doctor.query.filter(or_(*specialty_filters)).limit(limit - len(recommended_doctors)).all()
                
                for doc in doctors:
                    if doc not in recommended_doctors:
                        recommended_doctors.append(doc)
            except Exception as e:
                logger.warning(f"Error finding doctors by specialty: {str(e)}")
        
        # Third attempt: Find by general body part match in specialty
        if len(recommended_doctors) < limit and body_part:
            try:
                doctors = Doctor.query.filter(
                    Doctor.specialty.ilike(f"%{body_part}%")
                ).limit(limit - len(recommended_doctors)).all()
                
                for doc in doctors:
                    if doc not in recommended_doctors:
                        recommended_doctors.append(doc)
            except Exception as e:
                logger.warning(f"Error finding doctors by body part: {str(e)}")
        
        return recommended_doctors[:limit]
        
    except Exception as e:
        logger.error(f"Error getting doctor recommendations: {str(e)}")
        return []

def get_procedure_recommendations(analysis, limit=5):
    """
    Get procedure recommendations based on the analysis results.
    
    Args:
        analysis (dict): The analysis results from analyze_health_query
        limit (int, optional): Maximum number of procedures to recommend
        
    Returns:
        list: Recommended procedure objects
    """
    from models import Procedure
    
    try:
        # Extract the body part and potential procedures from the analysis
        body_part = analysis.get("body_part", "").lower() if analysis.get("body_part") else ""
        primary_concern = analysis.get("primary_concern", "").lower()
        potential_procedures = analysis.get("potential_procedures", [])
        
        recommended_procedures = []
        
        # Map body parts to categories for precise matching
        body_part_map = {
            "hair": ["scalp", "head"],
            "face": ["cheek", "chin", "forehead"],
            "nose": ["nostril", "nasal"],
            "skin": ["complexion", "dermal"],
            "eye": ["eyelid", "vision"],
            "neck": ["throat", "cervical"]
        }
        
        # Determine primary body area category
        primary_body_area = None
        for area, synonyms in body_part_map.items():
            if area in body_part or any(s in body_part for s in synonyms):
                primary_body_area = area
                break
        
        # For hair-related concerns, only recommend hair treatments
        hair_related_terms = ["hair", "scalp", "bald", "thin hair", "hairline", "receding"]
        is_hair_related = (
            primary_body_area == "hair" or 
            "hair" in primary_concern or 
            any(term in primary_concern for term in hair_related_terms)
        )
        
        # For facial concerns, only recommend face treatments
        face_related_terms = ["face", "facial", "cheek", "wrinkle", "aging", "chin"]
        is_face_related = (
            primary_body_area == "face" or
            "face" in primary_concern or
            any(term in primary_concern for term in face_related_terms)
        )
        
        # For nose concerns, only recommend nose treatments
        nose_related_terms = ["nose", "nasal", "nostril", "breathing", "rhinoplasty"]
        is_nose_related = (
            primary_body_area == "nose" or
            "nose" in primary_concern or
            any(term in primary_concern for term in nose_related_terms)
        )
        
        # First, try to find procedures that match the potential procedures from the analysis
        if potential_procedures:
            for proc_name in potential_procedures:
                procedures = Procedure.query.filter(
                    Procedure.procedure_name.ilike(f"%{proc_name}%")
                ).all()
                
                for proc in procedures:
                    # Apply strict body part filtering
                    if is_hair_related and "hair" not in proc.body_part.lower() and "scalp" not in proc.body_part.lower():
                        continue
                    if is_face_related and "face" not in proc.body_part.lower():
                        continue
                    if is_nose_related and "nose" not in proc.body_part.lower():
                        continue
                        
                    if proc not in recommended_procedures:
                        recommended_procedures.append(proc)
                
                # Break if we have enough recommendations
                if len(recommended_procedures) >= limit:
                    break
        
        # If we don't have enough, try a more direct match by exact body part
        if len(recommended_procedures) < limit and body_part:
            body_part_procedures = Procedure.query.filter(
                Procedure.body_part.ilike(f"%{body_part}%")
            ).all()
            
            for proc in body_part_procedures:
                # Apply the same strict filtering
                if is_hair_related and "hair" not in proc.body_part.lower() and "scalp" not in proc.body_part.lower():
                    continue
                if is_face_related and "face" not in proc.body_part.lower():
                    continue
                if is_nose_related and "nose" not in proc.body_part.lower():
                    continue
                    
                if proc not in recommended_procedures:
                    recommended_procedures.append(proc)
                    
                if len(recommended_procedures) >= limit:
                    break
        
        # If we still don't have any recommendations, fallback to basic category matching
        # but only if we have a clear body area match
        if len(recommended_procedures) == 0 and primary_body_area:
            # For hair issues, only show hair treatments
            if is_hair_related:
                hair_procedures = Procedure.query.filter(
                    (Procedure.body_part.ilike("%hair%") | Procedure.body_part.ilike("%scalp%") | Procedure.body_part.ilike("%head%"))
                ).limit(limit).all()
                recommended_procedures.extend(hair_procedures)
            
            # For face issues, only show face treatments
            elif is_face_related:
                face_procedures = Procedure.query.filter(
                    Procedure.body_part.ilike("%face%")
                ).limit(limit).all()
                recommended_procedures.extend(face_procedures)
            
            # For nose issues, only show nose treatments
            elif is_nose_related:
                nose_procedures = Procedure.query.filter(
                    Procedure.body_part.ilike("%nose%")
                ).limit(limit).all()
                recommended_procedures.extend(nose_procedures)
        
        # Keep only unique procedures and limit to requested count
        unique_procedures = []
        for proc in recommended_procedures:
            if proc not in unique_procedures:
                unique_procedures.append(proc)
            if len(unique_procedures) >= limit:
                break
        
        return unique_procedures
        
    except Exception as e:
        logger.error(f"Error getting procedure recommendations: {str(e)}")
        return []

def test_gemini_connection():
    """Test the Gemini API connection."""
    try:
        model = genai.GenerativeModel('models/gemini-1.5-pro')
        response = model.generate_content("Hello, are you working?")
        return True, "Gemini API connection successful"
    except Exception as e:
        return False, f"Gemini API connection failed: {str(e)}"

if __name__ == "__main__":
    # Test Gemini connection
    success, message = test_gemini_connection()
    print(message)