// Package Filters JavaScript
class PackageFilters {
    constructor() {
        this.searchInput = document.getElementById('searchInput');
        this.locationInput = document.getElementById('locationInput');
        this.categorySelect = document.getElementById('categorySelect');
        this.searchSuggestions = document.getElementById('searchSuggestions');
        this.locationDropdown = document.getElementById('locationDropdown');
        this.advancedFiltersToggle = document.getElementById('advancedFiltersToggle');
        this.advancedFiltersSection = document.getElementById('advancedFiltersSection');
        this.useLocationBtn = document.getElementById('useLocationBtn');
        
        this.currentSearchSuggestions = [];
        this.currentLocationSuggestions = [];
        
        this.init();
    }

    init() {
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.searchPackages(e.target.value);
            });
        }

        if (this.locationInput) {
            this.locationInput.addEventListener('input', (e) => {
                this.searchLocations(e.target.value);
            });
        }

        if (this.advancedFiltersToggle) {
            this.advancedFiltersToggle.addEventListener('click', () => {
                this.toggleAdvancedFilters();
            });
        }

        if (this.useLocationBtn) {
            this.useLocationBtn.addEventListener('click', () => {
                this.getCurrentLocation();
            });
        }

        // Hide dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.position-relative')) {
                this.hideAllDropdowns();
            }
        });
    }

    async searchPackages(query) {
        if (query.length < 2) {
            this.hideSearchSuggestions();
            return;
        }

        try {
            console.log('Searching packages for:', query);
            const response = await fetch(`/api/search/packages?q=${encodeURIComponent(query)}`);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Package search response:', data);
                
                if (data.success && data.suggestions && data.suggestions.length > 0) {
                    this.currentSearchSuggestions = data.suggestions;
                    this.showSearchSuggestions();
                } else {
                    this.hideSearchSuggestions();
                }
            }
        } catch (error) {
            console.error('Error searching packages:', error);
        }
    }

    async searchLocations(query) {
        if (query.length < 2) {
            this.hideLocationDropdown();
            return;
        }

        try {
            const response = await fetch(`/api/search/locations?q=${encodeURIComponent(query)}&type=package`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.suggestions && data.suggestions.length > 0) {
                    this.currentLocationSuggestions = data.suggestions;
                    this.showLocationDropdown();
                } else {
                    this.hideLocationDropdown();
                }
            }
        } catch (error) {
            console.error('Error searching locations:', error);
        }
    }

    showSearchSuggestions() {
        if (!this.searchSuggestions || !this.currentSearchSuggestions.length) return;

        let html = '';
        this.currentSearchSuggestions.forEach((suggestion, index) => {
            html += `
                <div class="dropdown-item" data-index="${index}" data-value="${suggestion.text}">
                    <i class="fas ${suggestion.icon} me-2 text-muted"></i>
                    <div>
                        <span class="fw-medium">${suggestion.text}</span>
                        <small class="text-muted d-block">${suggestion.subtitle}</small>
                    </div>
                </div>
            `;
        });

        this.searchSuggestions.innerHTML = html;
        this.searchSuggestions.style.display = 'block';

        // Add click handlers
        this.searchSuggestions.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                const value = item.getAttribute('data-value');
                this.searchInput.value = value;
                this.hideSearchSuggestions();
                
                // Auto-submit the form
                const form = document.getElementById('filterForm');
                if (form) form.submit();
            });
        });
    }

    showLocationDropdown() {
        if (!this.locationDropdown || !this.currentLocationSuggestions.length) return;

        let html = '';
        this.currentLocationSuggestions.forEach((suggestion, index) => {
            html += `
                <div class="dropdown-item" data-index="${index}" data-value="${suggestion.text}">
                    <i class="fas fa-map-marker-alt me-2 text-muted"></i>
                    <span class="fw-medium">${suggestion.text}</span>
                </div>
            `;
        });

        this.locationDropdown.innerHTML = html;
        this.locationDropdown.style.display = 'block';

        // Add click handlers
        this.locationDropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                const value = item.getAttribute('data-value');
                this.locationInput.value = value;
                this.hideLocationDropdown();
            });
        });
    }

    hideSearchSuggestions() {
        if (this.searchSuggestions) {
            this.searchSuggestions.style.display = 'none';
        }
    }

    hideLocationDropdown() {
        if (this.locationDropdown) {
            this.locationDropdown.style.display = 'none';
        }
    }

    hideAllDropdowns() {
        this.hideSearchSuggestions();
        this.hideLocationDropdown();
    }

    toggleAdvancedFilters() {
        if (this.advancedFiltersSection) {
            const isVisible = this.advancedFiltersSection.style.display !== 'none';
            this.advancedFiltersSection.style.display = isVisible ? 'none' : 'block';
            
            // Update toggle icon
            const icon = this.advancedFiltersToggle.querySelector('i');
            if (icon) {
                icon.className = isVisible ? 'fas fa-chevron-down me-1' : 'fas fa-chevron-up me-1';
            }
        }
    }

    getCurrentLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    // You can implement reverse geocoding here
                    console.log('Current position:', position.coords);
                    // For now, just set a placeholder
                    this.locationInput.value = 'Current Location';
                },
                (error) => {
                    console.error('Error getting location:', error);
                    alert('Unable to get your current location. Please enter manually.');
                }
            );
        } else {
            alert('Geolocation is not supported by this browser.');
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('filterForm')) {
        new PackageFilters();
        console.log('Package filters initialized successfully');
    }
});