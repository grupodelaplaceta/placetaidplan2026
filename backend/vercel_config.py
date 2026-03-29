"""
Vercel Serverless Configuration for PlacetaID
Optimized for edge functions and serverless environments
"""

import os
from datetime import timedelta


class VercelConfig:
    """Base configuration for Vercel serverless deployment"""
    
    # Flask
    PROPAGATE_EXCEPTIONS = True
    PRESERVE_CONTEXT_ON_EXCEPTION = True
    
    # Database
    # For Vercel, use serverless databases like:
    # - Supabase (PostgreSQL) - recommended
    # - PlanetScale (MySQL) - good alternative
    # - MongoDB Atlas - NoSQL option
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 1,
        "max_overflow": 0,
    }
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_EXPIRY_HOURS = 24
    JWT_REFRESH_EXPIRY_DAYS = 30
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Encryption
    MASTER_ENCRYPTION_KEY = os.getenv('MASTER_ENCRYPTION_KEY', '')
    DIP_HASH_SALT = os.getenv('DIP_HASH_SALT', '')
    
    # Redis (use Upstash for Vercel)
    REDIS_URL = os.getenv('REDIS_URL', '')
    
    # CORS
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'https://vercel.app').split(',')
    
    # Vercel-specific
    DEBUG = False
    TESTING = False
    PREFERRED_URL_SCHEME = 'https'


class VercelProductionConfig(VercelConfig):
    """Production config for Vercel deployment"""
    
    # Database URL for serverless
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', '')
    
    # Security headers for production
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'nonce-{nonce}'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Vercel limits - optimize for serverless
    FUNCTION_TIMEOUT = 60  # seconds
    FUNCTION_MEMORY = 1024  # MB
