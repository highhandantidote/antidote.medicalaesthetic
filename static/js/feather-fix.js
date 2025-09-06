/**
 * Simple Feather Icons Fix
 * Direct initialization without complex retry logic
 */

console.log("Feather fix loaded");

// Simple initialization function
function initFeather() {
    if (typeof feather !== 'undefined' && feather.replace) {
        try {
            feather.replace();
            console.log("✅ Feather icons loaded successfully");
        } catch (error) {
            console.error("❌ Feather error:", error);
        }
    } else {
        console.log("⚠️ Feather not available");
    }
}

// Try multiple initialization points
document.addEventListener('DOMContentLoaded', initFeather);
window.addEventListener('load', initFeather);

// Also expose globally for manual calls
window.initFeather = initFeather;

// Try immediate initialization if DOM is already ready
if (document.readyState !== 'loading') {
    initFeather();
}