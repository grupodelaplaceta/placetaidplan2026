/**
 * PlacetaID Frontend - Configuration
 */

const CONFIG = {
    // API Configuration
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:5000',
    API_TIMEOUT: 30000, // 30 seconds
    
    // OAuth Parameters (passed from backend)
    OAUTH: {
        clientId: new URLSearchParams(window.location.search).get('client_id') || '',
        redirectUri: new URLSearchParams(window.location.search).get('redirect_uri') || '',
        state: new URLSearchParams(window.location.search).get('state') || '',
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
