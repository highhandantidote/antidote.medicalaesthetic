/**
 * Stats Counter Animation
 * Animates the statistics numbers on the homepage with a counting effect
 */

document.addEventListener('DOMContentLoaded', function() {
    // Function to animate counting for an element
    function animateCounter(element) {
        const targetValue = parseInt(element.getAttribute('data-count'));
        const duration = 2000; // Animation duration in milliseconds
        const frameDuration = 1000 / 60; // 60fps
        const totalFrames = Math.round(duration / frameDuration);
        let frame = 0;
        const suffix = element.querySelector('span')?.textContent || '';
        
        // Starting value
        let currentValue = 0;
        
        // Calculate the increment per frame
        const increment = targetValue / totalFrames;
        
        // Start the animation
        const counter = setInterval(() => {
            frame++;
            currentValue += increment;
            
            // Update the element with the current count
            if (frame === totalFrames) {
                // Ensure we end with the exact target value
                element.innerHTML = targetValue + suffix;
                clearInterval(counter);
            } else {
                // Round to avoid decimal values during counting
                element.innerHTML = Math.floor(currentValue) + suffix;
            }
        }, frameDuration);
    }
    
    // Create an Intersection Observer to trigger counters when visible
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Start animation when elements become visible
                animateCounter(entry.target);
                // Unobserve after triggering the animation
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    // Observe all stat counter elements
    document.querySelectorAll('.stat-value').forEach(counter => {
        observer.observe(counter);
    });
});