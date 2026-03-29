/* ============================================
   INDEX.JS - Landing Page Interactivity
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    initializeIndexPage();
});

function initializeIndexPage() {
    // Initialize smooth scrolling for anchor links
    initializeSmoothScroll();
    
    // Initialize FAQ accordion
    initializeFAQ();
    
    // Initialize theme preference
    initializeTheme();
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initializeSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // Skip if href is just "#"
            if (href === '#') return;
            
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Initialize FAQ accordion
 */
function initializeFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const summary = item.querySelector('summary');
        
        summary.addEventListener('click', function(e) {
            // Close other open FAQ items
            faqItems.forEach(otherItem => {
                if (otherItem !== item && otherItem.hasAttribute('open')) {
                    otherItem.removeAttribute('open');
                }
            });
        });
    });
    
    // Allow keyboard navigation
    faqItems.forEach(item => {
        const summary = item.querySelector('summary');
        
        summary.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                if (item.hasAttribute('open')) {
                    item.removeAttribute('open');
                } else {
                    item.setAttribute('open', '');
                }
            }
        });
    });
}

/**
 * Initialize theme preference
 */
function initializeTheme() {
    // Check for saved theme preference or default to system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme) {
        applyTheme(savedTheme);
    } else if (prefersDark) {
        applyTheme('dark');
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        applyTheme(e.matches ? 'dark' : 'light');
    });
}

/**
 * Apply theme to document
 */
function applyTheme(theme) {
    if (theme === 'dark') {
        document.documentElement.style.colorScheme = 'dark';
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.style.colorScheme = 'light';
        localStorage.setItem('theme', 'light');
    }
}

/**
 * Log page analytics (for development)
 */
function logPageEvent(eventName, eventData = {}) {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log(`[PlacetaID Analytics] ${eventName}`, eventData);
    }
}

/**
 * Track user navigation
 */
function trackNavigation() {
    const links = document.querySelectorAll('a');
    
    links.forEach(link => {
        link.addEventListener('click', function() {
            const href = this.getAttribute('href');
            const text = this.textContent.trim();
            
            logPageEvent('navigation_click', {
                href: href,
                text: text,
                timestamp: new Date().toISOString()
            });
        });
    });
}

/**
 * Initialize analytics tracking
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', trackNavigation);
} else {
    trackNavigation();
}

// Export for use in console
window.PlacetaIDIndex = {
    initializeIndexPage,
    initializeSmoothScroll,
    initializeFAQ,
    initializeTheme,
    applyTheme,
    logPageEvent,
    trackNavigation
};
