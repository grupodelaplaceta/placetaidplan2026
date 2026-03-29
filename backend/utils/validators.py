"""
Validation utilities for PlacetaID
"""

import re
import pyotp
from datetime import datetime


class Validators:
    """Input validation utilities"""
    
    @staticmethod
    def validate_dip(dip: str) -> bool:
        """Validate DIP format and checksum"""
        if not dip:
            return False
        
        # Remove hyphens
        dip_clean = dip.replace('-', '').upper()
        
        # Check length and format
        if len(dip_clean) != 9:
            return False
        
        if not (dip_clean[:8].isdigit() and dip_clean[8].isalpha()):
            return False
        
        # Validate checksum
        LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
        number = int(dip_clean[:8])
        expected_letter = LETTERS[number % 23]
        
        return dip_clean[8] == expected_letter
    
    @staticmethod
    def validate_2fa_code(code: str) -> bool:
        """Validate 2FA code format"""
        if not code:
            return False
        
        # Remove spaces
        code_clean = code.replace(' ', '')
        
        # Must be 6 digits
        return len(code_clean) == 6 and code_clean.isdigit()
    
    @staticmethod
    def validate_totp(secret: str, code: str) -> bool:
        """Validate TOTP code against secret"""
        try:
            code_clean = code.replace(' ', '')
            
            if not Validators.validate_2fa_code(code):
                return False
            
            totp = pyotp.TOTP(secret)
            
            # Allow for 30 second window (current and previous)
            return totp.verify(code_clean, valid_window=1)
        except Exception:
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        # Spanish phone format
        pattern = r'^(\+34|0034|34)?[6789]\d{8}$'
        return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/.*)?$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IPv4 or IPv6 address"""
        # IPv4
        ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        # IPv6 (simplified)
        ipv6_pattern = r'^(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$'
        
        return bool(re.match(ipv4_pattern, ip)) or bool(re.match(ipv6_pattern, ip))
    
    @staticmethod
    def sanitize_input(value: str, max_length: int = 255) -> str:
        """Sanitize user input"""
        if not value:
            return ""
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Limit length
        value = value[:max_length]
        
        # Trim whitespace
        return value.strip()
    
    @staticmethod
    def format_dip(dip: str) -> str:
        """Format DIP to standard format"""
        dip_clean = dip.replace('-', '').upper()
        
        if len(dip_clean) == 9:
            return f"{dip_clean[:4]}-{dip_clean[4:8]}-{dip_clean[8]}"
        
        return dip_clean


# Create instance
validators = Validators()
