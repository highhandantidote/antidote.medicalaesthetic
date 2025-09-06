#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facial Analysis Visualization Module

This module provides canvas drawing and visualization functions for 
displaying geometric analysis results on facial images.
"""

import json
import base64
import logging
from typing import Dict, List, Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

class FacialVisualizationGenerator:
    """Generate visualization data for facial analysis canvas overlays."""
    
    def __init__(self):
        """Initialize the visualization generator."""
        self.golden_ratio = 1.618
        
        # Standard colors for different analysis types
        self.colors = {
            'golden_ratio': '#4361ee',
            'symmetry': '#7e3af2', 
            'thirds': '#16a34a',
            'fifths': '#dc2626',
            'landmarks': '#f59e0b',
            'measurements': '#0891b2'
        }
    
    def generate_golden_ratio_overlay(self, landmarks_data: Dict, analysis_results: Dict) -> Dict:
        """
        Generate golden ratio visualization data for canvas overlay.
        
        Args:
            landmarks_data: Facial landmarks data
            analysis_results: Golden ratio analysis results
            
        Returns:
            Dictionary containing drawing instructions for canvas
        """
        try:
            landmarks = landmarks_data['landmarks']
            golden_analysis = analysis_results.get('golden_ratio_analysis', {})
            
            # Image dimensions for scaling
            img_width = landmarks_data['image_dimensions']['width']
            img_height = landmarks_data['image_dimensions']['height']
            
            visualization_data = {
                'canvas_width': img_width,
                'canvas_height': img_height,
                'elements': []
            }
            
            # 1. Draw golden ratio rectangles
            face_bounds = landmarks_data['face_bounds']
            golden_rectangles = self._calculate_golden_rectangles(face_bounds)
            
            for rect in golden_rectangles:
                visualization_data['elements'].append({
                    'type': 'rectangle',
                    'x': rect['x'],
                    'y': rect['y'],
                    'width': rect['width'],
                    'height': rect['height'],
                    'stroke_color': self.colors['golden_ratio'],
                    'stroke_width': 2,
                    'fill': 'transparent'
                })
            
            # 2. Draw measurement lines
            measurements = golden_analysis.get('measurements', {})
            
            # Face length line
            if 10 in landmarks and 18 in landmarks:
                forehead = landmarks[10]
                chin = landmarks[18]
                visualization_data['elements'].append({
                    'type': 'line',
                    'x1': forehead['x'],
                    'y1': forehead['y'],
                    'x2': chin['x'], 
                    'y2': chin['y'],
                    'stroke_color': self.colors['measurements'],
                    'stroke_width': 2,
                    'label': 'Face Length'
                })
            
            # Face width line
            if 234 in landmarks and 454 in landmarks:
                left_face = landmarks[234]
                right_face = landmarks[454]
                visualization_data['elements'].append({
                    'type': 'line',
                    'x1': left_face['x'],
                    'y1': left_face['y'],
                    'x2': right_face['x'],
                    'y2': right_face['y'],
                    'stroke_color': self.colors['measurements'],
                    'stroke_width': 2,
                    'label': 'Face Width'
                })
            
            # 3. Add annotation points for key measurements
            key_points = [10, 18, 234, 454, 133, 362, 61, 291]
            for point_idx in key_points:
                if point_idx in landmarks:
                    point = landmarks[point_idx]
                    visualization_data['elements'].append({
                        'type': 'circle',
                        'x': point['x'],
                        'y': point['y'],
                        'radius': 4,
                        'fill_color': self.colors['golden_ratio'],
                        'stroke_color': '#ffffff',
                        'stroke_width': 2,
                        'interactive': True,
                        'tooltip': self._get_point_description(point_idx)
                    })
            
            return visualization_data
            
        except Exception as e:
            logger.error(f"Error generating golden ratio overlay: {e}")
            return {'error': str(e)}
    
    def generate_symmetry_overlay(self, landmarks_data: Dict, analysis_results: Dict) -> Dict:
        """Generate symmetry analysis visualization data."""
        try:
            landmarks = landmarks_data['landmarks']
            symmetry_analysis = analysis_results.get('symmetry_analysis', {})
            
            img_width = landmarks_data['image_dimensions']['width']
            img_height = landmarks_data['image_dimensions']['height']
            
            visualization_data = {
                'canvas_width': img_width,
                'canvas_height': img_height,
                'elements': []
            }
            
            # Draw central midline
            midline_x = symmetry_analysis.get('midline_x', img_width / 2)
            visualization_data['elements'].append({
                'type': 'line',
                'x1': midline_x,
                'y1': 0,
                'x2': midline_x,
                'y2': img_height,
                'stroke_color': self.colors['symmetry'],
                'stroke_width': 2,
                'stroke_style': 'dashed',
                'label': 'Facial Midline'
            })
            
            # Draw symmetry point pairs
            symmetry_pairs = [
                (33, 362),    # Inner eye corners
                (133, 263),   # Outer eye corners
                (61, 291),    # Mouth corners
                (234, 454),   # Face edges
            ]
            
            for left_idx, right_idx in symmetry_pairs:
                if left_idx in landmarks and right_idx in landmarks:
                    left_point = landmarks[left_idx]
                    right_point = landmarks[right_idx]
                    
                    # Draw connection line
                    visualization_data['elements'].append({
                        'type': 'line',
                        'x1': left_point['x'],
                        'y1': left_point['y'],
                        'x2': right_point['x'],
                        'y2': right_point['y'],
                        'stroke_color': self.colors['symmetry'],
                        'stroke_width': 1,
                        'opacity': 0.6
                    })
                    
                    # Draw points
                    for point, side in [(left_point, 'left'), (right_point, 'right')]:
                        visualization_data['elements'].append({
                            'type': 'circle',
                            'x': point['x'],
                            'y': point['y'],
                            'radius': 3,
                            'fill_color': self.colors['symmetry'],
                            'stroke_color': '#ffffff',
                            'stroke_width': 1,
                            'interactive': True,
                            'tooltip': f"Symmetry point ({side})"
                        })
            
            return visualization_data
            
        except Exception as e:
            logger.error(f"Error generating symmetry overlay: {e}")
            return {'error': str(e)}
    
    def generate_facial_thirds_overlay(self, landmarks_data: Dict, analysis_results: Dict) -> Dict:
        """Generate facial thirds visualization data."""
        try:
            landmarks = landmarks_data['landmarks']
            thirds_analysis = analysis_results.get('facial_thirds_analysis', {})
            
            img_width = landmarks_data['image_dimensions']['width']
            img_height = landmarks_data['image_dimensions']['height']
            
            visualization_data = {
                'canvas_width': img_width,
                'canvas_height': img_height,
                'elements': []
            }
            
            # Key horizontal lines for facial thirds
            if 10 in landmarks and 9 in landmarks and 2 in landmarks and 18 in landmarks:
                forehead = landmarks[10]
                eyebrow = landmarks[9]
                nose_base = landmarks[2]
                chin = landmarks[18]
                
                # Estimate hairline
                hairline_y = forehead['y'] - (abs(forehead['y'] - eyebrow['y']) * 0.3)
                
                # Draw horizontal lines for thirds
                face_left = landmarks[234]['x'] if 234 in landmarks else 0
                face_right = landmarks[454]['x'] if 454 in landmarks else img_width
                
                third_lines = [
                    {'y': hairline_y, 'label': 'Hairline'},
                    {'y': eyebrow['y'], 'label': 'Eyebrow Line'}, 
                    {'y': nose_base['y'], 'label': 'Nose Base'},
                    {'y': chin['y'], 'label': 'Chin'}
                ]
                
                for line in third_lines:
                    visualization_data['elements'].append({
                        'type': 'line',
                        'x1': face_left,
                        'y1': line['y'],
                        'x2': face_right,
                        'y2': line['y'],
                        'stroke_color': self.colors['thirds'],
                        'stroke_width': 2,
                        'label': line['label']
                    })
            
            return visualization_data
            
        except Exception as e:
            logger.error(f"Error generating facial thirds overlay: {e}")
            return {'error': str(e)}
    
    def generate_facial_fifths_overlay(self, landmarks_data: Dict, analysis_results: Dict) -> Dict:
        """Generate facial fifths visualization data."""
        try:
            landmarks = landmarks_data['landmarks']
            fifths_analysis = analysis_results.get('facial_fifths_analysis', {})
            
            img_width = landmarks_data['image_dimensions']['width']
            img_height = landmarks_data['image_dimensions']['height']
            
            visualization_data = {
                'canvas_width': img_width,
                'canvas_height': img_height,
                'elements': []
            }
            
            # Vertical lines for facial fifths
            fifth_points = [234, 33, 133, 362, 263, 454]  # Left to right
            labels = ['Left Edge', 'Left Eye Outer', 'Left Eye Inner', 'Right Eye Inner', 'Right Eye Outer', 'Right Edge']
            
            for i, point_idx in enumerate(fifth_points):
                if point_idx in landmarks:
                    point = landmarks[point_idx]
                    
                    # Draw vertical line
                    visualization_data['elements'].append({
                        'type': 'line',
                        'x1': point['x'],
                        'y1': 0,
                        'x2': point['x'],
                        'y2': img_height,
                        'stroke_color': self.colors['fifths'],
                        'stroke_width': 1,
                        'stroke_style': 'dashed',
                        'label': labels[i] if i < len(labels) else f'Point {i+1}'
                    })
            
            return visualization_data
            
        except Exception as e:
            logger.error(f"Error generating facial fifths overlay: {e}")
            return {'error': str(e)}
    
    def generate_neoclassical_overlay(self, landmarks_data: Dict, analysis_results: Dict) -> Dict:
        """Generate neoclassical canons visualization data."""
        try:
            landmarks = landmarks_data['landmarks']
            canon_analysis = analysis_results.get('neoclassical_canons', {})
            
            img_width = landmarks_data['image_dimensions']['width']
            img_height = landmarks_data['image_dimensions']['height']
            
            visualization_data = {
                'canvas_width': img_width,
                'canvas_height': img_height,
                'elements': []
            }
            
            # Eye width measurements
            if 133 in landmarks and 33 in landmarks and 362 in landmarks:
                left_eye_inner = landmarks[133]
                left_eye_outer = landmarks[33]
                right_eye_inner = landmarks[362]
                
                # Draw eye width
                visualization_data['elements'].append({
                    'type': 'line',
                    'x1': left_eye_inner['x'],
                    'y1': left_eye_inner['y'],
                    'x2': left_eye_outer['x'],
                    'y2': left_eye_outer['y'],
                    'stroke_color': '#e11d48',
                    'stroke_width': 3,
                    'label': 'Eye Width'
                })
                
                # Draw eye separation
                visualization_data['elements'].append({
                    'type': 'line',
                    'x1': left_eye_inner['x'],
                    'y1': left_eye_inner['y'],
                    'x2': right_eye_inner['x'],
                    'y2': right_eye_inner['y'],
                    'stroke_color': '#059669',
                    'stroke_width': 3,
                    'label': 'Eye Separation'
                })
            
            # Nose width
            if 220 in landmarks and 305 in landmarks:
                nose_left = landmarks[220]
                nose_right = landmarks[305]
                
                visualization_data['elements'].append({
                    'type': 'line',
                    'x1': nose_left['x'],
                    'y1': nose_left['y'],
                    'x2': nose_right['x'],
                    'y2': nose_right['y'],
                    'stroke_color': '#7c2d12',
                    'stroke_width': 3,
                    'label': 'Nose Width'
                })
            
            # Mouth width
            if 61 in landmarks and 291 in landmarks:
                mouth_left = landmarks[61]
                mouth_right = landmarks[291]
                
                visualization_data['elements'].append({
                    'type': 'line',
                    'x1': mouth_left['x'],
                    'y1': mouth_left['y'],
                    'x2': mouth_right['x'],
                    'y2': mouth_right['y'],
                    'stroke_color': '#9333ea',
                    'stroke_width': 3,
                    'label': 'Mouth Width'
                })
            
            return visualization_data
            
        except Exception as e:
            logger.error(f"Error generating neoclassical overlay: {e}")
            return {'error': str(e)}
    
    def _calculate_golden_rectangles(self, face_bounds: Dict) -> List[Dict]:
        """Calculate golden ratio rectangles within face bounds."""
        rectangles = []
        
        # Main face rectangle
        face_width = face_bounds['width']
        face_height = face_bounds['height']
        
        # Golden rectangle within face bounds
        if face_width / face_height > self.golden_ratio:
            # Face is wider, fit height
            golden_width = face_height * self.golden_ratio
            x_offset = (face_width - golden_width) / 2
            rectangles.append({
                'x': face_bounds['min_x'] + x_offset,
                'y': face_bounds['min_y'],
                'width': golden_width,
                'height': face_height
            })
        else:
            # Face is taller, fit width
            golden_height = face_width / self.golden_ratio
            y_offset = (face_height - golden_height) / 2
            rectangles.append({
                'x': face_bounds['min_x'],
                'y': face_bounds['min_y'] + y_offset,
                'width': face_width,
                'height': golden_height
            })
        
        return rectangles
    
    def _get_point_description(self, landmark_idx: int) -> str:
        """Get description for landmark point."""
        point_descriptions = {
            10: "Forehead Center",
            18: "Chin Bottom",
            234: "Left Face Edge",
            454: "Right Face Edge",
            133: "Left Eye Inner Corner",
            362: "Right Eye Inner Corner",
            33: "Left Eye Outer Corner",
            263: "Right Eye Outer Corner",
            61: "Left Mouth Corner",
            291: "Right Mouth Corner",
            1: "Nose Tip",
            2: "Nose Base",
            9: "Between Eyebrows"
        }
        return point_descriptions.get(landmark_idx, f"Landmark {landmark_idx}")
    
    def generate_canvas_javascript(self, visualization_data: Dict, canvas_id: str) -> str:
        """
        Generate JavaScript code for drawing on HTML5 canvas.
        
        Args:
            visualization_data: Visualization data from overlay generation methods
            canvas_id: HTML canvas element ID
            
        Returns:
            JavaScript code string for canvas drawing
        """
        js_code = f"""
// Canvas drawing code for {canvas_id}
const canvas = document.getElementById('{canvas_id}');
if (canvas) {{
    const ctx = canvas.getContext('2d');
    const visualizationData = {json.dumps(visualization_data)};
    
    // Set canvas dimensions
    canvas.width = visualizationData.canvas_width;
    canvas.height = visualizationData.canvas_height;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw each element
    visualizationData.elements.forEach(element => {{
        ctx.save();
        
        switch(element.type) {{
            case 'line':
                ctx.beginPath();
                ctx.moveTo(element.x1, element.y1);
                ctx.lineTo(element.x2, element.y2);
                ctx.strokeStyle = element.stroke_color || '#000000';
                ctx.lineWidth = element.stroke_width || 1;
                if (element.stroke_style === 'dashed') {{
                    ctx.setLineDash([5, 5]);
                }}
                ctx.stroke();
                break;
                
            case 'rectangle':
                ctx.beginPath();
                ctx.rect(element.x, element.y, element.width, element.height);
                ctx.strokeStyle = element.stroke_color || '#000000';
                ctx.lineWidth = element.stroke_width || 1;
                ctx.stroke();
                if (element.fill && element.fill !== 'transparent') {{
                    ctx.fillStyle = element.fill;
                    ctx.fill();
                }}
                break;
                
            case 'circle':
                ctx.beginPath();
                ctx.arc(element.x, element.y, element.radius || 3, 0, 2 * Math.PI);
                if (element.fill_color) {{
                    ctx.fillStyle = element.fill_color;
                    ctx.fill();
                }}
                if (element.stroke_color) {{
                    ctx.strokeStyle = element.stroke_color;
                    ctx.lineWidth = element.stroke_width || 1;
                    ctx.stroke();
                }}
                break;
        }}
        
        ctx.restore();
    }});
}}
"""
        return js_code
    
    def generate_measurement_annotations(self, analysis_results: Dict) -> List[Dict]:
        """Generate interactive annotation data for measurements."""
        annotations = []
        
        # Golden ratio measurements
        golden_analysis = analysis_results.get('golden_ratio_analysis', {})
        measurements = golden_analysis.get('measurements', {})
        
        for measurement_name, data in measurements.items():
            annotations.append({
                'type': 'measurement',
                'name': measurement_name.replace('_', ' ').title(),
                'measured_ratio': data.get('ratio', 0),
                'ideal_ratio': data.get('ideal', 0),
                'score': data.get('score', 0),
                'category': 'golden_ratio'
            })
        
        # Symmetry measurements  
        symmetry_analysis = analysis_results.get('symmetry_analysis', {})
        asymmetries = symmetry_analysis.get('asymmetry_details', [])
        
        for asymmetry in asymmetries:
            annotations.append({
                'type': 'asymmetry',
                'feature': asymmetry.get('feature', ''),
                'symmetry_score': asymmetry.get('symmetry_score', 0),
                'category': 'symmetry'
            })
        
        return annotations

def test_visualization(image_path: str):
    """Test function for visualization generation."""
    try:
        from .facial_landmarks import FacialLandmarkDetector
        from .geometric_analysis import FacialGeometricAnalyzer
        
        # Detect landmarks and analyze
        detector = FacialLandmarkDetector()
        analyzer = FacialGeometricAnalyzer()
        
        landmarks_data = detector.detect_landmarks(image_path)
        analysis_results = analyzer.analyze_face(image_path)
        
        if landmarks_data and 'error' not in analysis_results:
            # Generate visualizations
            viz_gen = FacialVisualizationGenerator()
            
            golden_overlay = viz_gen.generate_golden_ratio_overlay(landmarks_data, analysis_results)
            symmetry_overlay = viz_gen.generate_symmetry_overlay(landmarks_data, analysis_results)
            
            print("✅ Visualization generation completed successfully")
            print(f"Golden ratio overlay elements: {len(golden_overlay.get('elements', []))}")
            print(f"Symmetry overlay elements: {len(symmetry_overlay.get('elements', []))}")
            return True
        else:
            print("❌ Failed to generate visualizations - missing landmark or analysis data")
            return False
            
    except Exception as e:
        print(f"❌ Visualization test failed: {e}")
        return False

if __name__ == "__main__":
    test_image = "static/uploads/face_analysis/test_image.jpg"
    test_visualization(test_image)