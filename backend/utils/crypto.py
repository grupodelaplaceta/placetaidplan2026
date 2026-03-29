"""
Cryptographic utilities for PlacetaID
DIP encryption and hashing
"""

import hashlib
import os
import base64
from cryptography.fernet import Fernet


class CryptoManager:
    """Manage encryption and hashing operations"""
    
    def __init__(self):
        self.master_key = os.getenv('MASTER_ENCRYPTION_KEY', '')
        self.dip_salt = os.getenv('DIP_HASH_SALT', 'default-salt-change-me')
    
    def encrypt_dip(self, dip: str) -> str:
        """Encrypt DIP with Fernet (symmetric encryption)"""
        try:
            if not self.master_key:
                # For development only
                return base64.b64encode(dip.encode()).decode()
            
            f = Fernet(self.master_key.encode())
            encrypted = f.encrypt(dip.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            raise ValueError(f"Encryption error: {e}")
    
    def decrypt_dip(self, encrypted_dip: str) -> str:
        """Decrypt DIP"""
        try:
            if not self.master_key:
                # For development only
                return base64.b64decode(encrypted_dip.encode()).decode()
            
            f = Fernet(self.master_key.encode())
            decrypted = f.decrypt(base64.b64decode(encrypted_dip.encode()))
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Decryption error: {e}")
    
    def hash_dip(self, dip: str) -> str:
        """Generate SHA256 hash for DIP validation"""
        salted = f"{self.dip_salt}{dip}"
        return hashlib.sha256(salted.encode()).hexdigest()
    
    def validate_dip_checksum(self, dip: str) -> bool:
        """Validate Spanish DIP checksum algorithm"""
        dip = dip.replace('-', '')
        
        if len(dip) != 9:
            return False
        
        try:
            numbers = dip[:8]
            letter = dip[8].upper()
            
            LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
            expected_letter = LETTERS[int(numbers) % 23]
            
            return letter == expected_letter
        except (ValueError, IndexError):
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt using bcrypt-like approach"""
        salt = hashlib.sha256(os.urandom(32)).hexdigest()
        hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"{salt}${hashed}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify hashed password"""
        try:
            salt, stored_hash = hashed.split('$')
            computed_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
            
            # Timing-safe comparison
            return self._constant_time_compare(computed_hash, stored_hash)
        except Exception:
            return False
    
    @staticmethod
    def _constant_time_compare(a: str, b: str) -> bool:
        """Timing-safe string comparison"""
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate random token"""
        return base64.urlsafe_b64encode(os.urandom(length)).decode().rstrip('=')


# Create singleton instance
crypto_manager = CryptoManager()
