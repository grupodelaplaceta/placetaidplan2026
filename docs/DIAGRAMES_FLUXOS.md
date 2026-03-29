# DIAGRAMES I FLUXOS VISUALS

## 1. FLUX PRINCIPAL D'AUTENTICACIÓ (Diagrama Sequence)

```mermaid
sequenceDiagram
    participant User as 👤 Usuario
    participant WebExt as 🌐 loteria.org
    participant Gateway as 🔐 id.laplaceta.org
    participant Backend as 🐍 Backend API
    participant DB as 🗄️ MySQL DB
    participant Cache as 💾 Redis

    User->>WebExt: 1. Clica "Identificar"
    activate WebExt
    WebExt->>Gateway: 2. Redirect a /oauth/authorize
    activate Gateway
    
    Gateway->>Gateway: 3. Valida client_id & redirect_uri
    Gateway->>User: 4. Renderitza login form
    deactivate Gateway
    
    User->>Gateway: 5. Envia DIP + 2FA
    activate Gateway
    
    Gateway->>Backend: 6. POST /oauth/validate
    activate Backend
    
    Backend->>DB: 7. Query citizens per DIP hash
    activate DB
    DB-->>Backend: Data citizen
    deactivate DB
    
    Backend->>Backend: 8. Validar 2FA (timing-safe)
    Backend->>Cache: 9. Comprovar rate limit
    activate Cache
    Cache-->>Backend: OK o BLOCKED
    deactivate Cache
    
    alt 2FA Valid
        Backend->>DB: 10. Insert authorization code
        activate DB
        DB-->>Backend: Code stored
        deactivate DB
        
        Backend->>Backend: 11. Generate JWT
        Backend-->>Gateway: { access_token, redirect_uri }
    else 2FA Invalid
        Backend->>DB: 10a. Log failed attempt
        Backend-->>Gateway: { error: 'invalid_credentials' }
    end
    
    deactivate Backend
    Gateway-->>User: 12. HTTP 302 redirect
    deactivate Gateway
    
    User->>WebExt: 13. Redirigit via callback
    WebExt->>Gateway: 14. POST /oauth/token { code }
    activate Gateway
    
    Gateway->>Backend: 15. Validate & exchange code
    activate Backend
    Backend->>DB: 16. Validate code
    DB-->>Backend: Code valid
    Backend->>DB: 17. Mark code as used
    Backend-->>Gateway: JWT token
    deactivate Backend
    
    Gateway-->>WebExt: { access_token }
    deactivate Gateway
    
    WebExt-->>User: 16. ✅ Login complete!
    deactivate WebExt

    rect rgb(200, 150, 255)
    Note over User,WebExt: DIP i 2FA NUNCA sortixen de Gateway!
    end
```

## 2. ARQUITECTURA DE SEGURETAT (Diagrama C4)

```mermaid
graph TB
    subgraph "🌐 Client Layer"
        WEB1["loteria.laplaceta.org"]
        WEB2["notaries.laplaceta.org"]
    end
    
    subgraph "🔐 PlacetaID Gateway (id.laplaceta.org)"
        UI["📄 HTML/CSS/JS<br/>Frontend"]
        CSRF["🛡️ CSRF Protection<br/>State Tokens"]
        FORM["📋 Login Form"]
        
        subgraph "Backend API (Python/Flask)"
            AUTH["🔑 Auth Service"]
            TOKEN["🎟️ Token Service"]
            RATE["📊 Rate Limiter"]
            ENCR["🔐 Encryption/Hashing"]
        end
        
        MIDDLEWARE["Middleware<br/>- HTTPS/TLS 1.3<br/>- Rate Limit<br/>- Logging"]
    end
    
    subgraph "💾 Storage"
        DB["MySQL Database<br/>- Citizens<br/>- Tokens<br/>- Lockouts<br/>- Audit Logs"]
        CACHE["Redis Cache<br/>- Rate Limits<br/>- Sessions<br/>- Revocation List"]
    end
    
    WEB1 -.->|OAuth Redirect| FORM
    WEB2 -.->|OAuth Redirect| FORM
    
    FORM -->|DIP + 2FA| CSRF
    CSRF -->|Validat| UI
    UI -->|POST /validate| AUTH
    AUTH -->|Rate Check| RATE
    AUTH -->|Encript/Hash| ENCR
    AUTH -->|Query| DB
    RATE -->|Store/Check| CACHE
    ENCR -->|Verify| DB
    AUTH -->|Generate JWT| TOKEN
    TOKEN -->|Return Token| UI
    
    UI -.->|Redirect w/ Code| WEB1
    UI -.->|Redirect w/ Code| WEB2
    
    MIDDLEWARE ---| Proteccions| AUTH
    MIDDLEWARE ---| Headers| WEB1
    MIDDLEWARE ---| Headers| WEB2
    
    style FORM fill:#ff6b6b
    style AUTH fill:#4ecdc4
    style DB fill:#45b7d1
    style CACHE fill:#f9ca24
```

## 3. FLUX DE BLOQUEIG PER FORÇA BRUTA

```mermaid
graph TD
    A["Intent 1-2<br/>Credencials Fallits"] -->|Error genèric| B["Mostrar Error<br/>I/3 intents"]
    
    C["Intent 3<br/>Fallit"] -->|Rate Limit| D{"Redis Check<br/>Failed Count?"}
    
    D -->|< 3| E["Mostrar Error<br/>2/3 intents"]
    D -->|>= 3| F["🚫 BLOQUEIG IMMEDIAT"]
    
    F --> G["INSERT account_lockouts<br/>locked_until = NOW + 24h"]
    G --> H["Log AUDIT_EVENT<br/>ACCOUNT_LOCKED"]
    H --> I["UI mostra<br/>🔒 Compte blocat"]
    I --> J["Mostrar opcionas:<br/>- Espera 24h<br/>- Contacta suport<br/>seu.laplaceta.org/unlock"]
    
    K["Usuario contacta suport"] -->|Email/Telèfon| L["Seu Electrònica"]
    L -->|Verifica identitat| M["Generar unlock token"]
    M -->|Email link| N["Usuario fa click"]
    N -->|GET /admin/unlock?token=| O["UPDATE account_lockouts<br/>locked_until = NOW - 1min"]
    O --> P["✅ Compte desblocat"]
    P --> Q["Usuario pot intentar login"]
    
    style F fill:#ff6b6b,color:#fff
    style P fill:#51cf66,color:#fff
    style J fill:#ffd43b,color:#000
```

## 4. CICLE DE VIDA DE TOKENS

```mermaid
stateDiagram-v2
    [*] --> Authorization: /oauth/authorize
    
    Authorization --> Form: Genera state token
    Form --> Validate: Usuario introdueix credentials
    
    Validate --> CodeGenerated: 2FA correcta
    CodeGenerated --> CodeExpires: 5 minuts
    CodeExpires --> [*]: Expirat sense usar
    
    CodeGenerated --> TokenExchange: POST /oauth/token
    TokenExchange --> JWT: Genera JWT (24h)
    
    JWT --> Active: Token actiu
    Active --> Refresh: Usuari demana renovació
    Refresh --> NewJWT: Nova token generada
    NewJWT --> Active
    
    Active --> Logout: Usuario fa logout
    Logout --> Revoked: Afegit a revocation list
    Revoked --> [*]: Expirat (24h més)
    
    Active --> Expired: 24 hores passes
    Expired --> [*]: Espirat, requereix login
```

## 5. ESTRUCTURA DE JWT

```mermaid
graph LR
    subgraph "JWT Token"
        HEADER["📋 HEADER<br/>{ alg: RS256, typ: JWT }"]
        PAYLOAD["📦 PAYLOAD<br/>{ sub, nom, age_tier, exp }"]
        SIGN["✍️ SIGNATURE<br/>RSA256(header.payload,key)"]
    end
    
    HEADER -->|base64| HEADER64["eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9"]
    PAYLOAD -->|base64| PAYLOAD64["eyJzdWIiOiJjaXRpemVuXzEyMzQ1In0="]
    SIGN -->|RSA| SIGN64["SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"]
    
    HEADER64 -->|dot| FINAL["eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjaXRpemVuXzEyMzQ1In0=.SflKxwRJ..."]
    PAYLOAD64 -->|dot| FINAL
    SIGN64 -->|dot| FINAL
    
    FINAL -->|Enviat a Client| USAGE["localStorage.setItem('auth_token', jwt)"]
    
    style HEADER fill:#ff6b6b
    style PAYLOAD fill:#4ecdc4
    style SIGN fill:#f9ca24
```

## 6. MATRIU DE SEGURETAT - Rate Limiting

```mermaid
graph LR
    subgraph "L1 [IP Global]"
        L1A["20 req/min<br/>per IP"]
        L1B["Bloqueig 5min"]
    end
    
    subgraph "L2 [DIP Specific]"
        L2A["3 intents/24h<br/>per DIP"]
        L2B["Bloqueig 24h"]
    end
    
    subgraph "L3 [OAuth Client]"
        L3A["1000 req/hora<br/>per client"]
        L3B["HTTP 429"]
    end
    
    subgraph "L4 [Session]"
        L4A["10 renovacions/dia"]
        L4B["Re-auth requerida"]
    end
    
    REQ["Request Incoming"]
    -->|Avalua| L1A
    L1A -->|Fallida| L1B
    L1B -->|Bloqueig| DENY["❌ REJECTED"]
    
    L1A -->|Passa| L2A
    L2A -->|Fallida| L2B
    L2B -->|Bloqueig| DENY
    
    L2A -->|Passa| L3A
    L3A -->|Failida| L3B
    L3B -->|Error| DENY
    
    L3A -->|Passa| L4A
    L4A -->|Failida| L4B
    L4B -->|Error| DENY
    
    L4A -->|Passa| ALLOW["✅ ALLOWED<br/>Process Request"]
    
    style DENY fill:#ff6b6b,color:#fff
    style ALLOW fill:#51cf66,color:#fff
```

## 7. RESPONSIBILITATS PER CAPA

```mermaid
graph TB
    subgraph "🌐 Frontend (HTML/CSS/JS)"
        F1["✓ Mostrar form de login"]
        F2["✓ Validar format en client"]
        F3["✓ Auto-focus entre camps"]
        F4["✓ Mostrar countdown 2FA"]
        F5["✗ NO conservar DIP ni 2FA"]
    end
    
    subgraph "🔐 Gateway Backend"
        B1["✓ Validar format DIP"]
        B2["✓ Validar 2FA timing-safe"]
        B3["✓ Rate limiting check"]
        B4["✓ Generar JWT signat"]
        B5["✗ NO retornar DIP ni 2FA en resposta"]
    end
    
    subgraph "💾 Database"
        D1["✓ DIP xifrat + hash"]
        D2["✓ Almacenar tokens"]
        D3["✓ Log de totes les acciones"]
        D4["✓ Índexos per performance"]
        D5["✗ NO guardar 2FA code"]
    end
    
    subgraph "🌐 Web Externa"
        W1["✓ Guardar JWT en localStorage"]
        W2["✓ Validar state token"]
        W3["✓ Usar JWT per totes les requests"]
        W4["✗ NO contactar directament citizens BD"]
    end
    
    F1 -->|HTTP POST| B1
    B1 -->|Query| D1
    B4 -->|Token| W1
    W1 -->|Bearer JWT| B3
    B3 -->|Check| D2
    
    style F5 fill:#ff6b6b,color:#fff
    style B5 fill:#ff6b6b,color:#fff
    style D5 fill:#ff6b6b,color:#fff
    style W4 fill:#ff6b6b,color:#fff
```

## 8. PÀGINA DE LOGIN - Wireframe

```
┌────────────────────────────────────────────────┐
│                                                │
│  ┌─────────────────────────────────────────┐  │
│  │         🔐 PlacetaID                   │  │
│  │  Identificació Segura de la Placeta   │  │
│  └─────────────────────────────────────────┘  │
│                                               │
│  ┌─────────────────────────────────────────┐  │
│  │ Has sol·licitat accés de:              │  │
│  │ 📍 loteria.laplaceta.org              │  │
│  └─────────────────────────────────────────┘  │
│                                               │
│  ┌─────────────────────────────────────────┐  │
│  │ 📋 DIP (Document d'Identitat)         │  │
│  │ [____] - [____] - [_]                 │  │
│  │                                        │  │
│  │ 🔐 Codi 2FA (6 dígits)                │  │
│  │ [___] [___]                           │  │
│  │                                        │  │
│  │ ⚠️  Teus dades no s'emmagatzen       │  │
│  │                                        │  │
│  │ ┌────────────────────────────────┐   │  │
│  │ │ 🔵 VALIDAR I ACCEDIR           │   │  │
│  │ └────────────────────────────────┘   │  │
│  │                                        │  │
│  │ [?] No tinc 2FA  |  [🆘] Problemes  │  │
│  └─────────────────────────────────────────┘  │
│                                               │
│ Privacitat | Termes | Seguretat | Contacte  │
│                                               │
└────────────────────────────────────────────────┘
```

## 9. ERROR STATES - Pantallas

```mermaid
graph TB
    subgraph "Attempt 1-2"
        E1["❌ Credencials Incorrectes<br/>(Attempt 1/3)"]
    end
    
    subgraph "Attempt 3"
        E2["❌ Credencials Incorrectes<br/>COMPTE BLOCAT"]
        E2 --> E3["Timer: 23h 47m 12s"]
        E3 --> E4["Link: seu.laplaceta.org/unlock"]
    end
    
    subgraph "Lockout State"
        E5["🔒 Compte Temporalment Blocat"]
        E5 --> E6["Raó: 3 intents fallits"]
        E6 --> E7["Blocat fins: 30/03/2026 14:32"]
        E7 --> E8["Opcions:<br/>1. Espera 24h<br/>2. Contacta suport<br/>3. Report fraude"]
    end
    
    E1 -.->|Mostra error genèric| E1
    E1 -->|3r intent| E2
    E2 -->|Immediatament| E5
```

## 10. FLUXO DE DADES - End to End

```mermaid
graph LR
    USER["👤 Usuario"]
    USER -->|1. Click Login| WEBEXT["🌐 Web Externa"]
    WEBEXT -->|2. Redirect| GATEWAY["🔐 PlacetaID Gateway"]
    
    GATEWAY -->|3. HTML Form| BROWSER["🌐 Browser"]
    BROWSER -->|4. DIP + 2FA| GATEWAY
    
    GATEWAY -->|5. Validate| BACKEND["🐍 Backend"]
    BACKEND -->|6. Query| DB["🗄️ MySQL DB"]
    DB -->|7. Return Data| BACKEND
    
    BACKEND -->|8. Generate JWT| CACHE["💾 Redis"]
    CACHE -->|9. Store Session| CACHE
    
    BACKEND -->|10. Return Token| GATEWAY
    GATEWAY -->|11. Redirect| WEBEXT
    WEBEXT -->|12. Save Token| BROWSER
    
    BROWSER -->|13. API Calls| WEBEXT
    WEBEXT -->|14. Validate Token| BACKEND
    BACKEND -->|15. Return Data| WEBEXT
    WEBEXT -->|16. Show Content| USER
    
    style USER fill:#e1f5ff
    style GATEWAY fill:#c8e6c9
    style BACKEND fill:#fff9c4
    style DB fill:#ffccbc
    style CACHE fill:#f0f4c3
    style WEBEXT fill:#dcedc8
```

---

**Nota**: Aquests diagrames es poden renderitzar usant:
- **Mermaid Viewer**: https://mermaid.live
- **VS Code Extension**: Markdown Preview Mermaid Support
- **Confluence/Jira**: Integració nativa Mermaid

