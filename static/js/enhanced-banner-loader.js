/**
 * Enhanced Banner Loader with Mobile/Desktop Image Support
 * 
 * This script handles loading banners with separate images for mobile and desktop devices.
 * If no mobile image is provided, the desktop image is used for all devices.
 */

// Device detection utility
function isMobileDevice() {
    return window.innerWidth <= 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Get appropriate image URL based on device with WebP optimization
function getImageForDevice(slide) {
    const isMobile = isMobileDevice();
    
    // Check if this is the main banner that has optimized versions
    if (slide.image_url && slide.image_url.includes('20250714081643_YouTube_Banner')) {
        if (isMobile) {
            return '/static/images/mobile-optimized/main_banner_mobile.webp';
        } else {
            return '/static/images/optimized/main_banner_desktop.webp';
        }
    }
    
    // For other banners, use mobile/desktop versions if available
    if (isMobile && slide.mobile_image_url) {
        return slide.mobile_image_url;
    }
    
    // Otherwise use desktop image
    return slide.image_url;
}

// Enhanced banner HTML generation with mobile/desktop image support
function generateBannerHTML(banner) {
    if (!banner.slides || banner.slides.length === 0) {
        return null; // Return null to indicate no content should be shown
    }

    const sliderId = `banner-slider-${banner.id}`;
    let html = `<div class="banner-slider" id="${sliderId}">`;

    // Generate slides
    banner.slides.forEach((slide, index) => {
        const isActive = index === 0 ? 'active' : '';
        const imageUrl = getImageForDevice(slide);
        
        html += `
            <div class="slide ${isActive}" data-slide-index="${index}">
                <a href="${slide.redirect_url}" class="banner-link" data-slide-id="${slide.id}" target="_blank">
                    <div class="slide-content" style="background-image: url('${imageUrl}');" data-desktop-image="${slide.image_url}" data-mobile-image="${slide.mobile_image_url || ''}">
                        <!-- Content will be background image only -->
                    </div>
                </a>
            </div>
        `;
    });

    // Add navigation if multiple slides
    if (banner.slides.length > 1) {
        html += `
            <button class="slide-nav prev" onclick="changeSlide('${sliderId}', -1)">
                <i class="fas fa-chevron-left"></i>
            </button>
            <button class="slide-nav next" onclick="changeSlide('${sliderId}', 1)">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

        // Add slide dots
        html += '<div class="slide-dots">';
        banner.slides.forEach((_, index) => {
            const isActive = index === 0 ? 'active' : '';
            html += `<button class="slide-dot ${isActive}" onclick="goToSlide('${sliderId}', ${index})"></button>`;
        });
        html += '</div>';
    }

    html += '</div>';
    return html;
}

// Enhanced slider initialization with responsive image handling
function initSingleSlider(sliderElement) {
    const sliderId = sliderElement.id;
    
    // Auto-advance slides every 5 seconds
    setInterval(() => {
        changeSlide(sliderId, 1);
    }, 5000);
    
    // Add resize listener to handle image switching
    window.addEventListener('resize', () => {
        updateSliderImagesForDevice(sliderElement);
    });
    
    // Initial image update
    updateSliderImagesForDevice(sliderElement);
}

// Update slider images based on current device
function updateSliderImagesForDevice(sliderElement) {
    const slides = sliderElement.querySelectorAll('.slide-content');
    
    slides.forEach(slideContent => {
        const desktopImage = slideContent.getAttribute('data-desktop-image');
        const mobileImage = slideContent.getAttribute('data-mobile-image');
        
        const isMobile = isMobileDevice();
        const imageUrl = (isMobile && mobileImage) ? mobileImage : desktopImage;
        
        slideContent.style.backgroundImage = `url('${imageUrl}')`;
    });
}

// Slide navigation functions
function changeSlide(sliderId, direction) {
    const slider = document.getElementById(sliderId);
    if (!slider) return;
    
    const slides = slider.querySelectorAll('.slide');
    const dots = slider.querySelectorAll('.slide-dot');
    const currentSlide = slider.querySelector('.slide.active');
    const currentIndex = Array.from(slides).indexOf(currentSlide);
    
    let newIndex = currentIndex + direction;
    
    // Handle wrap-around
    if (newIndex >= slides.length) {
        newIndex = 0;
    } else if (newIndex < 0) {
        newIndex = slides.length - 1;
    }
    
    // Update slides
    slides.forEach((slide, index) => {
        slide.classList.toggle('active', index === newIndex);
    });
    
    // Update dots
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === newIndex);
    });
}

function goToSlide(sliderId, index) {
    const slider = document.getElementById(sliderId);
    if (!slider) return;
    
    const slides = slider.querySelectorAll('.slide');
    const dots = slider.querySelectorAll('.slide-dot');
    
    // Update slides
    slides.forEach((slide, slideIndex) => {
        slide.classList.toggle('active', slideIndex === index);
    });
    
    // Update dots
    dots.forEach((dot, dotIndex) => {
        dot.classList.toggle('active', dotIndex === index);
    });
}

// Enhanced banner content loading
function loadBannerContent(position, container) {
    console.log(`Loading banner content for position ${position} into container:`, container);
    
    // Check if banner exists before showing loader
    fetch(`/api/banners/${position}`)
        .then(response => {
            console.log(`API response status for ${position}:`, response.status);
            return response.json();
        })
        .then(data => {
            console.log(`API data for ${position}:`, data);
            
            // If no banner or no slides, hide container immediately
            if (!data.success || !data.banner || !data.banner.slides || data.banner.slides.length === 0) {
                console.log(`No banner content for position ${position}, hiding container`);
                container.style.display = 'none';
                return;
            }
            
            // Show loading state only if banner exists
            const loader = container.querySelector('.banner-loader');
            if (loader) {
                loader.style.display = 'block';
            }
            
            // Small delay to show loader (better UX)
            setTimeout(() => {
                // Hide loader
                if (loader) {
                    loader.style.display = 'none';
                }
            
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
                    }
                }
                
                // Add click event listeners for tracking
                const slides = container.querySelectorAll('.banner-link');
                slides.forEach(slide => {
                    slide.addEventListener('click', function(event) {
                        const slideId = this.getAttribute('data-slide-id');
                        console.log(`Banner slide clicked: ${slideId}`);
                        
                        // Record click asynchronously
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
                
            }, 100); // Small delay to show loader briefly
        })
        .catch(error => {
            console.error(`Error loading banner for position ${position}:`, error);
            container.style.display = 'none';
        });
}

// Enhanced banner loader function
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
        // Try alternate method
        const altContainer = document.querySelector(`#${containerId}, .banner-container[id="${containerId}"]`);
        if (altContainer) {
            loadBannerContent(position, altContainer);
            return;
        } else {
            console.error("Container not found with alternative method either");
            return;
        }
    }
    
    loadBannerContent(position, container);
}

// Banner position mapping (should match your existing configuration)
const bannerPositionMap = {
    'hero_banner': 'hero-banner',
    'between_hero_stats': 'banner-1',
    'between_treatment_categories': 'banner-2',
    'between_popular_procedures': 'banner-3',
    'between_top_specialists': 'banner-4',
    'between_community_posts': 'banner-5',
    'before_footer': 'banner-6'
};

// Load all banners on document ready
document.addEventListener('DOMContentLoaded', function() {
    console.log("Enhanced banner loader started with mobile/desktop image support");
    
    // Load each banner
    Object.keys(bannerPositionMap).forEach(position => {
        console.log(`Loading banner for position: ${position}`);
        loadBanner(position);
    });
});