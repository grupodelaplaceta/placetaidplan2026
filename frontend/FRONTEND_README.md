# PlacetaID Frontend

Frontend moderno y seguro para el sistema de autenticación centralizado PlacetaID.

## 📁 Estructura del Proyecto

```
frontend/
├── index.html              # Landing page - Página de bienvenida
├── login.html              # Página de login - Formulario de autenticación
├── dashboard.html          # Panel de usuario - Gestión de cuenta y 2FA
├── static/
│   ├── css/
│   │   ├── style.css       # Estilos globales
│   │   ├── login.css       # Estilos específicos de login
│   │   ├── dashboard.css   # Estilos específicos del dashboard
│   │   └── index.css       # Estilos de la landing page
│   └── js/
│       ├── config.js       # Configuración centralizada
│       ├── utils.js        # Funciones utilitarias
│       ├── api-client.js   # Cliente HTTP para la API
│       ├── login.js        # Lógica de login
│       ├── dashboard.js    # Lógica del dashboard
│       └── index.js        # Lógica de la landing page
└── README.md               # Este archivo
```

## 🎨 Diseño y Responsividad

- **Desktop**: Optimizado para pantallas de 1200px en adelante
- **Tablet**: Adaptado para 768px a 1200px
- **Mobile**: Completamente responsive desde 320px

### Breakpoints CSS

```css
Mobile: 480px
Tablet: 768px
Desktop: 1200px
```

## 🌓 Modo Oscuro

El frontend incluye soporte completo para modo oscuro mediante:
- Variables CSS automáticas
- Media query `prefers-color-scheme: dark`
- Almacenamiento de preferencia del usuario

## 📄 Páginas

### 1. Landing Page (index.html)

- Introducción a PlacetaID
- Características de seguridad
- Cumplimiento normativo
- FAQ
- CTA (Call To Action) hacia login
- Footer con enlaces

**Características:**
- Hero section con gradiente
- Grid de características animadas
- Accordion FAQ interactivo
- Estadísticas de seguridad
- Formulario de contacto

### 2. Página de Login (login.html)

- Autenticación en dos pasos:
  1. Validación de DIP (4-4-1 dígitos)
  2. Validación de código TOTP (6 dígitos)

**Características:**
- Campos de entrada con auto-enfoque
- Validación de checksum de DIP
- Indicador visual de progreso
- Mensajes de error detallados
- Pantalla de éxito previa a redirección
- Botón atrás para reintentar

**DIP Input Format:**
```
XXXXXXXX-D-CHK
Ej: 12345678-A-23
```

**Validaciones:**
- Formato correcto
- Checksum según algoritmo español (módulo 23)
- Código TOTP válido (6 dígitos)

### 3. Panel de Usuario (dashboard.html)

- Perfil de usuario con información de cuenta
- Gestión de sesiones activas
- Setup y gestión de autenticación de dos factores
- Historial de actividad
- Botón de logout

**Características:**
- Verificación de autenticación al cargar
- Carga de perfil desde API
- Modal wizard para configurar 2FA
- Visualización de código QR
- Códigos de respaldo
- Administración de sesiones
- Auditoría de accesos

## 🔐 Seguridad

### Frontend Security

1. **HTTPS Obligatorio**
   - Solo conexiones encriptadas
   - Redirección automática en producción

2. **CSRF Protection**
   - Tokens de estado en OAuth2
   - Validación de origen

3. **XSS Prevention**
   - HTML escapeado en todas las salidas
   - Content Security Policy (CSP)
   - No uso de eval()

4. **Local Storage**
   - Solo tokens de sesión
   - Sin datos sensibles (DIP nunca se almacena)
   - Limpieza al logout

5. **Input Validation**
   - Validación en cliente (UX)
   - Validación en servidor (seguridad)
   - DIP checksum verification

## 🚀 Desarrollo

### Requisitos

- Navegador moderno (Chrome, Firefox, Safari, Edge)
- Servidor HTTP local (http-server, Live Server, etc.)
- Backend PlacetaID ejecutándose (http://localhost:5000)

### Servidor Local

Opción 1: Python
```bash
# Python 3
python -m http.server 8000

# Python 2
python -m SimpleHTTPServer 8000
```

Opción 2: Node.js (http-server)
```bash
npm install -g http-server
http-server
```

Opción 3: VS Code Live Server
```
Extensión: Live Server de Ritwick Dey
Click derecho en index.html → Open with Live Server
```

### Configuración de Desarrollo

Editar en [frontend/static/js/config.js](static/js/config.js):

```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:5000',  // URL del backend
    OAUTH_CLIENT_ID: 'placeta-web-client',
    OAUTH_REDIRECT_URI: 'http://localhost:8000/dashboard.html',
    // más configuración...
};
```

### Integración con Backend

El frontend se conecta al backend de Flask mediante:

1. **API Client** ([static/js/api-client.js](static/js/api-client.js))
   - Manejo centralizado de peticiones
   - Gestión de errores
   - Timeout automático (30s)

2. **Endpoints Utilizados**

```
POST /oauth/authorize
  Body: { dip: string, code?: string }
  Response: { requires_2fa, citizen_id, authorization_code }

POST /oauth/token
  Body: { code: string }
  Response: { access_token, refresh_token, expires_in }

GET /oauth/profile
  Headers: { Authorization: Bearer <token> }
  Response: { citizen_id, status, age_tier, created_at, last_login }

POST /oauth/2fa/enable
  Headers: { Authorization: Bearer <token> }
  Response: { secret, qr_code, is_generated }

POST /oauth/2fa/confirm
  Body: { code: string }
  Headers: { Authorization: Bearer <token> }
  Response: { backup_codes }

POST /oauth/2fa/disable
  Body: { code?: string }
  Headers: { Authorization: Bearer <token> }
  Response: { success }

POST /oauth/logout
  Headers: { Authorization: Bearer <token> }
  Response: { success }

GET /health
  Response: { status, timestamp }
```

## 📦 Dependencias

**Externas:** Ninguna ✨

El frontend es 100% vanilla JavaScript, HTML y CSS. No hay dependencias npm.

**Performance Benefits:**
- Carga más rápida
- Sin vulnerabilidades de dependencias
- Control total del código
- Compatible con cualquier navegador moderno

## 🎯 Funcionalidades

### Core Features

✅ **Autenticación de dos factores**
- DIP validation
- TOTP (Time-based One-Time Password)
- QR code generation
- Backup codes

✅ **Gestión de Sesiones**
- Token storage seguro
- Auto-logout en token expirado
- Refresh token rotation

✅ **UI/UX**
- Responsive design
- Dark mode support
- Animaciones suave
- Feedback en tiempo real

✅ **Seguridad**
- Validación de cliente
- HTTPS enforcement
- CORS handling
- Rate limiting awareness

## 🧪 Testing Manual

### Test Login Flow

1. Navegar a `/login.html`
2. Ingresar DIP válido: `12345678-A-23`
3. Ingresar código TOTP: `123456`
4. Verificar redirección a dashboard
5. Verificar token en localStorage

### Test Dashboard

1. Estar autenticado
2. Navegar a `/dashboard.html`
3. Verificar carga de perfil
4. Probar configurar 2FA
5. Probar deshabilitar 2FA
6. Probar logout

### Test Responsive

1. Abrir DevTools (F12)
2. Activar Device Emulation
3. Probar en:
   - iPhone 12 (390px)
   - iPad (768px)
   - Desktop (1920px)

## 🚢 Despliegue

### Vercel

1. Conectar repositorio a Vercel
2. Configurar build command: Ninguno (es estático)
3. Configurar output directory: `frontend`
4. Configurar variable de entorno `VITE_API_URL`

### Vercel vercel.json

```json
{
  "buildCommand": "",
  "outputDirectory": "frontend",
  "env": {
    "VITE_API_URL": "@placeta_api_url"
  }
}
```

### Docker

```dockerfile
FROM node:18-alpine AS base
WORKDIR /app
COPY frontend .
RUN npm install -g http-server

EXPOSE 8080
CMD ["http-server", "-p", "8080"]
```

### Nginx

```nginx
server {
    listen 80;
    server_name placetaid.com;
    
    root /var/www/placetaid/frontend;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # API proxy
    location /api {
        proxy_pass http://backend:5000;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Performance

### Lighthouse Scores (Objetivo)

- **Performance**: 95+
- **Accessibility**: 90+
- **Best Practices**: 90+
- **SEO**: 90+

### Optimizaciones

- CSS minificado
- JS sin dependencias (vanilla)
- Múltiples estilos para diferentes estados
- Lazy loading de imágenes (cuando aplique)
- Service Worker (opcional para PWA)

## 🐛 Troubleshooting

### "API connection refused"

- Verificar que backend está corriendo en `http://localhost:5000`
- Verificar CORS headers en backend
- Revisar URL en `config.js`

### "Invalid token" en dashboard

- Verificar que token existe en localStorage
- Verificar que token no ha expirado
- Válido: hace <1 hora
- Inválido: más viejo que TTL configurado

### "DIP format invalid"

- Verificar formato: `XXXXXXXX-D-CHK`
- Verificar checksum (módulo 23)
- Usar DIP de prueba: `12345678-A-23`

### "TOTP code not accepted"

- Verificar que código tiene 6 dígitos
- Verificar sincronización de reloj (NTP)
- Esperar al siguiente intervalo de 30s

## 📚 Documentación Adicional

- [API Backend](../backend/BACKEND_README.md)
- [Despliegue en Vercel](../VERCEL_DEPLOYMENT.md)
- [Arquitectura General](../docs/01-ARCHITECTURE.md)
- [Flujo OAuth2](../docs/02-OAUTH2_FLOW.md)
- [Seguridad](../docs/03-SECURITY.md)

## 📝 Notas de Desarrollo

### Convenciones de Código

- Usar camelCase para variables y funciones
- Usar CONST_NAME para constantes
- Comentarios en español
- Máximo 80 caracteres por línea en archivos CSS

### Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Compatibilidad

- ES6+ JavaScript
- CSS Grid y Flexbox
- LocalStorage API
- Fetch API
- Promises/async-await

## 🔄 Control de Versiones

```bash
# Dependencias de desarrollo
npm install --save-dev prettier eslint

# Formatear código
npm run format

# Linting
npm run lint

# Build (si fuera necesario)
npm run build
```

## 📄 Licencia

Parte del proyecto PlacetaID. Ver LICENSE en raíz del proyecto.

## ✍️ Autor

Desarrollado por GitHub Copilot
Año: 2024
