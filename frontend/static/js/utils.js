/**
 * PlacetaID Frontend - Utility Functions
 */

const Utils = {
    /**
     * Show alert message
     */
    showAlert: function(message, type = 'info', duration = CONFIG.UI.errorDisplayDuration) {
        const container = document.getElementById('alert-container');
        
        // Clear existing alerts
        container.innerHTML = '';
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            <span class="alert-icon">${this.getAlertIcon(type)}</span>
            <span class="alert-message">${message}</span>
        `;
        
        container.appendChild(alert);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                alert.remove();
            }, duration);
        }
        
        return alert;
    },
    
    /**
     * Get alert icon based on type
     */
    getAlertIcon: function(type) {
        const icons = {
            success: '✓',
            error: '✕',
            info: 'ℹ',
            warning: '⚠'
        };
        return icons[type] || 'ℹ';
    },
    
    /**
     * Clear all alerts
     */
    clearAlerts: function() {
        document.getElementById('alert-container').innerHTML = '';
    },
    
    /**
     * Validate DIP format
     */
    validateDIPFormat: function(dipFull) {
        if (!dipFull || typeof dipFull !== 'string') return false;
        
        // Remove hyphens
        const dip = dipFull.replace(/-/g, '').toUpperCase();
        
        // Check length
        if (dip.length !== 9) return false;
        
        // First 8 must be digits
        if (!dip.substring(0, 8).match(/^\d{8}$/)) return false;
        
        // Last character must be letter
        if (!dip.substring(8).match(/^[A-Z]$/)) return false;
        
        return true;
    },
    
    /**
     * Validate DIP checksum (Spanish algorithm)
     */
    validateDIPChecksum: function(dipFull) {
        if (!this.validateDIPFormat(dipFull)) return false;
        
        const dip = dipFull.replace(/-/g, '').toUpperCase();
        const number = parseInt(dip.substring(0, 8), 10);
        const letter = dip.substring(8);
        
        const LETTERS = 'TRWAGMYFPDXBNJZSQVHLCKE';
        const expectedLetter = LETTERS[number % 23];
        
        return letter === expectedLetter;
    },
    
    /**
     * Format DIP with hyphens
     */
    formatDIP: function(segment1, segment2, segment3) {
        return `${segment1}-${segment2}-${segment3}`;
    },
    
    /**
     * Extract DIP segments
     */
    getDIPSegments: function() {
        const seg1 = document.getElementById('dip-segment-1').value;
        const seg2 = document.getElementById('dip-segment-2').value;
        const seg3 = document.getElementById('dip-segment-3').value;
        
        return {
            segment1: seg1,
            segment2: seg2,
            segment3: seg3,
            full: this.formatDIP(seg1, seg2, seg3)
        };
    },
    
    /**
     * Get TOTP code from input
     */
    getTOTPCode: function() {
        const input = document.getElementById('totp-input');
        return input.value.trim().replace(/\s/g, '');
    },
    
    /**
     * Validate TOTP format
     */
    validateTOTPFormat: function(code) {
        if (!code) return false;
        
        const clean = code.replace(/\s/g, '');
        
        // Must be 6 digits
        return /^\d{6}$/.test(clean);
    },
    
    /**
     * Show/hide form step
     */
    showStep: function(stepId) {
        // Hide all steps
        document.querySelectorAll('.form-step').forEach(step => {
            step.classList.add('hidden');
        });
        
        // Show target step
        const step = document.getElementById(stepId);
        if (step) {
            step.classList.remove('hidden');
            
            // Focus first input in step
            const input = step.querySelector('input');
            if (input) input.focus();
        }
    },
    
    /**
     * Set button loading state
     */
    setButtonLoading: function(buttonId, isLoading) {
        const btn = document.getElementById(buttonId);
        if (!btn) return;
        
        if (isLoading) {
            btn.classList.add('loading');
            btn.disabled = true;
        } else {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    },
    
    /**
     * Set input field validity state
     */
    setInputValidity: function(inputId, isValid) {
        const input = document.getElementById(inputId);
        if (!input) return;
        
        if (isValid) {
            input.classList.add('valid');
            input.classList.remove('invalid');
        } else if (isValid === false) {
            input.classList.add('invalid');
            input.classList.remove('valid');
        } else {
            input.classList.remove('valid', 'invalid');
        }
    },
    
    /**
     * Reset form to initial state
     */
    resetForm: function() {
        document.getElementById('login-form').reset();
        this.showStep('dip-step');
        this.clearAlerts();
        document.querySelectorAll('input').forEach(input => {
            input.classList.remove('valid', 'invalid');
        });
        Utils.setButtonLoading('validate-dip-btn', false);
        Utils.setButtonLoading('validate-totp-btn', false);
        document.getElementById('back-btn').classList.add('hidden');
    },
    
    /**
     * Log message (if logging enabled)
     */
    log: function(message, data = null) {
        if (CONFIG.FEATURES.enableLogging) {
            console.log(`[PlacetaID] ${message}`, data || '');
        }
    },
    
    /**
     * Log error (if logging enabled)
     */
    logError: function(message, error = null) {
        if (CONFIG.FEATURES.enableLogging) {
            console.error(`[PlacetaID] ERROR: ${message}`, error || '');
        }
    },
    
    /**
     * Debounce function calls
     */
    debounce: function(func, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    },
    
    /**
     * Check if device has touch support
     */
    isTouchDevice: function() {
        return (('ontouchstart' in window) ||
                (navigator.maxTouchPoints > 0) ||
                (navigator.msMaxTouchPoints > 0));
    },
    
    /**
     * Get user agent info
     */
    getUserAgent: function() {
        return navigator.userAgent;
    },
    
    /**
     * Get client IP (via backend if needed)
     */
    getClientInfo: function() {
        return {
            userAgent: this.getUserAgent(),
            language: navigator.language,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timestamp: new Date().toISOString()
        };
    }
};

// Export for use in other scripts
window.Utils = Utils;
