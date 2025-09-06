/**
 * Banner Slider functionality for Antidote platform
 * 
 * This script handles the rotation and interaction for banner sliders.
 */

// Initialize all sliders on document load
document.addEventListener('DOMContentLoaded', function() {
    // Find all sliders that need initialization (ones with multiple slides)
    const sliders = document.querySelectorAll('.banner-slider.needs-slider');
    sliders.forEach(initSingleSlider);
});

/**
 * Initialize a single slider with controls
 * @param {HTMLElement} slider - The slider container element
 */
function initSingleSlider(slider) {
    if (!slider) return;
    
    const slides = slider.querySelectorAll('.slide');
    const dots = slider.querySelectorAll('.slide-dot');
    const prevBtn = slider.querySelector('.slide-nav.prev');
    const nextBtn = slider.querySelector('.slide-nav.next');
    
    if (slides.length <= 1) return; // No need for slider controls with only one slide
    
    let currentIndex = 0;
    let interval = null;
    
    // Auto-rotation
    const startAutoSlide = () => {
        interval = setInterval(() => {
            currentIndex = (currentIndex + 1) % slides.length;
            setActiveSlide(slides, dots, currentIndex);
        }, 5000); // Change slide every 5 seconds
    };
    
    const stopAutoSlide = () => {
        if (interval) {
            clearInterval(interval);
            interval = null;
        }
    };
    
    // Previous button
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            stopAutoSlide();
            currentIndex = (currentIndex - 1 + slides.length) % slides.length;
            setActiveSlide(slides, dots, currentIndex);
            startAutoSlide();
        });
    }
    
    // Next button
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            stopAutoSlide();
            currentIndex = (currentIndex + 1) % slides.length;
            setActiveSlide(slides, dots, currentIndex);
            startAutoSlide();
        });
    }
    
    // Dot navigation
    dots.forEach((dot, index) => {
        dot.addEventListener('click', function() {
            stopAutoSlide();
            currentIndex = index;
            setActiveSlide(slides, dots, currentIndex);
            startAutoSlide();
        });
    });
    
    // Touch/swipe support for mobile
    setupSwipeSupport(slider, slides, dots, (direction) => {
        stopAutoSlide();
        if (direction === 'left') {
            currentIndex = (currentIndex + 1) % slides.length;
        } else if (direction === 'right') {
            currentIndex = (currentIndex - 1 + slides.length) % slides.length;
        }
        setActiveSlide(slides, dots, currentIndex);
        startAutoSlide();
    });
    
    // Start auto-rotation
    startAutoSlide();
}

/**
 * Set the active slide and update dot navigation
 * @param {NodeList} slides - The slide elements
 * @param {NodeList} dots - The dot navigation elements
 * @param {number} index - The index of the slide to activate
 */
function setActiveSlide(slides, dots, index) {
    // Update slides
    slides.forEach((slide, i) => {
        if (i === index) {
            slide.classList.add('active');
        } else {
            slide.classList.remove('active');
        }
    });
    
    // Update dots
    if (dots) {
        dots.forEach((dot, i) => {
            if (i === index) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }
}

/**
 * Setup touch/swipe support for a slider
 * @param {HTMLElement} slider - The slider container
 * @param {NodeList} slides - The slide elements
 * @param {NodeList} dots - The dot navigation elements
 * @param {Function} callback - Callback function to handle swipe direction
 */
function setupSwipeSupport(slider, slides, dots, callback) {
    let touchStartX = 0;
    let touchEndX = 0;
    
    // Minimum distance for a swipe
    const minSwipeDistance = 50;
    
    slider.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    
    slider.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, { passive: true });
    
    function handleSwipe() {
        const distance = touchEndX - touchStartX;
        if (Math.abs(distance) < minSwipeDistance) return;
        
        if (distance > 0) {
            // Swiped right
            callback('right');
        } else {
            // Swiped left
            callback('left');
        }
    }
}