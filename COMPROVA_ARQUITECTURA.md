# ✅ AUTOAVALUACIÓ - Entene la PlacetaID Arch?

Completa aquest quiz per verificar que has entès bé l'arquitectura.

## 📋 PREGUNTES DE CONCEPTES

### Nivell 1️⃣ - Conceptes Bàsics

**P1. Quin és el principal objectiu de PlacetaID?**
- [ ] Emmagatzemar totes les dades dels usuaris
- [✓] Actuar com a pasarela central per evitar que les webs externes vegin el DIP o 2FA
- [ ] Crear una xarxa social per a la Placeta
- [ ] Augmentar la velocitat de les webs externes

**P2. Per què el DIP mai surt de la UI de PlacetaID?**
- [✓] Per evitar que les webs externes malicioses o hackejades puguin robar identitats
- [ ] Perquè és més ràpid
- [ ] Perquè és més fàcil de programar
- [ ] No té motiu, és una decisió arbitrària

**P3. Quants intents de login es permeten per DIP?**
- [ ] 5 per dia
- [ ] 1 per hora
- [✓] 3 per 24 hores
- [ ] Sense límit si l'IP és diferent

**P4. Quant de temps dura un Authorization Code?**
- [ ] 1 hora
- [ ] 30 minuts
- [✓] 5 minuts
- [ ] 24 hores

**P5. Qui pot accedir a les dades de login correctes/fallides?**
- [ ] Totes les webs externes de la Placeta
- [ ] El registre públic de ciutadans
- [✓] Només el backend de PlacetaID i logs auditoria encriptats
- [ ] Qualsevol persona amb el nom de l'usuari

---

### Nivell 2️⃣ - Arquitectura i Seguretat

**P6. Quin algoritme s'usa per encriptar el DIP?**
- [✓] AES-256-GCM
- [ ] MD5
- [ ] Base64 (sense clau)
- [ ] Algsubreddit propietari de la competència

**P7. Com es valida el 2FA sense revelar el temps d'execució (timing attack)?**
- [✓] Comparació timing-safe (temps constant ~200ms sense importar si és correcte)
- [ ] Comparació normal amb if/else
- [ ] Hash segmentada
- [ ] No es prevé, confiem en que els atacants són lents

**P8. On es guardan els tokens JWT?**
- [ ] Base de dades MySQL
- [ ] Redis per sessions
- [ ] localStorage del navegador
- [✓] Tots els anteriors (MySQL per a verificació, Redis per performance, localStorage client)

**P9. Quina és la diferència entre Authorization Code i Access Token?**
- [✓] Code: temporal (5min), single-use, per intercanviar per JWT. Token: JWT vàlid 24h
- [ ] No hi ha diferència
- [ ] Code es per frontend, Token per backend
- [ ] Token s'usa per 2FA, Code per first login

**P10. Per què la UI és a id.laplaceta.org i no a altres dominis?**
- [✓] Per donar confiança als usuaris: saben que si la URL no és aquesta, no és oficial
- [ ] Per la tradició
- [ ] Per les estadístiques DNS
- [ ] No té raó, podria ser qualsevol lloc

---

### Nivell 3️⃣ - Implementació i Endpoints

**P11. Quin HTTP status es retorna si es supera el rate limit?**
- [ ] 400 Bad Request
- [ ] 401 Unauthorized
- [✓] 429 Too Many Requests
- [ ] 503 Service Unavailable

**P12. Quins camps es retornen al endpoint `/user/profile`?**
- [ ] DIP, password, 2FA secret
- [✓] nom, nom, age_tier, email, phone (sense DIP ni 2FA)
- [ ] Tota la BD del usuario
- [ ] Cap camp, és un endpoint admin

**P13. Com s'estructura un JWT?**
- [✓] header.payload.signature (base64.base64.base64)
- [ ] payload solament en base64
- [ ] payload + signature encriptada
- [ ] JSON emmagatzemat a BD

**P14. Quin algoritme s'usa per signar el JWT?**
- [ ] HMAC-SHA256
- [✓] RSA-256 (clau privada del servidor)
- [ ] El navegador la signa amb la clau pública
- [ ] Sense signatura, confiem en l'origen

**P15. Quin és el grant_type per intercanviar Authorization Code per JWT?**
- [ ] 'password'
- [ ] 'client_credentials'
- [✓] 'authorization_code'
- [ ] 'implicit'

---

### Nivell 4️⃣ - Detalls de Seguretat

**P16. Si algun atacant detecta el teu token JWT, com pot revolucionar-se?**
- [ ] Decodificant-lo (base64), ja que JWT estava clar
- [ ] Usant-lo directament per a requests autenticats
- [ ] Poent-lo en altre navegador
- [✓] Totes les anteriors (JWT és vàlid 24h si no es revoca)

**P17. Com es mitiga el risc del token compromès?**
- [ ] No es mitiga, és inevitable
- [✓] Rate limiting de renovacions, invalidació de sessions, audit logging, revocation list
- [ ] Agafant-lo cada 5 segons
- [ ] Demanant 2FA per cada request

**P18. Quina informació es guarda en l'audit log?**
- [✓] Totes: intents, logins, logouts, tokens revocats, IP, user-agent
- [ ] Solament logins exitosos
- [ ] Res, la privacitat és més important que l'auditoria
- [ ] Solament els errors

**P19. Si l'usuari perd accés al generador 2FA, com pot recuperar l'accés?**
- [ ] No pot, és compte per sempre
- [✓] Contactant la seu electrònica que verifica l'identitat i genera nou secret
- [ ] Demanant SMS backup (si ha config SMS)
- [ ] Contactant al admin per email (sense verificació)

**P20. Quant de temps es bloqueja un compte després de 3 intents fallits?**
- [ ] 15 minuts
- [ ] 1 hora
- [✓] 24 hores
- [ ] Permanent fins desbloqueig manual

---

## 📊 Marcador

**Enviat correctes** / **Total**: _____ / 20

```
16-20: ✅ EXPERT - Pots implementar solamente o revisar arquitectura
12-15: ⚠️  INTERMEDI - Comprens bien la arquitectura, need some refresher
10-11: 📚 PRINCIPIANT - Rellegeix la documentació, especially ARQUITECTURA.md
<10:  ❌ RECOMIENDA LECTURA - Start with README.md i DISSENY_UI.md
```

---

## 🎯 RESPOSTES CORRECTES

<details>
<summary>📖 Click per veure respostes</summary>

**P1**: B - No és un emmagatzem genéric, és una pasarela segura  
**P2**: A - Protecció contra webs externes compromeses  
**P3**: C - 3 per 24h és estàndard de força bruta  
**P4**: C - 5 minuts per limitar finestra de reutilització  
**P5**: C - Confinament total dels logs sensibles  

**P6**: A - AES-256 és estàndard militar  
**P7**: A - Timing-safe comparison prevé timing attacks  
**P8**: D - Alterna de performance: MySQL per auditoria, Redis per sessions, localStorage client  
**P9**: A - Concepte central d'OAuth2  
**P10**: A - Confiança de marca per al usuari  

**P11**: C - HTTP 429 és estàndard REST per rate limit  
**P12**: B - Mai no retorna secrets ni DIP  
**P13**: A - Format base64.base64.base64  
**P14**: B - RSA privada del servidor (no client-verifiable)  
**P15**: C - OAuth2 standard per Authorization Code flow  

**P16**: B+C - JWT pot ser ús immediatament si no expirat  
**P17**: C - Multiple layers: rate limit, revocation, audit  
**P18**: A - Auditoria complet és critical per forensics  
**P19**: B - Seu electrònica amb verificació de identitat  
**P20**: C - 24h és estàndard UX per força bruta  

</details>

---

## 🔍 ESCENARIS PRÀCTICS

### Escenari 1: Força Bruta Detection

**Situació**: Un atacant fa 15 intents fallits en 5 minuts desde l'IP 192.168.1.100

**Què hauria de passar?**
```
1. Intents 1-2:    ✓ Log, rate limit counter increment
2. Intent 3:       ✗ Response genèric error
3. Intents 4-15:   ✗ HTTP 429 "Too Many Requests"
4. IP blocked:     ✓ Afegida a blocklist 5 minuts
5. Email admin:    ✓ Alert suspicious activity

✓ CORRECTE si totes les acciones es donen
```

### Escenari 2: Token Theft

**Situació**: Algun aconsegueix el JWT d'en Joan (accidentalment exposed en git)

**Que passa?**
```
1. Atacant usa token:        ✓ Funciona (JWT vàlid 24h)
2. Accés dados verificat:    ✓ Acceptat com a valide
3. Audit log registrat:      ✓ Diferent IP/User-agent
4. Mitiga el risc:
   - João fa logout:         ✓ Revoca totes sessions
   - Admin detecta:          ✓ Patró anomal a audit
   - Token expirat en:       24h màximum

⚠️  VULNERABILITAT REAL
    - Mitigació: Short token lifetime, device fingerprinting, anomaly detection
```

### Escenari 3: Account Lockout Recovery

**Situació**: User Joan ha fet 3 intents fallits i está blocat

**Procés de recuperació:**
```
1. Joan contacta suport      ✓ seu.laplaceta.org
2. Verifica identitat:       ✓ Preguntes de seguretat o DNI
3. Sistema genera:           ✓ unlock_token únic
4. Email amb link:           ✓ seu.laplaceta.org/unlock?token=xyz
5. Joan fa click:            ✓ UPDATE account_lockouts SET locked_until=NOW()-1min
6. Joan pot intentar login:  ✓ Compte desblocat

✓ CORRECTE si totes les esteps se fan amb verificació
```

### Escenari 4: DIP Validation

**Situació**: Frontend envia DIP "1234-5678-A", backend ha de validar

**Passos backend:**
```
1. Format validation:        ✓ 4 dígits-4 dígits-1 letra
2. DIP checksum:             ✓ Calcula (1234567 % 23) = letra correcta?
3. Rate limit check:         ✓ Comprovar max intents per this IP
4. Hash DIP:                 ✓ SHA256(salt + dip)
5. Lookup:                   ✓ SELECT FROM citizens WHERE dip_hash = ?
6. Match found:              ✓ Proceed to 2FA validation
7. Otherwise:                ✓ Log attempt, return generic error

✓ CORRECTE si no retorna "DIP not found" (timing attack!)
```

---

## 🚨 ERRORES COMUNS A EVITAR

### ❌ ERROR 1: Retornar "DIP not found"
```python
# MAL ❌
if not citizen:
    return {'error': 'user_not_found'}  # Timing attack!
```

```python
# BÉ ✓
return {'error': 'invalid_credentials'}  # Always same response time
```

### ❌ ERROR 2: Gardar el DIP en plain text
```sql
-- MAL ❌
INSERT INTO users (dip) VALUES ('1234-5678-A');

-- BÉ ✓
INSERT INTO citizens (dip_encrypted, dip_hash) VALUES (AES_ENCRYPT(...), SHA256(...));
```

### ❌ ERROR 3: Permetre més de 3 intents sense bloqueig
```python
# MAL ❌
if failed_attempts > 100:  # Too high!
    lock_account()

# BÉ ✓
if failed_attempts >= 3:  # Aggressive, but standard
    lock_account()
```

### ❌ ERROR 4: No verificar state token (CSRF)
```python
# MAL ❌
def authorize():
    return render_template('login.html')  # No state checking!

# BÉ ✓
def authorize():
    state = request.args.get('state')
    redis.setex(f"oauth_state:{state}", 300, '1')
    return render_template('login.html', state=state)
```

### ❌ ERROR 5: Passar DIP en URL query parameter
```
# MAL ❌
GET /oauth/validate?dip=1234&2fa=123456
# Exposed in browser history + server logs!

# BÉ ✓
POST /oauth/validate
{ "dip": "...", "code_2fa": "..." }
# Sent in POST body + HTTPS
```

---

## 📚 RESURSOS PER APRENDRE MÉS

### Sobre OAuth2
- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)
- [Auth0 OAuth2 Guide](https://auth0.com/intro-to-iam/what-is-oauth-2)

### Sobre Seguretat
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/)

### Sobre Criptografia
- [Cryptography.io](https://cryptography.io/)
- [NIST on Encryption](https://csrc.nist.gov/)

### Sobre API Design
- [REST API Best Practices](https://restfulapi.net/)
- [API Security Checklist](https://github.com/shieldfy/API-Security-Checklist)

---

## ✅ Valida que:

- [ ] Entenc el flux OAuth2 principal
- [ ] Sé per qué el DIP mai surt de PlacetaID
- [ ] Comprenc el rate limiting multinivell
- [ ] Sé com s'encripta el DIP
- [ ] Entenc la validació timing-safe
- [ ] Sé com funcionan els Authorization Codes
- [ ] Sé que JWT es signat amb clau privada
- [ ] Comprenc el bloqueig per força bruta (3 intents / 24h)
- [ ] Sé com recuperar un compte blocat
- [ ] Entenc el flujo completo end-to-end

---

**Si has respost correctament > 16 preguntes**, passat a la secció de **Implementation**!
**Si has respost < 12 preguntes**, recomanem rellegir [ARQUITECTURA.md](docs/ARQUITECTURA.md).

