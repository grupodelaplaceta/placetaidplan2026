# JavaScript - Interacció del Frontend

## 📄 static/js/login.js

```javascript
/**
 * PlacetaID - Login Form Script
 * Maneja la validació de formulari i interacció amb usuario
 */

const LOGIN_CONFIG = {
    dip_segment_lengths: [4, 4, 1],
    totp_length: 6,
    timer_duration: 30,
    redirect_countdown: 3,
    api_timeout: 30000
};

class DIPInput {
    constructor() {
        this.segments = [
            document.getElementById('dipInput1'),
            document.getElementById('dipInput2'),
            document.getElementById('dipInput3')
        ];
        this.init();
    }

    init() {
        this.segments.forEach((input, index) => {
            input.addEventListener('input', (e) => this.handleInput(e, index));
            input.addEventListener('keydown', (e) => this.handleKeydown(e, index));
            input.addEventListener('paste', (e) => this.handlePaste(e, index));
            input.addEventListener('focus', (e) => e.target.select());
        });
    }

    handleInput(event, index) {
        const input = event.target;
        const value = input.value.replace(/[^0-9A-Za-z]/g, '').toUpperCase();
        
        if (index === 2) {
            // Última segment: solo letras
            input.value = value.replace(/[0-9]/g, '').slice(0, 1);
        } else {
            // Primeras: solo números
            input.value = value.replace(/[A-Za-z]/g, '');
        }

        // Auto-focus siguiente si completo
        if (input.value.length === LOGIN_CONFIG.dip_segment_lengths[index]) {
            if (index < this.segments.length - 1) {
                this.segments[index + 1].focus();
            } else {
                document.getElementById('totp2faInput').focus();
            }
        }
    }

    handleKeydown(event, index) {
        const input = event.target;
        
        // Backspace: mover al anterior
        if (event.key === 'Backspace' && input.value === '' && index > 0) {
            this.segments[index - 1].focus();
            this.segments[index - 1].value = '';
        }

        // Tab: navegar normalment
        // Enter: validar form
        if (event.key === 'Enter') {
            event.preventDefault();
            document.getElementById('loginForm').requestSubmit();
        }
    }

    handlePaste(event, index) {
        event.preventDefault();
        const pastedText = (event.clipboardData || window.clipboardData)
            .getData('text')
            .replace(/[^0-9A-Z]/g, '')
            .toUpperCase();

        if (pastedText.length < 9) {
            showError('Format de DIP incorrecte');
            return;
        }

        // Distribuir entre segments
        this.segments[0].value = pastedText.slice(0, 4);
        this.segments[1].value = pastedText.slice(4, 8);
        this.segments[2].value = pastedText.slice(8, 9);

        // Focus en 2FA
        document.getElementById('totp2faInput').focus();
    }

    getDIP() {
        return this.segments
            .map(input => input.value)
            .join('-');
    }

    isValid() {
        return this.segments.every((input, index) => 
            input.value.length === LOGIN_CONFIG.dip_segment_lengths[index]
        );
    }

    validate() {
        this.segments.forEach((input, index) => {
            const isValid = input.value.length === LOGIN_CONFIG.dip_segment_lengths[index];
            input.classList.toggle('valid', isValid);
            input.classList.toggle('error', !isValid && input.value.length > 0);
        });
    }
}

class TOTPInput {
    constructor() {
        this.input = document.getElementById('totp2faInput');
        this.timerText = document.querySelector('.timer-text');
        this.timerDot = document.querySelector('.timer-dot');
        this.init();
    }

    init() {
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.startTimer();
    }

    handleInput(event) {
        const value = event.target.value.replace(/[^0-9]/g, '');
        event.target.value = value.slice(0, 6);

        // Autoformat: xxx xxx
        if (value.length === 3) {
            event.target.value = value + ' ';
        } else if (value.length === 6) {
            event.target.value = value.slice(0, 3) + ' ' + value.slice(3);
        }
    }

    handleKeydown(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            document.getElementById('loginForm').requestSubmit();
        }
    }

    startTimer() {
        let timeLeft = LOGIN_CONFIG.timer_duration;
        
        const updateTimer = () => {
            this.timerText.textContent = `${timeLeft}s`;
            
            // Cambiar color según tiempo
            if (timeLeft <= 5) {
                this.timerDot.style.animationDuration = '0.4s';
                this.timerText.style.color = 'var(--error)';
            }
            
            timeLeft--;
            if (timeLeft >= 0) {
                setTimeout(updateTimer, 1000);
            } else {
                this.timerText.textContent = 'Expirat';
                this.timerDot.style.display = 'none';
                showWarning('El codi TOTP ha expirat. Introdueix el nou.');
            }
        };
        
        updateTimer();
    }

    getCode() {
        return this.input.value.replace(/\s/g, '');
    }

    isValid() {
        return this.getCode().length === 6 && /^\d{6}$/.test(this.getCode());
    }
}

class FormValidator {
    constructor() {
        this.dipInput = new DIPInput();
        this.totp = new TOTPInput();
        this.form = document.getElementById('loginForm');
        this.submitBtn = document.getElementById('submitBtn');
        this.attachEvents();
    }

    attachEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    handleSubmit(event) {
        event.preventDefault();

        // Validar DIP
        if (!this.dipInput.isValid()) {
            this.dipInput.validate();
            showError('Si us plau, introdueix un DIP vàlid (format: 1234-5678-A)');
            return;
        }

        // Validar TOTP
        if (!this.totp.isValid()) {
            showError('Si us plau, introdueix un codi 2FA vàlid (6 dígits)');
            this.totp.input.classList.add('error');
            return;
        }

        // Enviar formulari
        this.submitForm();
    }

    async submitForm() {
        this.submitBtn.disabled = true;
        const btnText = this.submitBtn.querySelector('.btn-text');
        const btnSpinner = this.submitBtn.querySelector('.btn-spinner');
        
        btnText.style.display = 'none';
        btnSpinner.style.display = 'flex';

        try {
            const formData = new FormData(this.form);
            
            // Reconstruir DIP sense guiones per al servidor
            const dip = this.dipInput.getDIP().replace(/-/g, '');
            formData.set('dip', dip);
            formData.set('code_2fa', this.totp.getCode());

            const response = await fetch('/oauth/validate', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin',
                timeout: LOGIN_CONFIG.api_timeout
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showSuccess(data.message);
                
                // Countdown i redirig
                let countdown = data.countdown || LOGIN_CONFIG.redirect_countdown;
                const timer = setInterval(() => {
                    countdown--;
                    if (countdown <= 0) {
                        clearInterval(timer);
                        window.location.href = data.redirect_uri;
                    }
                });

            } else {
                // Error de credencials
                let errorMessage = data.message || 'Error de validació';
                
                if (data.error === 'account_locked') {
                    showError(
                        `🔒 ${errorMessage}\n` +
                        `Blocat fins: ${new Date(data.locked_until).toLocaleString()}\n` +
                        `Desbloqueja a: ${data.unlock_url}`,
                        {
                            type: 'lockout',
                            unlockUrl: data.unlock_url
                        }
                    );
                } else {
                    const attempts = data.attempts_remaining || 0;
                    const attemptInfo = attempts > 0 
                        ? `\nIntent: ${data.attempt}/3` 
                        : '';
                    
                    showError(`❌ ${errorMessage}${attemptInfo}`);
                }
            }

        } catch (error) {
            console.error('Form submission error:', error);
            showError('Error de connexió. Si us plau, intenta-ho més tard.');
        } finally {
            this.submitBtn.disabled = false;
            btnText.style.display = 'block';
            btnSpinner.style.display = 'none';
        }
    }
}

class TabManager {
    constructor() {
        this.tabs = document.querySelectorAll('[role=\"tab\"]');
        this.panels = document.querySelectorAll('[role=\"tabpanel\"]');
        this.activeTab = null;
        this.init();
    }

    init() {
        this.tabs.forEach(tab => {
            tab.addEventListener('click', (e) => this.selectTab(e.target));
            tab.addEventListener('keydown', (e) => this.handleKeydown(e));
        });
    }

    selectTab(tab) {
        const panelId = tab.getAttribute('aria-controls');
        const panel = document.getElementById(panelId);

        if (!panel) return;

        // Deseleccionar tab anterior
        if (this.activeTab) {
            this.activeTab.setAttribute('aria-selected', 'false');
            const oldPanelId = this.activeTab.getAttribute('aria-controls');
            document.getElementById(oldPanelId)?.classList.remove('active');
        }

        // Seleccionar novo tab
        tab.setAttribute('aria-selected', 'true');
        panel.classList.add('active');
        this.activeTab = tab;

        // Si es SMS o Email, solicitar código
        const tabName = tab.dataset.tab;
        if (tabName === 'sms') {
            this.requestSMSCode();
        } else if (tabName === 'email') {
            this.requestEmailCode();
        }
    }

    handleKeydown(event) {
        const { key } = event;
        let nextTab;

        switch (key) {
            case 'ArrowLeft':
            case 'ArrowUp':
                event.preventDefault();
                nextTab = this.activeTab.previousElementSibling;
                break;
            case 'ArrowRight':
            case 'ArrowDown':
                event.preventDefault();
                nextTab = this.activeTab.nextElementSibling;
                break;
            case 'Home':
                event.preventDefault();
                nextTab = this.tabs[0];
                break;
            case 'End':
                event.preventDefault();
                nextTab = this.tabs[this.tabs.length - 1];
                break;
            default:
                return;
        }

        if (nextTab) {
            this.selectTab(nextTab);
            nextTab.focus();
        }
    }

    async requestSMSCode() {
        const btn = document.getElementById('sendSmsBtn');
        btn.disabled = true;
        btn.textContent = 'Enviant...';

        try {
            const response = await fetch('/oauth/send-2fa-sms', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                btn.textContent = '✓ Codi enviat (SMS)';
                setTimeout(() => {
                    btn.textContent = 'Enviar codi per SMS';
                    btn.disabled = false;
                }, 3000);

                // Mostrar input per al codi
                const codeInput = document.querySelector('input[name=\"code_sms\"]');
                codeInput.style.display = 'block';
                codeInput.focus();
            }
        } catch (error) {
            console.error('SMS request error:', error);
            btn.textContent = 'Error enviant SMS';
            btn.disabled = false;
        }
    }

    async requestEmailCode() {
        const btn = document.getElementById('sendEmailBtn');
        btn.disabled = true;
        btn.textContent = 'Enviant...';

        try {
            const response = await fetch('/oauth/send-2fa-email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                btn.textContent = '✓ Codi enviat (Email)';
                setTimeout(() => {
                    btn.textContent = 'Enviar codi per email';
                    btn.disabled = false;
                }, 3000);

                const codeInput = document.querySelector('input[name=\"code_email\"]');
                codeInput.style.display = 'block';
                codeInput.focus();
            }
        } catch (error) {
            console.error('Email request error:', error);
            btn.textContent = 'Error enviant email';
            btn.disabled = false;
        }
    }
}

// Utils: Mostrar missatges
function showError(message, options = {}) {
    const container = document.getElementById('errorContainer');
    const messageEl = document.getElementById('errorMessage');
    const form = document.getElementById('loginForm');

    messageEl.textContent = message;
    container.classList.remove('fade-out');
    container.style.display = 'flex';

    // Si és lockout, afegir link de desbloqueig
    if (options.type === 'lockout' && options.unlockUrl) {
        const detailsEl = document.getElementById('errorDetails');
        detailsEl.innerHTML = `<a href="${options.unlockUrl}" class="link-help" target="_blank">Desbloqueja ara →</a>`;
        detailsEl.style.display = 'block';
    }

    // Scroll a error
    container.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function showSuccess(message) {
    const container = document.getElementById('successContainer');
    const messageEl = container.querySelector('.alert-message');
    
    messageEl.textContent = message;
    container.style.display = 'flex';
    container.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function showWarning(message) {
    console.warn(message);
    // Hacer una notificación sutil sin bloquer
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    const formValidator = new FormValidator();
    const tabManager = new TabManager();

    // Focus al primer input
    document.getElementById('dipInput1').focus();

    // Esconder errores al hacer cambios
    const inputs = document.querySelectorAll('input[type=\"text\"]');
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            document.getElementById('errorContainer').style.display = 'none';
        });
    });
});
```

## 📄 static/js/utils.js

```javascript
/**
 * Utilidades compartidas para PlacetaID
 */

// Validación de DIP (algoritmo español)
function validateDIPChecksum(dip) {
    dip = dip.replace(/-/g, '').toUpperCase();
    
    if (dip.length !== 9) return false;
    
    const numbers = dip.substring(0, 8);
    const letter = dip.charAt(8);
    
    const LETTERS = 'TRWAGMYFPDXBNJZSQVHLCKE';
    const expectedLetter = LETTERS[parseInt(numbers) % 23];
    
    return letter === expectedLetter;
}

// Format DIP visually
function formatDIP(dip) {
    dip = dip.replace(/[^0-9A-Z]/g, '').toUpperCase();
    if (dip.length === 9) {
        return `${dip.slice(0, 4)}-${dip.slice(4, 8)}-${dip.slice(8)}`;
    }
    return dip;
}

// Simular TOTP (para testing)
function generateTOTPSecret() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    let secret = '';
    for (let i = 0; i < 32; i++) {
        secret += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return secret;
}

// Timing-safe comparison
function constantTimeCompare(a, b) {
    if (a.length !== b.length) return false;
    
    let result = 0;
    for (let i = 0; i < a.length; i++) {
        result |= a.charCodeAt(i) ^ b.charCodeAt(i);
    }
    return result === 0;
}

// Cookie management
const CookieUtil = {
    set: (name, value, options = {}) => {
        let cookieString = `${name}=${encodeURIComponent(value)}`;
        
        if (options.expires) {
            cookieString += `; expires=${options.expires.toUTCString()}`;
        }
        
        if (options.maxAge) {
            cookieString += `; max-age=${options.maxAge}`;
        }
        
        if (options.path) {
            cookieString += `; path=${options.path}`;
        }
        
        if (options.domain) {
            cookieString += `; domain=${options.domain}`;
        }
        
        if (options.secure) {
            cookieString += '; secure';
        }
        
        if (options.sameSite) {
            cookieString += `; samesite=${options.sameSite}`;
        }
        
        document.cookie = cookieString;
    },
    
    get: (name) => {
        const nameEQ = `${name}=`;
        const cookies = document.cookie.split(';');
        
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(nameEQ)) {
                return decodeURIComponent(cookie.substring(nameEQ.length));
            }
        }
        return null;
    },
    
    delete: (name) => {
        CookieUtil.set(name, '', { maxAge: -1 });
    }
};

// Generar token CSRF
function generateCSRFToken() {
    return Array.from(crypto.getRandomValues(new Uint8Array(32)))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

// Performance monitoring
const PerformanceUtil = {
    mark: (name) => {
        if (window.performance?.mark) {
            performance.mark(name);
        }
    },
    
    measure: (name, startMark, endMark) => {
        if (window.performance?.measure) {
            performance.measure(name, startMark, endMark);
        }
    }
};

```

