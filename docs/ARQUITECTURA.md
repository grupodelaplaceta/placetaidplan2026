# ARQUITECTURA DE REDIRECCIONS - PlacetaID Gateway

## 1. FLUX D'AUTENTICACIÓ (OAuth2-Style)

### Actors del Sistema
- 👤 **Usuari**: Ciutadà que vol autenticar-se
- 🌐 **Web Externa**: Servei (ex: loteria.laplaceta.org)
- 🔐 **Gateway PlacetaID**: id.laplaceta.org (Autenticador Central)
- 💾 **Backend API**: Servidor de validació
- 🗄️ **Base de Dades**: Registres de ciutadans i bloqueigs

---

## 2. SEQÜÈNCIA DETALLADA DE REDIRECCIONS

```
┌─────────────┐
│   WEB EXT   │ (loteria.laplaceta.org)
│  "Identificar" │
└────────┬────┘
         │
         │ 1. User clica "Identificar amb PlacetaID"
         │
         ▼
    ┌────────────────────────┐
    │   GENERAR STATE TOKEN  │
    │  (aleatori, secret)    │
    └────────┬───────────────┘
             │
             │ 2. redirect_uri = https://loteria.laplaceta.org/callback
             │    state = abc123xyz789
             │    scope = "profile age-tier"
             │
             ▼
    ┌──────────────────────────────────────────┐
    │  PlacetaID Gateway (id.laplaceta.org)   │
    │  GET /oauth/authorize?                   │
    │      client_id=loteria                   │
    │      &redirect_uri=https://...           │
    │      &state=abc123xyz789                 │
    │      &scope=profile%20age-tier           │
    └────────┬─────────────────────────────────┘
             │
             │ 3. RENDER PANTALLA DE LOGIN
             │    (UI sencura de PlacetaID)
             │
             ▼
    ╔════════════════════════════════╗
    ║  PANTALLA DE LOGIN             ║
    ║  [DIP: __________  ]           ║
    ║  [2FA: __________  ]           ║
    ║  [VALIDAR]                     ║
    ╚═════────┬──────────────────────╝
              │
              │ 4. Usuari entra DIP + 2FA
              │    POST /oauth/validate
              │    { dip, code_2fa }
              │
              ▼
    ┌──────────────────────────────┐
    │ BACKEND VALIDATION            │
    │ 1. Comprovar existència DIP   │
    │ 2. Validar 2FA               │
    │ 3. Bloqueum si 3+ intents    │
    │ 4. Retornar errors específics │
    └────────┬─────────────────────┘
             │
     ┌───────┴───────┬──────────────┐
     │ ✓ VALID       │ ✗ INVALID    │
     ▼               ▼
  JWT +          ERROR
  REFRESH      (Comptador
              d'intents)
     │               │
     │               │ 5. UI mostra error o bloqueig
     │               │    "3 intents incorrectes"
     │               │    "Contacta amb seu electrònica"
     │               │
     │               └─ LOOP NOVAMENT A PANTALLA?
     │                  (si intents < 3)
     │
     │ 6. GENERAR AUTHORIZATION CODE
     │    (vàlid només 5 minuts)
     │
     ▼
  ┌────────────────────────────────────┐
  │ REDIRECCIÓ A WEB EXTERNA          │
  │ 302 Location:                      │
  │ https://loteria.laplaceta.org/    │
  │   callback?                        │
  │   code=AUTH_CODE_12345            │
  │   &state=abc123xyz789             │
  │   &session_token=jwt_token        │
  └────────┬───────────────────────────┘
           │
           │ 7. NAVEGADOR segueix redirecció
           │    (Usuari torna a web original)
           │
           ▼
  ┌──────────────────────────────────┐
  │ WEB EXTERNA (/callback)          │
  │ 1. Verifica state coincideix     │
  │ 2. Guarda session_token         │
  │ 3. Redirecció a pàgina privada   │
  └──────────────────────────────────┘
           │
           │ 8. VALIDAR TOKEN (backend a backend)
           │    POST /token/validate
           │    { session_token }
           │    ↓
           │ RESPOSTA:
           │ {
           │   "valid": true,
           │   "nom": "Joan Martí García",
           │   "age_tier": "2",  (Major de 18)
           │   "exp": 1234567890
           │ }
           │
           ▼
  ┌──────────────────────────────────┐
  │ ✓ USUARI AUTENTICAT              │
  │ Pot accedir a contingut privat   │
  │ Sessió creada localment          │
  └──────────────────────────────────┘
```

---

## 3. ENDPOINTS PRINCIPALS DE L'API

### Gateway (PlacetaID - id.laplaceta.org)

| Mètode | Endpoint | Descripció | Auth |
|--------|----------|-----------|------|
| GET | `/oauth/authorize` | Inicia flux d'autenticació | Query params |
| POST | `/oauth/validate` | Valida DIP + 2FA | Session |
| POST | `/oauth/token` | Intercanvia code per JWT | Code + secret |
| POST | `/token/validate` | Valida JWT d'un token | Bearer |
| POST | `/oauth/logout` | Invalida token | Bearer |
| GET | `/user/profile` | Obté dades usuari | Bearer |

### Web Externa (loteria.laplaceta.org)

```javascript
// 1. Redirigir a PlacetaID
function loginWithPlacetaID() {
  const state = generateRandomState();
  sessionStorage.setItem('oauth_state', state);
  
  const params = new URLSearchParams({
    client_id: 'loteria',
    redirect_uri: 'https://loteria.laplaceta.org/callback',
    state: state,
    scope: 'profile age-tier'
  });
  
  window.location = `https://id.laplaceta.org/oauth/authorize?${params}`;
}

// 2. Processar callback
function handleCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');
  const sessionToken = params.get('session_token');
  
  // Verificar state
  if (state !== sessionStorage.getItem('oauth_state')) {
    throw new Error('State tampering detected');
  }
  
  // Guardar token
  localStorage.setItem('session_token', sessionToken);
  
  // Redirigir a home
  window.location = '/dashboard';
}
```

---

## 4. CICLE DE VIDA DE TOKENS

### Authorization Code
- **Durada**: 5 minuts
- **Format**: Aleatori (32 chars)
- **Usos**: Només 1 ús, aleshores s'invalida
- **Propòsit**: Intercanvi per JWT

### JWT Session Token
- **Durada**: 24h (renovable)
- **Payload**:
  ```json
  {
    "sub": "user_12345",
    "nom": "Joan Martí",
    "age_tier": "2",
    "dip_hash": "sha256(dip)",
    "client_id": "loteria",
    "iat": 1234567890,
    "exp": 1234654290
  }
  ```
- **Secret**: Clau privada PlacetaID (RSA-256)

### Refresh Token
- **Durada**: 30 dies
- **Propòsit**: Renovar JWT sense login novament
- **Rotació**: Nou token a cada renovació

---

## 5. FLUX DE BLOQUEIG PER FORÇA BRUTA

```
┌─────────────────────────────────┐
│ Intent 1-2: Credentials fallits │
│ → Mostrar error genèric         │
│ → Comptar 1 intent              │
│ → Esperar 2 segons              │
└──────────────┬──────────────────┘
               │
               ▼
        ┌──────────────┐
        │ 3r Intent    │
        │ incorrecte   │
        └──────┬───────┘
               │
               ▼
  ┌────────────────────────────────┐
  │ BLOQUEIG IMMEDIAT              │
  │ • Credencials guardades        │
  │ • Bloqueig registrat amb temps │
  │ • Mostrar:                     │
  │   "Compte blocat per 24h"      │
  │   "3 intents incorrectes"      │
  │   "Desbloqueja a:"             │
  │   🔗 seu.laplaceta.org/unlock  │
  │   ⏲️ Temps restant: 23h 47m   │
  └────────────────────────────────┘
```

---

## 6. MESURES DE SEGURETAT IMPLEMENTADES

✅ **Rate Limiting**: 3 intents per IP per 24h
✅ **HTTPS Obligatori**: Totes les redirects amb HTTPS
✅ **CSRF Protection**: State token verificat
✅ **Timing Attack Prevention**: Resposta constant (200ms)
✅ **Log Audit**: Tots els intents registrats
✅ **IP Blacklisting**: Bloqueig automàtic de força bruta
✅ ** 2FA Obligatori**: Nul·la autenticació sense 2FA
✅ **DIP Encriptada**: Emmagatzematge xifrat a BD

---

## 7. DISSENY DEL FLUX A NIVELL DE NAVEGADOR

### FASE 1: Redirecció Inicial
```
Usuario @ loteria.laplaceta.org
    ↓ Clica "Identificar"
Redirecció  → id.laplaceta.org/oauth/authorize?...
    ↓
PlacetaID Loads + Renderitza UI de Login
```

### FASE 2: Validació Credentials
```
UI PlacetaID (Frontend)
    ↓ User ingressa DIP + 2FA
POST /oauth/validate (AJAX)
    ↓ Backend valida
← Resposta: { success: true/false, errors: [...] }
    ↓
Si success → Mostrar countdown 3s
Si error → Mostrar missatge + camp fou refocus
```

### FASE 3: Redirecció Segura
```
After validation success:
    ↓
Backend genera JWT + Authorization Code
    ↓
302 Redirect amb token a query param
    ↓
Browser → loteria.laplaceta.org/callback?code=...&session_token=...
    ↓
Frontend de loteria emmagatzema token en localStorage
    ↓
✓ Usuari autenticat
```

