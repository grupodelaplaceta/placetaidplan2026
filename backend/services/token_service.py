"""
Token service for PlacetaID - JWT and authorization code handling
"""

from datetime import datetime, timedelta
from functools import wraps
import jwt
import secrets
from models import db, Session, AuthorizationCode, AuditLog
from config import Config


class TokenService:
    """JWT and authorization code management"""
    
    def __init__(self):
        self.secret_key = Config.JWT_SECRET_KEY
        self.algorithm = 'HS256'
        self.access_token_expiry = Config.JWT_EXPIRY_HOURS
        self.refresh_token_expiry = Config.JWT_REFRESH_EXPIRY_DAYS
        self.auth_code_expiry_minutes = 10
    
    def generate_authorization_code(self, citizen_id: str, client_id: str, 
                                   redirect_uri: str, state: str, scope: str = 'openid profile') -> str:
        """
        Generate OAuth2 authorization code
        
        Returns:
            Authorization code string
        """
        code = secrets.token_urlsafe(32)
        
        auth_code = AuthorizationCode(
            code=code,
            citizen_id=citizen_id,
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
            scope=scope,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=self.auth_code_expiry_minutes)
        )
        
        db.session.add(auth_code)
        db.session.commit()
        
        AuditLog.log_event(
            'oauth',
            'authorization_code_generated',
            '127.0.0.1',
            citizen_id=citizen_id,
            status='success',
            metadata={'client_id': client_id}
        )
        
        return code
    
    def validate_authorization_code(self, code: str, client_id: str, 
                                   redirect_uri: str) -> tuple[bool, str]:
        """
        Validate authorization code
        
        Returns:
            (is_valid, citizen_id or error_message)
        """
        auth_code = AuthorizationCode.query.filter_by(code=code).first()
        
        if not auth_code:
            return False, 'Invalid authorization code'
        
        # Check if expired
        if auth_code.is_expired():
            return False, 'Authorization code expired'
        
        # Check if already used
        if auth_code.is_used:
            # Log potential attack
            AuditLog.log_event(
                'oauth',
                'authorization_code_reuse_attempt',
                '127.0.0.1',
                citizen_id=auth_code.citizen_id,
                status='blocked'
            )
            return False, 'Authorization code already used'
        
        # Verify client_id and redirect_uri match
        if auth_code.client_id != client_id or auth_code.redirect_uri != redirect_uri:
            return False, 'Client ID or redirect URI mismatch'
        
        # Mark as used
        auth_code.is_used = True
        auth_code.used_at = datetime.utcnow()
        db.session.commit()
        
        return True, auth_code.citizen_id
    
    def generate_access_token(self, citizen_id: str, ip_address: str, 
                            device_fingerprint: str = None) -> tuple[str, str]:
        """
        Generate JWT access token and refresh token
        
        Returns:
            (access_token, refresh_token)
        """
        now = datetime.utcnow()
        access_expiry = now + timedelta(hours=self.access_token_expiry)
        refresh_expiry = now + timedelta(days=self.refresh_token_expiry)
        
        # Generate refresh token
        refresh_token = secrets.token_urlsafe(32)
        
        # Create access token payload
        access_payload = {
            'citizen_id': citizen_id,
            'token_type': 'access',
            'iat': now,
            'exp': access_expiry,
            'iss': 'placetaid'
        }
        
        # Sign access token
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        
        # Store session in database
        session = Session(
            citizen_id=citizen_id,
            token=access_token,
            token_type='access',
            refresh_token=refresh_token,
            refresh_token_expires_at=refresh_expiry,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            expires_at=access_expiry
        )
        
        db.session.add(session)
        db.session.commit()
        
        AuditLog.log_event(
            'token',
            'access_token_generated',
            ip_address,
            citizen_id=citizen_id,
            status='success'
        )
        
        return access_token, refresh_token
    
    def refresh_access_token(self, refresh_token: str, ip_address: str) -> tuple[bool, str, str]:
        """
        Refresh access token using refresh token
        
        Returns:
            (is_valid, new_access_token, error_message)
        """
        # Find session with this refresh token
        session = Session.query.filter_by(refresh_token=refresh_token).first()
        
        if not session:
            AuditLog.log_event(
                'token',
                'refresh_token_invalid',
                ip_address,
                status='failed'
            )
            return False, '', 'Invalid refresh token'
        
        # Check if refresh token is expired
        if session.refresh_token_expires_at and datetime.utcnow() > session.refresh_token_expires_at:
            AuditLog.log_event(
                'token',
                'refresh_token_expired',
                ip_address,
                citizen_id=session.citizen_id,
                status='failed'
            )
            return False, '', 'Refresh token expired'
        
        # Check if session is revoked
        if session.is_revoked:
            AuditLog.log_event(
                'token',
                'refresh_token_revoked',
                ip_address,
                citizen_id=session.citizen_id,
                status='blocked'
            )
            return False, '', 'Session has been revoked'
        
        # Limit refresh rate to prevent abuse
        if not self._check_refresh_rate_limit(session.citizen_id):
            AuditLog.log_event(
                'token',
                'refresh_rate_limit_exceeded',
                ip_address,
                citizen_id=session.citizen_id,
                status='blocked'
            )
            return False, '', 'Too many refresh attempts'
        
        # Generate new tokens
        new_access_token, new_refresh_token = self.generate_access_token(
            session.citizen_id, ip_address, session.device_fingerprint
        )
        
        # Invalidate old refresh token (rotate it)
        session.refresh_token = None
        session.is_revoked = True
        db.session.commit()
        
        return True, new_access_token, ''
    
    def validate_access_token(self, token: str) -> tuple[bool, dict]:
        """
        Validate JWT access token
        
        Returns:
            (is_valid, token_payload or error_dict)
        """
        try:
            # Decode and verify token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get('token_type') != 'access':
                return False, {'error': 'Invalid token type'}
            
            # Check if session exists and is not revoked
            session = Session.query.filter_by(token=token).first()
            if not session or session.is_revoked:
                return False, {'error': 'Session not found or revoked'}
            
            # Update last activity
            session.update_activity()
            
            return True, payload
            
        except jwt.ExpiredSignatureError:
            return False, {'error': 'Token expired'}
        except jwt.InvalidTokenError as e:
            return False, {'error': f'Invalid token: {str(e)}'}
    
    def revoke_token(self, token: str, ip_address: str) -> bool:
        """
        Revoke a token by marking its session as revoked
        
        Returns:
            True on success
        """
        session = Session.query.filter_by(token=token).first()
        
        if session:
            session.is_revoked = True
            db.session.commit()
            
            AuditLog.log_event(
                'token',
                'token_revoked',
                ip_address,
                citizen_id=session.citizen_id,
                status='success'
            )
            return True
        
        return False
    
    def revoke_citizen_sessions(self, citizen_id: str, ip_address: str, 
                               except_token: str = None) -> int:
        """
        Revoke all sessions for a citizen
        
        Returns:
            Number of sessions revoked
        """
        sessions = Session.query.filter_by(citizen_id=citizen_id, is_revoked=False).all()
        
        count = 0
        for session in sessions:
            if except_token and session.token == except_token:
                continue
            
            session.is_revoked = True
            count += 1
        
        db.session.commit()
        
        if count > 0:
            AuditLog.log_event(
                'token',
                'citizen_sessions_revoked',
                ip_address,
                citizen_id=citizen_id,
                status='success',
                metadata={'count': count}
            )
        
        return count
    
    def _check_refresh_rate_limit(self, citizen_id: str, max_refreshes_per_day: int = 10) -> bool:
        """
        Check refresh rate limit
        
        Returns:
            True if within limit, False otherwise
        """
        window_start = datetime.utcnow() - timedelta(hours=24)
        
        refresh_count = Session.query.filter(
            Session.citizen_id == citizen_id,
            Session.created_at >= window_start
        ).count()
        
        return refresh_count < max_refreshes_per_day
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired and revoked sessions
        
        Returns:
            Number of sessions deleted
        """
        expired = Session.query.filter(
            Session.expires_at < datetime.utcnow()
        ).delete()
        
        revoked_old = Session.query.filter(
            Session.is_revoked,
            Session.updated_at < datetime.utcnow() - timedelta(days=7)
        ).delete()
        
        db.session.commit()
        
        return expired + revoked_old
    
    def cleanup_expired_auth_codes(self) -> int:
        """
        Clean up expired authorization codes
        
        Returns:
            Number of codes deleted
        """
        deleted = AuthorizationCode.query.filter(
            AuthorizationCode.expires_at < datetime.utcnow()
        ).delete()
        
        db.session.commit()
        
        return deleted


# Create service instance
token_service = TokenService()


def require_auth(f):
    """
    Decorator to require valid JWT token
    
    Usage:
        @require_auth
        def my_route():
            citizen_id = request.auth['citizen_id']
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Invalid authorization header'}), 401
        
        if not token:
            return jsonify({'error': 'Authorization token required'}), 401
        
        is_valid, payload = token_service.validate_access_token(token)
        
        if not is_valid:
            return jsonify(payload), 401
        
        request.auth = payload
        request.citizen_id = payload['citizen_id']
        
        return f(*args, **kwargs)
    
    return decorated_function
