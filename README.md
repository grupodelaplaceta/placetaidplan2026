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

