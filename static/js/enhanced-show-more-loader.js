/**
 * Enhanced Show More with Loading Indicators
 * Adds loading states to existing show more functionality
 */

// Enhanced Show More for Procedures
function enhanceShowMoreProcedures() {
    const showMoreBtn = document.getElementById('showMoreProcedures');
    const loadingDiv = document.getElementById('proceduresLoading');
    
    if (showMoreBtn) {
        showMoreBtn.addEventListener('click', function() {
            // Add loading state to button
            this.classList.add('loading');
            this.innerHTML = '<span class="btn-text">Loading More...</span>';
            
            // Show loading indicator
            if (loadingDiv) {
                loadingDiv.style.display = 'block';
                loadingDiv.innerHTML = `
                    <div class="text-center py-4">
                        <div class="spinner"></div>
                        <div class="loading-text mt-2">Loading more procedures...</div>
                    </div>
                `;
            }
        });
    }
}

// Enhanced Show More for Doctors
function enhanceShowMoreDoctors() {
    const showMoreBtn = document.getElementById('showMoreDoctors');
    const loadingDiv = document.getElementById('doctorsLoading');
    
    if (showMoreBtn) {
        showMoreBtn.addEventListener('click', function() {
            // Add loading state to button
            this.classList.add('loading');
            this.innerHTML = '<span class="btn-text">Loading More...</span>';
            
            // Show loading indicator
            if (loadingDiv) {
                loadingDiv.style.display = 'block';
                loadingDiv.innerHTML = `
                    <div class="text-center py-4">
                        <div class="spinner"></div>
                        <div class="loading-text mt-2">Finding more doctors...</div>
                    </div>
                `;
            }
        });
    }
}

// Enhanced Show More for Packages - DISABLED (handled by inline pagination script)
function enhanceShowMorePackages() {
    // Packages pagination is handled by the inline script in packages/directory.html
    // This function is disabled to prevent conflicts
    console.log('Packages show-more enhancement disabled - using inline pagination');
}

// Initialize enhanced show more functionality
document.addEventListener('DOMContentLoaded', function() {
    enhanceShowMoreProcedures();
    enhanceShowMoreDoctors();
    enhanceShowMorePackages();
});

// Function to reset button states (for use in existing show more scripts)
function resetShowMoreButtonState(buttonId, originalText = 'Show More') {
    const button = document.getElementById(buttonId);
    if (button) {
        button.classList.remove('loading');
        button.innerHTML = `<span class="btn-text">${originalText}</span>`;
    }
}

// Function to hide loading indicators
function hideShowMoreLoading(loadingDivId) {
    const loadingDiv = document.getElementById(loadingDivId);
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

// Export functions for use in other scripts
window.resetShowMoreButtonState = resetShowMoreButtonState;
window.hideShowMoreLoading = hideShowMoreLoading;