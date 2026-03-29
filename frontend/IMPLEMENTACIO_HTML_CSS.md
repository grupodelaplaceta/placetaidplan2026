# IMPLEMENTACIÓ FRONTEND - HTML/CSS/JavaScript

## 📄 templates/login.html

```html
<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="theme-color" content="#0052CC">
    <meta name="description" content="PlacetaID - Identificació segura de La Placeta">
    
    <title>PlacetaID - Autenticació Segura</title>
    
    <!-- Favicons -->
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
    
    <!-- Styles -->
    <link rel="stylesheet" href="/static/css/reset.css">
    <link rel="stylesheet" href="/static/css/theme.css">
    <link rel="stylesheet" href="/static/css/login.css">
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body data-app-name="{{ app_name }}">
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/>
                    <path d="M12 6c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6z" fill="currentColor"/>
                </svg>
                <span class="logo-text">PlacetaID</span>
            </div>
            <h1 class="title">Identificació Segura de la Placeta</h1>
        </header>

        <!-- Main Content -->
        <main class="main">
            <!-- Información de la aplicación -->
            <div class="app-info" role="region" aria-label="Informació de l'aplicació">
                <svg class="app-icon" width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/>
                </svg>
                <div class="app-details">
                    <p class="app-context">
                        Has sol·licitat accés de seguretat des de:
                    </p>
                    <p class="app-name" aria-label="Aplicació: {{ app_name }}">
                        📍 {{ app_name }}
                    </p>
                </div>
            </div>

            <!-- Formularà de Login -->
            <form id="loginForm" class="login-form" method="POST" action="/oauth/validate">
                
                <!-- CSRF Token -->
                <input type="hidden" name="_csrf_token" value="{{ csrf_token }}" required>

                <!-- Secció 1: DIP -->
                <fieldset class="form-group">
                    <legend class="form-legend">
                        <label for="dipInput1" class="label-main">
                            📋 DIP (Document d'Identitat Personal)
                        </label>
                        <span class="form-hint">Número de 9 dígits amb formatat 1234-5678-A</span>
                    </legend>

                    <div class="input-group dip-input">
                        <input 
                            type="text" 
                            id="dipInput1" 
                            name="dipSegment1" 
                            class="dip-segment"
                            placeholder="____"
                            maxlength="4"
                            inputmode="numeric"
                            autocomplete="off"
                            required
                            aria-label="DIP - primers 4 dígits"
                        >
                        <span class="separator">-</span>
                        
                        <input 
                            type="text" 
                            id="dipInput2" 
                            name="dipSegment2" 
                            class="dip-segment"
                            placeholder="____"
                            maxlength="4"
                            inputmode="numeric"
                            autocomplete="off"
                            required
                            aria-label="DIP - següents 4 dígits"
                        >
                        <span class="separator">-</span>
                        
                        <input 
                            type="text" 
                            id="dipInput3" 
                            name="dipSegment3" 
                            class="dip-segment"
                            placeholder="_"
                            maxlength="1"
                            inputmode="text"
                            autocomplete="off"
                            required
                            aria-label="DIP - lletres de control"
                        >
                    </div>

                    <div class="input-info">
                        <svg class="icon-info" width="16" height="16" viewBox="0 0 24 24">
                            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
                            <text x="12" y="16" text-anchor="middle" font-size="12" font-weight="bold">i</text>
                        </svg>
                        <span class="info-text">Exemple: 1234-5678-A</span>
                    </div>
                </fieldset>

                <!-- Divider -->
                <div class="form-divider"></div>

                <!-- Secció 2: 2FA -->
                <fieldset class="form-group">
                    <legend class="form-legend">
                        <label for="totp2faInput" class="label-main">
                            🔐 Codi d'Autenticador (2FA)
                        </label>
                        <span class="form-hint">Codi de 6 dígits del teu generador</span>
                    </legend>

                    <!-- Tabs: TOTP / SMS / Email -->
                    <div class="auth-tabs" role="tablist">
                        <button 
                            type="button"
                            role="tab"
                            aria-selected="true"
                            aria-controls="totp-panel"
                            data-tab="totp"
                            class="tab-button active"
                        >
                            🔄 Generador (TOTP)
                        </button>
                        <button 
                            type="button"
                            role="tab"
                            aria-selected="false"
                            aria-controls="sms-panel"
                            data-tab="sms"
                            class="tab-button"
                        >
                            📱 SMS
                        </button>
                        <button 
                            type="button"
                            role="tab"
                            aria-selected="false"
                            aria-controls="email-panel"
                            data-tab="email"
                            class="tab-button"
                        >
                            📧 Email
                        </button>
                    </div>

                    <!-- TOTP Panel (Default) -->
                    <div id="totp-panel" role="tabpanel" class="tab-panel active">
                        <div class="input-wrapper">
                            <input 
                                type="text" 
                                id="totp2faInput" 
                                name="code_2fa" 
                                class="totp-input"
                                placeholder="______"
                                maxlength="6"
                                inputmode="numeric"
                                autocomplete="off"
                                required
                                aria-label="Codi TOTP de 6 dígits"
                            >
                            <div class="code-timer">
                                <span class="timer-dot"></span>
                                <span class="timer-text" aria-label="Temps de validació del codi">30s</span>
                            </div>
                        </div>
                        <p class="tab-hint">
                            Els codis es renoven cada 30 segons. 
                            <a href="/help/totp-setup" class="link-help">Com configurar TOTP?</a>
                        </p>
                    </div>

                    <!-- SMS Panel -->
                    <div id="sms-panel" role="tabpanel" class="tab-panel">
                        <p class="sms-number">📞 +34 *** *** 678</p>
                        <button type="button" class="btn-send-code" id="sendSmsBtn">
                            Enviar codi per SMS
                        </button>
                        <input 
                            type="text" 
                            name="code_sms" 
                            class="code-input"
                            placeholder="000000"
                            maxlength="6"
                            inputmode="numeric"
                            style="display: none;"
                        >
                        <p class="tab-hint">Ràpid i segur. Rebràs un codi de 6 dígits.</p>
                    </div>

                    <!-- Email Panel -->
                    <div id="email-panel" role="tabpanel" class="tab-panel">
                        <p class="email-address">📧 j***.m***@*.com</p>
                        <button type="button" class="btn-send-code" id="sendEmailBtn">
                            Enviar codi per email
                        </button>
                        <input 
                            type="text" 
                            name="code_email" 
                            class="code-input"
                            placeholder="000000"
                            maxlength="6"
                            inputmode="numeric"
                            style="display: none;"
                        >
                        <p class="tab-hint">Rebràs un codi de 6 dígits. Pot tardar fins a 2 minuts.</p>
                    </div>
                </fieldset>

                <!-- Advertència de Seguretat -->
                <div class="security-notice" role="region" aria-label="Avís de seguretat">
                    <svg class="icon-shield" width="20" height="20" viewBox="0 0 24 24">
                        <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z" stroke="currentColor" fill="none"/>
                    </svg>
                    <div class="notice-content">
                        <strong>La seguretat comença aquí</strong>
                        <ul class="notice-list">
                            <li>✓ Els teus dades no s'emmagatzemen al navegador</li>
                            <li>✓ Només validem i redirigim de forma segura</li>
                            <li>✓ Els codis 2FA mai es compartiràn</li>
                        </ul>
                    </div>
                </div>

                <!-- Botó Principal -->
                <button 
                    type="submit" 
                    class="btn-submit"
                    id="submitBtn"
                    aria-label="Validar credencials i accedir"
                >
                    <span class="btn-text">VALIDAR I ACCEDIR</span>
                    <span class="btn-spinner" style="display: none;">
                        <span class="spinner"></span>
                    </span>
                </button>

                <!-- Links secundaris -->
                <div class="form-links">
                    <a href="/help/no-authenticator" class="link-help">
                        ❓ No tinc generador 2FA?
                    </a>
                    <span class="separator">·</span>
                    <a href="/help/access-problems" class="link-help">
                        🆘 Problemes d'accés?
                    </a>
                </div>
            </form>

            <!-- Error Message Container -->
            <div id="errorContainer" class="alert alert-error" style="display: none;" role="alert">
                <svg class="alert-icon" width="20" height="20" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.8"/>
                    <path d="M12 6v6m0 3v1" stroke="white" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <div class="alert-content">
                    <p class="alert-message" id="errorMessage"></p>
                    <div id="errorDetails" style="display: none;"></div>
                </div>
            </div>

            <!-- Success Message Container -->
            <div id="successContainer" class="alert alert-success" style="display: none;" role="alert">
                <svg class="alert-icon" width="20" height="20" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" fill="currentColor"/>
                    <path d="M9 12l2 2 4-4" stroke="white" stroke-width="2" fill="none"/>
                </svg>
                <div class="alert-content">
                    <p class="alert-message">✅ Autenticació exitosa!</p>
                    <p class="alert-subtext" id="countdownText">Redirigint a {{ app_name }}... 3s</p>
                </div>
            </div>
        </main>

        <!-- Footer -->
        <footer class="footer">
            <nav class="footer-nav">
                <a href="/privacy" class="footer-link">Privacitat</a>
                <a href="/terms" class="footer-link">Termes de Servei</a>
                <a href="/security" class="footer-link">Seguretat</a>
                <a href="/contact" class="footer-link">Contacte</a>
            </nav>
            <p class="footer-text">© 2026 La Placeta. Tots els drets reservats</p>
        </footer>
    </div>

    <!-- Scripts -->
    <script src="/static/js/utils.js"></script>
    <script src="/static/js/login.js"></script>
</body>
</html>
```

## 🎨 static/css/login.css

```css
/* Variables */
:root {
    --primary: #0052CC;
    --primary-hover: #003D99;
    --success: #16A34A;
    --error: #DC2626;
    --warning: #D97706;
    --background: #FFFFFF;
    --surface: #F5F7FA;
    --border: #E5E7EB;
    --text-primary: #1F2937;
    --text-secondary: #6B7280;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    --radius: 8px;
    --transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* Reset */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
}

.container {
    background: var(--background);
    border-radius: var(--radius);
    box-shadow: var(--shadow-lg);
    max-width: 600px;
    width: 100%;
    overflow: hidden;
    animation: slideInUp 400ms ease-out;
}

@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Header */
.header {
    padding: 32px;
    text-align: center;
    border-bottom: 1px solid var(--border);
    background: linear-gradient(to bottom, #fff, var(--surface));
}

.logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin-bottom: 16px;
    color: var(--primary);
    font-size: 24px;
    font-weight: 700;
}

.logo svg {
    width: 32px;
    height: 32px;
}

.title {
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary);
}

/* Main Content */
.main {
    padding: 32px;
}

/* App Info */
.app-info {
    display: flex;
    gap: 12px;
    padding: 16px;
    background: var(--surface);
    border-radius: var(--radius);
    margin-bottom: 24px;
}

.app-icon {
    flex-shrink: 0;
    color: var(--primary);
}

.app-context {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 4px;
}

.app-name {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
}

/* Form Groups */
.form-group {
    border: none;
    margin-bottom: 24px;
}

.form-legend {
    border: none;
}

.label-main {
    display: block;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
}

.form-hint {
    display: block;
    font-size: 13px;
    color: var(--text-secondary);
    margin-bottom: 16px;
}

/* DIP Input */
.dip-input {
    display: flex;
    align-items: center;
    gap: 4px;
}

.dip-segment,
.totp-input {
    flex: 1;
    padding: 12px 16px;
    border: 2px solid var(--border);
    border-radius: var(--radius);
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 2px;
    text-align: center;
    font-family: 'Courier New', monospace;
    transition: var(--transition);
    background: var(--background);
}

.dip-segment:nth-child(1) {
    flex: 0 0 auto;
    width: 80px;
}

.dip-segment:nth-child(3) {
    flex: 0 0 auto;
    width: 80px;
}

.dip-segment:nth-child(5) {
    flex: 0 0 auto;
    width: 40px;
}

.separator {
    color: var(--text-secondary);
    font-weight: 700;
}

.dip-segment:focus,
.totp-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(0, 82, 204, 0.1);
}

.dip-segment.valid,
.totp-input.valid {
    border-color: var(--success);
}

.dip-segment.error,
.totp-input.error {
    border-color: var(--error);
}

.input-info {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    font-size: 13px;
    color: var(--text-secondary);
}

.icon-info {
    flex-shrink: 0;
    color: var(--text-secondary);
}

/* Form Divider */
.form-divider {
    height: 1px;
    background: var(--border);
    margin: 24px 0;
}

/* Auth Tabs */
.auth-tabs {
    display: flex;
    gap: 4px;
    margin-bottom: 16px;
    border-bottom: 2px solid var(--border);
}

.tab-button {
    background: none;
    border: none;
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    transition: var(--transition);
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
}

.tab-button:hover {
    color: var(--text-primary);
}

.tab-button.active {
    color: var(--primary);
    border-color: var(--primary);
}

/* Tab Panels */
.tab-panel {
    display: none;
}

.tab-panel.active {
    display: block;
    animation: fadeIn 200ms ease-out;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.input-wrapper {
    position: relative;
    display: flex;
    gap: 12px;
    align-items: center;
}

.totp-input {
    flex: 1;
}

.code-timer {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
}

.timer-dot {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--success);
    animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.timer-text {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    min-width: 24px;
    text-align: right;
}

.tab-hint {
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 8px;
}

.link-help {
    color: var(--primary);
    text-decoration: none;
    transition: var(--transition);
}

.link-help:hover {
    text-decoration: underline;
}

.sms-number,
.email-address {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 12px;
}

.btn-send-code {
    width: 100%;
    padding: 12px 16px;
    background: var(--surface);
    border: 2px solid var(--border);
    border-radius: var(--radius);
    font-size: 14px;
    font-weight: 600;
    color: var(--primary);
    cursor: pointer;
    transition: var(--transition);
}

.btn-send-code:hover {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
}

/* Security Notice */
.security-notice {
    display: flex;
    gap: 12px;
    padding: 16px;
    background: #ECFDF5;
    border: 1px solid #D1FAE5;
    border-radius: var(--radius);
    margin-bottom: 24px;
}

.icon-shield {
    flex-shrink: 0;
    color: var(--success);
}

.notice-content {
    flex: 1;
}

.notice-content strong {
    display: block;
    font-size: 14px;
    color: #065F46;
    margin-bottom: 8px;
}

.notice-list {
    list-style: none;
    font-size: 13px;
    color: #047857;
    line-height: 1.6;
}

/* Botó Submit */
.btn-submit {
    width: 100%;
    padding: 14px 20px;
    background: var(--primary);
    color: white;
    border: none;
    border-radius: var(--radius);
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: var(--transition);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.btn-submit:hover:not(:disabled) {
    background: var(--primary-hover);
    box-shadow: var(--shadow-md);
}

.btn-submit:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.btn-spinner {
    display: flex;
    align-items: center;
    gap: 8px;
}

.spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Form Links */
.form-links {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin-top: 16px;
    font-size: 13px;
}

.separator {
    color: var(--border);
}

/* Alerts */
.alert {
    padding: 16px;
    border-radius: var(--radius);
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    animation: slideInUp 300ms ease-out;
}

.alert-error {
    background: #FEE2E2;
    border: 1px solid #FECACA;
}

.alert-success {
    background: #DBEAFE;
    border: 1px solid #BFDBFE;
}

.alert-icon {
    flex-shrink: 0;
}

.alert-error .alert-icon {
    color: var(--error);
}

.alert-success .alert-icon {
    color: #3B82F6;
}

.alert-content {
    flex: 1;
}

.alert-message {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
}

.alert-error .alert-message {
    color: #7F1D1D;
}

.alert-success .alert-message {
    color: #1E40AF;
}

.alert-subtext {
    font-size: 13px;
    color: var(--text-secondary);
)
}

.alert-error \.alert-subtext {
    color: #991B1B;
}

/* Footer */
.footer {
    padding: 24px 32px;
    border-top: 1px solid var(--border);
    text-align: center;
    background: var(--surface);
}

.footer-nav {
    display: flex;
    justify-content: center;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}

.footer-link {
    font-size: 13px;
    color: var(--text-secondary);
    text-decoration: none;
    transition: var(--transition);
}

.footer-link:hover {
    color: var(--primary);
}

.footer-text {
    font-size: 12px;
    color: var(--text-secondary);
}

/* Responsive */
@media (max-width: 640px) {
    .container {
        border-radius: 0;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
    }

    .header {
        padding: 16px;
    }

    .title {
        font-size: 18px;
    }

    .main {
        padding: 20px;
        flex: 1;
    }

    .dip-segment:nth-child(1),
    .dip-segment:nth-child(3),
    .dip-segment:nth-child(5) {
        flex: 1;
        width: auto;
    }

    .auth-tabs {
        flex-wrap: wrap;
    }

    .tab-button {
        padding: 10px 12px;
        font-size: 12px;
    }

    .btn-submit {
        padding: 14px 16px;
    }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
    body {
        background: #1a1a2e;
    }

    .container {
        background: #2d2d44;
        color: #e0e0e0;
    }

    :root {
        --background: #2d2d44;
        --text-primary: #e0e0e0;
        --text-secondary: #a0a0b0;
        --border: #3d3d54;
        --surface: #3d3d54;
    }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

@media (forced-colors: active) {
    .btn-submit,
    .btn-send-code {
        border: 2px solid CanvasText;
    }
    
    .btn-submit:focus {
        outline: 2px solid CanvasText;
        outline-offset: 2px;
    }
}
```

