"""
SQLAlchemy models for PlacetaID database
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, Index
from sqlalchemy.dialects.mysql import LONGBLOB
import uuid

db = SQLAlchemy()


class Citizen(db.Model):
    """Citizen/user account"""
    __tablename__ = 'citizens'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dip_encrypted = db.Column(LONGBLOB, nullable=False, unique=True, index=True)
    dip_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    age_tier = db.Column(db.String(10), nullable=False, default='unknown')  # 'adult', 'minor', 'unknown'
    
    # 2FA Settings
    totp_secret = db.Column(db.String(32), nullable=True)  # Base32 encoded secret
    totp_enabled = db.Column(db.Boolean, nullable=False, default=False)
    backup_codes = db.Column(db.JSON, nullable=True)  # List of backup codes
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active', 'locked', 'disabled'
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    login_country = db.Column(db.String(2), nullable=True)  # ISO 3166-1 alpha-2
    login_device = db.Column(db.String(255), nullable=True)
    
    # Relationships
    login_attempts = db.relationship('LoginAttempt', backref='citizen', lazy=True, cascade='all, delete-orphan')
    lockouts = db.relationship('AccountLockout', backref='citizen', lazy=True, cascade='all, delete-orphan')
    sessions = db.relationship('Session', backref='citizen', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Citizen {self.id[:8]}...>"
    
    def is_locked(self) -> bool:
        """Check if citizen account is locked"""
        return self.status == 'locked'
    
    def get_active_lockout(self) -> 'AccountLockout':
        """Get active lockout if any"""
        lockout = AccountLockout.query.filter_by(
            citizen_id=self.id,
            status='active'
        ).first()
        
        if lockout and lockout.is_expired():
            lockout.status = 'expired'
            db.session.commit()
            return None
        
        return lockout
    
    def update_last_login(self, country: str = None, device: str = None):
        """Update last login timestamp and metadata"""
        self.last_login_at = datetime.utcnow()
        if country:
            self.login_country = country
        if device:
            self.login_device = device
        db.session.commit()


class LoginAttempt(db.Model):
    """Track login attempts for rate limiting and audit"""
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    citizen_id = db.Column(db.String(36), db.ForeignKey('citizens.id'), nullable=False)
    
    attempt_type = db.Column(db.String(20), nullable=False)  # 'dip', 'totp', 'success'
    status = db.Column(db.String(20), nullable=False)  # 'success', 'failed_dip', 'failed_totp', 'rate_limited'
    
    ip_address = db.Column(db.String(45), nullable=False, index=True)  # IPv4 or IPv6
    user_agent = db.Column(db.Text, nullable=True)
    device_fingerprint = db.Column(db.String(64), nullable=True)
    
    error_reason = db.Column(db.String(255), nullable=True)  # 'invalid_dip', 'invalid_totp', 'account_locked', etc.
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_citizen_created', 'citizen_id', 'created_at'),
        Index('idx_ip_created', 'ip_address', 'created_at'),
    )
    
    def __repr__(self):
        return f"<LoginAttempt {self.id[:8]}... status={self.status}>"


class AccountLockout(db.Model):
    """Track account lockouts"""
    __tablename__ = 'account_lockouts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    citizen_id = db.Column(db.String(36), db.ForeignKey('citizens.id'), nullable=False, unique=True)
    
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active', 'expired', 'released'
    reason = db.Column(db.String(50), nullable=False)  # 'failed_attempts', 'security_hold'
    
    failed_attempts = db.Column(db.Integer, nullable=False, default=0)
    
    locked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)  # 24 hours from locked_at
    released_at = db.Column(db.DateTime, nullable=True)
    
    release_reason = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f"<AccountLockout citizen={self.citizen_id[:8]}...>"
    
    def is_expired(self) -> bool:
        """Check if lockout has expired"""
        return datetime.utcnow() > self.expires_at and self.status == 'active'
    
    def get_remaining_time(self) -> timedelta:
        """Get remaining lockout time"""
        remaining = self.expires_at - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else timedelta(seconds=0)


class Session(db.Model):
    """Active user sessions"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    citizen_id = db.Column(db.String(36), db.ForeignKey('citizens.id'), nullable=False)
    
    token = db.Column(db.String(255), nullable=False, unique=True, index=True)
    token_type = db.Column(db.String(20), nullable=False)  # 'access', 'refresh'
    
    refresh_token = db.Column(db.String(255), nullable=True, unique=True)  # For access tokens
    refresh_token_expires_at = db.Column(db.DateTime, nullable=True)
    
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text, nullable=True)
    device_fingerprint = db.Column(db.String(64), nullable=True)
    
    is_revoked = db.Column(db.Boolean, nullable=False, default=False)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)  # JWT expiration
    
    last_activity_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Session {self.id[:8]}... citizen={self.citizen_id[:8]}...>"
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        return datetime.utcnow() > self.expires_at or self.is_revoked
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
        db.session.commit()


class AuthorizationCode(db.Model):
    """OAuth2 authorization codes"""
    __tablename__ = 'authorization_codes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(64), nullable=False, unique=True, index=True)
    citizen_id = db.Column(db.String(36), db.ForeignKey('citizens.id'), nullable=False)
    
    client_id = db.Column(db.String(255), nullable=False, index=True)  # OAuth client identifier
    redirect_uri = db.Column(db.String(2048), nullable=False)
    
    state = db.Column(db.String(255), nullable=False)  # CSRF token
    scope = db.Column(db.String(255), nullable=False, default='openid profile')
    
    is_used = db.Column(db.Boolean, nullable=False, default=False)
    used_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)  # 10 minutes from creation
    
    def __repr__(self):
        return f"<AuthorizationCode {self.code[:8]}...>"
    
    def is_expired(self) -> bool:
        """Check if authorization code has expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if code can be used"""
        return not self.is_used and not self.is_expired()


class AuditLog(db.Model):
    """Security audit log"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    citizen_id = db.Column(db.String(36), db.ForeignKey('citizens.id'), nullable=True)
    
    event_type = db.Column(db.String(50), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)  # 'login_success', 'login_failed', 'totp_enabled', etc.
    
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(20), nullable=False)  # 'success', 'failed', 'blocked'
    error_message = db.Column(db.Text, nullable=True)
    
    metadata = db.Column(db.JSON, nullable=True)  # Additional context
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_citizen_event_created', 'citizen_id', 'event_type', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLog {self.id[:8]}... action={self.action}>"
    
    @staticmethod
    def log_event(event_type: str, action: str, ip_address: str, status: str = 'success', 
                  citizen_id: str = None, error_message: str = None, metadata: dict = None):
        """Create audit log entry"""
        log = AuditLog(
            event_type=event_type,
            action=action,
            ip_address=ip_address,
            status=status,
            citizen_id=citizen_id,
            error_message=error_message,
            metadata=metadata or {}
        )
        db.session.add(log)
        db.session.commit()
        return log
