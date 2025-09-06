/**
 * Optimized Hero Banner Loader - Simplified for performance
 * Only loads the hero banner, all other banners have been removed
 */

// Initialize hero banner loading
document.addEventListener('DOMContentLoaded', function() {
    console.log("Smart banner loader started");
    
    // Check for hero banner - restored functionality
    fetch(`/api/banners/active-positions?v=${Date.now()}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.positions && data.positions.includes('hero_banner')) {
                console.log("Active banner positions:", data.positions);
                loadHeroBanner();
            } else {
                console.log("No hero banner found, hiding container");
                const heroContainer = document.getElementById('hero-banner');
                if (heroContainer) {
                    heroContainer.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Error fetching banner positions:', error);
            const heroContainer = document.getElementById('hero-banner');
            if (heroContainer) {
                heroContainer.style.display = 'none';
            }
        });
});

function loadHeroBanner() {
    const container = document.getElementById('hero-banner');
    
    if (!container) {
        console.error('Hero banner container not found');
        return;
    }
    
    // Show container and loading state
    container.style.display = 'block';
    const loader = container.querySelector('.banner-loader');
    if (loader) {
        loader.style.display = 'block';
    }
    
    // Load hero banner content with cache-busting
    fetch(`/api/banners/hero_banner?v=${Date.now()}`)
        .then(response => response.json())
        .then(data => {
            if (loader) {
                loader.style.display = 'none';
            }
            
            if (data.success && data.banner && data.banner.slides && data.banner.slides.length > 0) {
                displayBanner(data.banner, container);
            } else {
                container.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error loading hero banner:', error);
            if (loader) {
                loader.style.display = 'none';
            }
            container.style.display = 'none';
        });
}

function displayBanner(banner, container) {
    const slide = banner.slides[0];
    
    // Determine the best image to use
    const isMobile = window.innerWidth <= 768;
    const baseImageUrl = (isMobile && slide.mobile_image_url) ? slide.mobile_image_url : slide.image_url;
    const imageUrl = `${baseImageUrl}?v=${Date.now()}`;
    
    const bannerHtml = `
        <div class="banner-slider" style="position: relative; height: 200px; border-radius: 15px; overflow: hidden;">
            <div class="slide active" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0;">
                <a href="${slide.redirect_url}" class="banner-link" data-slide-id="${slide.id}">
                    <div class="slide-content" style="background-image: url('${imageUrl}'); background-size: cover; background-position: center; height: 100%; width: 100%; border-radius: 15px;">
                    </div>
                </a>
            </div>
        </div>
    `;
    
    container.innerHTML = bannerHtml;
    
    // Track impression
    trackBannerImpression(slide.id);
    
    // Add click tracking
    const bannerLink = container.querySelector('.banner-link');
    if (bannerLink) {
        bannerLink.addEventListener('click', function() {
            trackBannerClick(slide.id);
        });
    }
}

// Track banner impression (simplified - no CSRF required)
function trackBannerImpression(slideId) {
    fetch('/api/banners/impression', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ slide_id: slideId })
    }).then(response => {
        if (response.ok) {
            console.log("✅ Banner impression tracked successfully");
        } else {
            console.warn("⚠️ Banner impression tracking failed:", response.status);
        }
    }).catch(error => {
        console.error('Error tracking banner impression:', error);
    });
}

// Track banner click
function trackBannerClick(slideId) {
    fetch('/api/banners/click', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ slide_id: slideId })
    }).catch(error => {
        console.error('Error tracking banner click:', error);
    });
}