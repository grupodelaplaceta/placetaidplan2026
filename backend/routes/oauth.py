"""
OAuth2 routes for PlacetaID
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from services.auth_service import auth_service
from services.token_service import token_service, require_auth
from services.rate_limiter import rate_limiter, RateLimitConfig
from models import db, Citizen, AuditLog
from utils.validators import validators
from functools import wraps


oauth_bp = Blueprint('oauth', __name__, url_prefix='/oauth')


@oauth_bp.before_request
def before_oauth_request():
    """Log all OAuth requests"""
    request.start_time = datetime.utcnow()


@oauth_bp.after_request
def after_oauth_request(response):
    """Log OAuth request result"""
    if hasattr(request, 'start_time'):
        duration = (datetime.utcnow() - request.start_time).total_seconds()
        # You could log duration here for monitoring
    return response


@oauth_bp.route('/authorize', methods=['GET', 'POST'])
def authorize():
    """
    OAuth2 Authorization endpoint
    
    GET: Returns login form
    POST: Validates DIP, returns next step (TOTP or success)
    """
    # Rate limit by IP
    is_limited, rate_info = rate_limiter.is_rate_limited(
        f'ip:{request.remote_addr}',
        RateLimitConfig.IP_LIMIT['max_requests'],
        RateLimitConfig.IP_LIMIT['window_seconds']
    )
    
    if is_limited:
        return jsonify({
            'error': 'Too many requests',
            'retry_after': rate_info['retry_after']
        }), 429
    
    if request.method == 'GET':
        # Return login form
        client_id = request.args.get('client_id')
        redirect_uri = request.args.get('redirect_uri')
        state = request.args.get('state')
        scope = request.args.get('scope', 'openid profile')
        
        # Validate parameters
        if not all([client_id, redirect_uri, state]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        if not validators.validate_url(redirect_uri):
            return jsonify({'error': 'Invalid redirect_uri'}), 400
        
        # Render login form with parameters embedded
        return render_template('login.html', 
                              client_id=client_id,
                              redirect_uri=redirect_uri,
                              state=state,
                              scope=scope)
    
    elif request.method == 'POST':
        # Validate DIP
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
        
        dip = data.get('dip', '').strip()
        code = data.get('code')  # TOTP code
        
        if not dip:
            return jsonify({'error': 'DIP required'}), 400
        
        ip_address = request.remote_addr
        
        # Step 1: Validate DIP
        if not code:
            # First step: validate DIP only
            is_valid, error_msg, citizen = auth_service.validate_citizen_dip(dip, ip_address)
            
            if not is_valid:
                return jsonify({
                    'error': error_msg,
                    'step': 'dip'
                }), 401
            
            # DIP valid, check if 2FA is required
            if citizen.totp_enabled:
                return jsonify({
                    'success': True,
                    'step': 'totp',
                    'message': 'DIP valid, please enter TOTP code',
                    'citizen_id': citizen.id  # Temporary, for client-side use only
                }), 200
            else:
                # 2FA not enabled, skip to authorization
                return jsonify({
                    'success': True,
                    'step': 'authorize',
                    'citizen_id': citizen.id
                }), 200
        
        else:
            # Second step: validate TOTP code
            # First validate DIP again
            is_valid, error_msg, citizen = auth_service.validate_citizen_dip(dip, ip_address)
            
            if not is_valid:
                return jsonify({
                    'error': 'Invalid DIP',
                    'step': 'dip'
                }), 401
            
            # Now validate TOTP
            is_valid_2fa, error_msg_2fa = auth_service.validate_2fa_code(citizen, code, ip_address)
            
            if not is_valid_2fa:
                return jsonify({
                    'error': error_msg_2fa,
                    'step': 'totp'
                }), 401
            
            # Both DIP and TOTP valid
            return jsonify({
                'success': True,
                'step': 'authorize',
                'citizen_id': citizen.id
            }), 200


@oauth_bp.route('/token', methods=['POST'])
def token():
    """
    OAuth2 Token endpoint
    
    Exchanges authorization code for access token
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid request body'}), 400
    
    grant_type = data.get('grant_type')
    
    if grant_type == 'authorization_code':
        return handle_authorization_code_flow(data)
    elif grant_type == 'refresh_token':
        return handle_refresh_token_flow(data)
    else:
        return jsonify({'error': f'Unsupported grant_type: {grant_type}'}), 400


def handle_authorization_code_flow(data: dict):
    """Handle authorization code grant flow"""
    code = data.get('code')
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    redirect_uri = data.get('redirect_uri')
    
    if not all([code, client_id, redirect_uri]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # TODO: Validate client_secret against registered client
    # For now, we'll assume it's valid
    
    # Validate authorization code
    is_valid, citizen_id_or_error = token_service.validate_authorization_code(
        code, client_id, redirect_uri
    )
    
    if not is_valid:
        return jsonify({'error': citizen_id_or_error}), 401
    
    citizen_id = citizen_id_or_error
    ip_address = request.remote_addr
    
    # Generate access token
    access_token, refresh_token = token_service.generate_access_token(
        citizen_id, ip_address
    )
    
    # Get citizen to update last login
    citizen = Citizen.query.get(citizen_id)
    if citizen:
        citizen.update_last_login(device=request.headers.get('User-Agent', 'Unknown'))
    
    AuditLog.log_event(
        'authentication',
        'login_success',
        ip_address,
        citizen_id=citizen_id,
        status='success',
        metadata={'method': 'oauth2_code'}
    )
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 86400  # 24 hours
    }), 200


def handle_refresh_token_flow(data: dict):
    """Handle refresh token grant flow"""
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'refresh_token required'}), 400
    
    ip_address = request.remote_addr
    
    is_valid, new_access_token, error_msg = token_service.refresh_access_token(
        refresh_token, ip_address
    )
    
    if not is_valid:
        return jsonify({'error': error_msg}), 401
    
    return jsonify({
        'access_token': new_access_token,
        'token_type': 'Bearer',
        'expires_in': 86400
    }), 200


@oauth_bp.route('/validate', methods=['POST'])
def validate():
    """
    Validate and complete citizen authentication
    
    This endpoint receives the citizen_id and generates authorization code
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid request body'}), 400
    
    citizen_id = data.get('citizen_id')
    client_id = data.get('client_id')
    redirect_uri = data.get('redirect_uri')
    state = data.get('state')
    scope = data.get('scope', 'openid profile')
    
    if not all([citizen_id, client_id, redirect_uri, state]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Verify citizen exists
    citizen = Citizen.query.get(citizen_id)
    if not citizen:
        return jsonify({'error': 'Citizen not found'}), 404
    
    # Generate authorization code
    code = token_service.generate_authorization_code(
        citizen_id, client_id, redirect_uri, state, scope
    )
    
    return jsonify({
        'code': code,
        'state': state
    }), 200


@oauth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    Log out user and revoke current token
    """
    token = request.headers.get('Authorization', '').split(' ')[-1]
    ip_address = request.remote_addr
    
    token_service.revoke_token(token, ip_address)
    
    AuditLog.log_event(
        'authentication',
        'logout',
        ip_address,
        citizen_id=request.citizen_id,
        status='success'
    )
    
    return jsonify({'message': 'Logged out successfully'}), 200


@oauth_bp.route('/profile', methods=['GET'])
@require_auth
def profile():
    """
    Get authenticated citizen's profile
    """
    citizen = Citizen.query.get(request.citizen_id)
    
    if not citizen:
        return jsonify({'error': 'Citizen not found'}), 404
    
    return jsonify({
        'citizen_id': citizen.id,
        'age_tier': citizen.age_tier,
        'status': citizen.status,
        'totp_enabled': citizen.totp_enabled,
        'last_login_at': citizen.last_login_at.isoformat() if citizen.last_login_at else None,
        'created_at': citizen.created_at.isoformat()
    }), 200


@oauth_bp.route('/2fa/enable', methods=['POST'])
@require_auth
def enable_2fa():
    """
    Enable 2FA for authenticated citizen
    """
    citizen = Citizen.query.get(request.citizen_id)
    
    if not citizen:
        return jsonify({'error': 'Citizen not found'}), 404
    
    if citizen.totp_enabled:
        return jsonify({'error': '2FA already enabled'}), 400
    
    # Generate new 2FA secret and backup codes
    result = auth_service.enable_2fa(citizen)
    
    return jsonify({
        'secret': result['secret'],
        'qr_uri': result['qr_uri'],
        'backup_codes': result['backup_codes'],
        'message': 'Scan the QR code with your authenticator app. Save backup codes in a secure location.'
    }), 200


@oauth_bp.route('/2fa/confirm', methods=['POST'])
@require_auth
def confirm_2fa():
    """
    Confirm 2FA setup by verifying TOTP code
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid request body'}), 400
    
    code = data.get('code')
    
    if not code:
        return jsonify({'error': 'TOTP code required'}), 400
    
    citizen = Citizen.query.get(request.citizen_id)
    
    if not citizen:
        return jsonify({'error': 'Citizen not found'}), 404
    
    if auth_service.confirm_2fa(citizen, code):
        return jsonify({
            'message': '2FA successfully enabled',
            'totp_enabled': True
        }), 200
    else:
        return jsonify({'error': 'Invalid TOTP code'}), 401


@oauth_bp.route('/2fa/disable', methods=['POST'])
@require_auth
def disable_2fa():
    """
    Disable 2FA for authenticated citizen
    
    Requires current TOTP code for security
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid request body'}), 400
    
    code = data.get('code')
    
    if not code:
        return jsonify({'error': 'TOTP code required'}), 400
    
    citizen = Citizen.query.get(request.citizen_id)
    
    if not citizen:
        return jsonify({'error': 'Citizen not found'}), 404
    
    if not citizen.totp_enabled:
        return jsonify({'error': '2FA not enabled'}), 400
    
    # Verify TOTP code before disabling
    is_valid_2fa, _ = auth_service.validate_2fa_code(citizen, code, request.remote_addr)
    
    if not is_valid_2fa:
        return jsonify({'error': 'Invalid TOTP code'}), 401
    
    if auth_service.disable_2fa(citizen):
        return jsonify({
            'message': '2FA successfully disabled',
            'totp_enabled': False
        }), 200
    else:
        return jsonify({'error': 'Failed to disable 2FA'}), 500


@oauth_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400


@oauth_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401


@oauth_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded'}), 429


@oauth_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500
