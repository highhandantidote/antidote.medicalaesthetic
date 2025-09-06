// Optimized Banner Loader with WebP support and lazy loading
console.log('Optimized banner loader started');

// WebP support detection
function supportsWebP() {
    return new Promise((resolve) => {
        const webP = new Image();
        webP.onload = webP.onerror = () => {
            resolve(webP.height === 2);
        };
        webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
    });
}

// Mobile detection
function isMobile() {
    return window.innerWidth <= 768;
}

// Optimized banner loading with WebP support
async function loadOptimizedBanner() {
    const container = document.getElementById('hero-banner');
    if (!container) return;
    
    try {
        const response = await fetch(`/api/banners/hero_banner?v=${Date.now()}`);
        const data = await response.json();
        
        if (data.success && data.banner && data.banner.slides.length > 0) {
            const slide = data.banner.slides[0];
            const webpSupported = await supportsWebP();
            const mobile = isMobile();
            
            // Determine the best image format and size
            let imageUrl = slide.image_url;
            
            if (webpSupported) {
                // Use WebP version if available
                if (mobile && slide.mobile_image_url) {
                    imageUrl = slide.mobile_image_url.includes('.webp') ? slide.mobile_image_url : slide.mobile_image_url.replace('.png', '.webp');
                } else {
                    imageUrl = slide.image_url.includes('.webp') ? slide.image_url : slide.image_url.replace('.png', '.webp');
                }
            } else {
                // Use PNG fallback for non-WebP browsers
                if (mobile && slide.mobile_image_url) {
                    imageUrl = slide.mobile_image_url.includes('.png') ? slide.mobile_image_url : slide.mobile_image_url.replace('.webp', '.png');
                } else {
                    imageUrl = slide.image_url.includes('.png') ? slide.image_url : slide.image_url.replace('.webp', '.png');
                }
            }
            
            // Add cache-busting parameter to image URL
            const cacheBustingParam = `?v=${Date.now()}`;
            const cacheBustedImageUrl = `${imageUrl}${cacheBustingParam}`;
            
            // Create optimized banner HTML without text overlay
            const bannerHTML = `
                <div class="slide-content" style="background-image: url('${cacheBustedImageUrl}');">
                    <a href="${slide.redirect_url}" class="banner-link" onclick="trackBannerClick(${slide.id})">
                    </a>
                </div>
            `;
            
            container.innerHTML = bannerHTML;
            
            // Track banner impression
            trackBannerImpression(slide.id);
            
            console.log('Optimized banner loaded successfully');
        } else {
            // Hide banner container if no content
            container.style.display = 'none';
            console.log('No banner content available');
        }
    } catch (error) {
        console.error('Error loading optimized banner:', error);
        container.style.display = 'none';
    }
}

// Track banner impression
function trackBannerImpression(slideId) {
    // Get CSRF token if available
    const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || 
                     document.querySelector('input[name=csrf_token]')?.value;
    
    const headers = {
        'Content-Type': 'application/json',
    };
    
    const data = { slide_id: slideId };
    
    // Add CSRF token if available
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
        data.csrf_token = csrfToken;
    }
    
    fetch('/api/banners/impression', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data)
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

// Initialize banner loading when DOM is ready
document.addEventListener('DOMContentLoaded', loadOptimizedBanner);

// Reinitialize on window resize for responsive images
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        const newMobile = isMobile();
        if (newMobile !== isMobile()) {
            loadOptimizedBanner();
        }
    }, 300);
});