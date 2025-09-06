/**
 * Advanced Carousel Effects for Category Slider
 * Multiple beautiful animation styles to choose from
 */

// Available animation effects
const CAROUSEL_EFFECTS = {
    // Simple, basic sliding effect
    BASIC_SLIDE: {
        name: 'Basic Slide',
        speed: 0.01,
        easing: 'linear',
        description: 'Simple, consistent sliding movement'
    }
};

// Current active effect (basic sliding)
let ACTIVE_EFFECT = CAROUSEL_EFFECTS.BASIC_SLIDE;

/**
 * Enhanced Infinite Carousel with Multiple Effect Options
 */
document.addEventListener('DOMContentLoaded', function() {
    initAdvancedCarousel();
});

function initAdvancedCarousel() {
    const container = document.querySelector('.scrolling-categories');
    if (!container) return;
    
    // Get the original items
    const originalItems = Array.from(container.children);
    if (originalItems.length < 2) return;
    
    // Create copies for infinite scrolling
    originalItems.forEach(item => {
        const clone = item.cloneNode(true);
        container.appendChild(clone);
    });
    
    // Animation variables
    let isScrolling = false;
    let scrollPosition = 0;
    let autoScrollAnimationId;
    let startTime = performance.now();
    let cycleStartTime = performance.now();
    let currentSpeed = ACTIVE_EFFECT.speed;
    
    // Start the selected animation effect
    function startAdvancedScroll() {
        if (autoScrollAnimationId) cancelAnimationFrame(autoScrollAnimationId);
        
        function animate(currentTime) {
            if (!isScrolling) {
                const elapsed = currentTime - startTime;
                let speed = ACTIVE_EFFECT.speed;
                
                // Simple linear movement - no fancy effects
                speed = ACTIVE_EFFECT.speed;
                
                // Update scroll position
                scrollPosition += speed;
                container.scrollLeft = scrollPosition;
                
                // Reset for infinite loop - fixed logic
                const maxScroll = container.scrollWidth / 2;
                if (scrollPosition >= maxScroll) {
                    scrollPosition = 0;
                    container.scrollLeft = 0;
                }
            }
            autoScrollAnimationId = requestAnimationFrame(animate);
        }
        
        autoScrollAnimationId = requestAnimationFrame(animate);
    }
    
    // Initialize the animation
    startAdvancedScroll();
    
    // Manual navigation with smooth transitions
    const prevBtn = document.querySelector('.scroll-prev');
    const nextBtn = document.querySelector('.scroll-next');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            isScrolling = true;
            const cardWidth = originalItems[0].offsetWidth + 24;
            const scrollDistance = cardWidth * 3;
            
            smoothScrollTo(container.scrollLeft, container.scrollLeft - scrollDistance, 600, () => {
                scrollPosition = container.scrollLeft;
                setTimeout(() => { isScrolling = false; }, 1000);
            });
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            isScrolling = true;
            const cardWidth = originalItems[0].offsetWidth + 24;
            const scrollDistance = cardWidth * 3;
            
            smoothScrollTo(container.scrollLeft, container.scrollLeft + scrollDistance, 600, () => {
                scrollPosition = container.scrollLeft;
                setTimeout(() => { isScrolling = false; }, 1000);
            });
        });
    }
    
    // Pause on hover for better user experience
    container.addEventListener('mouseenter', () => {
        isScrolling = true;
    });
    
    container.addEventListener('mouseleave', () => {
        scrollPosition = container.scrollLeft;
        setTimeout(() => { isScrolling = false; }, 500);
    });
    
    // Touch interaction handling
    container.addEventListener('touchstart', () => {
        isScrolling = true;
    });
    
    container.addEventListener('touchend', () => {
        scrollPosition = container.scrollLeft;
        setTimeout(() => { isScrolling = false; }, 1000);
    });
}

// Smooth scrolling helper function
function smoothScrollTo(start, target, duration, callback) {
    const startTime = performance.now();
    
    function animateScroll(currentTime) {
        const elapsedTime = currentTime - startTime;
        const scrollProgress = Math.min(elapsedTime / duration, 1);
        
        // Smooth easing function
        const easedProgress = scrollProgress < 0.5 
            ? 2 * scrollProgress * scrollProgress 
            : 1 - Math.pow(-2 * scrollProgress + 2, 2) / 2;
            
        const nextScrollPos = start + (target - start) * easedProgress;
        
        document.querySelector('.scrolling-categories').scrollLeft = nextScrollPos;
        
        if (elapsedTime < duration) {
            requestAnimationFrame(animateScroll);
        } else if (callback) {
            callback();
        }
    }
    
    requestAnimationFrame(animateScroll);
}

// Function to change animation effect (you can call this from console)
function changeCarouselEffect(effectName) {
    const effect = Object.values(CAROUSEL_EFFECTS).find(e => e.name === effectName);
    if (effect) {
        ACTIVE_EFFECT = effect;
        console.log(`Switched to ${effect.name}: ${effect.description}`);
        // Restart carousel with new effect
        initAdvancedCarousel();
    } else {
        console.log('Available effects:', Object.values(CAROUSEL_EFFECTS).map(e => e.name));
    }
}

// Export for global access
window.changeCarouselEffect = changeCarouselEffect;
window.CAROUSEL_EFFECTS = CAROUSEL_EFFECTS;