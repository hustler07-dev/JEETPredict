#!/usr/bin/env python3
"""
Enhanced Real Estate Price Prediction Server
============================================

A Flask-based web server for predicting real estate prices using machine learning.
Features robust error handling, flexible input validation, and comprehensive logging.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=['*'])  # Enable CORS for all origins

# Configuration
CONFIG = {
    'HOST': os.getenv('FLASK_HOST', '0.0.0.0'),
    'PORT': int(os.getenv('FLASK_PORT', 5001)),
    'DEBUG': os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
    'COLUMNS_PATH': os.getenv('COLUMNS_PATH', './Columnsnew.json'),
    'MODEL_PATH': os.getenv('MODEL_PATH', './Real Estate Data V21.pickle')
}


def validate_paths() -> bool:
    """Validate that required model files exist."""
    columns_path = Path(CONFIG['COLUMNS_PATH'])
    model_path = Path(CONFIG['MODEL_PATH'])
    
    if not columns_path.exists():
        logger.error(f"Columns file not found: {columns_path.absolute()}")
        return False
    
    if not model_path.exists():
        logger.error(f"Model file not found: {model_path.absolute()}")
        return False
    
    logger.info(f"Model files validated: {columns_path.absolute()}, {model_path.absolute()}")
    return True


def safe_type_conversion(value: Any, target_type: type, field_name: str) -> Any:
    """Safely convert value to target type with descriptive error messages."""
    if value is None or value == "":
        raise ValueError(f"{field_name} cannot be empty")
    
    try:
        if target_type == float:
            return float(value)
        elif target_type == int:
            # Handle cases like "2.0" -> 2
            return int(float(value))
        else:
            return target_type(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid {field_name}: '{value}' cannot be converted to {target_type.__name__}")


def extract_input_data(request_obj) -> Dict[str, Any]:
    """Extract and normalize input data from request (JSON or form-data)."""
    data = {}
    
    # Try JSON first, then form data
    if request_obj.is_json:
        data = request_obj.get_json(silent=True) or {}
    else:
        # Convert form data to dict
        data = dict(request_obj.form)
        # If form is empty, try to force JSON parsing
        if not data:
            data = request_obj.get_json(force=True, silent=True) or {}
    
    if not data:
        raise ValueError("No input data provided in request")
    
    logger.info(f"Extracted raw input data: {data}")
    return data


def get_flexible_key(data: Dict[str, Any], possible_keys: list) -> Optional[str]:
    """Get value from data using flexible key matching (case-insensitive)."""
    # First, try exact matches
    for key in possible_keys:
        if key in data and data[key] not in (None, "", "null"):
            return str(data[key]).strip()
    
    # Then try case-insensitive matches
    data_lower = {k.lower(): v for k, v in data.items()}
    for key in possible_keys:
        key_lower = key.lower()
        if key_lower in data_lower and data_lower[key_lower] not in (None, "", "null"):
            return str(data_lower[key_lower]).strip()
    
    return None


@app.route('/', methods=['GET'])
def home() -> Response:
    """Home endpoint with API information."""
    return jsonify({
        'message': '🏠 Real Estate Price Prediction API',
        'version': '2.0',
        'status': 'running',
        'endpoints': {
            'health': f"http://localhost:{CONFIG['PORT']}/health",
            'locations': f"http://localhost:{CONFIG['PORT']}/get_location_names",
            'predict': f"http://localhost:{CONFIG['PORT']}/predict_home_price"
        },
        'usage': {
            'predict_example': {
                'url': f"http://localhost:{CONFIG['PORT']}/predict_home_price",
                'method': 'POST',
                'body': {
                    'total_sqft': 1200,
                    'location': 'Whitefield, Bangalore',
                    'bhk': 3,
                    'bath': 2
                }
            }
        }
    })


@app.errorhandler(404)
def not_found(error) -> Response:
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'message': f'The requested URL was not found on the server',
        'available_endpoints': [
            f"GET http://localhost:{CONFIG['PORT']}/",
            f"GET http://localhost:{CONFIG['PORT']}/health",
            f"GET http://localhost:{CONFIG['PORT']}/get_location_names",
            f"POST http://localhost:{CONFIG['PORT']}/predict_home_price"
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error) -> Response:
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred on the server'
    }), 500


@app.route('/health', methods=['GET'])
def health_check() -> Response:
    """Health check endpoint."""
    try:
        # Test if model artifacts can be loaded
        locations_count = len(util.get_location_names())
        return jsonify({
            'status': 'healthy',
            'message': 'Server is running successfully',
            'locations_loaded': locations_count,
            'model_status': 'loaded' if util.__model else 'not_loaded'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'message': 'Server is experiencing issues',
            'error': str(e)
        }), 503


@app.route('/get_location_names', methods=['GET'])
def get_location_names() -> Response:
    """Get all available location names."""
    try:
        logger.info("Fetching location names...")
        locations = util.get_location_names()
        
        if not locations:
            logger.warning("No locations found in the dataset")
            return jsonify({
                'locations': [],
                'count': 0,
                'message': 'No locations available'
            })
        
        logger.info(f"Successfully retrieved {len(locations)} locations")
        return jsonify({
            'locations': locations,
            'count': len(locations),
            'message': 'Locations retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to get location names: {e}")
        return jsonify({
            'error': 'Failed to retrieve locations',
            'message': str(e),
            'locations': [],
            'count': 0
        }), 500


@app.route('/predict_home_price', methods=['POST'])
def predict_home_price():
    # Accept form-data or JSON
    data = request.form.to_dict() if request.form else request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    try:
        total_sqft = float(data.get('total_sqft') or data.get('totalSqft'))
        location = data['location']
        bhk = int(data.get('bhk'))
        bath = int(data.get('bath'))
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({'error': 'Invalid input', 'message': str(e)}), 400

    try:
        est_price = util.predict_price(location, total_sqft, bhk, bath)
        return jsonify({'Estimated_Price': est_price})
    except Exception as e:
        return jsonify({'error': 'Prediction failed', 'message': str(e)}), 500


def initialize_server():
    """Initialize server components."""
    logger.info("Initializing server...")
    
    # Validate paths
    if not validate_paths():
        logger.error("Path validation failed. Server may not function correctly.")
        return False
    
    # Pre-load artifacts to reduce first-request latency
    try:
        logger.info("Pre-loading model artifacts...")
        util.load_artifacts(CONFIG['COLUMNS_PATH'], CONFIG['MODEL_PATH'])
        locations_count = len(util.get_location_names())
        logger.info(f"Artifacts loaded successfully. {locations_count} locations available.")
        return True
    except Exception as e:
        logger.error(f"Failed to pre-load artifacts: {e}")
        logger.warning("Server will attempt lazy loading on first request.")
        return False


def main():
    """Main server entry point."""
    print("=" * 60)
    print("🏠 Real Estate Price Prediction Server")
    print("=" * 60)
    
    # Log configuration
    logger.info("Server configuration:")
    for key, value in CONFIG.items():
        logger.info(f"  {key}: {value}")
    
    # Initialize server components
    if not initialize_server():
        logger.error("Server initialization failed, but continuing with lazy loading...")
    
    print(f"\n🚀 Starting server on http://{CONFIG['HOST']}:{CONFIG['PORT']}")
    print(f"🌐 Local access: http://localhost:{CONFIG['PORT']}")
    print("\nAvailable endpoints:")
    print(f"  • GET  http://localhost:{CONFIG['PORT']}/health                - Health check")
    print(f"  • GET  http://localhost:{CONFIG['PORT']}/get_location_names    - Get all locations") 
    print(f"  • POST http://localhost:{CONFIG['PORT']}/predict_home_price    - Predict property price")
    print("\n" + "=" * 60)
    
    try:
        app.run(
            host=CONFIG['HOST'],
            port=CONFIG['PORT'],
            debug=CONFIG['DEBUG'],
            use_reloader=False,  # Disable reloader to prevent artifact reload issues
            threaded=True  # Enable threading for better concurrent handling
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()