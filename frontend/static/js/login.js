/**
 * PlacetaID Frontend - Login Flow Logic
 */

// State management
const LoginState = {
    currentStep: 'dip',
    validatedDIP: null,
    citizenId: null,
    authorizationCode: null,
    accessToken: null,
    isProcessing: false
};

// DOM Elements
const DOM = {
    form: null,
    dipSegment1: null,
    dipSegment2: null,
    dipSegment3: null,
    totpInput: null,
    validateDipBtn: null,
    validateTotpBtn: null,
    backBtn: null
};

/**
 * Initialize login page
 */
function initLogin() {
    Utils.log('Initializing login page');
    
    // Cache DOM elements
    cacheDOM();
    
    // Setup event listeners
    setupEventListeners();
    
    // Check API health
    checkAPIHealth();
    
    // Show first step
    Utils.showStep('dip-step');
}

/**
 * Cache DOM elements
 */
function cacheDOM() {
    DOM.form = document.getElementById('login-form');
    DOM.dipSegment1 = document.getElementById('dip-segment-1');
    DOM.dipSegment2 = document.getElementById('dip-segment-2');
    DOM.dipSegment3 = document.getElementById('dip-segment-3');
    DOM.totpInput = document.getElementById('totp-input');
    DOM.validateDipBtn = document.getElementById('validate-dip-btn');
    DOM.validateTotpBtn = document.getElementById('validate-totp-btn');
    DOM.backBtn = document.getElementById('back-btn');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // DIP Input - Auto-focus next segment
    DOM.dipSegment1.addEventListener('input', handleDIPSegmentInput);
    DOM.dipSegment2.addEventListener('input', handleDIPSegmentInput);
    DOM.dipSegment3.addEventListener('input', handleDIPSegmentInput);
    
    // DIP Backspace handling
    DOM.dipSegment1.addEventListener('keydown', handleDIPBackspace);
    DOM.dipSegment2.addEventListener('keydown', handleDIPBackspace);
    DOM.dipSegment3.addEventListener('keydown', handleDIPBackspace);
    
    // TOTP Input - Auto-format
    DOM.totpInput.addEventListener('input', handleTOTPInput);
    
    // Buttons
    DOM.validateDipBtn.addEventListener('click', handleValidateDIP);
    DOM.validateTotpBtn.addEventListener('click', handleValidateTOTP);
    DOM.backBtn.addEventListener('click', handleBack);
    
    // Form submission
    DOM.form.addEventListener('submit', (e) => e.preventDefault());
    
    Utils.log('Event listeners initialized');
}

/**
 * Handle DIP segment input
 */
function handleDIPSegmentInput(e) {
    const input = e.target;
    const value = input.value;
    
    // Allow only digits for first two segments, letters for third
    let filtered = value;
    if (input === DOM.dipSegment3) {
        filtered = value.replace(/[^A-Za-z]/g, '').toUpperCase();
    } else {
        filtered = value.replace(/[^0-9]/g, '');
    }
    
    input.value = filtered;
    
    // Move to next segment if filled
    if (filtered.length === input.maxLength) {
        if (input === DOM.dipSegment1) {
            DOM.dipSegment2.focus();
        } else if (input === DOM.dipSegment2) {
            DOM.dipSegment3.focus();
        }
    }
}

/**
 * Handle DIP segment backspace
 */
function handleDIPBackspace(e) {
    if (e.key !== 'Backspace') return;
    
    const input = e.target;
    
    // If input is empty, move to previous segment
    if (input.value === '') {
        if (input === DOM.dipSegment2) {
            e.preventDefault();
            DOM.dipSegment1.focus();
        } else if (input === DOM.dipSegment3) {
            e.preventDefault();
            DOM.dipSegment2.focus();
        }
    }
}

/**
 * Handle TOTP input
 */
function handleTOTPInput(e) {
    const input = e.target;
    
    // Allow only digits
    let value = input.value.replace(/[^0-9]/g, '');
    
    // Add space every 3 digits for readability
    if (value.length > 3) {
        value = value.substring(0, 3) + ' ' + value.substring(3, 6);
    }
    
    input.value = value;
}

/**
 * Validate DIP and move to 2FA step
 */
async function handleValidateDIP(e) {
    e.preventDefault();
    
    if (LoginState.isProcessing) return;
    
    // Get DIP segments
    const dipSegments = Utils.getDIPSegments();
    
    // Validate format
    if (!Utils.validateDIPFormat(dipSegments.full)) {
        Utils.showAlert('Formato de DIP inválido. Ejemplo: 1234-5678-X', 'error');
        Utils.setInputValidity('dip-segment-1', false);
        return;
    }
    
    // Validate checksum
    if (!Utils.validateDIPChecksum(dipSegments.full)) {
        Utils.showAlert('El DIP no es válido. Verifica el dígito de control.', 'error');
        Utils.setInputValidity('dip-segment-3', false);
        return;
    }
    
    // Set processing state
    LoginState.isProcessing = true;
    Utils.setButtonLoading('validate-dip-btn', true);
    
    Utils.log('Validating DIP', dipSegments.full);
    
    // Call API
    const response = await APIClient.validateDIP(dipSegments.full);
    
    if (!APIClient.handleError(response)) {
        LoginState.isProcessing = false;
        Utils.setButtonLoading('validate-dip-btn', false);
        Utils.setInputValidity('dip-segment-1', false);
        return;
    }
    
    // Store validated DIP and citizen ID
    LoginState.validatedDIP = dipSegments.full;
    LoginState.citizenId = response.citizen_id;
    
    Utils.log('DIP validated successfully', { citizenId: response.citizen_id, step: response.step });
    
    // Mark DIP inputs as valid
    Utils.setInputValidity('dip-segment-1', true);
    Utils.setInputValidity('dip-segment-2', true);
    Utils.setInputValidity('dip-segment-3', true);
    
    // Move to next step
    if (response.step === 'totp') {
        Utils.showStep('totp-step');
        LoginState.currentStep = 'totp';
        DOM.backBtn.classList.remove('hidden');
        Utils.showAlert('DIP válido. Ingresa tu código de verificación.', 'success', 3000);
    } else if (response.step === 'authorize') {
        // 2FA not enabled, proceed to authorization
        completeAuthorization();
    }
    
    LoginState.isProcessing = false;
    Utils.setButtonLoading('validate-dip-btn', false);
}

/**
 * Validate TOTP code
 */
async function handleValidateTOTP(e) {
    e.preventDefault();
    
    if (LoginState.isProcessing) return;
    
    const code = Utils.getTOTPCode();
    
    // Validate format
    if (!Utils.validateTOTPFormat(code)) {
        Utils.showAlert('El código debe tener 6 dígitos.', 'error');
        Utils.setInputValidity('totp-input', false);
        return;
    }
    
    // Set processing state
    LoginState.isProcessing = true;
    Utils.setButtonLoading('validate-totp-btn', true);
    
    Utils.log('Validating TOTP code');
    
    // Call API
    const response = await APIClient.validateTOTP(LoginState.validatedDIP, code);
    
    if (!APIClient.handleError(response)) {
        LoginState.isProcessing = false;
        Utils.setButtonLoading('validate-totp-btn', false);
        Utils.setInputValidity('totp-input', false);
        return;
    }
    
    // Mark TOTP as valid
    Utils.setInputValidity('totp-input', true);
    Utils.showAlert('Código verificado. Completando autenticación...', 'success', 2000);
    
    LoginState.isProcessing = false;
    Utils.setButtonLoading('validate-totp-btn', false);
    
    // Complete authorization
    completeAuthorization();
}

/**
 * Complete authorization after successful validation
 */
async function completeAuthorization() {
    Utils.log('Completing authorization');
    
    // Show loading step
    Utils.showStep('loading-step');
    LoginState.currentStep = 'loading';
    
    // Get authorization code
    const response = await APIClient.validateAuthorization(LoginState.citizenId);
    
    if (!APIClient.handleError(response)) {
        Utils.showStep('dip-step');
        Utils.resetForm();
        return;
    }
    
    // Store authorization code
    LoginState.authorizationCode = response.code;
    
    Utils.log('Authorization code received', { code: response.code });
    
    // Show success step
    Utils.showStep('success-step');
    LoginState.currentStep = 'success';
    
    // Prepare redirect
    setTimeout(() => {
        redirectToClient(response.code, response.state);
    }, CONFIG.UI.successRedirectDelay);
}

/**
 * Redirect to OAuth client with authorization code
 */
function redirectToClient(code, state) {
    // Build redirect URL
    const redirectUri = CONFIG.OAUTH.redirectUri;
    const redirectUrl = new URL(redirectUri);
    redirectUrl.searchParams.append('code', code);
    redirectUrl.searchParams.append('state', state);
    
    Utils.log('Redirecting to client', { redirectUrl: redirectUrl.toString() });
    
    // Perform redirect
    window.location.href = redirectUrl.toString();
}

/**
 * Go back to previous step
 */
function handleBack(e) {
    e.preventDefault();
    
    Utils.log('Going back to DIP step');
    
    // Reset TOTP input
    DOM.totpInput.value = '';
    Utils.setInputValidity('totp-input', null);
    
    // Show DIP step
    Utils.showStep('dip-step');
    LoginState.currentStep = 'dip';
    DOM.backBtn.classList.add('hidden');
    
    // Focus DIP input
    DOM.dipSegment1.focus();
}

/**
 * Check API health
 */
async function checkAPIHealth() {
    try {
        const response = await APIClient.getHealth();
        
        if (response.success) {
            Utils.log('API health check passed', response);
        } else {
            Utils.logError('API health check failed', response);
            Utils.showAlert('El servidor no está disponible. Por favor, intenta más tarde.', 'error', 0);
        }
    } catch (error) {
        Utils.logError('API health check error', error);
    }
}

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', initLogin);

/**
 * Handle page visibility changes
 */
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        Utils.log('Page hidden');
    } else {
        Utils.log('Page visible');
        // Optionally refresh token or session
    }
});

/**
 * Prevent autocomplete security bypass
 */
window.addEventListener('beforeunload', () => {
    // Clear sensitive data from state
    if (LoginState.validatedDIP) {
        LoginState.validatedDIP = null;
    }
});

// Prevent back button after successful login
if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.href);
}

Utils.log('Login script loaded');
