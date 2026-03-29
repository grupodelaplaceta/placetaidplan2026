/**
 * PlacetaID Frontend - Dashboard Logic
 */

// State management
const DashboardState = {
    accessToken: null,
    citizenData: null,
    isLoading: false
};

// DOM Elements cache
const DashboardDOM = {
    logoutBtn: null,
    twoFAModal: null,
    enableTwoFABtn: null,
    disableTwoFABtn: null,
    closeTwoFAModal: null,
    confirmTwoFABtn: null
};

/**
 * Initialize dashboard
 */
function initDashboard() {
    Utils.log('Initializing dashboard');
    
    // Check authentication
    checkAuthentication();
    
    // Cache DOM elements
    cacheDashboardDOM();
    
    // Load user data
    loadUserProfile();
    
    // Setup event listeners
    setupDashboardListeners();
}

/**
 * Check if user is authenticated
 */
function checkAuthentication() {
    // Get access token from localStorage or URL
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('access_token') || localStorage.getItem('access_token');
    
    if (!token) {
        Utils.log('No authentication token found, redirecting to login');
        window.location.href = '/login.html';
        return;
    }
    
    DashboardState.accessToken = token;
    localStorage.setItem('access_token', token);
    
    // Remove token from URL
    if (window.history.replaceState) {
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

/**
 * Cache dashboard DOM elements
 */
function cacheDashboardDOM() {
    DashboardDOM.logoutBtn = document.getElementById('logout-btn');
    DashboardDOM.twoFAModal = document.getElementById('2fa-modal');
    DashboardDOM.enableTwoFABtn = document.getElementById('enable-2fa-btn');
    DashboardDOM.disableTwoFABtn = document.getElementById('disable-2fa-btn');
    DashboardDOM.closeTwoFAModal = document.getElementById('close-2fa-modal');
    DashboardDOM.confirmTwoFABtn = document.getElementById('confirm-2fa-btn');
}

/**
 * Setup dashboard event listeners
 */
function setupDashboardListeners() {
    // Logout
    if (DashboardDOM.logoutBtn) {
        DashboardDOM.logoutBtn.addEventListener('click', handleLogout);
    }
    
    // 2FA
    if (DashboardDOM.enableTwoFABtn) {
        DashboardDOM.enableTwoFABtn.addEventListener('click', handleEnableTwoFA);
    }
    
    if (DashboardDOM.disableTwoFABtn) {
        DashboardDOM.disableTwoFABtn.addEventListener('click', handleDisableTwoFA);
    }
    
    if (DashboardDOM.closeTwoFAModal) {
        DashboardDOM.closeTwoFAModal.addEventListener('click', closeTwoFAModal);
    }
    
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href) {
                e.preventDefault();
                
                // Update active link
                document.querySelectorAll('.nav-link').forEach(l => {
                    l.classList.remove('active');
                });
                link.classList.add('active');
                
                // Scroll to section
                const sectionId = href.substring(1);
                const section = document.getElementById(sectionId);
                if (section) {
                    section.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
}

/**
 * Load user profile data
 */
async function loadUserProfile() {
    Utils.log('Loading user profile');
    
    DashboardState.isLoading = true;
    
    // Create API client with auth token
    const response = await fetch(`${CONFIG.API_BASE_URL}/oauth/profile`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${DashboardState.accessToken}`,
            'Content-Type': 'application/json'
        }
    });
    
    if (!response.ok) {
        Utils.logError('Failed to load profile', response.status);
        
        if (response.status === 401) {
            // Token expired, redirect to login
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
        }
        
        Utils.showAlert('Error al cargar el perfil', 'error');
        DashboardState.isLoading = false;
        return;
    }
    
    const data = await response.json();
    DashboardState.citizenData = data;
    
    Utils.log('Profile loaded', data);
    
    // Display user data
    displayUserProfile(data);
    
    DashboardState.isLoading = false;
}

/**
 * Display user profile information
 */
function displayUserProfile(data) {
    // Update profile information
    document.getElementById('citizen-id-display').textContent = data.citizen_id || '-';
    document.getElementById('account-status-display').textContent = data.status || '-';
    document.getElementById('age-tier-display').textContent = data.age_tier || 'Desconocido';
    
    // Format dates
    const createdAt = new Date(data.created_at);
    document.getElementById('created-at-display').textContent = createdAt.toLocaleDateString('es-ES');
    
    if (data.last_login_at) {
        const lastLogin = new Date(data.last_login_at);
        document.getElementById('last-login-display').textContent = lastLogin.toLocaleDateString('es-ES');
    } else {
        document.getElementById('last-login-display').textContent = 'Nunca';
    }
    
    // Update 2FA status
    updateTwoFAStatus(data.totp_enabled);
}

/**
 * Update 2FA status display
 */
function updateTwoFAStatus(isEnabled) {
    const statusBadge = document.getElementById('2fa-badge');
    const disabledContent = document.getElementById('2fa-disabled-content');
    const enabledContent = document.getElementById('2fa-enabled-content');
    
    if (isEnabled) {
        statusBadge.textContent = 'Activado';
        statusBadge.className = 'status-badge active';
        disabledContent.classList.add('hidden');
        enabledContent.classList.remove('hidden');
    } else {
        statusBadge.textContent = 'Desactivado';
        statusBadge.className = 'status-badge inactive';
        disabledContent.classList.remove('hidden');
        enabledContent.classList.add('hidden');
    }
}

/**
 * Handle enable 2FA
 */
async function handleEnableTwoFA() {
    Utils.log('Enabling 2FA');
    
    // Show modal
    DashboardDOM.twoFAModal.classList.remove('hidden');
    
    // Make API call to enable
    const response = await fetch(`${CONFIG.API_BASE_URL}/oauth/2fa/enable`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${DashboardState.accessToken}`,
            'Content-Type': 'application/json'
        }
    });
    
    if (!response.ok) {
        Utils.showAlert('Error al activar 2FA', 'error');
        return;
    }
    
    const data = await response.json();
    
    Utils.log('2FA enabled response', data);
    
    // Display QR code and secret
    document.getElementById('qr-code').src = data.qr_uri;
    document.getElementById('totp-secret').textContent = data.secret;
    
    // Display backup codes
    const backupCodesContainer = document.getElementById('backup-codes');
    backupCodesContainer.innerHTML = data.backup_codes
        .map(code => `<div class="backup-code">${code}</div>`)
        .join('');
    
    // Show step 2
    showTwoFAStep(2);
}

/**
 * Handle disable 2FA
 */
async function handleDisableTwoFA() {
    // Request verification code
    const code = prompt('Ingresa tu código 2FA para confirmar:');
    
    if (!code) return;
    
    Utils.log('Disabling 2FA');
    
    const response = await fetch(`${CONFIG.API_BASE_URL}/oauth/2fa/disable`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${DashboardState.accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code })
    });
    
    if (!response.ok) {
        const data = await response.json();
        Utils.showAlert(data.message || 'Error al desactivar 2FA', 'error');
        return;
    }
    
    Utils.showAlert('2FA desactivado correctamente', 'success');
    
    // Update status
    DashboardState.citizenData.totp_enabled = false;
    updateTwoFAStatus(false);
    
    closeTwoFAModal();
}

/**
 * Confirm 2FA setup
 */
async function confirmTwoFASetup() {
    const code = document.getElementById('2fa-verify-code').value;
    
    if (!Utils.validateTOTPFormat(code)) {
        Utils.showAlert('El código debe tener 6 dígitos', 'error');
        return;
    }
    
    Utils.log('Confirming 2FA setup');
    
    const response = await fetch(`${CONFIG.API_BASE_URL}/oauth/2fa/confirm`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${DashboardState.accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code })
    });
    
    if (!response.ok) {
        const data = await response.json();
        Utils.showAlert(data.message || 'Código inválido', 'error');
        return;
    }
    
    Utils.showAlert('2FA configurado correctamente', 'success');
    
    // Update status
    DashboardState.citizenData.totp_enabled = true;
    updateTwoFAStatus(true);
    
    closeTwoFAModal();
}

/**
 * Show specific 2FA setup step
 */
function showTwoFAStep(stepNumber) {
    document.querySelectorAll('.setup-step').forEach(step => {
        step.classList.add('hidden');
    });
    
    const stepId = `2fa-setup-step-${stepNumber}`;
    const step = document.getElementById(stepId);
    if (step) {
        step.classList.remove('hidden');
    }
    
    // Setup next button for step 1
    if (stepNumber === 1) {
        const nextBtn = document.getElementById('next-2fa-step-btn');
        nextBtn.onclick = () => showTwoFAStep(2);
    }
    
    // Setup next button for step 2
    if (stepNumber === 2) {
        const nextBtn = document.getElementById('next-2fa-verify-btn');
        nextBtn.onclick = () => showTwoFAStep(3);
    }
    
    // Setup confirm button for step 3
    if (stepNumber === 3) {
        DashboardDOM.confirmTwoFABtn.onclick = confirmTwoFASetup;
    }
}

/**
 * Close 2FA modal
 */
function closeTwoFAModal() {
    DashboardDOM.twoFAModal.classList.add('hidden');
    
    // Reset form
    document.getElementById('2fa-verify-code').value = '';
    showTwoFAStep(1);
}

/**
 * Handle logout
 */
async function handleLogout() {
    Utils.log('Logging out');
    
    // Call logout endpoint
    await fetch(`${CONFIG.API_BASE_URL}/oauth/logout`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${DashboardState.accessToken}`,
            'Content-Type': 'application/json'
        }
    });
    
    // Clear local storage
    localStorage.removeItem('access_token');
    
    // Redirect to login
    window.location.href = '/login.html';
}

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', initDashboard);

Utils.log('Dashboard script loaded');
