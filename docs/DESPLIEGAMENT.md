# GUIA DE DESPLIEGAMENT I IMPLEMENTACIÓ

## 🚀 Roadmap de Despliegament

### FASE 1: Setup & Infrastructure (Semanes 1-2)

#### 1.1 Base de Dades
```bash
# 1. Crear schema MySQL
mysql -u root -p < database/schema.sql

# 2. Verificar taules
mysql -u root -p placetaid_db << EOF
SHOW TABLES;
DESCRIBE citizens;
DESCRIBE authorization_codes;
EOF

# 3. Executar procediments
mysql -u root -p placetaid_db < database/procedures.sql

# 4. Crear índexs adicionals (per performance)
CREATE INDEX idx_login_attempts_date ON login_attempts(attempted_at);
CREATE INDEX idx_sessions_citizen ON session_tokens(citizen_id);
```

#### 1.2 Servidor Backend (Python/Flask)
```bash
# 1. Crear entorn virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Instalar dependències
pip install -r backend/requirements.txt

# 3. Crear fitxer .env
cp backend/.env.example backend/.env

# 4. Completar variables d'entorn
# DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/placetaid_db
# JWT_SECRET_KEY=<generar-clau-random-32-chars>
# MASTER_ENCRYPTION_KEY=<32-bytes-base64>
# DIP_HASH_SALT=<salt-random>

# 5. Test inicial
python backend/app.py --debug
```

#### 1.3 Servidor Frontend (HTML/CSS/JS)
```bash
# 1. Estructura
mkdir -p frontend/static/{css,js,images}
mkdir -p frontend/templates

# 2. Copiar fitxers
cp frontend/templates/login.html frontend/templates/
cp frontend/static/css/* frontend/static/css/
cp frontend/static/js/* frontend/static/js/

# 3. Servir amb Flask (integrat amb backend)
# Els templates es serveixen des de Flask directament
```

### FASE 2: Desenvolupament & Testing (Semanes 3-6)

#### 2.1 Tests Unitaris
```python
# backend/tests/test_auth.py
import unittest
from app import create_app, db
from models.citizen import Citizen

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_authorize_invalid_client(self):
        """Testejar que /oauth/authorize rebutja client inválid"""
        response = self.client.get('/oauth/authorize?client_id=invalid&redirect_uri=https://example.com&state=abc123')
        self.assertEqual(response.status_code, 400)
        self.assertIn('invalid_client', response.get_json()['error'])
    
    def test_login_success(self):
        """Testejar login exitós"""
        # Setup
        with self.app.app_context():
            citizen = Citizen(
                dip_encrypted='...',
                dip_hash='abc123...',
                full_name='Test User',
                age_tier='2'
            )
            db.session.add(citizen)
            db.session.commit()
        
        # Test
        response = self.client.post('/oauth/validate', data={
            'dip': '1234-5678-A',
            'code_2fa': '123456'
        })
        
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
```

#### 2.2 Tests d'Integració
```bash
# Probar flux complet
1. Visitar https://id.laplaceta.org/oauth/authorize?...
2. Introducir credencials correctes
3. Verificar redirecció amb token
4. Testejar token validation endpoint
5. Verificar logout revoca token
```

#### 2.3 Tests de Seguretat
```python
# backend/tests/test_security.py

def test_rate_limit():
    """Verificar rate limiting per IP"""
    for i in range(25):
        response = client.post('/oauth/validate', data={...})
    
    last_response = client.post('/oauth/validate', data={...})
    assert last_response.status_code == 429

def test_csrf_protection():
    """Verificar que POST sense CSRF token falla"""
    response = client.post('/oauth/validate', data={'dip': '...', 'code_2fa': '...'})
    assert response.status_code == 403

def test_timing_attack():
    """Verificar respostes pren temps constant"""
    import time
    
    times = []
    for _ in range(10):
        start = time.time()
        client.post('/oauth/validate', data={...})
        times.append(time.time() - start)
    
    # Verificar que totes les respostes pren ~200ms
    assert all(180 < t < 220 for t in times)
```

### FASE 3: Despliegament a Producció (Semanes 7-8)

#### 3.1 Certificats SSL/TLS
```bash
# 1. Generar certificat (Let's Encrypt recomençat)
certbot certonly \
  --standalone \
  -d id.laplaceta.org \
  -d seu.laplaceta.org

# 2. Configurar auto-renovació
certbot renew --dry-run  # test
certbot renew --agree-tos  # actual
```

#### 3.2 Configuració de Producció
```python
# backend/config.py - ProductionConfig
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # HTTPS redirection
    PREFERRED_URL_SCHEME = 'https'
    
    # Session cookies
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
```

#### 3.3 Deployar amb Gunicorn + Nginx
```bash
# 1. Instalar gunicorn
pip install gunicorn

# 2. Executar servidor
gunicorn \
  --workers 4 \
  --worker-class sync \
  --bind 127.0.0.1:8000 \
  --timeout 30 \
  --access-logfile - \
  --error-logfile - \
  app:app

# 3. Configurar Nginx
# /etc/nginx/sites-available/placetaid

upstream placetaid {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name id.laplaceta.org;
    
    ssl_certificate /etc/letsencrypt/live/id.laplaceta.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/id.laplaceta.org/privkey.pem;
    
    # Seguretat
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # CORS optimitzat per PlacetaID
    add_header Access-Control-Allow-Origin "https://*.laplaceta.org" always;
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
    
    location / {
        proxy_pass http://placetaid;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }
    
    # Caching de assets estàtics
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Redirecció HTTP → HTTPS
server {
    listen 80;
    server_name id.laplaceta.org;
    return 301 https://$server_name$request_uri;
}
```

#### 3.4 Monitorit i Logging
```python
# backend/middleware/logging.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """Configurar logging per a producció"""
    
    # Crear directori de logs
    os.makedirs('logs', exist_ok=True)
    
    # Handler per a errors
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    
    # Handler per a accés
    access_handler = RotatingFileHandler(
        'logs/access.log',
        maxBytes=10485760,
        backupCount=20
    )
    access_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    error_handler.setFormatter(formatter)
    access_handler.setFormatter(formatter)
    
    app.logger.addHandler(error_handler)
    app.logger.addHandler(access_handler)
```

### FASE 4: Post-Despliegment

#### 4.1 Monitorit de Seguretat
```bash
# Neteja automàtica de tokens expirats (diària)
# Crear cronjob per executar sp_cleanup_expired_tokens
0 2 * * * cd /srv/placetaid && ./scripts/cleanup.sh

# Alertes de sospita
- > 10 intents fallits per IP en 1h
- > 5 lockouts per dia
- Tokens modificats o revocats anormalment
```

#### 4.2 Documentació de Manteniment
```
📚 Guia de Suport (Seu Electrònica):

1. **Com desbloquejar compte:**
   - Admin panel → /admin/unlock
   - Verificar identitat del usuari
   - Enviar link de desbloqueig per email

2. **Com resetar 2FA:**
   - Si l'usuari perd accés al generador
   - Procediment manual + confirmació de dades
   - Generar novo secret TOTP

3. **Monitorit diàri:**
   - Revisar logs d'errors
   - Comprovar health check: GET /health
   - Verificar rate limits no s'excedeixen
   - Auditar accés administratiu
```

---

## 🏗️ Arquitectura General - Diagrama

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                 │
└──────────────┬──────────────────────────────┬──────────────────┘
               │                              │
        WEB EXTERNA                    WEB EXTERNA 2
      (loteria.org)                  (notaries.org)
          │ 1. Login                      │ 1. Login
          │                               │
          └───────────────┬───────────────┘
                          │
                          ▼
        ┌──────────────────────────────┐
        │  HTTPS (TLS 1.3)             │
        │  id.laplaceta.org            │
        │                              │
        │ ┌────────────────────────┐  │
        │ │  FRONTEND              │  │
        │ │  (HTML/CSS/JS)        │  │
        │ │  - Login Form         │  │
        │ │  - CSRF Protection    │  │
        │ │  - Tab Management     │  │
        │ └────────────────────────┘  │
        │                              │
        │ ┌────────────────────────┐  │
        │ │  BACKEND (Flask)       │  │
        │ │                        │  │
        │ │  /oauth/authorize      │ ◄──── OAuth Endpoints
        │ │  /oauth/validate       │
        │ │  /oauth/token          │
        │ │  /user/profile         │
        │ │                        │  │
        │ │  Rate Limiter (Redis)  │  │
        │ │  JWT Generator         │  │
        │ │  Session Manager       │  │
        │ └────────────────────────┘  │
        └──────────────┬───────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
    ┌─────────────┐           ┌─────────────┐
    │   MySQL DB  │           │  Redis      │
    │             │           │             │
    │ - Citizens  │           │ - Sessions  │
    │ - Tokens    │           │ - Rate Limits
    │ - Audit Logs│           │ - Cache     │
    └─────────────┘           └─────────────┘
```

---

## 📊 Diagrama de Flux (Seqüència)

```
USER           WEB EXTERN           GATEWAY             BACKEND              DB
 │              │                      │                   │                  │
 │──Login──────>│                      │                   │                  │
 │              │──Init OAuth──────────>                   │                  │
 │              │                      │                   │                  │
 │<──Redirect──X │                      │                  │                   │
 │              │<─────HTML Login──────│                  │                  │
 │              │                      │                   │                  │
 │──DIP+2FA────>│                      │                   │                  │
 │              │──POST /validate─────>│                   │                  │
 │              │                      │──Query────────────────>              │
 │              │                      │<──Result─────────│                  │
 │              │                      │──Validate 2FA────>                  │
 │              │                      │─Log attempt────────────────>       │
 │              │                      │<──Auth Code──────│                  │
 │              │                      │                   │                  │
 │              │<──JWT + Redirect────│                  │                  │
 │<──Redir────X │                      │                   │                  │
 │              │                      │                   │                  │
 │────Callback──────>                  │                   │                  │
 │              │───Validate Token────────────────────────>                  │
 │              │                      │                   │ Query            │
 │              │                      │                   │─────────>       │
 │              │<───Valid Response───│                  │                  │
 │<──Access────│                       │                  │                  │
 │ Granted     │                       │                   │                  │
```

---

## 🔒 Checklist de Seguretat Pre-Producció

- [ ] **HTTPS Obligatori**: Tots els endpoints usant TLS 1.3
- [ ] **Headers de Seguretat**: HSTS, CSP, X-Frame-Options configurats
- [ ] **Encriptació en Repòs**: DIP xifrat a BD, secrets 2FA encriptats
- [ ] **Rate Limiting**: 3 intents/24h per DIP, 20/min per IP
- [ ] **CSRF Protection**: State tokens verificats
- [ ] **Logging Audit**: Tots els intents registrats
- [ ] **Credentials Rotation**: Claus JWT renovades anualment
- [ ] **Backup Diàri**: BD safsada i encriptada
- [ ] **Disaster Recovery**: Plan de recuperació testat
- [ ] **Penetration Testing**: Audit de seguretat extern
- [ ] **GDPR Compliant**: Dret a oblit, consentiment, privacitat
- [ ] **Monitoring 24/7**: Alertes d'anomalies en temps real

---

## 📈 Mètriques de Monitorit

```json
{
  "performance": {
    "avg_login_time_ms": 1200,
    "p95_response_time_ms": 2500,
    "tokens_validated_per_hour": 15000
  },
  "security": {
    "failed_login_attempts_24h": 342,
    "accounts_locked": 12,
    "suspicious_ips_blocked": 5,
    "rate_limit_violations": 28
  },
  "availability": {
    "uptime_percentage": 99.97,
    "database_connections": 45,
    "api_error_rate": 0.02
  }
}
```

