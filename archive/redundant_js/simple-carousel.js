/**
 * Ultra-Simple CSS-Only Carousel
 * Pure CSS animations - perfectly smooth, never gets stuck
 */

document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.scrolling-categories');
    if (!container) return;
    
    // Clear any existing animations or intervals
    container.style.animation = 'none';
    container.style.transform = 'none';
    container.scrollLeft = 0;
    
    // Get original items
    const originalItems = Array.from(container.children);
    if (originalItems.length === 0) return;
    
    // Remove any existing clones first
    const existingClones = container.querySelectorAll('[data-clone="true"]');
    existingClones.forEach(clone => clone.remove());
    
    // Clone items for seamless infinite loop
    originalItems.forEach(item => {
        const clone = item.cloneNode(true);
        clone.setAttribute('data-clone', 'true');
        container.appendChild(clone);
    });
    
    // Set up container for CSS animation - preserve existing styles
    container.style.animation = 'smoothSlide 50s linear infinite';
    container.style.animationPlayState = 'running';
    
    // Create and inject CSS keyframes
    const existingStyle = document.getElementById('carousel-css');
    if (existingStyle) existingStyle.remove();
    
    const style = document.createElement('style');
    style.id = 'carousel-css';
    style.textContent = `
        @keyframes smoothSlide {
            0% { 
                transform: translateX(0); 
            }
            100% { 
                transform: translateX(-50%); 
            }
        }
        
        .scrolling-categories:hover {
            animation-play-state: paused;
        }
        
        .scrolling-categories {
            will-change: transform;
        }
    `;
    document.head.appendChild(style);
    
    // Fix arrow button functionality
    const prevBtn = document.querySelector('.scroll-prev');
    const nextBtn = document.querySelector('.scroll-next');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            container.style.animationPlayState = 'paused';
            const cardWidth = container.children[0].offsetWidth + 24;
            container.scrollLeft -= cardWidth * 3;
            setTimeout(() => {
                container.style.animationPlayState = 'running';
            }, 1000);
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            container.style.animationPlayState = 'paused';
            const cardWidth = container.children[0].offsetWidth + 24;
            container.scrollLeft += cardWidth * 3;
            setTimeout(() => {
                container.style.animationPlayState = 'running';
            }, 1000);
        });
    }
    
    console.log('✅ CSS-Only Carousel initialized - 50 second cycle, pauses on hover, arrow buttons working');
});