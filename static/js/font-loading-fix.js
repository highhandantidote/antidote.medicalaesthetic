
// Phase 4A Font Loading Fix
(function() {
    'use strict';
    
    // Font loading optimization
    function optimizeFontLoading() {
        // Add font-display: swap to existing fonts
        const fontLinks = document.querySelectorAll('link[href*="fonts.googleapis.com"]');
        fontLinks.forEach(link => {
            if (!link.href.includes('display=swap')) {
                link.href = link.href.replace('&display=swap', '').replace('display=swap', '') + '&display=swap';
            }
        });
        
        // Preload critical fonts
        const preloadFont = (fontUrl, fontFamily) => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = fontUrl;
            link.as = 'font';
            link.type = 'font/woff2';
            link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
        };
        
        // Add font-face loading class when fonts are loaded
        if ('fonts' in document) {
            document.fonts.ready.then(() => {
                document.body.classList.add('font-loaded');
            });
        }
    }
    
    // Run font optimization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', optimizeFontLoading);
    } else {
        optimizeFontLoading();
    }
})();
