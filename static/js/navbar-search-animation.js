/**
 * Navigation Bar Search Typewriting Animation
 * 
 * This script adds a typewriting effect to the navigation bar search input
 * showing example searches to inspire users.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get the search inputs from both desktop and mobile views
    const searchInputs = [
        document.getElementById('searchInput'),
        document.getElementById('mobileSearchInput')
    ];
    
    // Suggestions to display in the typewriter effect
    const suggestions = [
        // First show the prefix
        "search anything like...",
        
        // Then show 5 procedures
        "Lip Fillers",
        "Liposuction",
        "Gynecomastia",
        "Rhinoplasty", 
        "Chemical Peel",
        
        // 4 doctors with full names
        "Dr. Rajesh Sharma",
        "Dr. Priya Patel",
        "Dr. Vikram Gupta",
        "Dr. Sanya Khan",
        
        // 3 community topics
        "recovery after rhinoplasty",
        "cost of liposuction in Mumbai",
        "best doctors for hair transplant"
    ];
    
    // Set the animation speed (in milliseconds)
    const typingSpeed = 100;
    const erasingSpeed = 50;
    const pauseBeforeErasing = 2000;
    const pauseBeforeTyping = 700;
    
    // Animation variables
    let animationTimeouts = [null, null];
    
    /**
     * Start the typewriting animation for a search input
     * @param {HTMLElement} inputElement - The search input element
     * @param {number} inputIndex - Index of the input in the searchInputs array
     */
    function startTypingAnimation(inputElement, inputIndex) {
        if (!inputElement) return;
        
        let currentIndex = 0;
        let isTyping = true;
        let currentText = "";
        let charIndex = 0;
        
        // Clear any existing animation
        if (animationTimeouts[inputIndex]) {
            clearTimeout(animationTimeouts[inputIndex]);
        }
        
        // Reset placeholder
        inputElement.placeholder = "";
        
        /**
         * Main animation function that handles both typing and erasing
         */
        function animateText() {
            // Get the current suggestion
            const suggestion = suggestions[currentIndex];
            
            if (isTyping) {
                // Typing phase
                if (charIndex <= suggestion.length) {
                    currentText = suggestion.substring(0, charIndex);
                    inputElement.placeholder = currentText;
                    charIndex++;
                    
                    // Continue typing with random slight variations in speed
                    const randomDelay = typingSpeed + Math.random() * 50 - 25;
                    animationTimeouts[inputIndex] = setTimeout(animateText, randomDelay);
                } else {
                    // Finished typing, pause before erasing
                    isTyping = false;
                    animationTimeouts[inputIndex] = setTimeout(animateText, pauseBeforeErasing);
                }
            } else {
                // Erasing phase
                if (charIndex > 0) {
                    charIndex--;
                    currentText = suggestion.substring(0, charIndex);
                    inputElement.placeholder = currentText;
                    
                    // Continue erasing
                    animationTimeouts[inputIndex] = setTimeout(animateText, erasingSpeed);
                } else {
                    // Finished erasing, move to next suggestion
                    isTyping = true;
                    currentIndex = (currentIndex + 1) % suggestions.length;
                    
                    // Pause before typing next suggestion
                    animationTimeouts[inputIndex] = setTimeout(animateText, pauseBeforeTyping);
                }
            }
        }
        
        // Start the animation
        animateText();
    }
    
    /**
     * Stop the typewriting animation for a search input
     * @param {number} inputIndex - Index of the input in the searchInputs array
     */
    function stopTypingAnimation(inputIndex) {
        if (animationTimeouts[inputIndex]) {
            clearTimeout(animationTimeouts[inputIndex]);
            animationTimeouts[inputIndex] = null;
        }
    }
    
    // Initialize animation for each search input
    searchInputs.forEach((inputElement, index) => {
        if (!inputElement) return;
        
        // Start animation for empty inputs
        if (!inputElement.value) {
            startTypingAnimation(inputElement, index);
        }
        
        // Add event listeners to handle input focus/blur
        inputElement.addEventListener('focus', function() {
            stopTypingAnimation(index);
            if (!this.value) {
                this.placeholder = ''; // Clear placeholder on focus
            }
        });
        
        inputElement.addEventListener('blur', function() {
            if (!this.value) {
                startTypingAnimation(inputElement, index);
            }
        });
        
        // Handle input changes
        inputElement.addEventListener('input', function() {
            if (this.value) {
                stopTypingAnimation(index);
            }
        });
    });
});