# RESUM EXECUTIU - PlacetaID Gateway

## 👁️ Visió General del Projecte

**PlacetaID** és una pasarela centralitzada d'autenticació que prioritza la **seguretat** per sobre de tot. El seu objectiu és actuar com a node confiable per a totes les aplicacions de la Placeta (loteria, notaries, etc.).

## 🎯 Objectius Claus

1. **❌ Zero Trust per a Dades Sensibles**: DIP i 2FA mai es comparteixen amb webs externes
2. **✅ Control Centralitzat**: Un únic punt de validació per a tota la Placeta
3. **🔐 Seguretat per Defecte**: Rate limiting, encriptació, audit logging
4. **♿ Accessibilitat**: WCAG 2.1 AA, mobile-first
5. **🎨 Experiència Unificada**: Interfície consistent per a tots els serveis

## 🏗️ Estructura de Projecte

```
plid/
├── 📄 README.md                      # Introducció
├── 📁 docs/
│   ├── ARQUITECTURA.md               # Fluxos OAuth2-style, endpoints
│   ├── DISSENY_UI.md                 # Mockups, color palette, UX
│   ├── SEGURETAT_API.md              # Rate limiting, encriptació, tokens
│   └── DESPLIEGAMENT.md              # Roadmap, deployment guide
├── 🗄️ database/
│   └── schema.sql                    # MySQL schema, procedures, views
├── 🐍 backend/
│   ├── IMPLEMENTACIO_PYTHON.md       # Flask app, endpoints, services
│   ├── requirements.txt              # Python dependencies
│   ├── app.py                        # Main Flask application
│   ├── config.py                     # Configuration
│   ├── middleware/                   # Auth, rate limit, CSRF
│   ├── routes/                       # /oauth/*, /user/*, /admin/*
│   ├── models/                       # SQLAlchemy ORM
│   ├── services/                     # Business logic
│   └── utils/                        # Crypto, validators, JWT
└── 🎨 frontend/
    ├── IMPLEMENTACIO_HTML_CSS.md    # HTML template, CSS styles
    ├── IMPLEMENTACIO_JAVASCRIPT.md  # JS interactivity
    ├── templates/
    │   └── login.html               # Main login form
    ├── static/
    │   ├── css/
    │   │   ├── reset.css
    │   │   ├── theme.css
    │   │   └── login.css
    │   ├── js/
    │   │   ├── utils.js
    │   │   └── login.js
    │   └── images/
    │       ├── favicon.svg
    │       └── logo.svg
    └── public/
        └── error.html               # 404, 500 pages
```

## 🔄 Flux de Dades (Step-by-Step)

### Escenari: Usuari vol accedir a loteria.laplaceta.org

```
1️⃣  INICIACIÓ
    └─ Usuario clica "Identificar amb PlacetaID" a loteria.org
       ↓
       Generació de state token (aleatori, secret)
       ↓
       Redirecció a https://id.laplaceta.org/oauth/authorize?
           client_id=loteria
           redirect_uri=https://loteria.laplaceta.org/callback
           state=abc123xyz789

2️⃣  AUTENTICACIÓ
    └─ PlacetaID renderitza pantalla de login
       ↓
       Usuario ingressa:
       • DIP (1234-5678-A)
       • 2FA (123456 del generador TOTP)
       ↓
       POST /oauth/validate amb credentials
       
3️⃣  VALIDACIÓ BACKEND
    └─ Backend de PlacetaID processa:
       
       a) Validar format DIP
       b) Hash DIP → lookup a Citizens table
       c) Comprovar si compte està blocat
       d) Validar 2FA (timing-safe comparison)
       e) Si tot correcte:
          • Generar Authorization Code (5 min)
          • Emmagatzem a auth_codes table
          • Return response amb redirect URL
       f) Si error:
          • Registrar intent fallit
          • Comptador +1
          • Si ≥3: bloquejar compte 24h
          • Retornar error genèric (no revelar motiu)

4️⃣  GENERACIÓ DE TOKEN
    └─ Backend genera JWT amb payload:
       {
         "sub": "citizen_12345",
         "nom": "Joan Martí García",
         "age_tier": "2",
         "dip_hash": "sha256(salt+dip)",
         "iss": "id.laplaceta.org",
         "exp": 1743388800
       }
       ↓
       Token signat amb clau privada RSA-256
       ↓
       Return JWT a client

5️⃣  REDIRECCIÓ SEGURA
    └─ Browser redirigit a:
       https://loteria.laplaceta.org/callback?
           code=AUTH_CODE_xxxxx
           state=abc123xyz789
           session_token=JWT_xxxxx

6️⃣  VALIDACIÓ A LA WEB EXTERNA
    └─ loteria.org verifica:
       • state coincideix (CSRF check)
       • code no ha estat usat
       ↓
       Emmagatzem JWT a localStorage
       ↓
       Usuari redirigit a dashboard privat
       ↓
       ✅ ACCÉS CONCEDIT

7️⃣  LOGOUT
    └─ Usuario fa logout
       ↓
       Token revocatEN Redis (TTL 24h)
       ↓
       Nou login requereix credentials novament
```

## 🔐 Mecanismes de Seguretat Implementats

| Amenaza | Mecanisme | Ubicació |
|---------|-----------|----------|
| Força Bruta | Rate Limiting (3 intents/24h) + Account Lockout | Backend DB |
| CSRF | State Token + Verificació | Flash Session |
| XSS | Content-Security-Policy Headers | Nginx/Backend |
| MITM | HTTPS TLS 1.3 + HSTS | Infrastructure |
| Token Falsificat | JWT Signature RSA-256 | Backend |
| Token Reusat | Authorization Code single-use | Backend DB |
| Timing Attack | Cryptographic Timing-safe Comparison | Python hashlib |
| SQL Injection | Parameterized Queries (SQLAlchemy ORM) | Backend |
| DIP Leaked | Encriptació AES-256 + Hashing SHA-256 | Database |

## 📊 Comparativa vs. Altres Solucions

| Aspecte | PlacetaID | OAuth 2.0 Simple | SSO Tradicional |
|---------|-----------|------------------|-----------------|
| **Secrets en servidor** | ❌ No (decentralitzat) | ✅ Sí (risc) | ✅ Sí (risc) |
| **2FA obligatori** | ✅ Sí | ⚠️ Opcional | ⚠️ Opcional |
| **Rate Limiting** | ✅ Multinivell | ⚠️ Basic | ⚠️ Bàsic |
| **Audit Logging** | ✅ Complet | ⚠️ Parcial | ⚠️ Parcial |
| **Control de Marca** | ✅ UI Unificada | ❌ No | ✅ Unificada |
| **Complexitat** | ⚠️ Mitjana | ✅ Baixa | ⚠️ Alta |
| **Cost** | ✅ Desplegament propi | ✅ 0 | ⚠️ Propietari |

## 💾 Base de Dades - Taules Principals

### 🟦 citizens
```sql
id | dip_hash | full_name | age_tier | email | phone | created_at
```
- **Registre central de usuaris de la Placeta**
- DIP xifrat + hash per validació
- Age tiers: 0 (< 14), 1 (14-17), 2 (≥18)

### 🟦 authenticators_2fa
```sql
id | citizen_id | secret_encrypted | authenticator_type | is_active
```
- **Secrets 2FA per usuari**
- Suporta TOTP, SMS, Email
- 1 secret per tipus (única)

### 🟦 login_attempts
```sql
id | citizen_id | dip_hash | ip_address | attempt_stage | success | error_code
```
- **Auditoria de totes les tentatives**
- DIP_VALIDATION, 2FA_VALIDATION, SUCCESS
- Per rastrejar força bruta

### 🟦 account_lockouts
```sql
id | citizen_id | dip_hash | lockout_reason | locked_until | unlock_token
```
- **Registre de bloqueigs**
- 24h automàtic després de 3 intents
- Desbloqueig via seu.laplaceta.org

### 🟦 session_tokens
```sql
id | token_hash | citizen_id | client_id | expires_at | is_active | revoked_at
```
- **Tokens actius validats**
- 24h durabilitat
- Revocable per logout

### 🟦 audit_logs
```sql
id | event_type | citizen_id | ip_address | event_data | timestamp
```
- **Log complet de tot l'important**
- 7 anys de retenció (legal)
- Indexat per citizen_id i timestamp

## 🚀 Endpoints Principals

| Mètode | Endpoint | Propòsit | Auth |
|--------|----------|----------|------|
| GET | `/oauth/authorize` | Iniciar login | Query params |
| POST | `/oauth/validate` | Validar DIP+2FA | Session + CSRF |
| POST | `/oauth/token` | Intercanvi code→JWT | Basic auth |
| POST | `/token/validate` | Verificar JWT | Bearer |
| POST | `/oauth/refresh` | Renovar token | Refresh token |
| POST | `/oauth/logout` | Revocar sessió | Bearer |
| GET | `/user/profile` | Obtenir dades usuari | Bearer |

## 🎨 Frontend - Highlights

✅ **Responsiu**: 100% mobile & desktop  
✅ **Accessible**: WCAG 2.1 AA, screen reader support  
✅ **Modern**: CSS Grid, Flexbox, animations  
✅ **Performant**: Loading < 2s (LCP), JS async  
✅ **Segur**: No JS inline, CSP headers, CORS  

### Pantallas
1. **Login**: Entrada de DIP + 2FA (3 opcions)
2. **Validació**: Countdown amb spinner
3. **Èxit**: Countdown a redirecció
4. **Error**: Missatge descriptiu + intents restants
5. **Bloqueig**: 24h timer + link desbloqueig

## 📈 Métriques de Rendiment (Targets)

| Métrica | Target | Method |
|---------|--------|--------|
| **Login Time** | < 2s | Dashboard |
| **API Latency** | < 200ms | APM |
| **Uptime** | 99.9% | Monitoring |
| **Token Size** | < 1KB | Network tab |
| **Page Load** | < 3s | Lighthouse |

## 🛡️ Incident Response

### Escenaris

**Força Bruta Detectada**
```
1. Alert disparat (> 20 intents/IP/h)
2. IP afegida a blocklist
3. Token JWT revocats per IP
4. Enviar email a admins
5. Manual review per pattern
```

**Token Compromès**
```
1. Revocar immediatament via JTI
2. Força logout de todas les sessions de user
3. Audit log de revocation
4. Notificar usuari per email
5. Demana re-login amb 2FA
```

**Base de Dades Comprometida**
```
1. Activar mode disaster recovery
2. Restaurar des de backup xifrat
3. Invalidar totes les sessions
4. Cambiar claus d'encriptació
5. Audit complet de quin va ser accedit
```

## 📚 Documentació Resums

- **[ARQUITECTURA.md](ARQUITECTURA.md)** - Fluxos, endpoints, sequences
- **[DISSENY_UI.md](DISSENY_UI.md)** - Mockups, paleta colors, responsive
- **[SEGURETAT_API.md](SEGURETAT_API.md)** - Rate limits, encriptació, tokens
- **[DESPLIEGAMENT.md](DESPLIEGAMENT.md)** - Roadmap, setup, monitoring
- **[IMPLEMENTACIO_PYTHON.md](../backend/IMPLEMENTACIO_PYTHON.md)** - Flask code
- **[IMPLEMENTACIO_HTML_CSS.md](../frontend/IMPLEMENTACIO_HTML_CSS.md)** - UI code
- **[IMPLEMENTACIO_JAVASCRIPT.md](../frontend/IMPLEMENTACIO_JAVASCRIPT.md)** - JS code

## 🎓 Stack Tecnològic

**Backend**: Python 3.9+, Flask, SQLAlchemy, PyJWT, cryptography  
**Database**: MySQL 8.0+, Redis per sessions/cache  
**Frontend**: HTML5, CSS3 (Grid/Flex), Vanilla JS (ES6+)  
**Infrastructure**: Nginx, Gunicorn, Let's Encrypt TLS  
**Monitoring**: ELK Stack (Elasticsearch, Logstash, Kibana)  
**CI/CD**: GitHub Actions, Docker containers  

## 🔄 Roadmap Futur

### Fase 2 (Q3 2026)
- [ ] WebAuthn (FIDO2) como alternativa a 2FA
- [ ] Biometric authentication (fingerprint)
- [ ] Passwordless login
- [ ] Admin dashboard avanzado

### Fase 3 (Q4 2026)
- [ ] Machine learning per detectar fraude
- [ ] Multi-factor progressive scoring
- [ ] Single sign-on (SSO) unificado
- [ ] GraphQL API alternativa

## ✅ Checklists de Validació

### Pre-Producció
- [ ] Penetration testing complet
- [ ] Load testing (1.000+ req/s)
- [ ] Disaster recovery drill
- [ ] GDPR audit
- [ ] Compliance certificats

### Post-Deployment
- [ ] 24/7 Monitoring actiu
- [ ] Alertes configurades
- [ ] Runbook de incidents
- [ ] Team entrenament
- [ ] Public documentation

---

**Versió**: 1.0  
**Data**: Març 2026  
**Estatus**: ✅ Architecture Complete, Ready for Implementation  
**Contact**: security@laplaceta.org

