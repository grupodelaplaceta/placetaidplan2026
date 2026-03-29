/**
 * PlacetaID Frontend - Configuration
 */

const CONFIG = {
    // API Configuration - Static deployment, no backend
    // En producción, debe proveerse desde el backend (o inyección server-side) y NO hardcodear valores secret
    API_BASE_URL: window.PLACETAID_CONFIG?.API_BASE_URL || 'https://placetaidplan2026.vercel.app',
    API_TIMEOUT: 30000, // 30 seconds

    // OAuth Parameters (pasados desde backend / query params) - Demo mode
    OAUTH: {
        clientId: new URLSearchParams(window.location.search).get('client_id') || 'demo-client',
        redirectUri: new URLSearchParams(window.location.search).get('redirect_uri') || window.location.origin,
        state: new URLSearchParams(window.location.search).get('state') || 'demo-state',
        scope: new URLSearchParams(window.location.search).get('scope') || 'openid profile'
    },

    // DIP Configuration
    DIP: {
        segment1Length: 4,
        segment2Length: 4,
        segment3Length: 1,
        validLetters: 'TRWAGMYFPDXBNJZSQVHLCKE'
    },
    
    // TOTP Configuration
    TOTP: {
        length: 6,
        timeWindow: 1 // Allow 1 time step variance
    },
    
    // UI Configuration
    UI: {
        successRedirectDelay: 2000, // 2 seconds
        animationDuration: 300, // ms
        errorDisplayDuration: 5000 // 5 seconds
    },
    
    // Rate Limiting
    RATE_LIMIT: {
        maxAttempts: 3,
        lockoutDuration: 86400000 // 24 hours in ms
    },
    
    // Feature Flags
    FEATURES: {
        enableLogging: true,
        enableAnalytics: false
    }
};

// Log configuration in development
if (CONFIG.FEATURES.enableLogging) {
    console.log('[PlacetaID] Configuration loaded:', {
        apiUrl: CONFIG.API_BASE_URL,
        oauthClientId: CONFIG.OAUTH.clientId,
        environment: CONFIG.API_BASE_URL.includes('localhost') ? 'development' : 'production'
    });
}
