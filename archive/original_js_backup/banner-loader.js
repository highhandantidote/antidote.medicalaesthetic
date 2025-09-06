/**
 * Banner Loader for Antidote Platform
 * 
 * This script loads banner content from the server via AJAX and initializes the sliders.
 * It handles loading banners into designated containers based on their position.
 */

// Position to container ID mapping
const bannerPositionMap = {
    'between_hero_stats': 'banner-1',
    'between_treatment_categories': 'banner-2',
    'between_popular_procedures': 'banner-3',
    'between_top_specialists': 'banner-4',
    'between_community_posts': 'banner-5',
    'before_footer': 'banner-6'
};

// Banner template generator
function generateBannerHTML(banner) {
    // If no slides, return empty string
    if (!banner.slides || banner.slides.length === 0) {
        return '';
    }
    
    // Check if we need slider functionality (multiple slides)
    const needsSlider = banner.slides.length > 1;
    const sliderId = `banner-slider-${banner.id}`;
    
    // Start with the outer container
    let html = `<div class="banner-slider${needsSlider ? ' needs-slider' : ''}" id="${sliderId}">`;
    
    // Add the slides container
    html += '<div class="slides">';
    
    // Add each slide
    banner.slides.forEach((slide, index) => {
        html += `
            <div class="slide${index === 0 ? ' active' : ''}" data-slide-id="${slide.id}">
                <a href="${slide.redirect_url}" class="banner-link" data-slide-id="${slide.id}">
                    <div class="slide-content" style="background-image: url('${slide.image_url}');">
                        <!-- Text container removed as requested -->
                    </div>
                </a>
            </div>
        `;
    });
    
    html += '</div>';
    
    // Add navigation controls if needed
    if (needsSlider) {
        // Add prev/next buttons
        html += `
            <button class="slide-nav prev" aria-label="Previous slide">
                <i class="fas fa-chevron-left"></i>
            </button>
            <button class="slide-nav next" aria-label="Next slide">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;
        
        // Add dots navigation
        html += '<div class="slide-dots">';
        banner.slides.forEach((_, index) => {
            html += `<button class="slide-dot${index === 0 ? ' active' : ''}" data-slide-index="${index}" aria-label="Go to slide ${index + 1}"></button>`;
        });
        html += '</div>';
    }
    
    html += '</div>';
    
    return html;
}

// Function to process banner data and display it in a container
function loadBannerContent(position, container) {
    console.log(`Loading banner content for position ${position} into container:`, container);
    
    // Show loading state
    const loader = container.querySelector('.banner-loader');
    if (loader) {
        loader.style.display = 'block';
    } else {
        console.warn(`Loader not found in container for position ${position}`);
    }
    
    // Fetch banner data from the API
    fetch(`/api/banners/${position}`)
        .then(response => {
            console.log(`API response status for ${position}:`, response.status);
            return response.json();
        })
        .then(data => {
            console.log(`API data for ${position}:`, data);
            
            // Hide loader
            if (loader) {
                loader.style.display = 'none';
            }
            
            if (data.success && data.banner) {
                console.log(`Successfully loaded banner for ${position}`, data.banner);
                // Generate and insert banner HTML
                const bannerHTML = generateBannerHTML(data.banner);
                
                // Create a wrapper for the banner content
                const bannerContent = document.createElement('div');
                bannerContent.className = 'banner-content';
                bannerContent.innerHTML = bannerHTML;
                
                // Replace any existing banner content
                const existingContent = container.querySelector('.banner-content');
                if (existingContent) {
                    container.replaceChild(bannerContent, existingContent);
                } else {
                    container.appendChild(bannerContent);
                }
                
                // Initialize slider if needed
                if (data.banner.slides && data.banner.slides.length > 1) {
                    console.log(`Initializing slider for banner ${data.banner.id}`);
                    const sliderId = `banner-slider-${data.banner.id}`;
                    const sliderEl = document.getElementById(sliderId);
                    if (sliderEl) {
                        initSingleSlider(sliderEl);
                    } else {
                        console.error(`Slider element not found: ${sliderId}`);
                    }
                }
                
                // Add click event listeners for tracking
                const slides = container.querySelectorAll('.banner-link');
                console.log(`Found ${slides.length} banner links to track clicks`);
                slides.forEach(slide => {
                    slide.addEventListener('click', function(event) {
                        // Don't prevent default, let the link work normally
                        // Just record the click
                        const slideId = this.getAttribute('data-slide-id');
                        console.log(`Banner slide clicked: ${slideId}`);
                        
                        // Use fetch to record click, but don't wait for response
                        fetch(`/api/banners/slide/${slideId}/click`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        }).catch(error => {
                            console.error('Error recording banner click:', error);
                        });
                    });
                });
            } else {
                console.warn(`No banner data for position ${position} or API error`);
                // If no banner or error, just hide the container
                container.style.display = 'none';
            }
        })
        .catch(error => {
            console.error(`Error loading banner for position ${position}:`, error);
            if (loader) {
                loader.style.display = 'none';
            }
            container.style.display = 'none';
        });
}

// Function to load banners from the server
function loadBanner(position) {
    const containerId = bannerPositionMap[position];
    if (!containerId) {
        console.error(`Unknown banner position: ${position}`);
        return;
    }
    
    console.log(`Looking for container with ID: ${containerId}`);
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Banner container not found: ${containerId}`);
        // Try alternate method - maybe querySelector
        console.log("Trying alternative selector method");
        const altContainer = document.querySelector(`#${containerId}, .banner-container[id="${containerId}"]`);
        if (altContainer) {
            console.log("Found container using alternative selector:", altContainer);
            loadBannerContent(position, altContainer);
            return;
        } else {
            console.error("Container not found with alternative method either");
            return;
        }
    }
    
    // Use the common function for banner content loading
    loadBannerContent(position, container);
}

// Load all banners on document ready
document.addEventListener('DOMContentLoaded', function() {
    console.log("Banner loader started");
    
    // Debug banner containers
    Object.values(bannerPositionMap).forEach(containerId => {
        const container = document.getElementById(containerId);
        console.log(`Container "${containerId}" exists:`, !!container);
        if (container) {
            console.log(`Container "${containerId}" HTML:`, container.outerHTML);
        }
    });
    
    // Load each banner
    Object.keys(bannerPositionMap).forEach(position => {
        console.log(`Loading banner for position: ${position}`);
        loadBanner(position);
    });
});