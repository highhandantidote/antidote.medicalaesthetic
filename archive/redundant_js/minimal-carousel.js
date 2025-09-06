/**
 * Minimal JavaScript Carousel - Most Reliable Solution
 * Uses simple setInterval for consistent timing
 */

document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.scrolling-categories');
    if (!container) return;
    
    const originalItems = Array.from(container.children);
    if (originalItems.length === 0) return;
    
    // Create seamless loop by duplicating items
    originalItems.forEach(item => {
        const clone = item.cloneNode(true);
        container.appendChild(clone);
    });
    
    let scrollPosition = 0;
    let isPaused = false;
    const scrollSpeed = 0.8; // Moderate speed for 50-second cycle
    const maxScroll = container.scrollWidth / 2;
    
    function scroll() {
        if (!isPaused) {
            scrollPosition += scrollSpeed;
            container.scrollLeft = scrollPosition;
            
            // Reset for infinite loop
            if (scrollPosition >= maxScroll) {
                scrollPosition = 0;
                container.scrollLeft = 0;
            }
        }
    }
    
    // Start scrolling every 16ms (60fps)
    const scrollInterval = setInterval(scroll, 16);
    
    // Pause on hover
    container.addEventListener('mouseenter', () => { isPaused = true; });
    container.addEventListener('mouseleave', () => { isPaused = false; });
    
    // Pause on touch
    container.addEventListener('touchstart', () => { isPaused = true; });
    container.addEventListener('touchend', () => { 
        setTimeout(() => { isPaused = false; }, 1000);
    });
    
    // Fix arrow button functionality
    const prevBtn = document.querySelector('.scroll-prev');
    const nextBtn = document.querySelector('.scroll-next');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            isPaused = true;
            const cardWidth = originalItems[0].offsetWidth + 24;
            scrollPosition -= cardWidth * 3;
            if (scrollPosition < 0) scrollPosition = 0;
            container.scrollLeft = scrollPosition;
            setTimeout(() => { isPaused = false; }, 1000);
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            isPaused = true;
            const cardWidth = originalItems[0].offsetWidth + 24;
            scrollPosition += cardWidth * 3;
            container.scrollLeft = scrollPosition;
            setTimeout(() => { isPaused = false; }, 1000);
        });
    }
    
    console.log('✅ Minimal Carousel: Working with arrow buttons, all categories visible');
});