/**
 * Page-Specific Skeleton Loading System
 * Shows contextual skeleton loaders based on page type
 */

class PageSkeletonLoader {
    constructor() {
        this.init();
    }
    
    init() {
        this.bindNavigationEvents();
        console.log('Page skeleton loader initialized');
    }
    
    bindNavigationEvents() {
        // Override the navigation loader to show skeletons
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (this.shouldShowSkeleton(link)) {
                const pageType = this.getPageType(link.href);
                this.showSkeletonForPage(pageType);
            }
        });
        
        // Handle form submissions (search)
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.action && form.action.includes('search')) {
                this.showSkeletonForPage('search');
            }
        });
    }
    
    shouldShowSkeleton(link) {
        if (!link || !link.href) return false;
        
        // Same logic as navigation loader
        const href = link.href;
        return (
            href.startsWith(window.location.origin) &&
            !href.startsWith('mailto:') &&
            !href.startsWith('tel:') &&
            !href.startsWith('javascript:') &&
            !href.includes('#') &&
            !link.download &&
            link.target !== '_blank' &&
            href !== window.location.href
        );
    }
    
    getPageType(url) {
        if (url.includes('/procedures')) return 'procedures';
        if (url.includes('/doctors')) return 'doctors';
        if (url.includes('/packages')) return 'packages';
        if (url.includes('/clinic/all') || url.includes('/clinics')) return 'clinics';
        if (url.includes('/community')) return 'community';
        if (url.includes('/search')) return 'search';
        if (url.includes('/face-analysis')) return 'face-analysis';
        
        return 'general';
    }
    
    showSkeletonForPage(pageType) {
        // Hide existing content with fade out
        const mainContent = document.querySelector('main, .container, #content');
        if (mainContent) {
            mainContent.style.opacity = '0.3';
            mainContent.style.pointerEvents = 'none';
        }
        
        // Show appropriate skeleton
        this.hideAllSkeletons();
        
        const skeletonId = this.getSkeletonId(pageType);
        const skeleton = document.getElementById(skeletonId);
        
        if (skeleton) {
            skeleton.style.display = 'block';
            
            // Insert skeleton into main content area
            if (mainContent) {
                const skeletonContainer = document.createElement('div');
                skeletonContainer.className = 'skeleton-overlay';
                skeletonContainer.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    z-index: 100;
                    background: rgba(255, 255, 255, 0.9);
                    padding: 20px;
                `;
                
                // Clone skeleton content
                skeletonContainer.appendChild(skeleton.cloneNode(true));
                skeletonContainer.firstChild.style.display = 'block';
                
                // Add to main content
                if (mainContent.style.position !== 'relative') {
                    mainContent.style.position = 'relative';
                }
                mainContent.appendChild(skeletonContainer);
                
                // Auto-hide after timeout (fallback)
                setTimeout(() => {
                    this.hideSkeleton();
                }, 10000);
            }
        }
        
        console.log(`Showing skeleton for page type: ${pageType}`);
    }
    
    getSkeletonId(pageType) {
        const skeletonMap = {
            'procedures': 'proceduresSkeleton',
            'doctors': 'doctorsSkeleton', 
            'packages': 'packagesSkeleton',
            'clinics': 'clinicsSkeleton',
            'community': 'communitySkeleton',
            'search': 'searchSkeleton',
            'general': 'proceduresSkeleton' // Default fallback
        };
        
        return skeletonMap[pageType] || skeletonMap['general'];
    }
    
    hideAllSkeletons() {
        const skeletons = [
            'proceduresSkeleton',
            'doctorsSkeleton',
            'packagesSkeleton',
            'clinicsSkeleton',
            'communitySkeleton',
            'searchSkeleton'
        ];
        
        skeletons.forEach(id => {
            const skeleton = document.getElementById(id);
            if (skeleton) {
                skeleton.style.display = 'none';
            }
        });
    }
    
    hideSkeleton() {
        // Remove skeleton overlays
        document.querySelectorAll('.skeleton-overlay').forEach(overlay => {
            overlay.remove();
        });
        
        // Restore main content
        const mainContent = document.querySelector('main, .container, #content');
        if (mainContent) {
            mainContent.style.opacity = '1';
            mainContent.style.pointerEvents = 'auto';
        }
        
        this.hideAllSkeletons();
        console.log('Skeleton hidden');
    }
}

// Initialize page skeleton loader
document.addEventListener('DOMContentLoaded', () => {
    window.pageSkeletonLoader = new PageSkeletonLoader();
    
    // Listen for page load completion to hide skeletons
    window.addEventListener('load', () => {
        setTimeout(() => {
            if (window.pageSkeletonLoader) {
                window.pageSkeletonLoader.hideSkeleton();
            }
        }, 500);
    });
});

// Export for potential use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PageSkeletonLoader;
}