# IMPLEMENTACIÓ BACKEND - Flask REST API

## 📋 Estructura de Projecte

```
backend/
├── app.py                    # Aplicació principal
├── requirements.txt          # Dependències Python
├── config.py                # Configuració
├── .env.example              # Variables d'entorn
├── middleware/
│   ├── auth.py               # Validació JWT, CSRF
│   ├── rate_limit.py         # Rate limiting
│   └── logging.py            # Audit logging
├── routes/
│   ├── oauth.py              # /oauth/* endpoints
│   ├── user.py               # /user/* endpoints
│   └── admin.py              # Admin endpoints
├── models/
│   ├── citizen.py            # Model Citizen
│   ├── token.py              # Model Token
│   └── lockout.py            # Model Lockout
├── utils/
│   ├── crypto.py             # Encriptació
│   ├── validators.py         # Validacions
│   └── jwt_handler.py        # JWT generat/validació
└── services/
    ├── auth_service.py       # Lògica d'autenticació
    ├── token_service.py      # Gestió de tokens
    └── notification_service.py # Notificacions (SMS, email)
```

## 🚀 app.py Principal

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from datetime import timedelta
import logging
from dotenv import load_dotenv
import os

# Carregar variables d'entorn
load_dotenv()

# Inicialitzar extensións
db = SQLAlchemy()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_name='development'):
    """Factory pattern per crear app Flask"""
    app = Flask(__name__)
    
    # Configuració
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://user:pass@localhost:3306/placetaid'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['ENV'] = config_name
    
    # CORS
    CORS(app, resources={
        r"/oauth/*": {"origins": ["https://id.laplaceta.org"]},
        r"/user/*": {"origins": ["https://*.laplaceta.org"]}
    })
    
    # Inicialitzar extensions
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    
    # Configurar logging
    logger = logging.getLogger()
    handler = logging.FileHandler('logs/placetaid.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Registrar blueprints
    from routes import oauth_bp, user_bp, admin_bp
    app.register_blueprint(oauth_bp, url_prefix='/oauth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'bad_request', 'message': str(e)}), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'unauthorized', 'message': str(e)}), 401
    
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({'error': 'rate_limit_exceeded', 'message': str(e)}), 429
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f'Server error: {e}')
        return jsonify({'error': 'server_error', 'message': 'Internal error'}), 500
    
    # Health check
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'healthy', 'service': 'PlacetaID Gateway'}), 200
    
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        ssl_context='adhoc'  # HTTPS
    )
```

## 🔐 utils/crypto.py

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import hashlib
import os
import base64

class CryptoManager:
    def __init__(self):
        self.master_key = os.getenv('MASTER_ENCRYPTION_KEY')
        self.dip_salt = os.getenv('DIP_HASH_SALT')
    
    def encrypt_dip(self, dip: str) -> str:
        """Xifra DIP amb AES-256"""
        f = Fernet(self.master_key.encode())
        encrypted = f.encrypt(dip.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_dip(self, encrypted_dip: str) -> str:
        """Desxifra DIP"""
        f = Fernet(self.master_key.encode())
        decrypted = f.decrypt(base64.b64decode(encrypted_dip.encode()))
        return decrypted.decode()
    
    def hash_dip(self, dip: str) -> str:
        """Generador hash SHA256 per validació"""
        salted = f"{self.dip_salt}{dip}"
        return hashlib.sha256(salted.encode()).hexdigest()
    
    def validate_dip_checksum(self, dip: str) -> bool:
        """Validar algoritme de suma de verificació espanyol"""
        dip = dip.replace('-', '')
        if len(dip) != 9:
            return False
        
        # Algoritme DNI España
        numbers = dip[:8]
        letter = dip[8].upper()
        
        LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
        expected_letter = LETTERS[int(numbers) % 23]
        
        return letter == expected_letter

crypto = CryptoManager()
```

## 🛡️ middleware/auth.py

```python
from flask import request, jsonify, current_app
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
import jwt
import os

def require_api_signature(f):
    """Validar que el servidor client firmi les peticions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Per a Backend-to-Backend requests
        signature = request.headers.get('X-API-Signature')
        timestamp = request.headers.get('X-API-Timestamp')
        client_id = request.headers.get('X-API-Client')
        
        if not all([signature, timestamp, client_id]):
            return jsonify({'error': 'missing_signature'}), 401
        
        # Validar timestamp (no més de 5 min)
        import time
        if abs(time.time() - int(timestamp)) > 300:
            return jsonify({'error': 'timestamp_expired'}), 401
        
        # TODO: Validar signadura basada en client_secret
        
        return f(*args, **kwargs)
    return decorated_function

def csrf_protect(f):
    """Validar token CSRF en POST/PUT/DELETE"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            csrf_token = request.values.get('_csrf_token') or \
                        request.headers.get('X-CSRF-Token')
            
            if not csrf_token:
                return jsonify({'error': 'csrf_token_missing'}), 403
            
            # Validar contra sessió
            session_token = request.cookies.get('session')
            # TODO: Validar que csrf_token pertany a session
            
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_account(limit_per_day=3):
    """Rate limit per compte (DIP)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            dip_hash = request.form.get('dip_hash')
            
            # TODO: Comprovar límit en Redis o DB
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

## 📡 routes/oauth.py

```python
from flask import Blueprint, request, render_template, redirect, jsonify, session
from flask_limiter.util import get_remote_address
from services.auth_service import AuthService
from services.token_service import TokenService
from middleware.auth import csrf_protect
from models.citizen import Citizen
from utils.crypto import crypto
from utils.validators import validate_dip, validate_totp
from app import limiter, db
import os
import secrets
from datetime import datetime, timedelta
import logging

oauth_bp = Blueprint('oauth', __name__)
logger = logging.getLogger(__name__)

auth_service = AuthService()
token_service = TokenService()

# =====================================================
# 1. INICIAR FLUX D'AUTENTICACIÓ
# =====================================================

@oauth_bp.route('/authorize', methods=['GET'])
def authorize():
    """Renderitza pantalla de login"""
    
    try:
        # Obté paràmetres
        client_id = request.args.get('client_id')
        redirect_uri = request.args.get('redirect_uri')
        state = request.args.get('state')
        scope = request.args.get('scope', 'profile age-tier')
        
        # Validacions
        if not all([client_id, redirect_uri, state]):
            return jsonify({'error': 'missing_parameters'}), 400
        
        # Verificar client_id i redirect_uri
        client = auth_service.get_oauth_client(client_id)
        if not client:
            logger.warning(f'OAuth authorize: unknown client {client_id}')
            return jsonify({'error': 'invalid_client'}), 400
        
        if redirect_uri not in client.allowed_redirect_uris:
            logger.warning(f'{client_id} tentant redirecció no autoritzada')
            return jsonify({'error': 'invalid_redirect_uri'}), 400
        
        # Guardar paràmetres en sessió
        session['oauth_state'] = state
        session['client_id'] = client_id
        session['redirect_uri'] = redirect_uri
        session['scope'] = scope
        session['csrf_token'] = secrets.token_urlsafe(32)
        
        # Renderitzar formulari de login
        return render_template('login.html', 
            app_name=client.app_name,
            app_icon=client.app_icon_url,
            csrf_token=session['csrf_token']
        )
    
    except Exception as e:
        logger.error(f'OAuth authorize error: {e}')
        return jsonify({'error': 'server_error'}), 500

# =====================================================
# 2. VALIDAR CREDENTIALS (DIP + 2FA)
# =====================================================

@oauth_bp.route('/validate', methods=['POST'])
@csrf_protect
@limiter.limit("3 per 24 hour")
def validate():
    """Validar DIP + 2FA"""
    
    try:
        dip = request.form.get('dip', '').replace('-', '')
        code_2fa = request.form.get('code_2fa', '')
        
        ip_address = get_remote_address()
        user_agent = request.headers.get('User-Agent', '')[:500]
        
        # Validar format
        if not validate_dip(dip):
            logger.warning(f'Invalid DIP format from {ip_address}')
            return jsonify({
                'success': False,
                'error': 'invalid_format',
                'message': 'Format de DIP incorrecte'
            }), 400
        
        # Calcular hash DIP
        dip_hash = crypto.hash_dip(dip)
        
        # Comprovar si compte està blocat
        lockout = auth_service.check_lockout(dip_hash)
        if lockout:
            logger.warning(f'Account locked: {dip_hash} from {ip_address}')
            return jsonify({
                'success': False,
                'error': 'account_locked',
                'message': f'Compte blocat fins {lockout.locked_until}',
                'locked_until': lockout.locked_until.isoformat(),
                'unlock_url': 'https://seu.laplaceta.org/unlock'
            }), 429
        
        # Buscar ciudadà
        citizen = Citizen.query.filter_by(dip_hash=dip_hash).first()
        
        if not citizen:
            # Registrar intent fallat
            auth_service.log_attempt(
                dip_hash=dip_hash,
                ip_address=ip_address,
                user_agent=user_agent,
                attempt_stage='DIP_VALIDATION',
                success=False,
                error_code='INVALID_DIP'
            )
            
            return jsonify({
                'success': False,
                'error': 'invalid_credentials',
                'message': 'Credencials incorrectes'
            }), 400
        
        # Validar 2FA
        if not validate_totp(citizen.id, code_2fa):
            auth_service.log_attempt(
                citizen_id=citizen.id,
                dip_hash=dip_hash,
                ip_address=ip_address,
                user_agent=user_agent,
                attempt_stage='2FA_VALIDATION',
                success=False,
                error_code='INVALID_2FA'
            )
            
            # Comprovar si s'arriba a 3 intents
            failed_count = auth_service.get_failed_attempts(dip_hash, hours=24)
            if failed_count >= 3:
                auth_service.lock_account(
                    dip_hash=dip_hash,
                    citizen_id=citizen.id,
                    reason='MAX_ATTEMPTS'
                )
                
                logger.warning(f'Account locked (3 attempts): {dip_hash}')
                return jsonify({
                    'success': False,
                    'error': 'account_locked',
                    'message': '3 intents incorrectes. Compte blocat 24h'
                }), 429
            
            return jsonify({
                'success': False,
                'error': 'invalid_credentials',
                'message': 'Codi 2FA incorrecte',
                'attempt': failed_count + 1,
                'attempts_remaining': 3 - failed_count - 1
            }), 400
        
        # ✅ CREDENTIALS VÁLIDS
        
        # Generar authorization code (vàlid 5 min)
        auth_code = token_service.generate_authorization_code(
            citizen_id=citizen.id,
            client_id=session['client_id'],
            redirect_uri=session['redirect_uri'],
            scope=session['scope'],
            expires_in=300  # 5 minuts
        )
        
        # Registrar intent exitós
        auth_service.log_attempt(
            citizen_id=citizen.id,
            dip_hash=dip_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            attempt_stage='2FA_VALIDATION',
            success=True
        )
        
        logger.info(f'Successful auth: citizen {citizen.id}')
        
        # Retornar URL de redirecció
        redirect_url = f"{session['redirect_uri']}?code={auth_code}&state={session['oauth_state']}"
        
        return jsonify({
            'success': True,
            'message': 'Autenticació exitosa',
            'redirect_uri': redirect_url,
            'countdown': 3  # segundos para redirigir
        }), 200
    
    except Exception as e:
        logger.error(f'OAuth validate error: {e}')
        return jsonify({'error': 'server_error'}), 500

# =====================================================
# 3. INTERCANVIAR CODE PER JWT
# =====================================================

@oauth_bp.route('/token', methods=['POST'])
@require_api_signature  # Backend-to-Backend
def token():
    """Intercanviar authorization code per JWT"""
    
    try:
        grant_type = request.form.get('grant_type')
        code = request.form.get('code')
        redirect_uri = request.form.get('redirect_uri')
        client_id = request.form.get('client_id') or \
                   request.authorization.username
        client_secret = request.authorization.password if request.authorization else None
        
        # Validar grant type
        if grant_type != 'authorization_code':
            return jsonify({'error': 'unsupported_grant_type'}), 400
        
        # Verificar client_secret
        client = auth_service.verify_client(client_id, client_secret)
        if not client:
            logger.warning(f'Invalid client credentials: {client_id}')
            return jsonify({'error': 'invalid_client'}), 401
        
        # Validar code
        auth_code = token_service.get_authorization_code(code)
        if not auth_code:
            return jsonify({'error': 'invalid_grant', 
                          'error_description': 'Code no vàlid'}), 400
        
        if auth_code.client_id != client_id:
            return jsonify({'error': 'invalid_client'}), 400
        
        if auth_code.redirect_uri != redirect_uri:
            return jsonify({'error': 'invalid_request',
                          'error_description': 'redirect_uri mismatch'}), 400
        
        if auth_code.is_used:
            logger.warning(f'Code already used: {code}')
            return jsonify({'error': 'invalid_grant',
                          'error_description': 'Code ja usat'}), 400
        
        # Generar JWT i refresh token
        access_token = token_service.generate_jwt(
            citizen_id=auth_code.citizen_id,
            client_id=client_id
        )
        
        refresh_token = token_service.generate_refresh_token(
            citizen_id=auth_code.citizen_id,
            client_id=client_id
        )
        
        # Marcar code com a usat
        token_service.mark_code_as_used(code)
        
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 86400,  # 24h
            'refresh_token': refresh_token,
            'scope': auth_code.scope
        }), 200
    
    except Exception as e:
        logger.error(f'OAuth token error: {e}')
        return jsonify({'error': 'server_error'}), 500

# =====================================================
# 4. VALIDAR TOKEN
# =====================================================

@oauth_bp.route('/token/validate', methods=['POST'])
def validate_token():
    """Validar JWT (Backend-to-Backend)"""
    
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'missing_token'}), 400
        
        # Validar i obtenir payload
        payload = token_service.validate_jwt(token)
        if not payload:
            return jsonify({'valid': False, 'error': 'invalid_token'}), 401
        
        return jsonify({
            'valid': True,
            'citizen_id': payload['sub'],
            'nom': payload['nom'],
            'age_tier': payload['age_tier'],
            'client_id': payload['client_id'],
            'issued_at': payload['iat'],
            'expires_at': payload['exp']
        }), 200
    
    except Exception as e:
        logger.error(f'Token validate error: {e}')
        return jsonify({'error': 'server_error'}), 500

# =====================================================
# 5. LOGOUT
# =====================================================

@oauth_bp.route('/logout', methods=['POST'])
def logout():
    """Revocar token"""
    
    try:
        data = request.get_json()
        token = data.get('token')
        revoke_all = data.get('revoke_all', False)
        
        if not token:
            return jsonify({'error': 'missing_token'}), 400
        
        payload = token_service.validate_jwt(token)
        if not payload:
            return jsonify({'error': 'invalid_token'}), 401
        
        citizen_id = payload['sub']
        
        if revoke_all:
            # Revocar totes les sessions del usuari
            token_service.revoke_all_sessions(citizen_id)
        else:
            # Revocar solament aquesta sessió
            token_service.revoke_token(payload['jti'])
        
        logger.info(f'Logout: citizen {citizen_id}')
        
        return jsonify({'message': 'Sessió finalitzada correctament'}), 200
    
    except Exception as e:
        logger.error(f'Logout error: {e}')
        return jsonify({'error': 'server_error'}), 500
```

## 📦 requirements.txt

```
Flask==2.3.3
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.0.5
Flask-JWT-Extended==4.5.2
Flask-Limiter==3.5.0
PyMySQL==1.1.0
cryptography==41.0.3
python-dotenv==1.0.0
pyotp==2.9.0
gunicorn==21.2.0
```

## 🌍 config.py

```python
import os
from datetime import timedelta

class Config:
    """Configuració base"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
```

