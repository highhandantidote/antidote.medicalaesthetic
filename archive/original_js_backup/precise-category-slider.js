/**
 * Precise Category Slider - 0.2 second intervals with arrow control
 * Each category slides out every 0.2 seconds, user can control with arrows
 */

document.addEventListener('DOMContentLoaded', function() {
    initPreciseCategorySlider();
});

function initPreciseCategorySlider() {
    const container = document.querySelector('.scrolling-categories');
    if (!container) return;
    
    // Get the original items and create copies for infinite loop
    const originalItems = Array.from(container.children);
    if (originalItems.length < 2) return;
    
    // Create copies for seamless infinite scrolling
    originalItems.forEach(item => {
        const clone = item.cloneNode(true);
        container.appendChild(clone);
    });
    
    // Calculate card width including gap
    const cardWidth = originalItems[0].offsetWidth + 24; // width + gap
    
    // Animation variables
    let isManualControl = false;
    let autoSlideInterval;
    let currentPosition = 0;
    let manualControlTimeout;
    
    // Auto-slide every 0.6 seconds (600ms) for smooth, relaxed viewing
    function startAutoSlide() {
        if (autoSlideInterval) clearInterval(autoSlideInterval);
        
        autoSlideInterval = setInterval(() => {
            if (!isManualControl) {
                slideToNext();
            }
        }, 600); // 0.6 seconds
    }
    
    // Slide to next category smoothly
    function slideToNext() {
        currentPosition += cardWidth;
        container.scrollLeft = currentPosition;
        
        // Reset position for infinite loop
        const maxScroll = container.scrollWidth / 2;
        if (currentPosition >= maxScroll) {
            currentPosition = 0;
            container.scrollLeft = 0;
        }
    }
    
    // Slide to previous category smoothly
    function slideToPrevious() {
        currentPosition -= cardWidth;
        
        // Handle negative position for infinite loop
        if (currentPosition < 0) {
            const maxScroll = container.scrollWidth / 2;
            currentPosition = maxScroll - cardWidth;
        }
        
        container.scrollLeft = currentPosition;
    }
    
    // Manual control with arrows
    const prevBtn = document.querySelector('.scroll-prev');
    const nextBtn = document.querySelector('.scroll-next');
    
    function enableManualControl() {
        isManualControl = true;
        
        // Clear any existing timeout
        if (manualControlTimeout) clearTimeout(manualControlTimeout);
        
        // Resume auto-slide after 3 seconds of no interaction
        manualControlTimeout = setTimeout(() => {
            isManualControl = false;
        }, 3000);
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            enableManualControl();
            slideToPrevious();
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            enableManualControl();
            slideToNext();
        });
    }
    
    // Keyboard controls
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            enableManualControl();
            slideToPrevious();
            e.preventDefault();
        } else if (e.key === 'ArrowRight') {
            enableManualControl();
            slideToNext();
            e.preventDefault();
        }
    });
    
    // Touch/mouse interaction pauses auto-slide
    container.addEventListener('mouseenter', () => {
        enableManualControl();
    });
    
    container.addEventListener('mouseleave', () => {
        // Resume auto-slide after 1 second
        if (manualControlTimeout) clearTimeout(manualControlTimeout);
        manualControlTimeout = setTimeout(() => {
            isManualControl = false;
        }, 1000);
    });
    
    // Touch events
    container.addEventListener('touchstart', () => {
        enableManualControl();
    });
    
    container.addEventListener('touchend', () => {
        // Sync current position with actual scroll position
        currentPosition = container.scrollLeft;
        
        // Resume auto-slide after 2 seconds
        if (manualControlTimeout) clearTimeout(manualControlTimeout);
        manualControlTimeout = setTimeout(() => {
            isManualControl = false;
        }, 2000);
    });
    
    // Handle window resize
    window.addEventListener('resize', () => {
        // Recalculate card width on resize
        const newCardWidth = originalItems[0].offsetWidth + 24;
        if (newCardWidth !== cardWidth) {
            location.reload(); // Restart slider with new dimensions
        }
    });
    
    // Add ultra-smooth CSS transitions
    container.style.scrollBehavior = 'smooth';
    container.style.transition = 'scroll-left 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
    
    // Start the auto-slide
    startAutoSlide();
    
    console.log('Precise Category Slider initialized: 0.6s intervals, ultra-smooth transitions');
}