// Force Mobile Back Button Visibility - JavaScript Emergency Fix
console.log('Mobile back button force script loaded');

// Prevent multiple executions
let isProcessing = false;

function createFloatingBackButton() {
    // Check if we're on desktop (screen width >= 992px)
    if (window.innerWidth >= 992) {
        console.log('Desktop detected - not creating back button');
        return;
    }
    
    // Create a floating back button that's positioned absolutely
    const isHomepage = document.body.classList.contains('homepage');
    if (isHomepage) {
        console.log('Homepage detected - not creating back button');
        return;
    }

    // Remove existing floating button if it exists
    const existingBtn = document.querySelector('.floating-back-btn');
    if (existingBtn) {
        console.log('Removing existing floating back button');
        existingBtn.remove();
    }

    console.log('Creating floating back button...');
    
    const floatingBtn = document.createElement('button');
    floatingBtn.className = 'floating-back-btn';
    floatingBtn.onclick = function() { window.history.back(); };
    // Use a simple text arrow instead of FontAwesome icon
    floatingBtn.innerHTML = '←';
    
    // Position it in the center of the navbar area - simple arrow design
    floatingBtn.style.cssText = `
        position: fixed !important;
        top: 12px !important;
        left: 20px !important;
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 100000 !important;
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 8px !important;
        width: auto !important;
        height: auto !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    `;
    
    // Style the text arrow
    floatingBtn.style.cssText += `
        color: #4FACFE !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        line-height: 1 !important;
        text-align: center !important;
        font-family: Arial, sans-serif !important;
    `;
    
    // Add hover effects - simple opacity change
    floatingBtn.addEventListener('mouseenter', function() {
        this.style.opacity = '0.7 !important';
        this.style.transform = 'translateX(-2px) !important';
    });
    
    floatingBtn.addEventListener('mouseleave', function() {
        this.style.opacity = '1 !important';
        this.style.transform = 'translateX(0) !important';
    });
    
    // Add to body
    document.body.appendChild(floatingBtn);
    
    console.log('Floating back button created and added to page');
}

function forceMobileBackButtonVisibility() {
    // Prevent multiple simultaneous executions
    if (isProcessing) {
        console.log('Already processing back buttons - skipping');
        return;
    }
    
    isProcessing = true;
    console.log('Forcing mobile back button visibility...');
    
    // Check if we're on desktop (screen width >= 992px)
    if (window.innerWidth >= 992) {
        console.log('Desktop detected - skipping back button completely');
        isProcessing = false;
        return;
    }
    
    // Find all mobile back buttons (only on mobile)
    const backButtons = document.querySelectorAll('.mobile-back-btn');
    console.log('Found back buttons:', backButtons.length);
    
    backButtons.forEach((button, index) => {
        console.log(`Processing button ${index + 1}:`, button);
        
        // Force visibility with inline styles
        button.style.cssText = `
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            z-index: 99999 !important;
            background: transparent !important;
            border: none !important;
            padding: 12px !important;
            margin-right: 8px !important;
            min-width: 44px !important;
            min-height: 44px !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        `;
        
        // Force icon visibility
        const icon = button.querySelector('i');
        if (icon) {
            console.log(`Processing icon for button ${index + 1}:`, icon);
            icon.style.cssText = `
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                color: #4FACFE !important;
                font-size: 20px !important;
                font-weight: 600 !important;
                line-height: 1 !important;
                width: 20px !important;
                height: 20px !important;
                text-align: center !important;
                margin: 0 !important;
            `;
        }
        
        // Remove any problematic classes
        button.classList.remove('d-lg-none', 'btn', 'btn-link', 'p-0', 'me-3');
        
        console.log(`Button ${index + 1} forced to be visible`);
    });
    
    // Check if we're on non-homepage
    const isHomepage = document.body.classList.contains('homepage');
    console.log('Is homepage:', isHomepage);
    
    // Only create floating button if no existing buttons were found or made visible
    if (backButtons.length === 0) {
        createFloatingBackButton();
    }
    
    // Reset processing flag
    isProcessing = false;
}

// Run immediately when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', forceMobileBackButtonVisibility);
} else {
    forceMobileBackButtonVisibility();
}

// Also run after a short delay to catch any dynamic content (but only once)
let hasRunDelayed = false;
setTimeout(() => {
    if (!hasRunDelayed) {
        hasRunDelayed = true;
        forceMobileBackButtonVisibility();
    }
}, 500);

// Add window resize listener to handle screen size changes
window.addEventListener('resize', function() {
    forceMobileBackButtonVisibility();
});

console.log('Mobile back button force script initialization complete');