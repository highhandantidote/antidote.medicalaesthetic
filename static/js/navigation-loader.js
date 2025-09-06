/**
 * Navigation Loading System
 * Provides comprehensive loading indicators for page navigation
 */

class NavigationLoader {
    constructor() {
        this.isLoading = false;
        this.loadingTimeout = null;
        this.progressInterval = null;
        this.currentProgress = 0;
        
        this.init();
    }
    
    init() {
        this.createLoaderElements();
        this.bindNavigationEvents();
        this.handleBrowserNavigation();
        
        // Handle page load completion
        window.addEventListener('load', () => {
            this.hideLoader();
        });
        
        console.log('Navigation loader initialized');
    }
    
    createLoaderElements() {
        // Create main page loader
        if (!document.getElementById('pageLoader')) {
            const loader = document.createElement('div');
            loader.id = 'pageLoader';
            loader.className = 'page-loader';
            loader.innerHTML = `
                <div class="spinner"></div>
                <div class="loading-text" id="loadingText">Loading...</div>
            `;
            document.body.appendChild(loader);
        }
        
        // Create progress bar
        if (!document.getElementById('progressBar')) {
            const progressBar = document.createElement('div');
            progressBar.id = 'progressBar';
            progressBar.className = 'progress-bar-loader';
            document.body.appendChild(progressBar);
        }
    }
    
    bindNavigationEvents() {
        // Handle all anchor tag clicks
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            
            if (this.shouldShowLoader(link)) {
                this.showLoader(this.getLoadingMessage(link.href));
                this.startProgressBar();
                
                // Add loading state to the clicked link
                link.classList.add('loading');
                
                // Set timeout for slow loading pages
                this.setLoadingTimeout();
            }
        });
        
        // Handle form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.method && form.method.toLowerCase() === 'get') {
                this.showLoader('Searching...');
                this.startProgressBar();
            }
        });
        
        // Handle search form specifically
        const searchForms = document.querySelectorAll('form[action*="search"]');
        searchForms.forEach(form => {
            form.addEventListener('submit', () => {
                this.showLoader('Searching procedures and doctors...');
                this.startProgressBar();
            });
        });
    }
    
    shouldShowLoader(link) {
        if (!link) return false;
        
        const href = link.href;
        if (!href) return false;
        
        // Don't show loader for:
        // - External links
        // - Anchors on same page
        // - Download links
        // - mailto/tel links
        // - JavaScript links
        if (
            href.startsWith('mailto:') ||
            href.startsWith('tel:') ||
            href.startsWith('javascript:') ||
            href.includes('#') && href.split('#')[0] === window.location.href.split('#')[0] ||
            link.target === '_blank' ||
            link.download ||
            !href.startsWith(window.location.origin)
        ) {
            return false;
        }
        
        // Don't show loader if already on the same page
        if (href === window.location.href) {
            return false;
        }
        
        return true;
    }
    
    getLoadingMessage(url) {
        const messages = {
            '/procedures': 'Loading procedures...',
            '/doctors': 'Loading doctors...',
            '/packages/': 'Loading treatment packages...',
            '/packages': 'Loading treatment packages...',
            '/clinic/all': 'Loading clinics...',
            '/community': 'Loading community posts...',
            '/face-analysis/': 'Loading face analysis...',
            '/face-analysis': 'Loading face analysis...',
            '/ai-recommendations': 'Loading AI recommendations...',
            '/search': 'Searching...',
            '/login': 'Loading login page...',
            '/register': 'Loading registration...',
            '/dashboard': 'Loading dashboard...'
        };
        
        // Find matching message
        for (const [path, message] of Object.entries(messages)) {
            if (url.includes(path)) {
                return message;
            }
        }
        
        // Check for dynamic routes
        if (url.includes('/doctor/')) {
            return 'Loading doctor profile...';
        } else if (url.includes('/procedure/')) {
            return 'Loading procedure details...';
        } else if (url.includes('/clinic/')) {
            return 'Loading clinic information...';
        }
        
        return 'Loading page...';
    }
    
    showLoader(message = 'Loading...') {
        if (this.isLoading) return;
        
        this.isLoading = true;
        const loader = document.getElementById('pageLoader');
        const loadingText = document.getElementById('loadingText');
        
        if (loader && loadingText) {
            loadingText.textContent = message;
            loader.classList.add('active');
        }
        
        // Show progress bar
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.style.display = 'block';
        }
        
        console.log(`Showing loader: ${message}`);
    }
    
    hideLoader() {
        if (!this.isLoading) return;
        
        this.isLoading = false;
        const loader = document.getElementById('pageLoader');
        const progressBar = document.getElementById('progressBar');
        
        // Complete progress bar
        if (progressBar) {
            progressBar.style.width = '100%';
            setTimeout(() => {
                progressBar.style.display = 'none';
            }, 200);
        }
        
        if (loader) {
            loader.classList.remove('active');
        }
        
        // Remove loading states from links
        document.querySelectorAll('.nav-link.loading, .btn.loading, a.loading').forEach(el => {
            el.classList.remove('loading');
        });
        
        // Clear timeout
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
            this.loadingTimeout = null;
        }
        
        // Clear progress interval
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
        this.currentProgress = 0;
        console.log('Loader hidden');
    }
    
    startProgressBar() {
        const progressBar = document.getElementById('progressBar');
        if (!progressBar) return;
        
        this.currentProgress = 0;
        progressBar.style.width = '0%';
        
        // Simulate progress
        this.progressInterval = setInterval(() => {
            this.currentProgress += Math.random() * 15;
            if (this.currentProgress > 90) {
                this.currentProgress = 90; // Don't complete until page loads
            }
            progressBar.style.width = this.currentProgress + '%';
        }, 200);
    }
    
    setLoadingTimeout() {
        // If page takes too long, show a different message
        this.loadingTimeout = setTimeout(() => {
            const loadingText = document.getElementById('loadingText');
            if (loadingText && this.isLoading) {
                loadingText.textContent = 'Still loading... Please wait';
            }
            
            // Set another timeout for very slow loading
            this.loadingTimeout = setTimeout(() => {
                if (this.isLoading) {
                    const loadingText = document.getElementById('loadingText');
                    if (loadingText) {
                        loadingText.textContent = 'Taking longer than expected...';
                    }
                }
            }, 5000);
        }, 3000);
    }
    
    handleBrowserNavigation() {
        // Handle browser back/forward buttons
        window.addEventListener('beforeunload', () => {
            this.showLoader('Loading...');
        });
        
        // Handle page show (for back/forward cache)
        window.addEventListener('pageshow', () => {
            this.hideLoader();
        });
        
        // Handle visibility change (when user switches tabs)
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && this.isLoading) {
                // Reset loader state when user comes back to tab
                setTimeout(() => {
                    this.hideLoader();
                }, 1000);
            }
        });
    }
    
    // Public methods for manual control
    show(message) {
        this.showLoader(message);
        this.startProgressBar();
    }
    
    hide() {
        this.hideLoader();
    }
    
    // Method for AJAX requests
    showForAjax(message = 'Loading...') {
        this.showLoader(message);
    }
    
    hideForAjax() {
        this.hideLoader();
    }
}

// Initialize the navigation loader when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.navigationLoader = new NavigationLoader();
});

// Export for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NavigationLoader;
}