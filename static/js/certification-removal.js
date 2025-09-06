// NUCLEAR CERTIFICATION REMOVAL JAVASCRIPT
// This script will run on every page load to remove certification content

(function() {
    'use strict';
    
    // Function to remove certification content aggressively
    function removeAllCertificationContent() {
        // Method 1: Remove by text content
        const textNodesToRemove = [];
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const certificationTexts = [
            'Trusted Expertise',
            'Certified Professionals',
            'Trusted Expertise, Certified Professionals',
            'ISAPS',
            'FDA',
            'CE'
        ];
        
        let textNode;
        while (textNode = walker.nextNode()) {
            const text = textNode.textContent.trim();
            if (certificationTexts.some(term => text.includes(term))) {
                textNodesToRemove.push(textNode);
            }
        }
        
        // Remove text nodes and their containers
        textNodesToRemove.forEach(textNode => {
            let container = textNode.parentElement;
            while (container && container !== document.body) {
                const containerText = container.textContent.trim();
                if (containerText.includes('Trusted Expertise') && 
                    containerText.includes('Certified Professionals') &&
                    containerText.length < 500) {
                    if (container.parentNode) {
                        container.parentNode.removeChild(container);
                    }
                    break;
                }
                container = container.parentElement;
            }
        });
        
        // Method 2: Remove by image attributes
        const imageSelectors = [
            'img[alt*="ISAPS"]',
            'img[alt*="FDA"]',
            'img[alt*="CE"]',
            'img[src*="isaps"]',
            'img[src*="fda"]',
            'img[src*="cert"]',
            'img[title*="ISAPS"]',
            'img[title*="FDA"]',
            'img[title*="CE"]',
            'img[alt*="isaps" i]',
            'img[alt*="fda" i]',
            'img[alt*="ce" i]',
            'img[src*="isaps" i]',
            'img[src*="fda" i]',
            'img[src*="cert" i]'
        ];
        
        imageSelectors.forEach(selector => {
            const images = document.querySelectorAll(selector);
            images.forEach(img => {
                // Remove the image and its container
                let container = img.parentElement;
                while (container && container !== document.body) {
                    const containerText = container.textContent.trim();
                    if (containerText.includes('Trusted') || 
                        containerText.includes('Certified') ||
                        containerText.includes('ISAPS') ||
                        containerText.includes('FDA') ||
                        containerText.includes('CE')) {
                        if (container.parentNode) {
                            container.parentNode.removeChild(container);
                        }
                        break;
                    }
                    container = container.parentElement;
                }
            });
        });
        
        // Method 3: Remove by container class patterns
        const containerSelectors = [
            '.certification-section',
            '.certification-logos',
            '.cert-logos',
            '.trusted-logos',
            '.medical-certifications',
            '.accreditation-section',
            '.accreditation-logos',
            '.trust-section',
            '.expertise-section',
            '.professionals-section',
            '.trust-logos',
            '.medical-logos',
            '.certification-container',
            '.trust-container',
            '.expertise-container',
            '.professional-container',
            '.trust-badges',
            '.medical-badges',
            '.certification-badges',
            '.accreditation-badges',
            '.trust-seals',
            '.medical-seals',
            '.certification-seals',
            '.accreditation-seals',
            'div[class*="trust"]',
            'div[class*="certifi"]',
            'div[class*="expertise"]',
            'div[class*="professional"]',
            'div[class*="accred"]',
            'div[class*="medical-cert"]',
            'div[class*="trust-badge"]',
            'div[class*="cert-badge"]',
            'section[class*="trust"]',
            'section[class*="certifi"]',
            'section[class*="expertise"]',
            'section[class*="professional"]',
            'section[class*="accred"]'
        ];
        
        containerSelectors.forEach(selector => {
            const containers = document.querySelectorAll(selector);
            containers.forEach(container => {
                if (container.parentNode) {
                    container.parentNode.removeChild(container);
                }
            });
        });
        
        // Method 4: Remove by content analysis
        const allElements = document.querySelectorAll('div, section, article, aside, p, h1, h2, h3, h4, h5, h6, span');
        allElements.forEach(element => {
            const text = element.textContent.trim();
            const innerHTML = element.innerHTML || '';
            
            // Check if element contains certification content
            if ((text.includes('Trusted Expertise') && text.includes('Certified Professionals')) ||
                (innerHTML.includes('ISAPS') && innerHTML.includes('FDA') && innerHTML.includes('CE')) ||
                (text.includes('Trusted Expertise, Certified Professionals'))) {
                
                // Remove the element
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
            }
        });
        
        // Method 5: Desktop-specific targeted removal (avoid hiding clinic cards)
        if (window.innerWidth >= 769) {
            // Only target very specific certification elements
            const certificationElements = document.querySelectorAll('div, section, p, span, h1, h2, h3, h4, h5, h6');
            certificationElements.forEach(element => {
                const text = element.textContent || '';
                const innerHTML = element.innerHTML || '';
                
                // Only remove if it's specifically a certification section
                if ((text.includes('Trusted Expertise') && text.includes('Certified Professionals')) ||
                    (innerHTML.includes('ISAPS') && innerHTML.includes('FDA') && innerHTML.includes('CE')) ||
                    (text === 'Trusted Expertise, Certified Professionals')) {
                    
                    // Additional safety checks to avoid removing clinic cards
                    if (text.length < 200 && 
                        element.children.length < 5 && 
                        !element.classList.contains('clinic-card') &&
                        !element.closest('.clinic-card') &&
                        !element.classList.contains('card') &&
                        !element.closest('.card')) {
                        if (element.parentNode) {
                            element.parentNode.removeChild(element);
                        }
                    }
                }
            });
        }
        
        console.log('Certification removal completed');
    }
    
    // Function to inject aggressive CSS
    function injectAggressiveCss() {
        const style = document.createElement('style');
        style.textContent = `
            /* NUCLEAR CSS REMOVAL */
            *:contains("Trusted Expertise") { display: none !important; }
            *:contains("Certified Professionals") { display: none !important; }
            *:contains("ISAPS") { display: none !important; }
            *:contains("FDA") { display: none !important; }
            *:contains("CE") { display: none !important; }
            
            /* Hide images */
            img[alt*="ISAPS"], img[alt*="FDA"], img[alt*="CE"],
            img[src*="isaps"], img[src*="fda"], img[src*="cert"],
            img[title*="ISAPS"], img[title*="FDA"], img[title*="CE"] {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                height: 0 !important;
                width: 0 !important;
            }
            
            /* Desktop-specific hiding - More targeted to avoid clinic cards */
            @media (min-width: 769px) {
                /* Only target specific certification sections, not broad containers */
                .certification-section:has(img[alt*="ISAPS"]), 
                .certification-section:has(img[alt*="FDA"]), 
                .certification-section:has(img[alt*="CE"]),
                .trust-section:has(img[alt*="ISAPS"]), 
                .trust-section:has(img[alt*="FDA"]), 
                .trust-section:has(img[alt*="CE"]),
                .text-center:has(img[alt*="ISAPS"]):not(.clinic-card):not(.card),
                .text-center:has(img[alt*="FDA"]):not(.clinic-card):not(.card),
                .text-center:has(img[alt*="CE"]):not(.clinic-card):not(.card) {
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                    height: 0 !important;
                    width: 0 !important;
                    position: absolute !important;
                    left: -9999px !important;
                    top: -9999px !important;
                }
                
                /* Ensure clinic cards are always visible */
                .clinic-card, .clinic-card *, .card.clinic-card, .card.clinic-card * {
                    display: block !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                    position: static !important;
                    left: auto !important;
                    top: auto !important;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Run immediately
    injectAggressiveCss();
    removeAllCertificationContent();
    
    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            removeAllCertificationContent();
        });
    } else {
        removeAllCertificationContent();
    }
    
    // Run periodically for the first 30 seconds
    let counter = 0;
    const intervalId = setInterval(function() {
        removeAllCertificationContent();
        counter++;
        if (counter >= 60) { // 60 times in 30 seconds
            clearInterval(intervalId);
        }
    }, 500);
    
    // Run on window resize (in case content reflows)
    window.addEventListener('resize', function() {
        setTimeout(removeAllCertificationContent, 100);
    });
    
    // Set up MutationObserver to catch dynamically added content
    const observer = new MutationObserver(function(mutations) {
        let shouldRemove = false;
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const text = node.textContent || '';
                        if (text.includes('Trusted') || text.includes('Certified') || 
                            text.includes('ISAPS') || text.includes('FDA') || text.includes('CE')) {
                            shouldRemove = true;
                        }
                    }
                });
            }
        });
        
        if (shouldRemove) {
            setTimeout(removeAllCertificationContent, 100);
        }
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('Nuclear certification removal system activated');
})();