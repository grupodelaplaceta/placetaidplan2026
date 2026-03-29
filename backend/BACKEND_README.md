# PlacetaID Backend - Setup and Documentation

## Overview

PlacetaID backend is a centralized authentication gateway built with Flask that provides secure OAuth2-compatible authentication with DIP (Spanish ID) and 2FA validation.

## Project Structure

```
backend/
├── app.py                    # Main Flask application factory
├── config.py                # Configuration for dev/prod/test
├── models.py                # SQLAlchemy ORM models
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── wsgi.py                  # WSGI entry point for production
├── utils/
│   ├── __init__.py
│   ├── crypto.py           # Encryption and hashing utilities
│   └── validators.py       # Input validation utilities
├── services/
│   ├── __init__.py
│   ├── auth_service.py     # Authentication business logic
│   ├── token_service.py    # JWT token management
│   └── rate_limiter.py     # Rate limiting service
├── routes/
│   ├── __init__.py
│   └── oauth.py            # OAuth2 endpoints
├── templates/
│   └── login.html          # Login form (self-contained with CSS/JS)
└── logs/                   # Application logs
```

## Quick Start - Development

### 1. Prerequisites

- Python 3.9+
- MySQL 8.0+ (or SQLite for dev)
- Redis 6.0+ (optional, required for production rate limiting)
- pip or poetry

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Environment Setup

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Development database (SQLite)
DATABASE_URL=sqlite:///placetaid_dev.db

# Generate a strong JWT secret
JWT_SECRET_KEY=your-32-character-minimum-secret-key-here

# For production: generate via python -c "import secrets; print(secrets.token_hex(32))"
MASTER_ENCRYPTION_KEY=your-32-byte-base64-encoded-key
DIP_HASH_SALT=your-random-salt-here

# Flask settings
FLASK_ENV=development
FLASK_DEBUG=True

# Redis (optional for development)
REDIS_URL=redis://localhost:6379/0
```

### 4. Initialize Database

```bash
python
# Or manual initialization
flask db init
flask db migrate
flask db upgrade
```

### 5. Run Development Server

```bash
python app.py
```

Server runs at `http://localhost:5000`

## API Endpoints

### OAuth2 Flow

#### POST `/oauth/authorize`
Initiate login with DIP validation

```json
{
  "dip": "12345678X",
  "code": "123456"  // TOTP code (optional if 2FA enabled)
}
```

Response:
```json
{
  "success": true,
  "step": "totp",  // or "authorize" or "dip"
  "citizen_id": "uuid"
}
```

#### POST `/oauth/token`
Exchange authorization code for access token

```json
{
  "grant_type": "authorization_code",
  "code": "code_from_authorize",
  "client_id": "client_id",
  "redirect_uri": "https://client.example.com/callback",
  "client_secret": "client_secret"
}
```

#### GET `/oauth/profile`
Get authenticated user profile (requires Authorization header)

```
Authorization: Bearer <access_token>
```

### 2FA Management

#### POST `/oauth/2fa/enable`
Enable TOTP 2FA for user

Response:
```json
{
  "secret": "JBSWY3DPEBLW64TMMQ======",
  "qr_uri": "otpauth://totp/PlacetaID:uuid...",
  "backup_codes": ["CODE1", "CODE2", ...]
}
```

#### POST `/oauth/2fa/confirm`
Confirm 2FA setup with TOTP code

```json
{
  "code": "123456"
}
```

#### POST `/oauth/2fa/disable`
Disable 2FA (requires current TOTP code)

```json
{
  "code": "123456"
}
```

#### POST `/oauth/logout`
Revoke current session token

## Security Features

### DIP Protection
- **Encryption**: AES-256-GCM (Fernet) encryption at rest
- **Hashing**: SHA-256 with salt for lookups
- **Never transmitted**: DIP stays in gateway, never sent to clients

### Rate Limiting
- **IP-based**: 20 requests per minute
- **DIP-based**: 3 attempts per 24 hours
- **OAuth client**: 5 requests per minute
- **Token refresh**: 10 refreshes per 24 hours

### Account Lockout
- **Automatic**: After 3 failed DIP attempts
- **Duration**: 24 hours per lockout
- **Manual release**: Admin unlock available

### JWT Security
- **Signing**: RS256 (RSA) algorithm
- **Expiration**: 24 hours for access tokens
- **Refresh tokens**: 30 days rotation
- **Session tracking**: All tokens stored in database

### Input Validation
- **DIP**: Spanish algorithm validation (modulo 23 checksum)
- **TOTP**: 6-digit numeric codes with time window
- **Email/Phone**: Format validation
- **URLs**: HTTPS-only for OAuth redirects

## Database Schema

### Citizen
- Encrypted DIP storage
- Account status (active, locked, disabled)
- 2FA configuration
- Login metadata

### LoginAttempt
- Track all authentication attempts
- IP address and device info
- Success/failure reason
- Rate limiting data

### AccountLockout
- Track locked accounts
- Lockout duration and expiration
- Reason for lockout
- Manual release tracking

### Session
- JWT token storage
- Refresh token management
- Device fingerprinting
- Activity tracking

### AuthorizationCode
- OAuth2 authorization codes
- One-time-use validation
- State token for CSRF protection
- Scope tracking

### AuditLog
- Security event logging
- All authentication actions
- Error tracking
- Compliance audit trail

## Development Tools

### Database Migrations

```bash
# Create new migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Testing

```bash
python -m pytest tests/
python -m pytest tests/ -v
python -m pytest tests/test_auth.py::test_dip_validation
```

### Debugging

Enable debug mode in `.env`:
```env
FLASK_DEBUG=True
```

## Production Deployment

### 1. Install Gunicorn

```bash
pip install gunicorn
```

### 2. Create `.env.production`

```env
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://user:pass@db.example.com:3306/placetaid
JWT_SECRET_KEY=your-very-long-random-key-min-32-chars
MASTER_ENCRYPTION_KEY=base64-encoded-32-byte-key
REDIS_URL=redis://redis.example.com:6379/0
ALLOWED_ORIGINS=https://id.laplaceta.org,https://app.laplaceta.org
```

### 3. Run with Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### 4. Requirements for Production
- SSL certificate (Let's Encrypt recommended)
- Nginx reverse proxy
- MySQL database
- Redis cache
- Monitoring (Prometheus + Grafana recommended)
- Log aggregation (ELK or CloudWatch)

## Configuration

### Environment Variables

| Variable | Required | Default | Note |
|----------|----------|---------|------|
| FLASK_ENV | No | development | development, testing, production |
| DATABASE_URL | Yes | sqlite | MySQL recommended for prod |
| JWT_SECRET_KEY | Yes | None | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| MASTER_ENCRYPTION_KEY | Yes | None | 32-byte base64 encoded key for DIP encryption |
| DIP_HASH_SALT | Yes | None | Random salt for DIP hashing |
| REDIS_URL | No | redis://localhost:6379 | Required for production rate limiting |
| ALLOWED_ORIGINS | No | http://localhost:3000 | Comma-separated list of allowed origins |

## Troubleshooting

### Database Connection Error
- Check `DATABASE_URL` environment variable
- Verify database user permissions
- Ensure database exists: `CREATE DATABASE placetaid_db;`

### Redis Connection Error
- Start Redis: `redis-server`
- Check `REDIS_URL` environment variable
- For development, rate limiting falls back to in-memory storage

### Import Errors
- Ensure you're in the `backend` directory
- Install dependencies: `pip install -r requirements.txt`
- Add backend to PYTHONPATH: `export PYTHONPATH=$PYTHONPATH:$(pwd)`

### CORS Errors
- Check `ALLOWED_ORIGINS` environment variable
- Ensure client URL is in the list
- Development: Use `http://localhost:3000`

## Monitoring and Logging

### Log Files
- `logs/errors.log` - Application errors
- Console output - Development mode

### Health Check
```bash
curl http://localhost:5000/health
```

## Security Checklist

- [ ] Change all default secrets in `.env.production`
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure CORS origins for specific services only
- [ ] Set up database user with minimal permissions
- [ ] Enable audit logging
- [ ] Configure monitoring and alerting
- [ ] Regular security updates for dependencies
- [ ] Database backups (daily or hourly)
- [ ] Redis persistence enabled
- [ ] Rate limiting properly configured

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [OAuth2 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
