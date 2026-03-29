#!/usr/bin/env python3
"""
PlacetaID - Centralized Authentication Gateway
Main Flask application
"""

import os
import logging
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from config import DevelopmentConfig, ProductionConfig, TestingConfig
from models import db, AuditLog
from routes.oauth import oauth_bp


def create_app(config_name='development'):
    """
    Application factory
    
    Args:
        config_name: 'development', 'production', or 'testing'
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Load configuration
    if config_name == 'production':
        config = ProductionConfig()
    elif config_name == 'testing':
        config = TestingConfig()
    else:
        config = DevelopmentConfig()
    
    app.config.from_object(config)
    
    # Initialize database
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Initialize extensions
    cors_origins = app.config.get('ALLOWED_ORIGINS', ['http://localhost:3000'])
    CORS(app, 
         resources={r"/oauth/*": {"origins": cors_origins}},
         supports_credentials=True)
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    jwt = JWTManager(app)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # File handler for errors
    error_handler = logging.FileHandler('logs/errors.log')
    error_handler.setLevel(logging.ERROR)
    app.logger.addHandler(error_handler)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    app.register_blueprint(oauth_bp)
    
    # Health check
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'PlacetaID Gateway',
            'version': '1.0.0'
        }), 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def index():
        """Root endpoint"""
        return jsonify({
            'service': 'PlacetaID - Centralized Authentication Gateway',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'oauth': '/oauth/*',
                'documentation': '/docs'
            }
        }), 200
    
    # Documentation placeholder
    @app.route('/docs', methods=['GET'])
    def docs():
        """API documentation"""
        return jsonify({
            'documentation': 'PlacetaID OAuth2 API',
            'endpoints': [
                '/oauth/authorize - OAuth2 authorization',
                '/oauth/token - Token exchange',
                '/oauth/validate - Validate credentials',
                '/oauth/logout - Sign out',
                '/oauth/profile - Get citizen profile',
                '/oauth/2fa/enable - Enable 2FA',
                '/oauth/2fa/confirm - Confirm 2FA setup',
                '/oauth/2fa/disable - Disable 2FA',
                '/users - GET/POST citizen management (demo)',
                '/audit-logs - GET audit records'
            ]
        }), 200

    # Citizen management for production readiness (demo endpoints)
    @app.route('/users', methods=['GET'])
    def list_users():
        citizens = []
        for c in Citizen.query.limit(100).all():
            citizens.append({
                'id': c.id,
                'dip_hash': c.dip_hash,
                'status': c.status,
                'totp_enabled': c.totp_enabled,
                'created_at': c.created_at.isoformat()
            })

        AuditLog.log_event(
            event_type='user_management',
            action='list_users',
            ip_address='system',
            status='success',
            metadata={'count': len(citizens)}
        )

        return jsonify({'users': citizens}), 200

    @app.route('/users', methods=['POST'])
    def create_user():
        from flask import request

        payload = request.get_json(silent=True) or {}
        dip_hash = payload.get('dip_hash')
        dependent_status = payload.get('status', 'active')

        if not dip_hash:
            return jsonify({'error': 'missing dip_hash'}), 400

        existing = Citizen.query.filter_by(dip_hash=dip_hash).first()
        if existing:
            return jsonify({'error': 'citizen exists'}), 409

        citizen = Citizen(
            dip_encrypted=b'',
            dip_hash=dip_hash,
            status=dependent_status,
            totp_enabled=payload.get('totp_enabled', False)
        )

        db.session.add(citizen)
        db.session.commit()

        AuditLog.log_event(
            event_type='user_management',
            action='create_user',
            ip_address=request.remote_addr or 'unknown',
            status='success',
            citizen_id=citizen.id,
            metadata={'status': citizen.status}
        )

        return jsonify({'id': citizen.id, 'status': citizen.status}), 201

    @app.route('/audit-logs', methods=['GET'])
    def list_audit_logs():
        logs = []
        for l in AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all():
            logs.append({
                'id': l.id,
                'event_type': l.event_type,
                'action': l.action,
                'status': l.status,
                'citizen_id': l.citizen_id,
                'created_at': l.created_at.isoformat(),
                'error_message': l.error_message,
                'metadata': l.metadata
            })

        return jsonify({'audit_logs': logs}), 200
    
    # Global error handlers
    @app.errorhandler(400)
    def bad_request(error):
        """400 Bad Request"""
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """401 Unauthorized"""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required or invalid credentials'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """403 Forbidden"""
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """404 Not Found"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """429 Rate Limit Exceeded"""
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.',
            'retry_after': error.description if hasattr(error, 'description') else '60'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 Internal Server Error"""
        db.session.rollback()
        
        AuditLog.log_event(
            'system',
            'internal_error',
            '127.0.0.1',
            status='failed',
            error_message=str(error)
        )
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """503 Service Unavailable"""
        return jsonify({
            'error': 'Service Unavailable',
            'message': 'The service is temporarily unavailable'
        }), 503
    
    # Request logging (for debugging in development)
    if app.debug:
        @app.before_request
        def log_request():
            """Log incoming requests in development"""
            from flask import request
            app.logger.debug(f'{request.method} {request.path} from {request.remote_addr}')
    
    return app


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000))
    )
