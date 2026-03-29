"""
Authentication service for PlacetaID
"""

from datetime import datetime, timedelta
from models import db, Citizen, LoginAttempt, AccountLockout, AuditLog
from utils.crypto import CryptoManager
from utils.validators import validators
import pyotp


class AuthService:
    """Authentication business logic"""
    
    # Rate limiting constants
    MAX_ATTEMPTS_PER_24H = 3
    LOCKOUT_DURATION_HOURS = 24
    
    def __init__(self):
        self.crypto = CryptoManager()
    
    def validate_citizen_dip(self, dip: str, ip_address: str) -> tuple[bool, str, Citizen]:
        """
        Validate citizen DIP and check for lockouts/rate limiting
        
        Returns:
            (is_valid, error_message, citizen_object)
        """
        # Validate DIP format
        if not validators.validate_dip(dip):
            self._log_attempt(None, 'dip', 'failed_dip', ip_address, 'Invalid DIP format')
            return False, 'Invalid DIP format', None
        
        try:
            # Hash the DIP for lookup
            dip_hash = self.crypto.hash_dip(dip)
            
            # Look up citizen
            citizen = Citizen.query.filter_by(dip_hash=dip_hash).first()
            
            if not citizen:
                # Log attempt for this DIP even if citizen doesn't exist
                # This prevents enumeration attacks by being consistent
                self._log_attempt(None, 'dip', 'failed_dip', ip_address, 'Citizen not found')
                return False, 'Invalid DIP or citizen not registered', None
            
            # Check if account is locked
            active_lockout = citizen.get_active_lockout()
            if active_lockout:
                remaining_time = active_lockout.get_remaining_time()
                self._log_attempt(citizen.id, 'dip', 'failed_dip', ip_address, 'Account locked')
                return False, f'Account locked for {int(remaining_time.total_seconds() // 60)} minutes', citizen
            
            # Check account status
            if citizen.status != 'active':
                self._log_attempt(citizen.id, 'dip', 'failed_dip', ip_address, f'Account {citizen.status}')
                return False, f'Account is {citizen.status}', citizen
            
            # Check rate limiting - 3 attempts per 24 hours
            failed_attempts = self._get_failed_attempts_in_window(citizen.id)
            
            if failed_attempts >= self.MAX_ATTEMPTS_PER_24H:
                # Create lockout
                self._create_lockout(citizen, 'failed_attempts')
                self._log_attempt(citizen.id, 'dip', 'rate_limited', ip_address, 'Rate limit exceeded')
                return False, f'Too many failed attempts. Account locked for {self.LOCKOUT_DURATION_HOURS} hours', citizen
            
            # DIP validation successful
            self._log_attempt(citizen.id, 'dip', 'success', ip_address)
            return True, '', citizen
            
        except Exception as e:
            AuditLog.log_event(
                'authentication',
                'dip_validation_error',
                ip_address,
                status='failed',
                error_message=str(e)
            )
            return False, 'An error occurred during validation', None
    
    def validate_2fa_code(self, citizen: Citizen, code: str, ip_address: str) -> tuple[bool, str]:
        """
        Validate 2FA TOTP code
        
        Returns:
            (is_valid, error_message)
        """
        # Validate code format
        if not validators.validate_2fa_code(code):
            self._log_attempt(citizen.id, 'totp', 'failed_totp', ip_address, 'Invalid code format')
            return False, 'Invalid code format'
        
        # Check if 2FA is enabled
        if not citizen.totp_enabled:
            # 2FA not enabled - this shouldn't happen but handle gracefully
            self._log_attempt(citizen.id, 'totp', 'failed_totp', ip_address, '2FA not enabled')
            return False, '2FA not enabled for this account'
        
        try:
            # Validate TOTP
            if not citizen.totp_secret:
                self._log_attempt(citizen.id, 'totp', 'failed_totp', ip_address, 'No TOTP secret')
                return False, 'TOTP secret not configured'
            
            is_valid = validators.validate_totp(citizen.totp_secret, code)
            
            if is_valid:
                self._log_attempt(citizen.id, 'totp', 'success', ip_address)
                return True, ''
            else:
                self._log_attempt(citizen.id, 'totp', 'failed_totp', ip_address, 'Invalid TOTP code')
                return False, 'Invalid verification code'
                
        except Exception as e:
            AuditLog.log_event(
                'authentication',
                'totp_validation_error',
                ip_address,
                citizen_id=citizen.id,
                status='failed',
                error_message=str(e)
            )
            return False, 'An error occurred during verification'
    
    def create_citizen(self, dip: str) -> Citizen:
        """
        Create a new citizen account
        
        Returns:
            Citizen object
        """
        if not validators.validate_dip(dip):
            raise ValueError("Invalid DIP format")
        
        # Check if citizen already exists
        dip_hash = self.crypto.hash_dip(dip)
        existing = Citizen.query.filter_by(dip_hash=dip_hash).first()
        
        if existing:
            raise ValueError("Citizen already exists")
        
        # Encrypt DIP
        dip_encrypted = self.crypto.encrypt_dip(dip)
        
        # Create citizen
        citizen = Citizen(
            dip_encrypted=dip_encrypted,
            dip_hash=dip_hash,
            status='active'
        )
        
        db.session.add(citizen)
        db.session.commit()
        
        AuditLog.log_event(
            'account',
            'citizen_created',
            '127.0.0.1',
            citizen_id=citizen.id,
            status='success'
        )
        
        return citizen
    
    def enable_2fa(self, citizen: Citizen) -> dict:
        """
        Enable 2FA for a citizen
        
        Returns:
            {
                'secret': base32_encoded_secret,
                'qr_code': qr_code_data_uri,
                'backup_codes': [list of backup codes]
            }
        """
        # Generate TOTP secret
        secret = pyotp.random_base32()
        
        # Generate backup codes (10 codes, 8 characters each)
        backup_codes = [self.crypto.generate_token(length=8) for _ in range(10)]
        
        # Hash backup codes for storage
        backup_codes_hashed = [self.crypto.hash_password(code) for code in backup_codes]
        
        # Update citizen
        citizen.totp_secret = secret
        citizen.backup_codes = backup_codes_hashed
        db.session.commit()
        
        # Generate QR code URI
        totp = pyotp.TOTP(secret)
        qr_uri = totp.provisioning_uri(
            name=f'PlacetaID:{citizen.id[:8]}',
            issuer_name='PlacetaID'
        )
        
        AuditLog.log_event(
            '2fa',
            '2fa_enabled',
            '127.0.0.1',
            citizen_id=citizen.id,
            status='success'
        )
        
        return {
            'secret': secret,
            'qr_uri': qr_uri,
            'backup_codes': backup_codes
        }
    
    def confirm_2fa(self, citizen: Citizen, code: str) -> bool:
        """
        Confirm 2FA setup by verifying first code
        
        Returns:
            True if valid, False otherwise
        """
        if not citizen.totp_secret:
            return False
        
        is_valid = validators.validate_totp(citizen.totp_secret, code)
        
        if is_valid:
            citizen.totp_enabled = True
            db.session.commit()
            
            AuditLog.log_event(
                '2fa',
                '2fa_confirmed',
                '127.0.0.1',
                citizen_id=citizen.id,
                status='success'
            )
            return True
        
        return False
    
    def disable_2fa(self, citizen: Citizen) -> bool:
        """
        Disable 2FA for a citizen
        
        Returns:
            True on success
        """
        citizen.totp_secret = None
        citizen.totp_enabled = False
        citizen.backup_codes = None
        db.session.commit()
        
        AuditLog.log_event(
            '2fa',
            '2fa_disabled',
            '127.0.0.1',
            citizen_id=citizen.id,
            status='success'
        )
        
        return True
    
    def unlock_account(self, citizen: Citizen, reason: str = 'manual_release') -> bool:
        """
        Manually unlock a locked account
        
        Returns:
            True on success
        """
        lockout = citizen.get_active_lockout()
        
        if lockout:
            lockout.status = 'released'
            lockout.released_at = datetime.utcnow()
            lockout.release_reason = reason
            db.session.commit()
            
            AuditLog.log_event(
                'account',
                'account_unlocked',
                '127.0.0.1',
                citizen_id=citizen.id,
                status='success',
                metadata={'reason': reason}
            )
            
            return True
        
        return False
    
    # Private helper methods
    
    def _log_attempt(self, citizen_id: str, attempt_type: str, status: str, 
                    ip_address: str, error_reason: str = None):
        """Log login attempt"""
        attempt = LoginAttempt(
            citizen_id=citizen_id,
            attempt_type=attempt_type,
            status=status,
            ip_address=ip_address,
            error_reason=error_reason
        )
        db.session.add(attempt)
        db.session.commit()
    
    def _get_failed_attempts_in_window(self, citizen_id: str) -> int:
        """Get number of failed attempts in last 24 hours"""
        window_start = datetime.utcnow() - timedelta(hours=24)
        
        failed = LoginAttempt.query.filter(
            LoginAttempt.citizen_id == citizen_id,
            LoginAttempt.attempt_type == 'dip',
            LoginAttempt.status == 'failed_dip',
            LoginAttempt.created_at >= window_start
        ).count()
        
        return failed
    
    def _create_lockout(self, citizen: Citizen, reason: str):
        """Create account lockout"""
        # Check if there's already an active lockout
        existing_lockout = citizen.get_active_lockout()
        
        if existing_lockout:
            # Don't create duplicate lockout
            return
        
        lockout = AccountLockout(
            citizen_id=citizen.id,
            reason=reason,
            locked_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=self.LOCKOUT_DURATION_HOURS)
        )
        
        citizen.status = 'locked'
        db.session.add(lockout)
        db.session.commit()


# Create service instance
auth_service = AuthService()
