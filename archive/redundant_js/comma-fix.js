/**
 * Comma Spacing Fix
 * 
 * This script works with comma-fixes.css to ensure proper comma placement
 * by adding spaces after commas for better visual presentation and fixing
 * vertical alignment issues with commas across the entire application.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Fix all comma spacing issues
    function fixCommaSpacing() {
        console.log("Applying comma fixes with DOM manipulation...");
        
        // Fix ALL commas anywhere in the document
        fixAllCommas();
        
        // Fix scrolling content areas (found in tabs on homepage)
        fixScrollingContent();
        
        // Fix search bar "Popular:" section 
        fixSearchPopular();
    }
    
    // Fix all commas everywhere in the document
    function fixAllCommas() {
        // Get all comma spans in the document
        const allCommaSpans = document.querySelectorAll('span.text-muted');
        
        allCommaSpans.forEach(span => {
            if (span.textContent === ',') {
                // Ensure proper styling directly on the element
                span.style.display = 'inline';
                span.style.verticalAlign = 'baseline';
                span.style.position = 'relative';
                span.style.top = '0';
                span.style.marginLeft = '-1px';
                span.style.marginRight = '3px';
                span.style.lineHeight = 'inherit';
                
                // Add space after comma if needed
                ensureSpaceAfterComma(span);
            }
        });
    }
    
    // Fix scrolling content areas in tabs
    function fixScrollingContent() {
        const scrollingContents = document.querySelectorAll('.scrolling-content');
        
        scrollingContents.forEach(container => {
            const links = container.querySelectorAll('a.text-decoration-none');
            
            links.forEach(link => {
                // Apply styling directly to links
                link.style.display = 'inline';
                link.style.verticalAlign = 'baseline';
                link.style.whiteSpace = 'nowrap';
                link.style.position = 'relative';
            });
        });
    }
    
    // Fix the "Popular:" section specifically found in search
    function fixSearchPopular() {
        // Find all elements that might contain "Popular:" text
        const popularSections = document.querySelectorAll('.search-form-container, form');
        
        popularSections.forEach(section => {
            const links = section.querySelectorAll('a.text-decoration-none');
            const commas = section.querySelectorAll('span.text-muted');
            
            // Apply specific styling for search area links
            links.forEach(link => {
                link.style.display = 'inline-block';
                link.style.verticalAlign = 'baseline';
                link.style.whiteSpace = 'nowrap';
            });
            
            // Apply specific styling for search area commas
            commas.forEach(comma => {
                if (comma.textContent === ',') {
                    comma.style.display = 'inline-block';
                    comma.style.verticalAlign = 'baseline';
                    comma.style.marginLeft = '-1px';
                    comma.style.marginRight = '3px';
                    
                    // Add space after comma if needed
                    ensureSpaceAfterComma(comma);
                }
            });
        });
    }
    
    // Helper function to ensure there's a space after commas
    function ensureSpaceAfterComma(span) {
        if (!span.nextSibling || span.nextSibling.nodeType !== Node.TEXT_NODE || span.nextSibling.textContent.trim() !== '') {
            const space = document.createTextNode(' ');
            if (span.nextSibling) {
                span.parentNode.insertBefore(space, span.nextSibling);
            } else {
                span.parentNode.appendChild(space);
            }
        }
    }
    
    // Run immediately
    fixCommaSpacing();
    
    // Also run after short delays to catch any dynamically loaded content
    setTimeout(fixCommaSpacing, 300);
    setTimeout(fixCommaSpacing, 1000);
    
    // Run one more time after page is fully loaded
    window.addEventListener('load', function() {
        fixCommaSpacing();
        // One final attempt after a delay
        setTimeout(fixCommaSpacing, 500);
    });
});