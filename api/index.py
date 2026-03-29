"""
PlacetaID - Vercel Serverless Demo
Simple Flask app for demo deployment
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os

# Create simple Flask app for demo
app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend')

# Enable CORS for all routes
CORS(app)

@app.route('/')
def index():
    """Serve the main login page"""
    return send_from_directory('../frontend', 'login.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('../frontend/static', path)

@app.route('/dashboard')
def dashboard():
    """Serve dashboard page"""
    return send_from_directory('../frontend', 'dashboard.html')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'PlacetaID Demo Server Running',
        'version': '1.0.0'
    })

@app.route('/oauth/authorize', methods=['GET', 'POST'])
def oauth_authorize():
    """Mock OAuth authorize endpoint for demo"""
    if request.method == 'GET':
        # Return the login form
        return send_from_directory('../frontend', 'login.html')
    else:
        # Mock successful authorization
        return jsonify({
            'success': True,
            'message': 'Demo authorization successful',
            'code': 'demo-auth-code-12345',
            'state': request.args.get('state', 'demo-state')
        })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

# Vercel will automatically detect and use this Flask app
