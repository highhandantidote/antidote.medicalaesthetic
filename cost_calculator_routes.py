"""
Treatment Cost Calculator routes.

This module provides routes for the treatment cost calculator functionality,
including procedure-specific options for accurate cost estimation.
"""
import json
import logging
from flask import Blueprint, render_template, jsonify, request, session
from sqlalchemy import select, text
from models import Procedure, db

# Create blueprint
cost_calculator_bp = Blueprint('cost_calculator', __name__, url_prefix='/cost-calculator')

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Model definitions for procedure options (without creating actual models)
class ProcedureOption:
    """Class to represent a procedure option (not a SQLAlchemy model)."""
    def __init__(self, id, procedure_id, option_name, option_type, is_required):
        self.id = id
        self.procedure_id = procedure_id
        self.option_name = option_name
        self.option_type = option_type
        self.is_required = is_required
        self.values = []
        
class OptionValue:
    """Class to represent an option value (not a SQLAlchemy model)."""
    def __init__(self, id, option_id, value_name, cost_factor, is_default):
        self.id = id
        self.option_id = option_id
        self.value_name = value_name
        self.cost_factor = cost_factor
        self.is_default = is_default

@cost_calculator_bp.route('/', methods=['GET'])
def cost_calculator():
    """Render the treatment cost calculator page."""
    try:
        # Get all procedures for the dropdown
        procedures = Procedure.query.order_by(Procedure.procedure_name).all()
        
        return render_template('cost_calculator.html', procedures=procedures)
    except Exception as e:
        logger.error(f"Error rendering cost calculator: {str(e)}")
        return render_template('error.html', message="Unable to load cost calculator. Please try again later.")

@cost_calculator_bp.route('/api/procedure/<int:procedure_id>', methods=['GET'])
def get_procedure_details(procedure_id):
    """Get procedure details for the calculator, including procedure-specific options."""
    try:
        procedure = Procedure.query.get(procedure_id)
        
        if not procedure:
            return jsonify({
                'success': False,
                'message': 'Procedure not found'
            }), 404
        
        # Convert to dictionary for JSON response
        procedure_data = {
            'id': procedure.id,
            'name': procedure.procedure_name,
            'description': procedure.short_description,
            'body_part': procedure.body_part,
            'min_cost': procedure.min_cost,
            'max_cost': procedure.max_cost,
            'avg_rating': procedure.avg_rating if hasattr(procedure, 'avg_rating') else None,
        }
        
        # Get procedure-specific options
        procedure_options = []
        
        # Query for options directly using raw SQL for simplicity
        option_query = text("""
            SELECT po.id, po.procedure_id, po.option_name, po.option_type, po.is_required
            FROM procedure_options po
            WHERE po.procedure_id = :procedure_id
            ORDER BY po.id
        """)
        options_result = db.session.execute(option_query, {'procedure_id': procedure_id}).fetchall()
        
        for opt in options_result:
            option = ProcedureOption(
                id=opt[0],
                procedure_id=opt[1],
                option_name=opt[2],
                option_type=opt[3],
                is_required=opt[4]
            )
            
            # Get values for this option
            value_query = text("""
                SELECT pov.id, pov.option_id, pov.value_name, pov.cost_factor, pov.is_default
                FROM procedure_option_values pov
                WHERE pov.option_id = :option_id
                ORDER BY pov.id
            """)
            values_result = db.session.execute(value_query, {'option_id': option.id}).fetchall()
            
            for val in values_result:
                option_value = OptionValue(
                    id=val[0],
                    option_id=val[1],
                    value_name=val[2],
                    cost_factor=val[3],
                    is_default=val[4]
                )
                # Convert to dictionary for JSON serialization
                option.values.append({
                    'id': option_value.id,
                    'value_name': option_value.value_name,
                    'cost_factor': option_value.cost_factor,
                    'is_default': option_value.is_default
                })
            
            # Convert option to dictionary for JSON serialization
            procedure_options.append({
                'id': option.id,
                'name': option.option_name,
                'type': option.option_type,
                'required': option.is_required,
                'values': option.values
            })
        
        # Add options to procedure data
        procedure_data['options'] = procedure_options
        
        return jsonify({
            'success': True,
            'procedure': procedure_data
        })
    except Exception as e:
        logger.error(f"Error fetching procedure details: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500