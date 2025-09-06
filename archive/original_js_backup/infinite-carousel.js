/**
 * Simple Infinite Carousel for Category Cards
 * Creates a smooth, continuous scrolling experience
 */

document.addEventListener('DOMContentLoaded', function() {
    initSimpleCarousel();
});

function initSimpleCarousel() {
    const container = document.querySelector('.scrolling-categories');
    if (!container) return;
    
    // Get the original items
    const originalItems = Array.from(container.children);
    if (originalItems.length < 2) return;
    
    // Create copies of all items to make the carousel appear infinite
    originalItems.forEach(item => {
        const clone = item.cloneNode(true);
        container.appendChild(clone);
    });
    
    // Variables for smooth auto-scrolling
    let isScrolling = false;
    let scrollAmount = 0.3; // Slower, smoother movement like a train
    let autoScrollInterval;
    let scrollPosition = 0;
    let autoScrollAnimationId;
    
    // Start auto-scrolling animation
    function startAutoScroll() {
        if (autoScrollAnimationId) cancelAnimationFrame(autoScrollAnimationId);
        
        function scroll() {
            if (!isScrolling) {
                // Increment scroll position
                scrollPosition += scrollAmount;
                container.scrollLeft = scrollPosition;
                
                // Reset when we reach the "clone section" to create the illusion of infinite scrolling
                const maxScroll = container.scrollWidth / 2;
                if (scrollPosition >= maxScroll) {
                    scrollPosition = 0;
                    container.scrollLeft = 0;
                }
            }
            autoScrollAnimationId = requestAnimationFrame(scroll);
        }
        
        // Start the animation loop
        autoScrollAnimationId = requestAnimationFrame(scroll);
    }
    
    // Initialize auto-scrolling
    startAutoScroll();
    
    // Setup manual navigation buttons
    const prevBtn = document.querySelector('.scroll-prev');
    const nextBtn = document.querySelector('.scroll-next');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            isScrolling = true;
            
            // Calculate distance to scroll (approximately 3 cards)
            const cardWidth = originalItems[0].offsetWidth + 24; // width + gap
            const scrollDistance = Math.min(container.clientWidth, cardWidth * 3);
            
            // Animate the scroll
            const startPos = container.scrollLeft;
            const targetPos = startPos - scrollDistance;
            
            smoothScrollTo(startPos, targetPos, 500, () => {
                // Update the scrollPosition variable to match actual scroll position
                scrollPosition = container.scrollLeft;
                
                // Resume auto-scrolling after a pause
                setTimeout(() => {
                    isScrolling = false;
                }, 500);
            });
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            isScrolling = true;
            
            // Calculate distance to scroll (approximately 3 cards)
            const cardWidth = originalItems[0].offsetWidth + 24; // width + gap
            const scrollDistance = Math.min(container.clientWidth, cardWidth * 3);
            
            // Animate the scroll
            const startPos = container.scrollLeft;
            const targetPos = startPos + scrollDistance;
            
            smoothScrollTo(startPos, targetPos, 500, () => {
                // Update the scrollPosition variable to match actual scroll position
                scrollPosition = container.scrollLeft;
                
                // Resume auto-scrolling after a pause
                setTimeout(() => {
                    isScrolling = false;
                }, 500);
            });
        });
    }
    
    // Smooth scroll animation helper function
    function smoothScrollTo(start, target, duration, callback) {
        const startTime = performance.now();
        
        function animateScroll(currentTime) {
            const elapsedTime = currentTime - startTime;
            
            // Calculate the next scroll position using easing
            const scrollProgress = Math.min(elapsedTime / duration, 1);
            const easedProgress = easeInOutQuad(scrollProgress);
            const nextScrollPos = start + (target - start) * easedProgress;
            
            // Apply the scroll position
            container.scrollLeft = nextScrollPos;
            
            // Continue animation if not complete
            if (elapsedTime < duration) {
                requestAnimationFrame(animateScroll);
            } else {
                // Animation complete, run callback if provided
                if (callback) callback();
            }
        }
        
        // Start the animation
        requestAnimationFrame(animateScroll);
    }
    
    // Easing function for smoother animation
    function easeInOutQuad(t) {
        return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    }
    
    // Handle manual interaction
    container.addEventListener('mousedown', () => {
        isScrolling = true;
    });
    
    container.addEventListener('touchstart', () => {
        isScrolling = true;
    });
    
    // Resume auto-scrolling after manual interaction
    container.addEventListener('mouseup', () => {
        // Wait a bit before resuming
        scrollPosition = container.scrollLeft;
        setTimeout(() => {
            isScrolling = false;
        }, 1000);
    });
    
    container.addEventListener('touchend', () => {
        // Wait a bit before resuming
        scrollPosition = container.scrollLeft;
        setTimeout(() => {
            isScrolling = false;
        }, 1000);
    });
    
    // Handle window resize to ensure proper positioning
    window.addEventListener('resize', () => {
        scrollPosition = container.scrollLeft;
    });
}

// Category images are now handled by the backend template
// Real medical procedure images are loaded directly from the database