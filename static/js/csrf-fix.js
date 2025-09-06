/**
 * Phase 4: CSRF Token Fix
 * Properly handle CSRF tokens in AJAX requests
 */

console.log("CSRF fix loaded");

// Get CSRF token from meta tag
function getCSRFToken() {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
        return csrfMeta.getAttribute('content');
    }
    
    // Fallback: try to get from form
    const csrfInput = document.querySelector('input[name="csrf_token"]');
    if (csrfInput) {
        return csrfInput.value;
    }
    
    console.warn("⚠️ CSRF token not found");
    return null;
}

// Enhanced fetch function with CSRF token
function fetchWithCSRF(url, options = {}) {
    const csrfToken = getCSRFToken();
    
    // Set up headers
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    // Add CSRF token to headers
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
        headers['X-Requested-With'] = 'XMLHttpRequest';
    }
    
    // Merge options
    const finalOptions = {
        ...options,
        headers
    };
    
    // Add CSRF token to body for POST requests
    if (options.method === 'POST' && options.body) {
        try {
            const bodyData = JSON.parse(options.body);
            bodyData.csrf_token = csrfToken;
            finalOptions.body = JSON.stringify(bodyData);
        } catch (e) {
            // Body is not JSON, try form data
            if (typeof options.body === 'string' && csrfToken) {
                finalOptions.body += `&csrf_token=${encodeURIComponent(csrfToken)}`;
            }
        }
    }
    
    return fetch(url, finalOptions);
}

// Fix banner impression API calls
function trackBannerImpression(bannerId, position) {
    const csrfToken = getCSRFToken();
    
    if (!csrfToken) {
        console.warn("⚠️ Cannot track banner impression: CSRF token not found");
        return;
    }
    
    const data = {
        banner_id: bannerId,
        position: position,
        csrf_token: csrfToken
    };
    
    fetch('/api/banners/impression', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
    }).then(response => {
        if (response.ok) {
            console.log("✅ Banner impression tracked successfully");
        } else {
            console.warn("⚠️ Banner impression tracking failed:", response.status);
        }
    }).catch(error => {
        console.error("❌ Banner impression tracking error:", error);
    });
}

// Expose functions globally
window.fetchWithCSRF = fetchWithCSRF;
window.getCSRFToken = getCSRFToken;
window.trackBannerImpression = trackBannerImpression;

console.log("✅ CSRF fix initialized");