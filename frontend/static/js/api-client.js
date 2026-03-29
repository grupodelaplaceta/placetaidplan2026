/**
 * PlacetaID Frontend - API Client
 */

const APIClient = {
    /**
     * Make API request
     */
    request: async function(endpoint, options = {}) {
        const url = CONFIG.API_BASE_URL + endpoint;
        const defaultOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout: CONFIG.API_TIMEOUT,
            credentials: 'include' // Include cookies for CORS
        };
        
        try {
            Utils.log(`Requesting: ${options.method || 'POST'} ${endpoint}`);
            
            const response = await fetch(url, {
                ...defaultOptions,
                ...options
            });
            
            // Parse response
            let data;
            try {
                data = await response.json();
            } catch (e) {
                data = { error: 'Invalid response format' };
            }
            
            Utils.log(`Response: ${response.status}`, data);
            
            // Handle HTTP errors
            if (!response.ok) {
                throw {
                    status: response.status,
                    error: data.error || 'Request failed',
                    message: data.message || data.error || 'An error occurred',
                    ...data
                };
            }
            
            return {
                success: true,
                status: response.status,
                ...data
            };
            
        } catch (error) {
            Utils.logError(`API request failed: ${endpoint}`, error);
            
            return {
                success: false,
                status: error.status || 0,
                error: error.error || 'Network error',
                message: error.message || 'Failed to connect to server'
            };
        }
    },
    
    /**
     * Validate DIP
     */
    validateDIP: async function(dip) {
        return this.request('/oauth/authorize', {
            method: 'POST',
            body: JSON.stringify({
                dip: dip
            })
        });
    },
    
    /**
     * Validate TOTP
     */
    validateTOTP: async function(dip, code) {
        return this.request('/oauth/authorize', {
            method: 'POST',
            body: JSON.stringify({
                dip: dip,
                code: code
            })
        });
    },
    
    /**
     * Get token from authorization code
     */
    getToken: async function(code, citizenId) {
        return this.request('/oauth/token', {
            method: 'POST',
            body: JSON.stringify({
                grant_type: 'authorization_code',
                code: code,
                client_id: CONFIG.OAUTH.clientId,
                redirect_uri: CONFIG.OAUTH.redirectUri
            })
        });
    },
    
    /**
     * Validate authorization
     */
    validateAuthorization: async function(citizenId) {
        return this.request('/oauth/validate', {
            method: 'POST',
            body: JSON.stringify({
                citizen_id: citizenId,
                client_id: CONFIG.OAUTH.clientId,
                redirect_uri: CONFIG.OAUTH.redirectUri,
                state: CONFIG.OAUTH.state,
                scope: CONFIG.OAUTH.scope
            })
        });
    },
    
    /**
     * Get health status
     */
    getHealth: async function() {
        return this.request('/health', {
            method: 'GET',
            body: null
        });
    },
    
    /**
     * Handle error response
     */
    handleError: function(response) {
        if (!response.success) {
            const errorMsg = response.message || response.error || 'An error occurred';
            Utils.showAlert(errorMsg, 'error');
            Utils.logError(errorMsg, response);
            return false;
        }
        return true;
    }
};

// Export for use in other scripts
window.APIClient = APIClient;
