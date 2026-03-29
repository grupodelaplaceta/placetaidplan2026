# SEGURETAT I ENDPOINTS API - PlacetaID Gateway

## 🔐 ESTRATÈGIA DE SEGURETAT

### 1. PROTECCIÓ DE DADES SENSIBLES

#### DIP (Número de Identificació Personal)
```
Emmagatzematge:
├─ dip_encrypted     → AES-256 amb clau de BD
├─ dip_hash          → SHA256(salt + DIP)
└─ Accés: Només validació directa

Transmissió:
├─ HTTPS TLS 1.3 obligatori
├─ Headers: HSTS, X-Content-Type-Options
└─ Sense cache en resposta
```

#### Codi 2FA
```
Gestió:
├─ NO s'emmagatzema mai en base de dades
├─ Validació en temps real contra generador TOTP
├─ Token caducat: 30 segons
└─ Comparació en 200ms fixos (timing attack prevention)

Transport:
├─ Sempre HTTPS
├─ Sense logging de codi (log_redacted)
└─ Rate limit: 3 codi/5min per IP
```

---

### 2. TOKENS I SESSIONS

#### JWT Structure (Session Token)
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key_id_2026_01"
  },
  "payload": {
    "sub": "citizen_12345",
    "dip_hash": "sha256_hash_only",
    "nom": "Joan Martí García",
    "age_tier": "2",
    "client_id": "loteria",
    "iss": "id.laplaceta.org",
    "aud": "*.laplaceta.org",
    "iat": 1743302400,
    "exp": 1743388800,
    "jti": "unique_token_id"
  },
  "signature": "RSA_256_signature"
}
```

#### Validació de Token
```python
def validate_token(token: str) -> dict:
    """
    1. Comprovar signatura RSA
    2. Verificar "exp" no expirat
    3. Validar "iss" és id.laplaceta.org
    4. Comprovar jti no està en revocation list
    5. Retornar payload si tot correcte
    """
    try:
        payload = jwt.decode(
            token,
            app.config['JWT_PUBLIC_KEY'],
            algorithms=['RS256'],
            audience='*.laplaceta.org'
        )
        
        # Comprovar si està revocation list
        if is_in_revocation_list(payload['jti']):
            raise TokenRevokedError()
        
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidSignatureError:
        raise TokenInvalidError()
```

---

### 3. RATE LIMITING I FORÇA BRUTA

#### Estratègia Multi-Nivell
```
Nivell 1: Per IP Global
├─ Límit: 20 intents/min
├─ Acció: Bloqueig temporal 5min
└─ Storage: Redis

Nivell 2: Per DIP Específic
├─ Límit: 3 intents/24h
├─ Acció: Account lockout complet
└─ Storage: MySQL

Nivell 3: Per OAuth Client
├─ Límit: 1000 req/hora
├─ Acció: HTTP 429 Too Many Requests
└─ Storage: Redis (headers RateLimit-*)

Nivell 4: Per Sessió
├─ Límit: 10 renovacions/dia
├─ Acció: Requereix re-autenticació
└─ Storage: Session tokens table
```

#### Implementació Redis
```python
def check_rate_limit(ip_address: str, identifier: str = None):
    """
    identifier: "dip:abc123" o "client:loteria"
    """
    redis_key = f"ratelimit:{ip_address}"
    if identifier:
        redis_key = f"ratelimit:{identifier}"
    
    current = redis_client.incr(redis_key)
    
    if current == 1:
        redis_client.expire(redis_key, 86400)  # 24h
    
    if current > MAX_ATTEMPTS:
        raise RateLimitExceededError(
            retry_after=redis_client.ttl(redis_key)
        )
    
    return current
```

---

### 4. CSRF & CLICK JACKING

#### State Token Protection
```python
def generate_state_token():
    """
    State token: ~32 bytes random, guardat en server
    Ús: Verificar que la redirecció ve de la mateixa sessió
    """
    state = secrets.token_urlsafe(32)
    redis_client.setex(
        f"oauth_state:{state}",
        300,  # 5 minuts vàlid
        json.dumps({
            "created_at": datetime.now().isoformat(),
            "ip_address": request.remote_addr
        })
    )
    return state

def verify_state_token(state: str):
    state_data = redis_client.get(f"oauth_state:{state}")
    if not state_data:
        raise StateTokenExpiredError()
    redis_client.delete(f"oauth_state:{state}")  # One-time use
    return json.loads(state_data)
```

#### Headers de Seguretat
```python
app.config.update(
    # HSTS: 2 anys, subdomiis, preload
    HSTS_HEADERS={'Strict-Transport-Security': 
        'max-age=63072000; includeSubDomains; preload'},
    
    # Content Security Policy
    CSP_HEADER={
        'Content-Security-Policy': 
        "default-src 'self'; script-src 'self' 'nonce-{nonce}'; style-src 'self' 'unsafe-inline'"
    },
    
    # Click-jacking
    CLICKJACK_HEADER={'X-Frame-Options': 'DENY'},
    
    # MIME sniffing
    SNIFF_HEADER={'X-Content-Type-Options': 'nosniff'},
    
    # XSS protection
    XSS_HEADER={'X-XSS-Protection': '1; mode=block'},
    
    # Referrer policy
    REFERRER_HEADER={'Referrer-Policy': 'strict-origin-when-cross-origin'}
)
```

---

### 5. ENCRIPTACIÓ & HASHING

#### Algorismes Recomanats
```
DIP Encriptació:
├─ Algoritme: AES-256-GCM
├─ Clau: Generada des de Master Key + Salt
├─ IV: Random 12 bytes
└─ Tag: Auth tag 16 bytes

Password 2FA Secret:
├─ Algoritme: Similar a DIP
├─ Rotació: Anual (backup codes)
└─ Backup codes: Bcrypt amb salt

DIP Hash (per validació):
├─ Algoritme: SHA-256
├─ Salt: Clau privada + timestamp
└─ Format: hex(sha256(salt + dip))
```

#### Key Management
```python
class KeyManager:
    def __init__(self):
        self.master_key = os.getenv('MASTER_ENCRYPTION_KEY')
        self.backup_key = os.getenv('BACKUP_ENCRYPTION_KEY')
    
    def encrypt_dip(self, dip: str) -> str:
        cipher = AES.new(self.master_key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(dip.encode())
        return base64.b64encode(cipher.nonce + tag + ciphertext).decode()
    
    def decrypt_dip(self, encrypted: str) -> str:
        data = base64.b64decode(encrypted)
        nonce = data[:12]
        tag = data[12:28]
        ciphertext = data[28:]
        
        cipher = AES.new(self.master_key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode()
    
    def hash_dip(self, dip: str) -> str:
        salt = os.getenv('DIP_HASH_SALT')
        return hashlib.sha256(f"{salt}{dip}".encode()).hexdigest()
```

---

## 📡 API ENDPOINTS

### 1. INICIAR FLUX D'AUTENTICACIÓ

**GET** `/oauth/authorize`

```
Query Parameters:
├─ client_id (string, required): 'loteria', 'notaries', etc.
├─ redirect_uri (string, required): URL validada del client
├─ state (string, required): Token aleatori del navegador
├─ scope (string, optional): 'profile age-tier' (default)
└─ prompt (string, optional): 'login' force re-auth, 'consent' ask perms

Resposta 200 OK:
├─ HTML: Pantalla de login de PlacetaID
├─ Session: NoSessionCookie establert (httpOnly, secure, samesite)
└─ CSRF Token en formulari ocult

Resposta 400 Bad Request:
├─ invalid_client: client_id desconegut
├─ invalid_redirect_uri: URI no autoritzada
└─ invalid_scope: scope no vàlid

Resposta 401 Unauthorized:
└─ Si ja autenticat, pot redirigir a consent screen directament

Validacions Servidor:
1. client_id existeix a oauth_clients
2. redirect_uri està en allowed_uris per client
3. scope és subset de allowed_scopes del client
4. redirect_uri usa HTTPS
```

### 2. VALIDAR CREDENTIALS (DIP + 2FA)

**POST** `/oauth/validate`

```
Content-Type: application/x-www-form-urlencoded

Body Paràmetres:
├─ dip (string): Nombre en format 1234-5678-A
├─ code_2fa (string): 6 dígits del generador
└─ csrf_token (string): Token CSRF del formulari

Response Headers:
├─ Set-Cookie: session_temp=... (5 min)
└─ X-RateLimit-Remaining: 2

Resposta 200 OK:
{
  "success": true,
  "message": "Credentials validats correctament",
  "redirect_uri": "https://loteria.laplaceta.org/callback?code=...&state=..."
}

Resposta 400 Bad Request:
{
  "success": false,
  "error": "invalid_credentials",
  "message": "DIP o 2FA incorrectes",
  "attempt": 1,
  "attempts_remaining": 2,
  "timestamp": "2026-03-29T14:32:17Z"
}

Resposta 429 Too Many Requests:
{
  "error": "account_locked",
  "message": "Compte blocat per 24 hores",
  "locked_until": "2026-03-30T14:32:17Z",
  "unlock_url": "https://seu.laplaceta.org/unlock",
  "retry_after": 86400
}

Backend Procés:
1. Rate limit check (per IP + per DIP)
2. check account_locked status
3. Validar format DIP (suma verificació)
4. SELECT FROM citizens WHERE dip_hash = hash(dip)
5. Si no trovest → increment counter, return error
6. Validar 2FA token (timing-safe comparison)
7. Si correcte → generate authorization_code
8. Emmagatzem a authorization_codes table
9. Log audit de SUCCESS
10. Return amb codi per a intercanvi de token
```

### 3. INTERCANVIAR CODE PER JWT

**POST** `/oauth/token`

```
Content-Type: application/x-www-form-urlencoded
Authorization: Basic base64(client_id:client_secret)

Body Paràmetres:
├─ grant_type (string): 'authorization_code' (required)
├─ code (string): Authorization code rebut
├─ redirect_uri (string): DEBE coincidir amb la de authorize
└─ client_id (string): Per a confirmació

Resposta 200 OK:
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "refresh_token": "def456xyz...",
  "scope": "profile age-tier"
}

Resposta 400 Bad Request:
{
  "error": "invalid_grant",
  "error_description": "Authorization code expirat o ja usat",
  "error_uri": "https://id.laplaceta.org/docs/errors#invalid_grant"
}

Backend Procés:
1. Validar client_secret (bcrypt compare)
2. Comprovar que code existeix i no expirat
3. Verificar use_count = 0 (una única ús)
4. Confirmar redirect_uri coincideix
5. Generar JWT amb payload
6. Generar Refresh Token
7. Marcar code ON USE
8. Retornar tokens
```

### 4. VALIDAR TOKEN (Backend a Backend)

**POST** `/token/validate`

```
Content-Type: application/json
Authorization: Bearer <service_token> (o Basic auth)

Body:
{
  "token": "eyJhbGc..."
}

Resposta 200 OK:
{
  "valid": true,
  "citizen_id": 12345,
  "nom": "Joan Martí García",
  "age_tier": "2",
  "dip_hash": "abc123def...",
  "issued_at": 1743302400,
  "expires_at": 1743388800,
  "client_id": "loteria"
}

Resposta 401 Unauthorized:
{
  "valid": false,
  "error": "token_expired",
  "message": "Token expirat fa 2 hores",
  "expired_at": 1743388800
}

Backend Procés:
1. Parse JWT i valida signatura
2. Comprovar jti no està en revocation list
3. Verificar expiració
4. SELECT FROM session_tokens WHERE token_hash = hash(token)
5. Retornar dades del payload
```

### 5. RENOVAR TOKEN (Refresh)

**POST** `/oauth/refresh`

```
Content-Type: application/x-www-form-urlencoded

Body:
├─ grant_type: 'refresh_token'
├─ refresh_token: 'def456xyz...'
├─ client_id: 'loteria'
└─ client_secret: '...' (si required)

Resposta 200 OK:
{
  "access_token": "eyJhbGc...(novo)",
  "token_type": "Bearer",
  "expires_in": 86400,
  "refresh_token": "ghi789abc...(novo, rotació)",
  "scope": "profile age-tier"
}

Resposta 400 Bad Request:
{
  "error": "invalid_grant",
  "error_description": "Refresh token no vàlid o expirat"
}

Backend Procés:
1. Hash refresh token
2. SELECT FROM refresh_tokens WHERE token_hash = hash
3. Comprovar is_revoked = FALSE
4. Comprovar expires_at > NOW()
5. Generar NOVO JWT
6. Generar NOVO refresh token (rotació)
7. Invalidar token anterior
8. Retornar tokens novos
```

### 6. DESAUTENTICAR (Logout)

**POST** `/oauth/logout`

```
Content-Type: application/json
Authorization: Bearer <token>

Body:
{
  "revoke_all": false  // true: revoca totes les sessions
}

Resposta 200 OK:
{
  "message": "Sessió finalitzada correctament",
  "revoked_tokens": 1
}

Backend Procés:
1. Parse JWT
2. UPDATE session_tokens SET is_active = FALSE, revoked_at = NOW()
3. Si revoke_all: afecta totes les sessions del usuari
4. Afegir jti a revocation list (redis, ~24h)
5. Log audit LOGOUT
```

### 7. OBTENIR PERFIL DE USUARI

**GET** `/user/profile`

```
Authorization: Bearer <token>

Resposta 200 OK:
{
  "citizen_id": 12345,
  "nom": "Joan Martí García",
  "email": "joan@example.com",
  "age_tier": "2",
  "date_of_birth": "1990-05-15",
  "phone_number": "+34 612 345 678",
  "authenticators": {
    "totp": { "enabled": true, "created_at": "2025-01-01" },
    "sms": { "enabled": false }
  },
  "last_login": "2026-03-29T13:00:00Z",
  "last_location": "71.23°N, 22.35°E (estimat)",
  "active_sessions": 2,
  "created_at": "2024-01-01T10:00:00Z"
}
```

---

## 🗄️ RATE LIMITING - Headers

```http
HTTP/1.1 200 OK

RateLimit-Limit: 20
RateLimit-Remaining: 15
RateLimit-Reset: 1743302400

Retry-After: 60  (si s'ha excedit)
```

---

## 🔍 ERROR CODES ESTANDARIZATS

| Codi | HTTP | Descripció | Acció Usuari |
|------|------|-----------|--------------|
| `invalid_credentials` | 400 | DIP o 2FA incorrecte | Reintentar |
| `account_locked` | 429 | > 3 intents fallits | Contactar suport |
| `token_expired` | 401 | JWT caducat | Fer login de nou |
| `invalid_client` | 400 | client_id no vàlid | Error tècnic (report) |
| `invalid_scope` | 400 | Scope no autoritzat | Error tècnic |
| `state_mismatch` | 403 | CSRF token invalid | Reintentar flow |
| `rate_limit_exceeded` | 429 | Massa intents | Esperar |

