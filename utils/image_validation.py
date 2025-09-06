#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Validation Module for Face Analysis

This module provides comprehensive image validation to ensure proper
frontal positioning and image quality for accurate facial analysis.
"""

import cv2
import numpy as np
import logging
from typing import Dict, Tuple, Optional
from .facial_landmarks import FacialLandmarkDetector

# Configure logging
logger = logging.getLogger(__name__)

class ImageValidator:
    """Validates facial images for proper positioning and quality."""
    
    def __init__(self):
        """Initialize the image validator."""
        self.landmark_detector = FacialLandmarkDetector()
        
        # Validation thresholds
        self.min_frontal_angle_threshold = 15  # degrees
        self.max_frontal_angle_threshold = 165  # degrees
        self.min_face_size_ratio = 0.15  # minimum face size relative to image
        self.max_face_size_ratio = 0.85  # maximum face size relative to image
        self.symmetry_threshold = 0.7  # minimum symmetry score for frontal view
        self.confidence_threshold = 0.8  # minimum detection confidence
    
    def validate_image(self, image_path: str) -> Dict:
        """
        Comprehensive validation of facial image for analysis suitability.
        
        Args:
            image_path: Path to the facial image
            
        Returns:
            Dictionary containing validation results and recommendations
        """
        validation_result = {
            'is_valid': False,
            'validation_score': 0.0,
            'issues': [],
            'recommendations': [],
            'face_angle': None,
            'face_size_ratio': None,
            'symmetry_score': None,
            'lighting_quality': None,
            'blur_detection': None
        }
        
        try:
            # Basic image checks
            image = cv2.imread(image_path)
            if image is None:
                validation_result['issues'].append("Could not read image file")
                return validation_result
            
            height, width = image.shape[:2]
            
            # Check image dimensions
            if width < 400 or height < 400:
                validation_result['issues'].append("Image resolution too low (minimum 400x400)")
                validation_result['recommendations'].append("Use a higher resolution image")
            
            # Detect facial landmarks
            landmarks_data = self.landmark_detector.detect_landmarks(image_path)
            if not landmarks_data:
                validation_result['issues'].append("No face detected in image")
                validation_result['recommendations'].append("Ensure face is clearly visible and well-lit")
                return validation_result
            
            landmarks = landmarks_data['landmarks']
            face_bounds = landmarks_data['face_bounds']
            
            # 1. Check face positioning (frontal vs profile)
            frontal_score, face_angle = self._check_frontal_positioning(landmarks)
            validation_result['face_angle'] = face_angle
            
            if frontal_score < 0.7:
                validation_result['issues'].append(f"Face not positioned frontally (angle: {face_angle:.1f}°)")
                validation_result['recommendations'].append("Face the camera directly for frontal view")
            
            # 2. Check face size in image
            face_size_ratio = self._check_face_size(face_bounds, width, height)
            validation_result['face_size_ratio'] = face_size_ratio
            
            if face_size_ratio < self.min_face_size_ratio:
                validation_result['issues'].append("Face too small in image")
                validation_result['recommendations'].append("Move closer to camera or crop image closer to face")
            elif face_size_ratio > self.max_face_size_ratio:
                validation_result['issues'].append("Face too large in image")
                validation_result['recommendations'].append("Move back from camera to show full face")
            
            # 3. Check facial symmetry for frontal validation
            symmetry_score = self._check_facial_symmetry(landmarks)
            validation_result['symmetry_score'] = symmetry_score
            
            if symmetry_score < self.symmetry_threshold:
                validation_result['issues'].append("Face appears asymmetrical or tilted")
                validation_result['recommendations'].append("Keep head straight and centered")
            
            # 4. Check lighting quality
            lighting_quality = self._check_lighting_quality(image, face_bounds)
            validation_result['lighting_quality'] = lighting_quality
            
            if lighting_quality < 0.6:
                validation_result['issues'].append("Poor lighting conditions")
                validation_result['recommendations'].append("Use even, well-distributed lighting")
            
            # 5. Check for blur
            blur_score = self._check_image_blur(image, face_bounds)
            validation_result['blur_detection'] = blur_score
            
            if blur_score > 50:  # Higher values indicate more blur
                validation_result['issues'].append("Image appears blurry")
                validation_result['recommendations'].append("Use a stable camera and ensure focus is on the face")
            
            # Calculate overall validation score
            scores = [frontal_score, symmetry_score, lighting_quality]
            if face_size_ratio >= self.min_face_size_ratio and face_size_ratio <= self.max_face_size_ratio:
                scores.append(1.0)
            else:
                scores.append(0.5)
            
            if blur_score <= 50:
                scores.append(1.0)
            else:
                scores.append(max(0.0, 1.0 - (blur_score - 50) / 50))
            
            validation_result['validation_score'] = np.mean(scores)
            validation_result['is_valid'] = validation_result['validation_score'] >= 0.7 and len(validation_result['issues']) <= 2
            
            logger.info(f"Image validation completed: Score {validation_result['validation_score']:.2f}, Valid: {validation_result['is_valid']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error during image validation: {e}")
            validation_result['issues'].append(f"Validation error: {str(e)}")
            return validation_result
    
    def _check_frontal_positioning(self, landmarks: Dict) -> Tuple[float, float]:
        """
        Check if face is positioned frontally using landmark analysis.
        
        Args:
            landmarks: Dictionary of facial landmarks
            
        Returns:
            Tuple of (frontal_score, estimated_angle)
        """
        try:
            # Get key points for angle calculation
            nose_tip = landmarks[1]  # Nose tip
            left_eye_corner = landmarks[33]  # Left eye inner corner
            right_eye_corner = landmarks[362]  # Right eye inner corner
            chin_center = landmarks[18]  # Chin center
            
            # Calculate face midline using nose tip and chin
            face_midline_x = (nose_tip['x'] + chin_center['x']) / 2
            
            # Calculate eye line
            eye_center_x = (left_eye_corner['x'] + right_eye_corner['x']) / 2
            
            # Calculate asymmetry between eye distances
            left_eye_to_midline = abs(left_eye_corner['x'] - face_midline_x)
            right_eye_to_midline = abs(right_eye_corner['x'] - face_midline_x)
            
            # Calculate angle deviation from frontal
            eye_line_deviation = abs(eye_center_x - face_midline_x)
            face_width = abs(right_eye_corner['x'] - left_eye_corner['x'])
            
            if face_width > 0:
                angle_ratio = eye_line_deviation / face_width
                estimated_angle = angle_ratio * 90  # Convert to degrees
                frontal_score = max(0.0, 1.0 - (angle_ratio * 2))
            else:
                estimated_angle = 90
                frontal_score = 0.0
            
            return frontal_score, estimated_angle
            
        except Exception as e:
            logger.error(f"Error checking frontal positioning: {e}")
            return 0.0, 90.0
    
    def _check_face_size(self, face_bounds: Dict, image_width: int, image_height: int) -> float:
        """Check if face size is appropriate relative to image."""
        face_area = face_bounds['width'] * face_bounds['height']
        image_area = image_width * image_height
        return face_area / image_area if image_area > 0 else 0.0
    
    def _check_facial_symmetry(self, landmarks: Dict) -> float:
        """Check facial symmetry as an indicator of frontal positioning."""
        try:
            # Compare distances from face center to left and right features
            nose_tip = landmarks[1]
            left_eye = landmarks[33]
            right_eye = landmarks[362]
            left_mouth = landmarks[61]
            right_mouth = landmarks[291]
            
            # Calculate distances from nose tip to each side
            left_eye_dist = np.sqrt((left_eye['x'] - nose_tip['x'])**2 + (left_eye['y'] - nose_tip['y'])**2)
            right_eye_dist = np.sqrt((right_eye['x'] - nose_tip['x'])**2 + (right_eye['y'] - nose_tip['y'])**2)
            
            left_mouth_dist = np.sqrt((left_mouth['x'] - nose_tip['x'])**2 + (left_mouth['y'] - nose_tip['y'])**2)
            right_mouth_dist = np.sqrt((right_mouth['x'] - nose_tip['x'])**2 + (right_mouth['y'] - nose_tip['y'])**2)
            
            # Calculate symmetry scores
            eye_symmetry = 1.0 - abs(left_eye_dist - right_eye_dist) / max(left_eye_dist, right_eye_dist)
            mouth_symmetry = 1.0 - abs(left_mouth_dist - right_mouth_dist) / max(left_mouth_dist, right_mouth_dist)
            
            return (eye_symmetry + mouth_symmetry) / 2
            
        except Exception as e:
            logger.error(f"Error checking facial symmetry: {e}")
            return 0.0
    
    def _check_lighting_quality(self, image: np.ndarray, face_bounds: Dict) -> float:
        """Analyze lighting quality in the facial region."""
        try:
            # Extract face region
            y1 = max(0, int(face_bounds['min_y']))
            y2 = min(image.shape[0], int(face_bounds['max_y']))
            x1 = max(0, int(face_bounds['min_x']))
            x2 = min(image.shape[1], int(face_bounds['max_x']))
            
            face_region = image[y1:y2, x1:x2]
            
            # Convert to grayscale for analysis
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Calculate lighting metrics
            mean_brightness = np.mean(gray_face)
            std_brightness = np.std(gray_face)
            
            # Good lighting: mean brightness 80-180, reasonable contrast (std > 20)
            brightness_score = 1.0 - abs(mean_brightness - 128) / 128
            contrast_score = min(1.0, std_brightness / 50)
            
            return (brightness_score + contrast_score) / 2
            
        except Exception as e:
            logger.error(f"Error checking lighting quality: {e}")
            return 0.5
    
    def _check_image_blur(self, image: np.ndarray, face_bounds: Dict) -> float:
        """Detect image blur using Laplacian variance."""
        try:
            # Extract face region
            y1 = max(0, int(face_bounds['min_y']))
            y2 = min(image.shape[0], int(face_bounds['max_y']))
            x1 = max(0, int(face_bounds['min_x']))
            x2 = min(image.shape[1], int(face_bounds['max_x']))
            
            face_region = image[y1:y2, x1:x2]
            
            # Convert to grayscale
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance (lower values indicate more blur)
            laplacian_variance = cv2.Laplacian(gray_face, cv2.CV_64F).var()
            
            return laplacian_variance
            
        except Exception as e:
            logger.error(f"Error checking image blur: {e}")
            return 100.0  # Assume blurry on error


def validate_face_image(image_path: str) -> Dict:
    """
    Convenience function to validate a facial image.
    
    Args:
        image_path: Path to the facial image
        
    Returns:
        Dictionary containing validation results
    """
    validator = ImageValidator()
    return validator.validate_image(image_path)


# Test function for development
if __name__ == "__main__":
    test_image = "static/uploads/face_analysis/test_image.jpg"
    result = validate_face_image(test_image)
    print(f"Validation result: {result}")