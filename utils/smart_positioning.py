#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Face Positioning System

Advanced positioning validation using MediaPipe landmarks for accurate
geometric analysis. Designed specifically for Golden Ratio, Facial Thirds/Fifths,
and Symmetry Analysis requirements.
"""

import cv2
import mediapipe as mp
import numpy as np
import logging
from typing import Dict, Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Initialize MediaPipe Face Mesh  
try:
    mp_face_mesh = mp.solutions.face_mesh
    mp_drawing = mp.solutions.drawing_utils
except AttributeError:
    # Fallback for different MediaPipe versions
    import mediapipe.python.solutions.face_mesh as mp_face_mesh
    import mediapipe.python.solutions.drawing_utils as mp_drawing

class SmartFacePositioning:
    """Smart face positioning validator using MediaPipe landmarks."""
    
    def __init__(self):
        """Initialize the smart positioning system."""
        self.face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=False,  # For video stream
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Key landmark indices for positioning analysis
        self.key_landmarks = {
            'nose_tip': 1,
            'left_eye_center': 468,  # Iris center
            'right_eye_center': 473,  # Iris center
            'left_eye_inner': 133,
            'right_eye_inner': 362,
            'left_eye_outer': 33,
            'right_eye_outer': 263,
            'mouth_left': 61,
            'mouth_right': 291,
            'forehead_center': 9,
            'chin_center': 18,
            'left_cheek': 234,
            'right_cheek': 454
        }
        
        # Positioning thresholds (more lenient than before)
        self.thresholds = {
            'max_head_rotation': 20.0,  # degrees
            'max_head_tilt': 15.0,      # degrees
            'min_face_size': 0.15,      # 15% of frame
            'max_face_size': 0.75,      # 75% of frame
            'min_eye_distance': 50,     # pixels
            'max_eye_distance': 300,    # pixels
            'center_tolerance': 0.15,   # 15% from center
            'symmetry_tolerance': 0.2   # 20% asymmetry allowed
        }
    
    def analyze_positioning(self, frame: np.ndarray) -> Dict:
        """
        Analyze face positioning in real-time video frame.
        
        Args:
            frame: Video frame as numpy array (BGR format)
            
        Returns:
            Dictionary with positioning analysis results
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = frame.shape[:2]
            
            # Process frame with MediaPipe
            results = self.face_mesh.process(rgb_frame)
            
            if not results.multi_face_landmarks:
                return {
                    'face_detected': False,
                    'positioning_score': 0.0,
                    'issues': ['No face detected'],
                    'recommendations': ['Position your face in the camera view'],
                    'is_ready_for_capture': False
                }
            
            # Get face landmarks
            face_landmarks = results.multi_face_landmarks[0]
            landmarks = self._extract_landmarks(face_landmarks, width, height)
            
            # Perform positioning analysis
            analysis = self._analyze_face_positioning(landmarks, width, height)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in positioning analysis: {e}")
            return {
                'face_detected': False,
                'positioning_score': 0.0,
                'issues': ['Analysis error'],
                'recommendations': ['Please try again'],
                'is_ready_for_capture': False
            }
    
    def _extract_landmarks(self, face_landmarks, width: int, height: int) -> Dict:
        """Extract key landmarks from MediaPipe results."""
        landmarks = {}
        
        for name, idx in self.key_landmarks.items():
            if idx < len(face_landmarks.landmark):
                landmark = face_landmarks.landmark[idx]
                landmarks[name] = {
                    'x': landmark.x * width,
                    'y': landmark.y * height,
                    'z': landmark.z * width  # Relative depth
                }
        
        return landmarks
    
    def _analyze_face_positioning(self, landmarks: Dict, width: int, height: int) -> Dict:
        """Perform comprehensive face positioning analysis."""
        issues = []
        recommendations = []
        scores = {}
        
        # 1. Face detection and size validation
        face_size_score, face_size_issues, face_size_recs = self._validate_face_size(landmarks, width, height)
        scores['face_size'] = face_size_score
        issues.extend(face_size_issues)
        recommendations.extend(face_size_recs)
        
        # 2. Head pose estimation (frontal positioning)
        head_pose_score, head_pose_issues, head_pose_recs = self._validate_head_pose(landmarks)
        scores['head_pose'] = head_pose_score
        issues.extend(head_pose_issues)
        recommendations.extend(head_pose_recs)
        
        # 3. Face centering validation
        centering_score, centering_issues, centering_recs = self._validate_face_centering(landmarks, width, height)
        scores['centering'] = centering_score
        issues.extend(centering_issues)
        recommendations.extend(centering_recs)
        
        # 4. Eye alignment validation
        eye_alignment_score, eye_issues, eye_recs = self._validate_eye_alignment(landmarks)
        scores['eye_alignment'] = eye_alignment_score
        issues.extend(eye_issues)
        recommendations.extend(eye_recs)
        
        # 5. Facial symmetry check
        symmetry_score, symmetry_issues, symmetry_recs = self._validate_facial_symmetry(landmarks)
        scores['symmetry'] = symmetry_score
        issues.extend(symmetry_issues)
        recommendations.extend(symmetry_recs)
        
        # Calculate overall positioning score (weighted average)
        weights = {
            'face_size': 0.2,
            'head_pose': 0.3,
            'centering': 0.2,
            'eye_alignment': 0.2,
            'symmetry': 0.1
        }
        
        overall_score = sum(scores[key] * weights[key] for key in scores)
        
        # Determine if ready for capture (more lenient threshold)
        is_ready = overall_score >= 0.75 and len(issues) == 0
        
        return {
            'face_detected': True,
            'positioning_score': round(overall_score, 2),
            'individual_scores': scores,
            'issues': issues,
            'recommendations': recommendations,
            'is_ready_for_capture': is_ready,
            'landmarks': landmarks
        }
    
    def _validate_face_size(self, landmarks: Dict, width: int, height: int) -> Tuple[float, list, list]:
        """Validate face size relative to frame."""
        if 'left_eye_inner' not in landmarks or 'right_eye_inner' not in landmarks:
            return 0.0, ['Cannot detect eyes'], ['Ensure your face is clearly visible']
        
        # Calculate eye distance as face size indicator
        left_eye = landmarks['left_eye_inner']
        right_eye = landmarks['right_eye_inner']
        eye_distance = np.sqrt((right_eye['x'] - left_eye['x'])**2 + (right_eye['y'] - left_eye['y'])**2)
        
        # Calculate face size ratio
        frame_diagonal = np.sqrt(width**2 + height**2)
        face_size_ratio = eye_distance / frame_diagonal
        
        issues = []
        recommendations = []
        
        if face_size_ratio < self.thresholds['min_face_size']:
            issues.append('Face too small - move closer to camera')
            recommendations.append('Move closer to the camera')
            score = face_size_ratio / self.thresholds['min_face_size']
        elif face_size_ratio > self.thresholds['max_face_size']:
            issues.append('Face too large - move away from camera')
            recommendations.append('Move further from the camera')
            score = self.thresholds['max_face_size'] / face_size_ratio
        else:
            score = 1.0
        
        return min(1.0, score), issues, recommendations
    
    def _validate_head_pose(self, landmarks: Dict) -> Tuple[float, list, list]:
        """Validate head pose for frontal positioning."""
        if not all(key in landmarks for key in ['nose_tip', 'left_eye_inner', 'right_eye_inner', 'forehead_center', 'chin_center']):
            return 0.0, ['Cannot detect face orientation'], ['Ensure your full face is visible']
        
        issues = []
        recommendations = []
        
        # Calculate head rotation (yaw) using eye positions
        left_eye = landmarks['left_eye_inner']
        right_eye = landmarks['right_eye_inner']
        eye_vector = np.array([right_eye['x'] - left_eye['x'], right_eye['y'] - left_eye['y']])
        eye_angle = np.abs(np.degrees(np.arctan2(eye_vector[1], eye_vector[0])))
        
        # Calculate head tilt using nose-to-forehead alignment
        nose = landmarks['nose_tip']
        forehead = landmarks['forehead_center']
        chin = landmarks['chin_center']
        
        # Vertical alignment check
        nose_vertical_offset = abs(nose['x'] - (forehead['x'] + chin['x']) / 2)
        face_width = abs(landmarks['right_eye_inner']['x'] - landmarks['left_eye_inner']['x'])
        tilt_ratio = nose_vertical_offset / face_width if face_width > 0 else 1.0
        
        # Score based on rotation and tilt
        rotation_score = max(0, 1 - (eye_angle / self.thresholds['max_head_rotation']))
        tilt_score = max(0, 1 - (tilt_ratio * 5))  # Convert ratio to degrees equivalent
        
        if eye_angle > self.thresholds['max_head_rotation']:
            issues.append(f'Head rotated too much ({eye_angle:.1f}°)')
            recommendations.append('Look directly at the camera')
        
        if tilt_ratio > 0.2:
            issues.append('Head tilted - straighten your head')
            recommendations.append('Keep your head straight and level')
        
        return min(rotation_score, tilt_score), issues, recommendations
    
    def _validate_face_centering(self, landmarks: Dict, width: int, height: int) -> Tuple[float, list, list]:
        """Validate face centering in frame."""
        if 'nose_tip' not in landmarks:
            return 0.0, ['Cannot detect face center'], ['Position your face in the center']
        
        nose = landmarks['nose_tip']
        frame_center_x = width / 2
        frame_center_y = height / 2
        
        # Calculate offset from center
        x_offset = abs(nose['x'] - frame_center_x) / (width / 2)
        y_offset = abs(nose['y'] - frame_center_y) / (height / 2)
        
        issues = []
        recommendations = []
        
        if x_offset > self.thresholds['center_tolerance']:
            if nose['x'] < frame_center_x:
                issues.append('Face positioned too far left')
                recommendations.append('Move slightly to your right')
            else:
                issues.append('Face positioned too far right')
                recommendations.append('Move slightly to your left')
        
        if y_offset > self.thresholds['center_tolerance']:
            if nose['y'] < frame_center_y:
                issues.append('Face positioned too high')
                recommendations.append('Move down slightly')
            else:
                issues.append('Face positioned too low')
                recommendations.append('Move up slightly')
        
        # Calculate centering score
        max_offset = max(x_offset, y_offset)
        score = max(0, 1 - (max_offset / self.thresholds['center_tolerance']))
        
        return score, issues, recommendations
    
    def _validate_eye_alignment(self, landmarks: Dict) -> Tuple[float, list, list]:
        """Validate horizontal eye alignment."""
        if not all(key in landmarks for key in ['left_eye_inner', 'right_eye_inner']):
            return 0.0, ['Cannot detect eyes'], ['Ensure both eyes are visible']
        
        left_eye = landmarks['left_eye_inner']
        right_eye = landmarks['right_eye_inner']
        
        # Calculate eye line angle
        y_diff = abs(right_eye['y'] - left_eye['y'])
        x_diff = abs(right_eye['x'] - left_eye['x'])
        eye_angle = np.degrees(np.arctan2(y_diff, x_diff)) if x_diff > 0 else 90
        
        issues = []
        recommendations = []
        
        if eye_angle > 10:  # More than 10 degrees tilt
            issues.append(f'Eyes not level ({eye_angle:.1f}° tilt)')
            recommendations.append('Keep your head level - eyes should be horizontal')
        
        score = max(0, 1 - (eye_angle / 15))  # 15 degrees maximum
        
        return score, issues, recommendations
    
    def _validate_facial_symmetry(self, landmarks: Dict) -> Tuple[float, list, list]:
        """Validate facial symmetry for geometric analysis."""
        if not all(key in landmarks for key in ['left_eye_inner', 'right_eye_inner', 'nose_tip']):
            return 0.0, ['Cannot analyze symmetry'], ['Ensure full face is visible']
        
        # Calculate face midline
        nose = landmarks['nose_tip']
        left_eye = landmarks['left_eye_inner']
        right_eye = landmarks['right_eye_inner']
        
        # Expected midline between eyes
        eye_midpoint_x = (left_eye['x'] + right_eye['x']) / 2
        
        # Check nose alignment with eye midline
        nose_offset = abs(nose['x'] - eye_midpoint_x)
        eye_distance = abs(right_eye['x'] - left_eye['x'])
        symmetry_ratio = nose_offset / eye_distance if eye_distance > 0 else 1.0
        
        issues = []
        recommendations = []
        
        if symmetry_ratio > self.thresholds['symmetry_tolerance']:
            issues.append('Face appears asymmetric in positioning')
            recommendations.append('Adjust position for better facial symmetry')
        
        score = max(0, 1 - (symmetry_ratio / self.thresholds['symmetry_tolerance']))
        
        return score, issues, recommendations

def test_positioning_system():
    """Test function for the smart positioning system."""
    positioning = SmartFacePositioning()
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return
    
    print("✅ Smart positioning system test started")
    print("Press 'q' to quit, 'c' to capture analysis")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Analyze positioning
        analysis = positioning.analyze_positioning(frame)
        
        # Display results
        if analysis['face_detected']:
            score = analysis['positioning_score']
            status = "READY" if analysis['is_ready_for_capture'] else "ADJUST"
            
            # Draw status on frame
            color = (0, 255, 0) if analysis['is_ready_for_capture'] else (0, 165, 255)
            cv2.putText(frame, f"{status} - Score: {score:.2f}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            # Draw issues
            for i, issue in enumerate(analysis['issues'][:3]):
                cv2.putText(frame, issue, (10, 70 + i*30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "No face detected", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Show frame
        cv2.imshow('Smart Face Positioning Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c') and analysis.get('is_ready_for_capture'):
            print("📸 Capture ready!")
            print(f"Analysis: {analysis}")
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Test completed")

if __name__ == "__main__":
    test_positioning_system()