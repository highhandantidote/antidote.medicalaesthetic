/**
 * Typing Animation for Search Placeholders
 * Creates a typewriter effect that cycles through different example searches
 */

class TypingAnimation {
    constructor(element, texts, options = {}) {
        this.element = element;
        this.texts = texts;
        this.options = {
            typeSpeed: 120,
            deleteSpeed: 60,
            pauseTime: 1800,
            loop: true,
            ...options
        };
        
        this.textIndex = 0;
        this.charIndex = 0;
        this.isDeleting = false;
        this.isPaused = false;
        
        this.start();
    }
    
    start() {
        this.type();
    }
    
    type() {
        const currentText = this.texts[this.textIndex];
        
        if (this.isDeleting) {
            // Remove characters one by one
            this.charIndex--;
            this.element.placeholder = currentText.substring(0, this.charIndex);
            
            if (this.charIndex === 0) {
                // Completely finished deleting, now switch to next word
                this.isDeleting = false;
                this.textIndex = (this.textIndex + 1) % this.texts.length;
                // Clear placeholder briefly before starting next word
                this.element.placeholder = '';
                // Wait before starting to type next word
                this.timeout = setTimeout(() => this.type(), 300);
                return;
            }
            
            this.timeout = setTimeout(() => this.type(), this.options.deleteSpeed);
        } else {
            // Add characters one by one
            this.element.placeholder = currentText.substring(0, this.charIndex + 1);
            this.charIndex++;
            
            if (this.charIndex === currentText.length) {
                // Finished typing current word, pause before deleting
                this.timeout = setTimeout(() => {
                    this.isDeleting = true;
                    this.type();
                }, this.options.pauseTime);
                return;
            }
            
            this.timeout = setTimeout(() => this.type(), this.options.typeSpeed);
        }
    }
    
    stop() {
        clearTimeout(this.timeout);
    }
}

// Initialize typing animations when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Doctor search placeholder texts - Popular procedures
    const doctorSearchTexts = [
        'Botox',
        'Lipo (Liposuction)',
        'Dermal Fillers',
        'Nose Job (Rhinoplasty)',
        'Laser Hair Removal',
        'Boob Job (Breast Augmentation)',
        'Fat Freezing (CoolSculpting)',
        'Eyelid Lift',
        'Chemical Peel',
        'Tummy Tuck'
    ];
    
    // Procedure search placeholder texts - Popular procedures
    const procedureSearchTexts = [
        'Botox',
        'Lipo (Liposuction)',
        'Dermal Fillers',
        'Nose Job (Rhinoplasty)',
        'Laser Hair Removal',
        'Boob Job (Breast Augmentation)',
        'Fat Freezing (CoolSculpting)',
        'Eyelid Lift',
        'Chemical Peel',
        'Tummy Tuck'
    ];
    
    // Discussion search placeholder texts
    const discussionSearchTexts = [
        'Recovery time, experiences, etc.',
        'Post-surgery care tips',
        'Before and after results',
        'Pain management advice',
        'Cost comparison reviews',
        'Doctor recommendations'
    ];
    
    // Location search placeholder texts - Top 10 Indian cities
    const locationSearchTexts = [
        'Mumbai',
        'Delhi',
        'Bangalore',
        'Chennai',
        'Pune',
        'Hyderabad',
        'Kolkata',
        'Ahmedabad',
        'Jaipur',
        'Gurgaon'
    ];
    
    // AI recommendation textarea placeholder texts - Multilingual
    const aiRecommendationTexts = [
        "I'm 32 and have some stubborn fat on my lower belly that isn't going away with workouts. I'm looking for a non-surgical way to tone it.",
        "मैं 32 साल की हूँ और मेरी निचले पेट की चर्बी एक्सरसाइज करने के बावजूद भी नहीं जा रही है। कोई नॉन-सर्जिकल तरीका चाहती हूँ जिससे टोनिंग हो सके।",
        "నేను 32 ఏళ్లవిడిని. నా కిందపొట్టపై ఉన్న కొవ్వు వ్యాయామం చేసినా తగ్గడం లేదు. శస్త్రచికిత్స అవసరం లేకుండా టోన్ అయ్యే మంచి మార్గం కావాలి."
    ];

    // Initialize animations for different search inputs
    const doctorSearchInput = document.getElementById('doctorSearch');
    const procedureSearchInput = document.getElementById('procedureSearch');
    const discussionSearchInput = document.getElementById('discussionSearch');
    const locationSearchInputs = document.querySelectorAll('input[name="location"]');
    const aiTextarea = document.getElementById('concerns');
    const aiCityInput = document.getElementById('city');
    
    let animations = [];
    let currentActiveInput = null;
    
    // Always animate when input is empty (regardless of focus)
    function shouldAnimate(input) {
        return !input.value;
    }
    
    function stopAllAnimations() {
        animations.forEach(animation => animation.stop());
        animations = [];
        currentActiveInput = null;
    }
    
    function startAnimation(input, texts) {
        if (shouldAnimate(input)) {
            // Check if animation already exists for this input
            const existingAnimation = animations.find(anim => anim.element === input);
            if (!existingAnimation) {
                const animation = new TypingAnimation(input, texts, {
                    typeSpeed: 100,
                    deleteSpeed: 50,
                    pauseTime: 2000
                });
                animations.push(animation);
                return animation;
            }
        }
    }
    
    function stopAnimation(input) {
        animations = animations.filter(animation => {
            if (animation.element === input) {
                animation.stop();
                return false;
            }
            return true;
        });
        if (currentActiveInput === input) {
            currentActiveInput = null;
        }
    }
    
    // Start animations for each input
    if (doctorSearchInput) {
        startAnimation(doctorSearchInput, doctorSearchTexts);
    }
    
    // Start continuous animations for all inputs
    if (aiTextarea) {
        startAnimation(aiTextarea, aiRecommendationTexts);
        
        // Only stop animation when user actually types
        aiTextarea.addEventListener('input', () => {
            if (aiTextarea.value) {
                stopAnimation(aiTextarea);
            } else {
                // Restart animation if input becomes empty
                setTimeout(() => startAnimation(aiTextarea, aiRecommendationTexts), 500);
            }
        });
    }
    
    if (aiCityInput) {
        startAnimation(aiCityInput, locationSearchTexts);
        
        aiCityInput.addEventListener('input', () => {
            if (aiCityInput.value) {
                stopAnimation(aiCityInput);
            } else {
                setTimeout(() => startAnimation(aiCityInput, locationSearchTexts), 500);
            }
        });
    }
    
    if (doctorSearchInput) {
        startAnimation(doctorSearchInput, doctorSearchTexts);
        
        doctorSearchInput.addEventListener('input', () => {
            if (doctorSearchInput.value) {
                stopAnimation(doctorSearchInput);
            } else {
                setTimeout(() => startAnimation(doctorSearchInput, doctorSearchTexts), 500);
            }
        });
    }
    
    if (procedureSearchInput) {
        startAnimation(procedureSearchInput, procedureSearchTexts);
        
        procedureSearchInput.addEventListener('input', () => {
            if (procedureSearchInput.value) {
                stopAnimation(procedureSearchInput);
            } else {
                setTimeout(() => startAnimation(procedureSearchInput, procedureSearchTexts), 500);
            }
        });
    }
    
    if (discussionSearchInput) {
        startAnimation(discussionSearchInput, discussionSearchTexts);
        
        discussionSearchInput.addEventListener('input', () => {
            if (discussionSearchInput.value) {
                stopAnimation(discussionSearchInput);
            } else {
                setTimeout(() => startAnimation(discussionSearchInput, discussionSearchTexts), 500);
            }
        });
    }
    
    // Handle location inputs
    locationSearchInputs.forEach(locationInput => {
        startAnimation(locationInput, locationSearchTexts);
        
        locationInput.addEventListener('input', () => {
            if (locationInput.value) {
                stopAnimation(locationInput);
            } else {
                setTimeout(() => startAnimation(locationInput, locationSearchTexts), 500);
            }
        });
    });
    
    // Handle tab changes - ensure animations continue for newly visible tabs
    const searchTabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    searchTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            const targetPane = document.querySelector(e.target.getAttribute('data-bs-target'));
            const searchInput = targetPane.querySelector('input[type="text"]');
            
            if (searchInput && !searchInput.value) {
                // Determine which texts to use based on the input
                let texts = doctorSearchTexts;
                if (searchInput.id === 'procedureSearch') {
                    texts = procedureSearchTexts;
                } else if (searchInput.id === 'discussionSearch') {
                    texts = discussionSearchTexts;
                } else if (searchInput.name === 'location') {
                    texts = locationSearchTexts;
                }
                
                // Start animation if it's not already running
                const existingAnimation = animations.find(anim => anim.element === searchInput);
                if (!existingAnimation) {
                    setTimeout(() => startAnimation(searchInput, texts), 300);
                }
            }
        });
    });
    
    // Clean up animations when page unloads
    window.addEventListener('beforeunload', () => {
        animations.forEach(animation => animation.stop());
    });
});