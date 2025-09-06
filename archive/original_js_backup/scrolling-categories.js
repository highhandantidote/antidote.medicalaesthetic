/**
 * Scrolling Categories Navigation
 * Premium-feel enhancement for category card scrolling with 
 * smooth transitions and auto-scroll functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all scrolling categories containers
    initAllScrollingCategories();
});

// Initialize all scrolling categories containers
function initAllScrollingCategories() {
    const containers = document.querySelectorAll('.scrolling-categories-container');
    if (!containers || containers.length === 0) return;
    
    // Set up each container
    containers.forEach(container => {
        const scrollContainer = container.querySelector('.scrolling-categories');
        const scrollPrevBtn = container.querySelector('.scroll-prev');
        const scrollNextBtn = container.querySelector('.scroll-next');
        
        if (scrollContainer && scrollPrevBtn && scrollNextBtn) {
            setupScrollingContainer(scrollContainer, scrollPrevBtn, scrollNextBtn);
        }
    });
}

// Setup a single scrolling container
function setupScrollingContainer(scrollContainer, scrollPrevBtn, scrollNextBtn) {
    let autoScrollInterval;
    let isHovering = false;
    
    // Scroll left when clicking the prev button
    scrollPrevBtn.addEventListener('click', function() {
        stopAutoScroll();
        animateScroll(-320);
    });
    
    // Scroll right when clicking the next button
    scrollNextBtn.addEventListener('click', function() {
        stopAutoScroll();
        animateScroll(320);
    });
    
    // Animate scroll with easing
    function animateScroll(distance) {
        const start = scrollContainer.scrollLeft;
        const startTime = performance.now();
        const duration = 500; // ms
        
        function step(timestamp) {
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic: progress = 1 - Math.pow(1 - progress, 3)
            const ease = 1 - Math.pow(1 - progress, 3);
            
            scrollContainer.scrollLeft = start + (distance * ease);
            
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        }
        
        window.requestAnimationFrame(step);
    }
    
    // Check if scrolling is possible (show/hide buttons)
    function checkScrollability() {
        const isScrollable = scrollContainer.scrollWidth > scrollContainer.clientWidth;
        const scrollLeft = scrollContainer.scrollLeft;
        const maxScrollLeft = scrollContainer.scrollWidth - scrollContainer.clientWidth;
        
        // Hide prev button if at start
        if (scrollLeft <= 5) {
            scrollPrevBtn.style.opacity = '0.6';
            scrollPrevBtn.style.pointerEvents = 'none';
            scrollPrevBtn.style.transform = 'scale(0.95)';
        } else {
            scrollPrevBtn.style.opacity = '1';
            scrollPrevBtn.style.pointerEvents = 'auto';
            scrollPrevBtn.style.transform = 'scale(1)';
        }
        
        // Hide next button if at end
        if (maxScrollLeft - scrollLeft <= 5) {
            scrollNextBtn.style.opacity = '0.6';
            scrollNextBtn.style.pointerEvents = 'none';
            scrollNextBtn.style.transform = 'scale(0.95)';
        } else {
            scrollNextBtn.style.opacity = '1';
            scrollNextBtn.style.pointerEvents = 'auto';
            scrollNextBtn.style.transform = 'scale(1)';
        }
        
        // Hide both buttons if not scrollable
        if (!isScrollable) {
            scrollPrevBtn.style.display = 'none';
            scrollNextBtn.style.display = 'none';
        } else {
            scrollPrevBtn.style.display = 'flex';
            scrollNextBtn.style.display = 'flex';
        }
    }
    
    // Auto-scroll functionality with hover pause
    function startAutoScroll() {
        if (autoScrollInterval) return;
        
        // Only auto-scroll if container is scrollable
        if (scrollContainer.scrollWidth > scrollContainer.clientWidth) {
            autoScrollInterval = setInterval(() => {
                if (!isHovering) {
                    const scrollLeft = scrollContainer.scrollLeft;
                    const maxScrollLeft = scrollContainer.scrollWidth - scrollContainer.clientWidth;
                    
                    // If we're at the end, go back to start
                    if (maxScrollLeft - scrollLeft < 5) {
                        scrollContainer.scrollTo({
                            left: 0,
                            behavior: 'smooth'
                        });
                    } else {
                        // Otherwise, scroll a bit
                        scrollContainer.scrollBy({
                            left: 2,
                            behavior: 'auto'
                        });
                    }
                    
                    checkScrollability();
                }
            }, 50);
        }
    }
    
    function stopAutoScroll() {
        if (autoScrollInterval) {
            clearInterval(autoScrollInterval);
            autoScrollInterval = null;
        }
    }
    
    // Pause auto-scroll when hovering
    scrollContainer.addEventListener('mouseenter', () => {
        isHovering = true;
    });
    
    scrollContainer.addEventListener('mouseleave', () => {
        isHovering = false;
    });
    
    // Check initially and on window resize
    checkScrollability();
    window.addEventListener('resize', checkScrollability);
    
    // Check when scrolling occurs
    scrollContainer.addEventListener('scroll', checkScrollability);
    
    // Start auto-scroll after 2 seconds
    setTimeout(startAutoScroll, 2000);
    
    // Add touch/swipe support
    let startX, startScrollLeft;
    
    scrollContainer.addEventListener('touchstart', (e) => {
        startX = e.touches[0].pageX;
        startScrollLeft = scrollContainer.scrollLeft;
        stopAutoScroll();
    }, { passive: true });
    
    scrollContainer.addEventListener('touchmove', (e) => {
        if (startX) {
            const x = e.touches[0].pageX;
            const walk = (startX - x) * 2;
            scrollContainer.scrollLeft = startScrollLeft + walk;
        }
    }, { passive: true });
    
    scrollContainer.addEventListener('touchend', () => {
        startX = null;
        setTimeout(startAutoScroll, 5000);
    });
}