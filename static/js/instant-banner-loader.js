/**
 * Instant Hero Banner Loader - Optimized for immediate loading
 * Eliminates API calls by using server-rendered data and preloaded images
 */

class InstantBannerLoader {
    constructor() {
        this.bannerData = null;
        this.container = null;
        this.isLoaded = false;
    }

    // Initialize with server-rendered data
    init(bannerData) {
        this.bannerData = bannerData;
        this.container = document.getElementById('hero-banner');
        
        if (!this.container) {
            console.log('Hero banner container not found');
            return;
        }

        if (!bannerData || !bannerData.slides || bannerData.slides.length === 0) {
            this.hideBanner();
            return;
        }

        // Load banner immediately
        this.loadBannerInstantly();
    }

    loadBannerInstantly() {
        const slide = this.bannerData.slides[0]; // Use first slide
        
        // Determine optimal image URL
        const isMobile = window.innerWidth <= 768;
        const imageUrl = (isMobile && slide.mobile_image_url) ? slide.mobile_image_url : slide.image_url;
        
        if (!imageUrl) {
            this.hideBanner();
            return;
        }

        // Create optimized banner HTML
        const bannerHtml = `
            <div class="banner-slider" style="position: relative; height: 300px; border-radius: 0; overflow: hidden;">
                <div class="slide active" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0;">
                    <a href="${slide.redirect_url || '#'}" class="banner-link" data-slide-id="${slide.id}">
                        <div class="slide-content" style="
                            background-image: url('${imageUrl}');
                            background-size: cover;
                            background-position: center;
                            background-repeat: no-repeat;
                            height: 100%;
                            width: 100%;
                            border-radius: 0;
                        "></div>
                    </a>
                </div>
            </div>
        `;
        
        // Insert banner HTML
        this.container.innerHTML = bannerHtml;
        this.container.style.display = 'block';
        this.isLoaded = true;
        
        // Track impression asynchronously (don't block loading)
        this.trackImpressionAsync(slide.id);
        
        // Add click tracking
        const bannerLink = this.container.querySelector('.banner-link');
        if (bannerLink) {
            bannerLink.addEventListener('click', () => {
                this.trackClickAsync(slide.id);
            });
        }
        
        console.log('✅ Hero banner loaded instantly');
    }

    hideBanner() {
        if (this.container) {
            this.container.style.display = 'none';
        }
        console.log('No hero banner data available');
    }

    // Async impression tracking (won't delay banner display)
    trackImpressionAsync(slideId) {
        // Use setTimeout to ensure this doesn't block banner rendering
        setTimeout(() => {
            fetch('/api/banners/impression', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ slide_id: slideId })
            }).then(response => {
                if (response.ok) {
                    console.log('✅ Banner impression tracked');
                } else {
                    console.log('⚠️ Banner impression tracking failed (non-blocking)');
                }
            }).catch(error => {
                console.log('⚠️ Banner impression error (non-blocking):', error.message);
            });
        }, 100); // Small delay to ensure banner is rendered first
    }

    // Async click tracking
    trackClickAsync(slideId) {
        fetch('/api/banners/click', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ slide_id: slideId })
        }).catch(error => {
            console.log('Banner click tracking error:', error.message);
        });
    }

    // Handle window resize for responsive images
    handleResize() {
        if (!this.isLoaded || !this.bannerData) return;
        
        const slide = this.bannerData.slides[0];
        const isMobile = window.innerWidth <= 768;
        const imageUrl = (isMobile && slide.mobile_image_url) ? slide.mobile_image_url : slide.image_url;
        
        const slideContent = this.container.querySelector('.slide-content');
        if (slideContent && imageUrl) {
            slideContent.style.backgroundImage = `url('${imageUrl}')`;
        }
    }
}

// Global instance
const instantBannerLoader = new InstantBannerLoader();

// Handle window resize with debouncing
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        instantBannerLoader.handleResize();
    }, 250);
});

// Export for server-side initialization
window.instantBannerLoader = instantBannerLoader;