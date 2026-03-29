/**
 * PlacetaID Frontend - Enhanced Login Flow (Demo Mode)
 */

// State management
const LoginState = {
    currentStep: 'dip',
    validatedDIP: null,
    isProcessing: false,
    demoMode: false,
    failedAttempts: 0,
    blocked: false
};

// DOM Elements
const DOM = {
    form: null,
    dipInput: null,
    totpInput: null,
    validateDipBtn: null,
    validateTotpBtn: null,
    backBtn: null,
    successScreen: null,
    lottieContainer: null,
    dipDisplay: null,
    alertContainer: null
};

/**
 * Initialize login for demo mode
 */
function initLogin() {
    console.log('Initializing login page...');
    
    // Cache DOM elements
    cacheDOM();
    
    // Check if query params exist for OAuth
    const hasRedirectUri = CONFIG.OAUTH.redirectUri && CONFIG.OAUTH.redirectUri.length > 0;
    
    // Set demo mode if no redirect URI
    LoginState.demoMode = !hasRedirectUri;
    
    if (LoginState.demoMode) {
        console.log('🎮 DEMO MODE ENABLED - No redirect URI detected');
        showAlert('Modo Demo: Funciona sin redirección', 'info', 0);
    }
    
    // Setup event listeners
    setupEventListeners();
    
    // Show first step
    showStep('dip-step');
}

/**
 * Cache DOM elements
 */
function cacheDOM() {
    DOM.form = document.getElementById('login-form');
    DOM.dipInput = document.getElementById('dip-input');
    DOM.totpInput = document.getElementById('totp-input');
    DOM.validateDipBtn = document.getElementById('validate-dip-btn');
    DOM.validateTotpBtn = document.getElementById('validate-totp-btn');
    DOM.backBtn = document.getElementById('back-btn');
    DOM.successScreen = document.getElementById('successScreen');
    DOM.lottieContainer = document.getElementById('lottieAnimation');
    DOM.dipDisplay = document.getElementById('displayDIP');
    DOM.alertContainer = document.getElementById('alert-container');
    DOM.statusMessage = document.getElementById('statusMessage');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // DIP Input - Auto-format to uppercase and remove invalid chars
    DOM.dipInput.addEventListener('input', handleDIPInput);
    
    // TOTP Input - Only numbers
    DOM.totpInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/[^0-9]/g, '');
    });
    
    // Button listeners
    DOM.validateDipBtn.addEventListener('click', handleValidateDIP);
    DOM.validateTotpBtn.addEventListener('click', handleValidateTOTP);
    DOM.backBtn.addEventListener('click', handleBack);
    
    // Manual redirect button
    const manualRedirectBtn = document.getElementById('manualRedirectBtn');
    if (manualRedirectBtn) {
        manualRedirectBtn.addEventListener('click', (e) => {
            e.preventDefault();
            completeAuthorization();
        });
    }
    
    // Form submission
    DOM.form.addEventListener('submit', (e) => e.preventDefault());
    
    console.log('Event listeners initialized');
}

/**
 * Handle DIP input - auto-format
 */
function handleDIPInput(e) {
    let value = e.target.value.toUpperCase();
    
    // Remove invalid characters - allow only 8 digits + 1 letter
    let cleaned = '';
    for (let i = 0; i < value.length && i < 9; i++) {
        if (i < 8) {
            // First 8 must be digits
            if (/[0-9]/.test(value[i])) {
                cleaned += value[i];
            }
        } else {
            // Last must be letter
            if (/[A-Z]/.test(value[i])) {
                cleaned += value[i];
            }
        }
    }
    
    e.target.value = cleaned;
}

/**
 * Validate DIP format
 */
function validateDIPFormat(dip) {
    if (!dip || dip.length !== 9) {
        return false;
    }
    
    // First 8 must be digits
    if (!/^\d{8}/.test(dip)) {
        return false;
    }
    
    // Last must be letter
    if (!/[A-Z]$/.test(dip)) {
        return false;
    }
    
    return true;
}

/**
 * Handle DIP validation
 */
async function handleValidateDIP() {
    if (LoginState.isProcessing) return;
    
    const dip = DOM.dipInput.value.trim().toUpperCase();
    
    // Validate format
    if (!validateDIPFormat(dip)) {
        LoginState.failedAttempts += 1;
        showMessage(`Intento ${LoginState.failedAttempts}/3: DIP inválido`, 'error');
        DOM.dipInput.classList.add('invalid');
        setTimeout(() => {
            DOM.dipInput.classList.remove('invalid');
        }, 500);
        if (LoginState.failedAttempts >= 3) {
            blockUser();
        }
        return;
    }
    
    LoginState.isProcessing = true;
    DOM.validateDipBtn.disabled = true;
    
    try {
        LoginState.validatedDIP = dip;
        
        if (LoginState.demoMode) {
            console.log('🎮 Demo Mode: Skipping TOTP, showing success');
            // In demo mode, skip TOTP and go directly to success
            completeAuthorization();
        } else {
            // In normal mode, proceed to TOTP
            showAlert(`✓ DIP válido: ${dip}`, 'success', 2000);
            showStep('totp-step');
        }
    } catch (error) {
        console.error('Error validating DIP:', error);
        showAlert('❌ Error al validar DIP', 'error');
    } finally {
        LoginState.isProcessing = false;
        DOM.validateDipBtn.disabled = false;
    }
}

/**
 * Handle TOTP validation
 */
async function handleValidateTOTP() {
    if (LoginState.isProcessing) return;
    
    const totp = DOM.totpInput.value.trim();
    
    // Validate format
    if (totp.length !== 6 || !/^\d{6}$/.test(totp)) {
        LoginState.failedAttempts += 1;
        showMessage(`Intento ${LoginState.failedAttempts}/3: Código TOTP inválido`, 'error');
        DOM.totpInput.classList.add('invalid');
        setTimeout(() => {
            DOM.totpInput.classList.remove('invalid');
        }, 500);
        if (LoginState.failedAttempts >= 3) {
            blockUser();
        }
        return;
    }
    
    LoginState.isProcessing = true;
    DOM.validateTotpBtn.disabled = true;
    showStep('loading-step');
    
    try {
        showAlert(`✓ Código verificado: ${totp}`, 'success', 2000);
        completeAuthorization();
    } catch (error) {
        console.error('Error validating TOTP:', error);
        showAlert('❌ Error al verificar código', 'error');
        showStep('totp-step');
    } finally {
        LoginState.isProcessing = false;
        DOM.validateTotpBtn.disabled = false;
    }
}

/**
 * Show specific form step
 */
function showStep(stepId) {
    // Hide all form steps
    document.querySelectorAll('.form-step').forEach(step => {
        step.classList.remove('active');
    });
    
    // Show target step
    const targetStep = document.getElementById(stepId);
    if (targetStep) {
        targetStep.classList.add('active');
    }
    
    // Auto-focus input
    setTimeout(() => {
        if (stepId === 'dip-step') {
            DOM.dipInput.focus();
        } else if (stepId === 'totp-step') {
            DOM.totpInput.focus();
        }
    }, 100);
}

/**
 * Handle back button
 */
function handleBack() {
    showStep('dip-step');
    DOM.dipInput.focus();
}

/**
 * Show/hide success screen
 */
function showSuccessScreen(dip) {
    // Hide form
    document.getElementById('login-form').style.display = 'none';
    
    // Show success screen
    DOM.successScreen.classList.add('active');
    
    // Display DIP
    DOM.dipDisplay.textContent = dip.toUpperCase();
    
    // Show GIF animations
    const gifAnimation = document.getElementById('gifAnimation');
    if (gifAnimation) {
        gifAnimation.style.display = 'block';
    }

    const gifAnimationDip = document.getElementById('gifAnimationDip');
    if (gifAnimationDip) {
        gifAnimationDip.style.display = 'block';
    }

    // Hide fallback and lottie containers
    const fallback = document.getElementById('fallbackAnimation');
    if (fallback) {
        fallback.classList.remove('active');
    }
    const lottieContainer = document.getElementById('lottieAnimation');
    if (lottieContainer) {
        lottieContainer.style.display = 'none';
    }

    
    console.log('✓ Success screen shown');
    
    // Auto-redirect after delay if not in demo mode
    if (!LoginState.demoMode) {
        setTimeout(() => {
            completeAuthorization();
        }, 3000);
    }
}

/**
 * Load Lottie animation
 */
function loadLottieAnimation() {
    const fallback = document.getElementById('fallbackAnimation');

    if (!window.lottie) {
        console.warn('Lottie not loaded, using fallback animation');
        if (fallback) {
            fallback.classList.add('active');
        }
        return;
    }

    if (fallback) {
        fallback.classList.remove('active');
    }

    // Simple success animation data (circle checkmark)
    const animationData = {
        v: '5.5.0',
        fr: 24,
        ip: 0,
        op: 120,
        w: 200,
        h: 200,
        nm: 'Success Checkmark',
        ddd: 0,
        assets: [],
        layers: [
            {
                ddd: 0,
                ind: 1,
                ty: 4,
                nm: 'Circle',
                sr: 1,
                ks: {
                    o: { a: 0, k: 100 },
                    r: { a: 0, k: 0 },
                    p: { a: 0, k: [100, 100, 0] },
                    a: { a: 0, k: [0, 0, 0] },
                    s: { a: 0, k: [100, 100, 100] }
                },
                ao: 0,
                shapes: [
                    {
                        ty: 'el',
                        d: 1,
                        s: { a: 0, k: [160, 160] },
                        p: { a: 0, k: [0, 0] },
                        nm: 'Ellipse 1',
                        mn: 'ADBE Vector Shape - Ellipse'
                    },
                    {
                        ty: 'st',
                        c: { a: 0, k: [0.09, 0.64, 0.29, 1] },
                        o: { a: 0, k: 100 },
                        w: { a: 0, k: 8 },
                        lc: 2,
                        lj: 2,
                        nm: 'Stroke 1',
                        mn: 'ADBE Vector Graphic - Stroke'
                    }
                ]
            }
        ]
    };
    
    try {
        const animation = lottie.loadAnimation({
            container: DOM.lottieContainer,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            animationData: animationData
        });
        console.log('✓ Lottie animation loaded');
    } catch (error) {
        console.warn('Could not load Lottie animation:', error);
    }
}

/**
 * Complete authorization and redirect
 */
async function completeAuthorization() {
    if (!LoginState.validatedDIP) {
        console.error('No validated DIP');
        return;
    }
    
    try {
        if (LoginState.demoMode) {
            console.log('🎮 Demo Mode: Simulating success screen');
            showSuccessScreen(LoginState.validatedDIP);
        } else {
            // In production, would exchange for authorization code
            const redirectUri = CONFIG.OAUTH.redirectUri;
            const authCode = 'demo-auth-code-' + Date.now();
            
            if (redirectUri) {
                const redirectUrl = `${redirectUri}?code=${authCode}&state=${CONFIG.OAUTH.state}`;
                console.log('Redirecting to:', redirectUrl);
                window.location.href = redirectUrl;
            } else {
                showSuccessScreen(LoginState.validatedDIP);
            }
        }
    } catch (error) {
        console.error('Authorization error:', error);
        showAlert('❌ Error en autorización', 'error');
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info', duration = 5000) {
    const container = DOM.alertContainer;
    
    // Clear existing alerts
    container.innerHTML = '';
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} show`;
    alert.textContent = message;
    
    container.appendChild(alert);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            alert.remove();
        }, duration);
    }
}

function showMessage(message, type = 'info', duration = 5000) {
    const status = DOM.statusMessage;
    if (!status) return;

    status.textContent = message;
    status.className = `status-message show status-${type}`;

    if (type === 'error') {
        status.style.background = 'linear-gradient(135deg, #dc2626, #7f1d1d)';
    } else if (type === 'success') {
        status.style.background = 'linear-gradient(135deg, #16a34a, #059669)';
    } else if (type === 'warning') {
        status.style.background = 'linear-gradient(135deg, #f59e0b, #d97706)';
    } else {
        status.style.background = 'linear-gradient(135deg, #6d28d9, #9333ea)';
    }

    status.style.display = 'block';

    if (duration > 0) {
        setTimeout(() => {
            status.style.display = 'none';
        }, duration);
    }
}

function blockUser() {
    LoginState.blocked = true;
    LoginState.isProcessing = false;
    DOM.validateDipBtn.disabled = true;
    DOM.validateTotpBtn.disabled = true;

    showMessage('⚠️ Usuario bloqueado tras 3 intentos fallidos. Intenta de nuevo más tarde.', 'error', 0);

    // Optionally show the login form as disabled
    const inputs = [DOM.dipInput, DOM.totpInput];
    inputs.forEach(input => {
        if (input) {
            input.disabled = true;
        }
    });

    // Add a visible class to highlight block state
    if (DOM.form) {
        DOM.form.classList.add('blocked');
    }
}

/**
 * Initialize on DOM ready
 */
document.addEventListener('DOMContentLoaded', initLogin);

// Also initialize if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLogin);
} else {
    initLogin();
}
