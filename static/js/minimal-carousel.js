/**
 * Minimal Carousel for Category Cards
 * Lightweight carousel functionality optimized for mobile category cards
 */

console.log("Minimal carousel.js loaded");

document.addEventListener('DOMContentLoaded', function() {
    // Initialize category carousels
    const categoryCarousels = document.querySelectorAll('.category-carousel');
    
    categoryCarousels.forEach(carousel => {
        initializeCategoryCarousel(carousel);
    });
});

function initializeCategoryCarousel(carousel) {
    const track = carousel.querySelector('.carousel-track');
    const cards = carousel.querySelectorAll('.category-card');
    const prevBtn = carousel.querySelector('.carousel-prev');
    const nextBtn = carousel.querySelector('.carousel-next');
    
    if (!track || !cards.length) return;
    
    let currentIndex = 0;
    const cardWidth = cards[0].offsetWidth + 16; // Include margin
    const maxIndex = Math.max(0, cards.length - 2); // Show 2 cards at once
    
    function updateCarousel() {
        const translateX = -(currentIndex * cardWidth);
        track.style.transform = `translateX(${translateX}px)`;
        
        // Update button states
        if (prevBtn) prevBtn.disabled = currentIndex === 0;
        if (nextBtn) nextBtn.disabled = currentIndex >= maxIndex;
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentIndex > 0) {
                currentIndex--;
                updateCarousel();
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentIndex < maxIndex) {
                currentIndex++;
                updateCarousel();
            }
        });
    }
    
    // Initialize
    updateCarousel();
    
    // Handle window resize
    window.addEventListener('resize', () => {
        updateCarousel();
    });
}