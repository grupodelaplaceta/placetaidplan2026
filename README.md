# PlacetaID - Pasarela de Identificació Centralitzada

## 📋 Descripció General

PlacetaID és una pasarela d'autenticació segura i centralizada que actua com a node d'identificació per a tots els serveis de la Placeta. El sistema garanteix que les dades sensibles (DIP i codi 2FA) **mai** es comparteixen amb les webs externes.

## 🎯 Principis de Seguretat

- ✅ **Aïllament Total**: Les webs externes mai veuen credentials
- ✅ **Control Centralitzat**: Un únic servei gestiona autenticació
- ✅ **Protecció de Marca**: UI cohesionada a totes les plataformes
- ✅ **Domini Segur**: URL verificable (id.laplaceta.org)
- ✅ **Gestió de Intents**: Control de força bruta amb bloqueigs

## 📁 Estructura del Projecte

```
plid/
├── docs/                 # Documentació
│   ├── ARQUITECTURA.md   # Especificació tècnica
│   ├── FLUXOS.md         # Diagrames de fluxo
│   └── SEGURETAT.md      # Política de seguretat
├── database/             # Scripts SQL i esquema
│   ├── schema.sql        # Estructura de taules
│   └── procedures.sql    # Procediments emmagatzemats
├── backend/              # API REST
│   ├── config/           # Configuració
│   ├── controllers/      # Endpoints
│   ├── middleware/       # Seguretat i validació
│   └── models/           # Esquema de dades
├── frontend/             # UI de PlacetaID
│   ├── public/           # Assets estàtics
│   ├── pages/            # Pantallas
│   ├── components/       # Components reutilitzables
│   └── styles/           # CSS responsiu
└── README.md
```

## 🔐 Sessions de Seguretat

1. Web Externa → Redirecció a PlacetaID
2. PlacetaID recull DIP + 2FA (no es guarda a sesió)
3. Backend valida contra BD de ciutadans
4. Generació de JWT + State Token
5. Redirecció a web original amb Token
6. Web valida token a backend de PlacetaID

## 🔧 Configuració segura amb .env i Vercel

- Crea `.env` a l'entorn local amb clau secretes i no la pujes a Git.
- El projecte ja inclou `.env.example` amb els noms de variables.
- Instala `dotenv-safe` (backend Node.js):
  - `npm install dotenv-safe`
  - `require('dotenv-safe').config();`
- Exemple `package.json` scripts:
  - `"start": "node server.js"`
  - `"dev": "nodemon server.js"`

## 📦 Deploy a Vercel (variables d'entorn)

- `vercel env add DATABASE_URL production`
- `vercel env add OAUTH_CLIENT_ID production`
- `vercel env add OAUTH_CLIENT_SECRET production`
- `vercel env add API_BASE_URL production`
- Consulteu `vercel env ls`

## 🛡️ Responsabilitat

No incloure secrets al frontend ni en commit. Utilitzeu `git-crypt` / `sops` / KeyVault per dades sensibles a CI/CD.

