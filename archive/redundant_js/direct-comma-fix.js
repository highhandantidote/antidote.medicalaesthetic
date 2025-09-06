/**
 * Direct JavaScript fix for comma position issues
 * This is a more aggressive approach to fix the commas no matter what
 */

document.addEventListener('DOMContentLoaded', function() {
    // Execute immediately on load
    fixCommas();
    
    // Then execute again after a slight delay to catch dynamically loaded content
    setTimeout(fixCommas, 100);
    setTimeout(fixCommas, 500);
    setTimeout(fixCommas, 1000);
    
    // Direct fix via inline styling to override all CSS
    function fixCommas() {
        console.log("Applying direct comma fixes...");
        
        // Target all comma elements with direct styling
        const commas = document.querySelectorAll('.text-muted');
        commas.forEach(comma => {
            // Only apply to comma elements
            if (comma.textContent.includes(',')) {
                comma.style.display = 'inline';
                comma.style.position = 'static';
                comma.style.float = 'none';
                comma.style.verticalAlign = 'baseline';
                comma.style.lineHeight = 'inherit';
                comma.style.margin = '0';
                comma.style.padding = '0';
                comma.style.paddingRight = '3px';
                comma.style.letterSpacing = 'normal';
            }
        });
        
        // Target all procedure links for consistent display
        const procedureLinks = document.querySelectorAll('a.text-decoration-none');
        procedureLinks.forEach(link => {
            // Add a space to the end of the link text if it doesn't already have one
            if (link.textContent && !link.textContent.endsWith(' ')) {
                link.textContent = link.textContent + ' ';
            }
            
            // Also set styling for consistent display
            link.style.display = 'inline';
            link.style.position = 'static';
            link.style.float = 'none';
            link.style.verticalAlign = 'baseline';
            link.style.lineHeight = 'inherit';
        });
        
        // Special focus on Popular sections - using a more compatible approach
        // Find all text-muted spans that might contain "Popular:"
        const popularTexts = document.querySelectorAll('.text-muted');
        popularTexts.forEach(text => {
            if (text.textContent.includes('Popular:')) {
                // This is a Popular header, get its parent container
                const container = text.closest('.mt-3.position-relative');
                if (container) {
                    // Find all links in this container
                    const sectionLinks = container.querySelectorAll('a.text-decoration-none');
                    sectionLinks.forEach(link => {
                        // Ensure each link in Popular sections has a space at the end
                        if (link.textContent && !link.textContent.endsWith(' ')) {
                            link.textContent = link.textContent + ' ';
                        }
                    });
                    
                    // Fix all commas in this container
                    const sectionCommas = container.querySelectorAll('.text-muted');
                    sectionCommas.forEach(comma => {
                        if (comma.textContent.includes(',')) {
                            comma.style.display = 'inline';
                            comma.style.position = 'static'; 
                            comma.style.verticalAlign = 'baseline';
                            comma.style.lineHeight = 'inherit';
                        }
                    });
                }
            }
        });
        
        // Target all procedure-link-wrap spans (which appear in some templates)
        const procedureLinkWraps = document.querySelectorAll('.procedure-link-wrap');
        procedureLinkWraps.forEach(wrap => {
            const link = wrap.querySelector('a.text-decoration-none');
            if (link && link.textContent && !link.textContent.endsWith(' ')) {
                link.textContent = link.textContent + ' ';
            }
        });
    }
});