#!/usr/bin/env python3
"""
API endpoints for doctor verification workflow.

This module defines the API endpoints for the doctor verification workflow,
using the functions from verify_doctor_workflow.py.
"""
import flask
from flask import Blueprint, request, jsonify
import logging
from verify_doctor_workflow import (
    get_pending_doctors,
    get_doctor_details,
    approve_doctor,
    reject_doctor,
    get_verification_stats,
    find_doctors_by_criteria
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a blueprint for doctor verification API
verification_api = Blueprint('verification_api', __name__, url_prefix='/api/verification')

@verification_api.route('/doctors/pending', methods=['GET'])
def api_get_pending_doctors():
    """Get a list of pending doctor verification requests."""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        doctors = get_pending_doctors(limit=limit, offset=offset)
        return jsonify({
            'success': True,
            'count': len(doctors),
            'doctors': doctors
        })
    except Exception as e:
        logger.error(f"Error in api_get_pending_doctors: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@verification_api.route('/doctors/<int:doctor_id>', methods=['GET'])
def api_get_doctor_details(doctor_id):
    """Get detailed information about a specific doctor."""
    try:
        doctor = get_doctor_details(doctor_id)
        if not doctor:
            return jsonify({
                'success': False,
                'error': f"Doctor with ID {doctor_id} not found"
            }), 404
        
        return jsonify({
            'success': True,
            'doctor': doctor
        })
    except Exception as e:
        logger.error(f"Error in api_get_doctor_details: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@verification_api.route('/doctors/<int:doctor_id>/approve', methods=['POST'])
def api_approve_doctor(doctor_id):
    """Approve a doctor's verification request."""
    try:
        # Get the current user ID (admin) from the session or request
        # This should be implemented with proper authentication
        admin_id = request.json.get('admin_id')
        
        # Approve the doctor
        success = approve_doctor(doctor_id, admin_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': f"Failed to approve doctor with ID {doctor_id}"
            }), 400
        
        return jsonify({
            'success': True,
            'message': f"Doctor with ID {doctor_id} approved successfully"
        })
    except Exception as e:
        logger.error(f"Error in api_approve_doctor: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@verification_api.route('/doctors/<int:doctor_id>/reject', methods=['POST'])
def api_reject_doctor(doctor_id):
    """Reject a doctor's verification request."""
    try:
        # Get rejection reason and admin ID from request
        reason = request.json.get('reason', "Verification requirements not met")
        admin_id = request.json.get('admin_id')
        
        # Reject the doctor
        success = reject_doctor(doctor_id, reason, admin_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': f"Failed to reject doctor with ID {doctor_id}"
            }), 400
        
        return jsonify({
            'success': True,
            'message': f"Doctor with ID {doctor_id} rejected successfully"
        })
    except Exception as e:
        logger.error(f"Error in api_reject_doctor: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@verification_api.route('/stats', methods=['GET'])
def api_get_verification_stats():
    """Get statistics on doctor verification."""
    try:
        stats = get_verification_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error in api_get_verification_stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@verification_api.route('/doctors/search', methods=['GET'])
def api_find_doctors():
    """Search for doctors by various criteria."""
    try:
        search_text = request.args.get('q')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        doctors = find_doctors_by_criteria(
            search_text=search_text,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'count': len(doctors),
            'doctors': doctors
        })
    except Exception as e:
        logger.error(f"Error in api_find_doctors: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# This blueprint should be registered in routes.py
def register_verification_api(app):
    """Register the verification API blueprint with the Flask app."""
    app.register_blueprint(verification_api)