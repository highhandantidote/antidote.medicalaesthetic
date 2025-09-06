#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Geometric Facial Analysis Module

This module provides mathematical analysis of facial features including
golden ratio calculations, facial thirds/fifths, symmetry analysis, and
other geometric measurements for aesthetic assessment.
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from .facial_landmarks import FacialLandmarkDetector

# Configure logging
logger = logging.getLogger(__name__)

class FacialGeometricAnalyzer:
    """Comprehensive geometric analysis of facial features."""
    
    def __init__(self):
        """Initialize the geometric analyzer."""
        self.landmark_detector = FacialLandmarkDetector()
        
        # Golden ratio constant
        self.golden_ratio = 1.618
        
        # Ideal facial proportions
        self.ideal_thirds = [33.33, 33.33, 33.33]  # Upper, middle, lower thirds
        self.ideal_fifths = [20.0, 20.0, 20.0, 20.0, 20.0]  # Five equal horizontal sections
    
    def analyze_face(self, image_path: str) -> Dict:
        """
        Perform comprehensive geometric analysis of a face.
        
        Args:
            image_path: Path to the facial image
            
        Returns:
            Dictionary containing all geometric analysis results
        """
        try:
            # Detect facial landmarks
            landmarks_data = self.landmark_detector.detect_landmarks(image_path)
            
            if not landmarks_data:
                return {'error': 'Could not detect facial landmarks'}
            
            landmarks = landmarks_data['landmarks']
            
            # Perform all geometric analyses
            results = {
                'golden_ratio_analysis': self.calculate_golden_ratio_score(landmarks),
                'facial_thirds_analysis': self.calculate_facial_thirds(landmarks),
                'facial_fifths_analysis': self.calculate_facial_fifths(landmarks),
                'symmetry_analysis': self.calculate_facial_symmetry(landmarks),
                'neoclassical_canons': self.calculate_neoclassical_canons(landmarks),
                'ogee_curve_analysis': self.calculate_ogee_curve(landmarks),
                'facial_harmony_score': None,  # Will be calculated after other analyses
                'landmarks_data': landmarks_data
            }
            
            # Calculate overall facial harmony score
            results['facial_harmony_score'] = self.calculate_facial_harmony(results)
            
            logger.info("Geometric analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in geometric analysis: {e}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def calculate_golden_ratio_score(self, landmarks: Dict) -> Dict:
        """
        Calculate golden ratio adherence score.
        
        The golden ratio (1.618) appears in many aesthetically pleasing proportions.
        We analyze multiple facial ratios and compare them to the golden ratio.
        """
        try:
            # Key measurements for golden ratio analysis
            measurements = {}
            
            # 1. Face length to width ratio
            # Face length: forehead to chin
            forehead_point = landmarks[10]  # Top of forehead
            chin_point = landmarks[18]  # Bottom of chin
            face_length = self.landmark_detector.calculate_distance(forehead_point, chin_point)
            
            # Face width: left to right cheekbone
            left_cheek = landmarks[234]
            right_cheek = landmarks[454]
            face_width = self.landmark_detector.calculate_distance(left_cheek, right_cheek)
            
            face_ratio = face_length / face_width if face_width > 0 else 0
            measurements['face_length_to_width'] = {
                'ratio': face_ratio,
                'ideal': self.golden_ratio,
                'score': self._calculate_ratio_score(face_ratio, self.golden_ratio)
            }
            
            # 2. Eye width to interpupillary distance
            left_eye_inner = landmarks[133]
            left_eye_outer = landmarks[33]
            right_eye_inner = landmarks[362]
            right_eye_outer = landmarks[263]
            
            eye_width = self.landmark_detector.calculate_distance(left_eye_inner, left_eye_outer)
            interpupillary_distance = self.landmark_detector.calculate_distance(left_eye_inner, right_eye_inner)
            
            eye_ratio = interpupillary_distance / eye_width if eye_width > 0 else 0
            measurements['interpupillary_to_eye_width'] = {
                'ratio': eye_ratio,
                'ideal': self.golden_ratio,
                'score': self._calculate_ratio_score(eye_ratio, self.golden_ratio)
            }
            
            # 3. Mouth width to nose width
            mouth_left = landmarks[61]
            mouth_right = landmarks[291]
            nose_left = landmarks[220]
            nose_right = landmarks[305]
            
            mouth_width = self.landmark_detector.calculate_distance(mouth_left, mouth_right)
            nose_width = self.landmark_detector.calculate_distance(nose_left, nose_right)
            
            mouth_nose_ratio = mouth_width / nose_width if nose_width > 0 else 0
            measurements['mouth_to_nose_width'] = {
                'ratio': mouth_nose_ratio,
                'ideal': self.golden_ratio,
                'score': self._calculate_ratio_score(mouth_nose_ratio, self.golden_ratio)
            }
            
            # 4. Face length to eye-mouth distance
            eye_center = self.landmark_detector.calculate_midpoint(left_eye_inner, right_eye_inner)
            mouth_center = self.landmark_detector.calculate_midpoint(mouth_left, mouth_right)
            eye_mouth_distance = self.landmark_detector.calculate_distance(eye_center, mouth_center)
            
            face_eye_mouth_ratio = face_length / eye_mouth_distance if eye_mouth_distance > 0 else 0
            measurements['face_to_eye_mouth_distance'] = {
                'ratio': face_eye_mouth_ratio,
                'ideal': self.golden_ratio,
                'score': self._calculate_ratio_score(face_eye_mouth_ratio, self.golden_ratio)
            }
            
            # Calculate overall golden ratio score
            scores = [m['score'] for m in measurements.values()]
            overall_score = sum(scores) / len(scores) if scores else 0
            
            return {
                'overall_score': round(overall_score, 1),
                'measurements': measurements,
                'interpretation': self._interpret_golden_ratio_score(overall_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating golden ratio score: {e}")
            return {'error': str(e)}
    
    def calculate_facial_thirds(self, landmarks: Dict) -> Dict:
        """
        Calculate facial thirds proportion analysis.
        
        The face should ideally be divided into three equal thirds:
        1. Hairline to eyebrows (upper third)
        2. Eyebrows to nose base (middle third) 
        3. Nose base to chin (lower third)
        """
        try:
            # Key reference points
            # Approximate hairline (extend above forehead)
            forehead_point = landmarks[10]
            eyebrow_point = landmarks[9]  # Between eyebrows
            nose_base = landmarks[2]  # Nose base
            chin_point = landmarks[18]  # Chin bottom
            
            # Estimate hairline position (typically 1.2-1.3 times forehead height above eyebrows)
            forehead_eyebrow_distance = self.landmark_detector.calculate_distance(forehead_point, eyebrow_point)
            hairline_y = forehead_point['y'] - (forehead_eyebrow_distance * 0.3)
            hairline_point = {'x': forehead_point['x'], 'y': hairline_y}
            
            # Calculate the three sections
            upper_third = abs(hairline_point['y'] - eyebrow_point['y'])
            middle_third = abs(eyebrow_point['y'] - nose_base['y'])
            lower_third = abs(nose_base['y'] - chin_point['y'])
            
            total_height = upper_third + middle_third + lower_third
            
            # Calculate percentages
            if total_height > 0:
                upper_percentage = (upper_third / total_height) * 100
                middle_percentage = (middle_third / total_height) * 100
                lower_percentage = (lower_third / total_height) * 100
            else:
                upper_percentage = middle_percentage = lower_percentage = 0
            
            proportions = [upper_percentage, middle_percentage, lower_percentage]
            
            # Calculate deviation from ideal
            deviation_score = self._calculate_proportion_deviation(proportions, self.ideal_thirds)
            
            return {
                'proportions': {
                    'upper_third': round(upper_percentage, 1),
                    'middle_third': round(middle_percentage, 1),
                    'lower_third': round(lower_percentage, 1)
                },
                'measurements': {
                    'upper_third_px': round(upper_third, 1),
                    'middle_third_px': round(middle_third, 1),
                    'lower_third_px': round(lower_third, 1),
                    'total_height_px': round(total_height, 1)
                },
                'deviation_score': round(deviation_score, 1),
                'interpretation': self._interpret_thirds_score(deviation_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating facial thirds: {e}")
            return {'error': str(e)}
    
    def calculate_facial_fifths(self, landmarks: Dict) -> Dict:
        """
        Calculate facial fifths proportion analysis.
        
        The face width should ideally be divided into five equal fifths:
        1. Left ear to left eye outer corner
        2. Left eye outer to inner corner  
        3. Between the eyes (inner corners)
        4. Right eye inner to outer corner
        5. Right eye outer corner to right ear
        """
        try:
            # Key horizontal measurement points
            left_ear_approx = landmarks[234]  # Left face edge
            left_eye_outer = landmarks[33]
            left_eye_inner = landmarks[133]
            right_eye_inner = landmarks[362]
            right_eye_outer = landmarks[263]
            right_ear_approx = landmarks[454]  # Right face edge
            
            # Calculate the five sections
            section_1 = self.landmark_detector.calculate_distance(left_ear_approx, left_eye_outer)
            section_2 = self.landmark_detector.calculate_distance(left_eye_outer, left_eye_inner)
            section_3 = self.landmark_detector.calculate_distance(left_eye_inner, right_eye_inner)
            section_4 = self.landmark_detector.calculate_distance(right_eye_inner, right_eye_outer)
            section_5 = self.landmark_detector.calculate_distance(right_eye_outer, right_ear_approx)
            
            total_width = section_1 + section_2 + section_3 + section_4 + section_5
            
            # Calculate percentages
            if total_width > 0:
                percentages = [
                    (section_1 / total_width) * 100,
                    (section_2 / total_width) * 100,
                    (section_3 / total_width) * 100,
                    (section_4 / total_width) * 100,
                    (section_5 / total_width) * 100
                ]
            else:
                percentages = [0, 0, 0, 0, 0]
            
            # Calculate deviation from ideal
            deviation_score = self._calculate_proportion_deviation(percentages, self.ideal_fifths)
            
            return {
                'proportions': {
                    'section_1': round(percentages[0], 1),
                    'section_2': round(percentages[1], 1),
                    'section_3': round(percentages[2], 1),
                    'section_4': round(percentages[3], 1),
                    'section_5': round(percentages[4], 1)
                },
                'measurements': {
                    'section_1_px': round(section_1, 1),
                    'section_2_px': round(section_2, 1),
                    'section_3_px': round(section_3, 1),
                    'section_4_px': round(section_4, 1),
                    'section_5_px': round(section_5, 1),
                    'total_width_px': round(total_width, 1)
                },
                'deviation_score': round(deviation_score, 1),
                'interpretation': self._interpret_fifths_score(deviation_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating facial fifths: {e}")
            return {'error': str(e)}
    
    def calculate_facial_symmetry(self, landmarks: Dict) -> Dict:
        """
        Calculate facial symmetry analysis.
        
        Compares left and right sides of the face across multiple reference points.
        """
        try:
            # Define the face midline using nose and chin
            nose_tip = landmarks[1]
            chin_center = landmarks[18]
            midline_x = (nose_tip['x'] + chin_center['x']) / 2
            
            # Key symmetry point pairs (left, right)
            symmetry_pairs = [
                (33, 362),    # Inner eye corners
                (133, 263),   # Outer eye corners
                (61, 291),    # Mouth corners
                (234, 454),   # Face edges
                (205, 425),   # Cheekbone points
                (172, 397),   # Jaw points
                (46, 276),    # Eyebrow points
            ]
            
            symmetry_scores = []
            asymmetry_details = []
            
            for left_idx, right_idx in symmetry_pairs:
                if left_idx in landmarks and right_idx in landmarks:
                    left_point = landmarks[left_idx]
                    right_point = landmarks[right_idx]
                    
                    # Calculate distance from midline for each point
                    left_distance = abs(left_point['x'] - midline_x)
                    right_distance = abs(right_point['x'] - midline_x)
                    
                    # Calculate symmetry score for this pair (0-1)
                    max_distance = max(left_distance, right_distance)
                    if max_distance > 0:
                        symmetry = 1 - abs(left_distance - right_distance) / max_distance
                        symmetry_scores.append(symmetry)
                        
                        # Track significant asymmetries
                        if symmetry < 0.85:  # Less than 85% symmetric
                            asymmetry_details.append({
                                'feature': self._get_feature_name(left_idx, right_idx),
                                'symmetry_score': round(symmetry * 100, 1),
                                'left_distance': round(left_distance, 1),
                                'right_distance': round(right_distance, 1)
                            })
            
            # Calculate overall symmetry score
            overall_symmetry = (sum(symmetry_scores) / len(symmetry_scores)) * 100 if symmetry_scores else 0
            
            return {
                'overall_score': round(overall_symmetry, 1),
                'midline_x': round(midline_x, 1),
                'individual_scores': [round(score * 100, 1) for score in symmetry_scores],
                'asymmetry_details': asymmetry_details,
                'interpretation': self._interpret_symmetry_score(overall_symmetry)
            }
            
        except Exception as e:
            logger.error(f"Error calculating facial symmetry: {e}")
            return {'error': str(e)}
    
    def calculate_neoclassical_canons(self, landmarks: Dict) -> Dict:
        """
        Calculate adherence to neoclassical beauty canons.
        
        Traditional rules of facial beauty from classical art and sculpture.
        """
        try:
            canons = {}
            
            # 1. Eye separation should equal eye width
            left_eye_inner = landmarks[133]
            left_eye_outer = landmarks[33]
            right_eye_inner = landmarks[362]
            
            eye_width = self.landmark_detector.calculate_distance(left_eye_inner, left_eye_outer)
            eye_separation = self.landmark_detector.calculate_distance(left_eye_inner, right_eye_inner)
            
            eye_ratio = eye_separation / eye_width if eye_width > 0 else 0
            canons['eye_separation_to_width'] = {
                'measured_ratio': round(eye_ratio, 2),
                'ideal_ratio': 1.0,
                'score': self._calculate_ratio_score(eye_ratio, 1.0)
            }
            
            # 2. Nose width should equal eye width
            nose_left = landmarks[220]
            nose_right = landmarks[305]
            nose_width = self.landmark_detector.calculate_distance(nose_left, nose_right)
            
            nose_eye_ratio = nose_width / eye_width if eye_width > 0 else 0
            canons['nose_width_to_eye_width'] = {
                'measured_ratio': round(nose_eye_ratio, 2),
                'ideal_ratio': 1.0,
                'score': self._calculate_ratio_score(nose_eye_ratio, 1.0)
            }
            
            # 3. Mouth width should be 1.5 times nose width
            mouth_left = landmarks[61]
            mouth_right = landmarks[291]
            mouth_width = self.landmark_detector.calculate_distance(mouth_left, mouth_right)
            
            mouth_nose_ratio = mouth_width / nose_width if nose_width > 0 else 0
            canons['mouth_width_to_nose_width'] = {
                'measured_ratio': round(mouth_nose_ratio, 2),
                'ideal_ratio': 1.5,
                'score': self._calculate_ratio_score(mouth_nose_ratio, 1.5)
            }
            
            # 4. Face width should be 4 times nose width
            face_width = self.landmark_detector.calculate_distance(landmarks[234], landmarks[454])
            face_nose_ratio = face_width / nose_width if nose_width > 0 else 0
            canons['face_width_to_nose_width'] = {
                'measured_ratio': round(face_nose_ratio, 2),
                'ideal_ratio': 4.0,
                'score': self._calculate_ratio_score(face_nose_ratio, 4.0)
            }
            
            # Calculate overall canon compliance
            scores = [canon['score'] for canon in canons.values()]
            overall_score = sum(scores) / len(scores) if scores else 0
            
            return {
                'overall_score': round(overall_score, 1),
                'canons': canons,
                'interpretation': self._interpret_canon_score(overall_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating neoclassical canons: {e}")
            return {'error': str(e)}
    
    def calculate_ogee_curve(self, landmarks: Dict) -> Dict:
        """
        Calculate ogee curve definition (S-curve from cheekbone to jawline).
        
        The ogee curve is considered a hallmark of youthful facial appearance.
        """
        try:
            # Define key points for ogee curve
            # Use cheekbone and jaw points to approximate the curve
            left_cheekbone = landmarks[205]
            left_jaw = landmarks[172]
            right_cheekbone = landmarks[425]
            right_jaw = landmarks[397]
            
            # Calculate curve definition for both sides
            left_curve_score = self._calculate_curve_definition(left_cheekbone, left_jaw, landmarks)
            right_curve_score = self._calculate_curve_definition(right_cheekbone, right_jaw, landmarks)
            
            # Average the scores
            overall_score = (left_curve_score + right_curve_score) / 2
            
            return {
                'overall_score': round(overall_score, 1),
                'left_side_score': round(left_curve_score, 1),
                'right_side_score': round(right_curve_score, 1),
                'interpretation': self._interpret_ogee_score(overall_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating ogee curve: {e}")
            return {'error': str(e)}
    
    def calculate_facial_harmony(self, analysis_results: Dict) -> Dict:
        """
        Calculate overall facial harmony score based on all analyses.
        
        Weighted combination of all geometric analysis results.
        """
        try:
            # Extract scores from various analyses
            golden_ratio_score = analysis_results.get('golden_ratio_analysis', {}).get('overall_score', 0)
            thirds_score = 100 - analysis_results.get('facial_thirds_analysis', {}).get('deviation_score', 100)
            fifths_score = 100 - analysis_results.get('facial_fifths_analysis', {}).get('deviation_score', 100)
            symmetry_score = analysis_results.get('symmetry_analysis', {}).get('overall_score', 0)
            canon_score = analysis_results.get('neoclassical_canons', {}).get('overall_score', 0)
            ogee_score = analysis_results.get('ogee_curve_analysis', {}).get('overall_score', 0)
            
            # Weighted scoring (weights sum to 1.0)
            weights = {
                'golden_ratio': 0.25,
                'facial_thirds': 0.20,
                'facial_fifths': 0.15,
                'symmetry': 0.25,
                'neoclassical_canons': 0.10,
                'ogee_curve': 0.05
            }
            
            # Calculate weighted average
            weighted_score = (
                golden_ratio_score * weights['golden_ratio'] +
                thirds_score * weights['facial_thirds'] +
                fifths_score * weights['facial_fifths'] +
                symmetry_score * weights['symmetry'] +
                canon_score * weights['neoclassical_canons'] +
                ogee_score * weights['ogee_curve']
            )
            
            return {
                'overall_score': round(weighted_score, 1),
                'component_scores': {
                    'golden_ratio': round(golden_ratio_score, 1),
                    'facial_thirds': round(thirds_score, 1),
                    'facial_fifths': round(fifths_score, 1),
                    'symmetry': round(symmetry_score, 1),
                    'neoclassical_canons': round(canon_score, 1),
                    'ogee_curve': round(ogee_score, 1)
                },
                'interpretation': self._interpret_harmony_score(weighted_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating facial harmony: {e}")
            return {'error': str(e)}
    
    # Helper methods for calculations and interpretations
    
    def _calculate_ratio_score(self, measured_ratio: float, ideal_ratio: float) -> float:
        """Calculate how close a measured ratio is to the ideal (0-100 scale)."""
        if ideal_ratio == 0:
            return 0
        deviation = abs(measured_ratio - ideal_ratio) / ideal_ratio
        score = max(0, 100 - (deviation * 100))
        return min(100, score)
    
    def _calculate_proportion_deviation(self, measured: List[float], ideal: List[float]) -> float:
        """Calculate deviation from ideal proportions."""
        if len(measured) != len(ideal):
            return 100
        
        total_deviation = sum(abs(m - i) for m, i in zip(measured, ideal))
        return min(100, total_deviation)
    
    def _calculate_curve_definition(self, cheekbone: Dict, jaw: Dict, landmarks: Dict) -> float:
        """Calculate the definition of the ogee curve."""
        # Simplified curve calculation based on the angle and distance
        # In a real implementation, this would involve more complex curve fitting
        
        # Calculate the vertical drop from cheekbone to jaw
        vertical_drop = abs(cheekbone['y'] - jaw['y'])
        
        # Calculate horizontal distance
        horizontal_distance = abs(cheekbone['x'] - jaw['x'])
        
        # A well-defined ogee curve has a good vertical-to-horizontal ratio
        if horizontal_distance > 0:
            curve_ratio = vertical_drop / horizontal_distance
            # Normalize to 0-100 scale (optimal ratio around 1.2-1.8)
            optimal_ratio = 1.5
            score = self._calculate_ratio_score(curve_ratio, optimal_ratio)
            return score
        
        return 50  # Neutral score if cannot calculate
    
    def _get_feature_name(self, left_idx: int, right_idx: int) -> str:
        """Get human-readable name for landmark pair."""
        feature_map = {
            (33, 362): "Inner Eye Corners",
            (133, 263): "Outer Eye Corners", 
            (61, 291): "Mouth Corners",
            (234, 454): "Face Edges",
            (205, 425): "Cheekbones",
            (172, 397): "Jaw Points",
            (46, 276): "Eyebrows"
        }
        return feature_map.get((left_idx, right_idx), "Unknown Feature")
    
    # Interpretation methods
    
    def _interpret_golden_ratio_score(self, score: float) -> str:
        """Provide interpretation of golden ratio score."""
        if score >= 85:
            return "Excellent adherence to golden ratio proportions"
        elif score >= 70:
            return "Good golden ratio proportions with minor deviations"
        elif score >= 55:
            return "Moderate golden ratio proportions"
        else:
            return "Significant deviation from golden ratio ideals"
    
    def _interpret_thirds_score(self, deviation: float) -> str:
        """Provide interpretation of facial thirds score."""
        if deviation <= 5:
            return "Excellent facial thirds proportions"
        elif deviation <= 10:
            return "Good facial thirds with minor variations"
        elif deviation <= 20:
            return "Moderate facial thirds proportions"
        else:
            return "Significant deviation from ideal facial thirds"
    
    def _interpret_fifths_score(self, deviation: float) -> str:
        """Provide interpretation of facial fifths score."""
        if deviation <= 8:
            return "Excellent facial fifths proportions"
        elif deviation <= 15:
            return "Good facial fifths with minor variations"
        elif deviation <= 25:
            return "Moderate facial fifths proportions"
        else:
            return "Significant deviation from ideal facial fifths"
    
    def _interpret_symmetry_score(self, score: float) -> str:
        """Provide interpretation of symmetry score."""
        if score >= 90:
            return "Excellent facial symmetry"
        elif score >= 80:
            return "Good facial symmetry with minor asymmetries"
        elif score >= 70:
            return "Moderate facial symmetry"
        else:
            return "Noticeable facial asymmetries"
    
    def _interpret_canon_score(self, score: float) -> str:
        """Provide interpretation of neoclassical canon score."""
        if score >= 85:
            return "Excellent adherence to classical beauty standards"
        elif score >= 70:
            return "Good adherence to classical proportions"
        elif score >= 55:
            return "Moderate adherence to classical standards"
        else:
            return "Significant deviation from classical beauty canons"
    
    def _interpret_ogee_score(self, score: float) -> str:
        """Provide interpretation of ogee curve score."""
        if score >= 80:
            return "Well-defined ogee curve suggesting youthful contours"
        elif score >= 60:
            return "Moderate ogee curve definition"
        elif score >= 40:
            return "Subtle ogee curve present"
        else:
            return "Minimal ogee curve definition"
    
    def _interpret_harmony_score(self, score: float) -> str:
        """Provide interpretation of overall facial harmony score."""
        if score >= 90:
            return "Exceptional facial harmony and proportions"
        elif score >= 80:
            return "Excellent facial harmony with minor imperfections"
        elif score >= 70:
            return "Good facial harmony overall"
        elif score >= 60:
            return "Moderate facial harmony"
        else:
            return "Significant opportunities for proportion enhancement"

def test_geometric_analysis(image_path: str):
    """Test function for geometric analysis."""
    analyzer = FacialGeometricAnalyzer()
    results = analyzer.analyze_face(image_path)
    
    if 'error' not in results:
        print("✅ Geometric analysis completed successfully")
        print(f"Golden Ratio Score: {results['golden_ratio_analysis']['overall_score']}")
        print(f"Symmetry Score: {results['symmetry_analysis']['overall_score']}")
        print(f"Facial Harmony: {results['facial_harmony_score']['overall_score']}")
        return True
    else:
        print(f"❌ Analysis failed: {results['error']}")
        return False

if __name__ == "__main__":
    # Test with a sample image
    test_image = "static/uploads/face_analysis/test_image.jpg"
    test_geometric_analysis(test_image)