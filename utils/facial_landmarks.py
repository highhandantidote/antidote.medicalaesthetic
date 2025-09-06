#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facial Landmarks Detection Module

This module provides facial landmark detection using MediaPipe for accurate
facial feature extraction and geometric analysis.
"""

import cv2
import mediapipe as mp
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

class FacialLandmarkDetector:
    """Facial landmark detection using MediaPipe Face Mesh."""
    
    def __init__(self):
        """Initialize the facial landmark detector."""
        self.face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        # Key facial landmark indices for analysis
        self.landmark_indices = {
            # Face outline (jaw line and forehead)
            'face_outline': [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109],
            
            # Eyes
            'left_eye': [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
            'right_eye': [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398],
            'left_eyebrow': [46, 53, 52, 51, 48, 115, 131, 134, 102, 49, 220, 305, 281, 277, 276, 283],
            'right_eyebrow': [276, 283, 282, 295, 285, 336, 296, 334, 293, 300, 276, 283, 282, 295, 285],
            
            # Nose
            'nose': [1, 2, 5, 4, 6, 19, 20, 94, 168, 195, 236, 3, 51, 48, 115, 131, 134, 102, 49, 220, 305, 281, 360, 279],
            'nose_tip': [1],
            'nose_bridge': [6, 5, 4, 1, 19, 94, 168],
            
            # Mouth
            'mouth_outer': [61, 84, 17, 314, 405, 320, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95],
            'mouth_inner': [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 320, 405, 314, 17, 84, 61, 78],
            'upper_lip': [61, 84, 17, 314, 405, 320, 308, 324, 318],
            'lower_lip': [78, 95, 88, 178, 87, 14, 317, 402, 318],
            
            # Chin and jaw
            'chin': [18, 175, 199, 200, 9, 10, 151, 175],
            'jaw_left': [172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323],
            'jaw_right': [397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127],
            
            # Key measurement points
            'midline_points': [10, 151, 9, 1, 2, 18],  # Forehead center, nose bridge, nose tip, chin
            'face_width_points': [234, 454],  # Left and right face edges
            'eye_corners': [33, 133, 362, 263],  # Inner eye corners (left, right)
            'mouth_corners': [61, 291],  # Left and right mouth corners
        }
    
    def detect_landmarks(self, image_path: str) -> Optional[Dict]:
        """
        Detect facial landmarks from an image.
        
        Args:
            image_path: Path to the facial image
            
        Returns:
            Dictionary containing normalized landmark coordinates and metadata
        """
        try:
            # Read and process image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not read image: {image_path}")
                return None
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Get image dimensions
            height, width = image.shape[:2]
            
            # Process image with MediaPipe
            results = self.face_mesh.process(rgb_image)
            
            if not results.multi_face_landmarks:
                logger.warning("No face detected in image")
                return None
            
            # Extract landmarks (use first face if multiple detected)
            face_landmarks = results.multi_face_landmarks[0]
            
            # Convert normalized coordinates to pixel coordinates
            landmarks = {}
            for idx, landmark in enumerate(face_landmarks.landmark):
                landmarks[idx] = {
                    'x': landmark.x * width,
                    'y': landmark.y * height,
                    'z': landmark.z * width  # Relative depth
                }
            
            # Calculate additional metrics
            face_bounds = self._calculate_face_bounds(landmarks)
            face_center = self._calculate_face_center(landmarks)
            
            return {
                'landmarks': landmarks,
                'image_dimensions': {'width': width, 'height': height},
                'face_bounds': face_bounds,
                'face_center': face_center,
                'landmark_indices': self.landmark_indices,
                'total_landmarks': len(landmarks)
            }
            
        except Exception as e:
            logger.error(f"Error detecting landmarks: {e}")
            return None
    
    def _calculate_face_bounds(self, landmarks: Dict) -> Dict:
        """Calculate bounding box of the face."""
        x_coords = [point['x'] for point in landmarks.values()]
        y_coords = [point['y'] for point in landmarks.values()]
        
        return {
            'min_x': min(x_coords),
            'max_x': max(x_coords),
            'min_y': min(y_coords),
            'max_y': max(y_coords),
            'width': max(x_coords) - min(x_coords),
            'height': max(y_coords) - min(y_coords)
        }
    
    def _calculate_face_center(self, landmarks: Dict) -> Dict:
        """Calculate the center point of the face."""
        # Use nose tip as face center reference
        nose_tip = landmarks.get(1, {'x': 0, 'y': 0})
        
        return {
            'x': nose_tip['x'],
            'y': nose_tip['y']
        }
    
    def get_key_points(self, landmarks_data: Dict, point_group: str) -> List[Dict]:
        """
        Get specific groups of landmark points.
        
        Args:
            landmarks_data: Output from detect_landmarks()
            point_group: Key from landmark_indices
            
        Returns:
            List of landmark coordinates for the specified group
        """
        if point_group not in self.landmark_indices:
            logger.error(f"Unknown point group: {point_group}")
            return []
        
        landmarks = landmarks_data['landmarks']
        indices = self.landmark_indices[point_group]
        
        return [landmarks[idx] for idx in indices if idx in landmarks]
    
    def calculate_distance(self, point1: Dict, point2: Dict) -> float:
        """Calculate Euclidean distance between two points."""
        return np.sqrt((point1['x'] - point2['x'])**2 + (point1['y'] - point2['y'])**2)
    
    def calculate_midpoint(self, point1: Dict, point2: Dict) -> Dict:
        """Calculate midpoint between two points."""
        return {
            'x': (point1['x'] + point2['x']) / 2,
            'y': (point1['y'] + point2['y']) / 2
        }
    
    def calculate_angle(self, point1: Dict, point2: Dict, point3: Dict) -> float:
        """
        Calculate angle at point2 formed by points 1-2-3.
        
        Returns angle in degrees.
        """
        # Vectors from point2 to point1 and point3
        v1 = np.array([point1['x'] - point2['x'], point1['y'] - point2['y']])
        v2 = np.array([point3['x'] - point2['x'], point3['y'] - point2['y']])
        
        # Calculate angle using dot product
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        
        # Handle numerical errors
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg

def test_landmark_detection(image_path: str):
    """Test function for landmark detection."""
    detector = FacialLandmarkDetector()
    result = detector.detect_landmarks(image_path)
    
    if result:
        print(f"✅ Successfully detected {result['total_landmarks']} landmarks")
        print(f"Face bounds: {result['face_bounds']}")
        print(f"Face center: {result['face_center']}")
        return True
    else:
        print("❌ Failed to detect landmarks")
        return False

if __name__ == "__main__":
    # Test with a sample image
    test_image = "static/uploads/face_analysis/test_image.jpg"
    test_landmark_detection(test_image)