/**
 * Enhanced Package Filtering System
 * Provides advanced filtering with autocomplete, geolocation, and real-time updates
 */

// Prevent multiple instantiations
if (typeof window.PackageFilters === 'undefined') {
    window.PackageFilters = class PackageFilters {
        constructor() {
            this.debounceTimer = null;
            this.currentCategories = [];
            this.currentLocations = [];
            this.userLocation = null;
            this.init();
        }

        init() {
            this.setupEventListeners();
            this.loadInitialData();
            this.setupActiveFilters();
            this.detectUserLocation();
        }

        setupEventListeners() {
            // Search input with debounced suggestions
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    this.debounceSearch(e.target.value);
                });
            }

            // Category input with autocomplete
            const categoryInput = document.getElementById('categoryInput');
            if (categoryInput) {
                categoryInput.addEventListener('input', (e) => {
                    this.searchCategories(e.target.value);
                });
                categoryInput.addEventListener('focus', () => {
                    this.showCategoryDropdown();
                });
                categoryInput.addEventListener('blur', (e) => {
                    setTimeout(() => this.hideCategoryDropdown(), 200);
                });
            }

            // Location input with autocomplete
            const locationInput = document.getElementById('locationInput');
            if (locationInput) {
                locationInput.addEventListener('input', (e) => {
                    this.searchLocations(e.target.value);
                });
                locationInput.addEventListener('focus', () => {
                    this.showLocationDropdown();
                });
                locationInput.addEventListener('blur', (e) => {
                    setTimeout(() => this.hideLocationDropdown(), 200);
                });
            }

            // Use location button
            const useLocationBtn = document.getElementById('useLocationBtn');
            if (useLocationBtn) {
                useLocationBtn.addEventListener('click', () => {
                    this.useCurrentLocation();
                });
            }

            // Category dropdown arrow click handler
            const categoryDropdownArrow = document.querySelector('#categoryInput + .dropdown-arrow');
            if (categoryDropdownArrow) {
                categoryDropdownArrow.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    document.getElementById('categoryInput').focus();
                    this.showCategoryDropdown();
                });
            }

            // Location dropdown arrow click handler
            const locationDropdownArrow = document.querySelector('#locationInput + .dropdown-arrow');
            if (locationDropdownArrow) {
                locationDropdownArrow.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    document.getElementById('locationInput').focus();
                    this.showLocationDropdown();
                });
            }

            // Quick price presets
            document.querySelectorAll('.quick-price').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const min = e.target.dataset.min;
                    const max = e.target.dataset.max;
                    this.setQuickPrice(min, max);
                });
            });

            // Clear filters button
            const clearFiltersBtn = document.getElementById('clearFilters');
            if (clearFiltersBtn) {
                clearFiltersBtn.addEventListener('click', () => {
                    this.clearAllFilters();
                });
            }

            // Close dropdowns on outside click
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.position-relative')) {
                    this.hideAllDropdowns();
                }
            });

            // Advanced filters toggle
            const advancedToggle = document.getElementById('advancedFiltersToggle');
            if (advancedToggle) {
                advancedToggle.addEventListener('click', () => {
                    this.toggleAdvancedFilters();
                });
            }
        }

        debounceSearch(query) {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.showSearchSuggestions(query);
            }, 300);
        }

        async showSearchSuggestions(query) {
            if (!query || query.length < 2) {
                this.hideSearchSuggestions();
                return;
            }

            try {
                const response = await fetch(`/api/packages/filters?search=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.success) {
                    this.renderSearchSuggestions(data.suggestions);
                }
            } catch (error) {
                console.error('Error loading search suggestions:', error);
            }
        }

        renderSearchSuggestions(suggestions) {
            const container = document.getElementById('searchSuggestions');
            if (!container) return;

            container.innerHTML = suggestions.map(item => `
                <div class="suggestion-item" data-type="${item.type}" data-value="${item.value}">
                    <div class="suggestion-text">${item.text}</div>
                    <div class="suggestion-subtext">${item.subtext}</div>
                </div>
            `).join('');

            // Add click handlers
            container.querySelectorAll('.suggestion-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    const type = e.currentTarget.dataset.type;
                    const value = e.currentTarget.dataset.value;
                    
                    if (type === 'category') {
                        document.getElementById('categoryInput').value = value;
                    } else if (type === 'location') {
                        document.getElementById('locationInput').value = value;
                    }
                    
                    this.hideSearchSuggestions();
                    this.submitForm();
                });
            });

            container.style.display = 'block';
        }

        hideSearchSuggestions() {
            const container = document.getElementById('searchSuggestions');
            if (container) {
                container.style.display = 'none';
            }
        }

        async searchCategories(query) {
            try {
                const response = await fetch(`/api/categories/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.success) {
                    this.currentCategories = data.categories;
                    this.renderCategoryDropdown(data.categories);
                }
            } catch (error) {
                console.error('Error searching categories:', error);
            }
        }

        renderCategoryDropdown(categories) {
            const dropdown = document.getElementById('categoryDropdown');
            if (!dropdown) return;

            dropdown.innerHTML = categories.map(cat => `
                <div class="dropdown-item" data-value="${cat.name}">
                    <div class="dropdown-text">${cat.name}</div>
                    <div class="dropdown-count">${cat.count} packages</div>
                </div>
            `).join('');

            // Add click handlers
            dropdown.querySelectorAll('.dropdown-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    const value = e.currentTarget.dataset.value;
                    document.getElementById('categoryInput').value = value;
                    this.hideCategoryDropdown();
                    this.updateActiveFilters();
                    this.submitForm();
                });
            });

            dropdown.style.display = 'block';
        }

        showCategoryDropdown() {
            this.searchCategories('');
        }

        hideCategoryDropdown() {
            const dropdown = document.getElementById('categoryDropdown');
            if (dropdown) {
                dropdown.style.display = 'none';
            }
        }

        async searchLocations(query) {
            try {
                const response = await fetch(`/api/locations/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.success) {
                    this.currentLocations = data.locations;
                    this.renderLocationDropdown(data.locations);
                }
            } catch (error) {
                console.error('Error searching locations:', error);
            }
        }

        renderLocationDropdown(locations) {
            const dropdown = document.getElementById('locationDropdown');
            if (!dropdown) return;

            dropdown.innerHTML = locations.map(loc => `
                <div class="dropdown-item" data-value="${loc.display_name}">
                    <div class="dropdown-text">${loc.display_name}</div>
                    <div class="dropdown-count">${loc.count} packages</div>
                </div>
            `).join('');

            // Add click handlers
            dropdown.querySelectorAll('.dropdown-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    const value = e.currentTarget.dataset.value;
                    document.getElementById('locationInput').value = value;
                    this.hideLocationDropdown();
                    this.updateActiveFilters();
                    this.submitForm();
                });
            });

            dropdown.style.display = 'block';
        }

        showLocationDropdown() {
            this.searchLocations('');
        }

        hideLocationDropdown() {
            const dropdown = document.getElementById('locationDropdown');
            if (dropdown) {
                dropdown.style.display = 'none';
            }
        }

        hideAllDropdowns() {
            this.hideSearchSuggestions();
            this.hideCategoryDropdown();
            this.hideLocationDropdown();
        }

        async detectUserLocation() {
            try {
                const response = await fetch('/api/geolocation');
                const data = await response.json();
                
                if (data.success) {
                    this.userLocation = data;
                    this.updateLocationButton();
                }
            } catch (error) {
                console.log('Could not detect location:', error);
            }
        }

        updateLocationButton() {
            const btn = document.getElementById('useLocationBtn');
            if (btn && this.userLocation) {
                btn.title = `Use current location (${this.userLocation.city})`;
                btn.style.display = 'block';
            }
        }

        useCurrentLocation() {
            if (this.userLocation) {
                document.getElementById('locationInput').value = this.userLocation.city;
                this.updateActiveFilters();
                this.submitForm();
            }
        }

        setQuickPrice(min, max) {
            document.getElementById('minPriceInput').value = min;
            document.getElementById('maxPriceInput').value = max || '';
            
            // Update button states
            document.querySelectorAll('.quick-price').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            this.updateActiveFilters();
            this.submitForm();
        }

        setupActiveFilters() {
            this.updateActiveFilters();
        }

        updateActiveFilters() {
            const activeFilters = document.getElementById('activeFilters');
            const filterTags = document.getElementById('filterTags');
            
            if (!activeFilters || !filterTags) return;

            const filters = [];
            
            // Check category
            const category = document.getElementById('categoryInput').value;
            if (category) {
                filters.push({
                    type: 'category',
                    value: category,
                    display: `Category: ${category}`
                });
            }
            
            // Check location
            const location = document.getElementById('locationInput').value;
            if (location) {
                filters.push({
                    type: 'location',
                    value: location,
                    display: `Location: ${location}`
                });
            }
            
            // Check price range
            const minPrice = document.getElementById('minPriceInput').value;
            const maxPrice = document.getElementById('maxPriceInput').value;
            if (minPrice || maxPrice) {
                const priceDisplay = `Price: ₹${minPrice || '0'} - ₹${maxPrice || '∞'}`;
                filters.push({
                    type: 'price',
                    value: `${minPrice}-${maxPrice}`,
                    display: priceDisplay
                });
            }

            if (filters.length > 0) {
                filterTags.innerHTML = filters.map(filter => `
                    <span class="badge bg-primary me-2">
                        ${filter.display}
                        <button type="button" class="btn-close btn-close-white ms-1" 
                                onclick="window.packageFilters.removeFilter('${filter.type}')"></button>
                    </span>
                `).join('');
                activeFilters.style.display = 'block';
            } else {
                activeFilters.style.display = 'none';
            }
        }

        removeFilter(type) {
            switch (type) {
                case 'category':
                    document.getElementById('categoryInput').value = '';
                    break;
                case 'location':
                    document.getElementById('locationInput').value = '';
                    break;
                case 'price':
                    document.getElementById('minPriceInput').value = '';
                    document.getElementById('maxPriceInput').value = '';
                    break;
            }
            
            this.updateActiveFilters();
            this.submitForm();
        }

        clearAllFilters() {
            document.getElementById('searchInput').value = '';
            document.getElementById('categoryInput').value = '';
            document.getElementById('locationInput').value = '';
            document.getElementById('minPriceInput').value = '';
            document.getElementById('maxPriceInput').value = '';
            
            this.updateActiveFilters();
            this.submitForm();
        }

        submitForm() {
            document.getElementById('filterForm').submit();
        }

        async loadInitialData() {
            try {
                // Load categories
                const categoriesResponse = await fetch('/api/categories/search');
                const categoriesData = await categoriesResponse.json();
                if (categoriesData.success) {
                    this.currentCategories = categoriesData.categories;
                }

                // Load locations
                const locationsResponse = await fetch('/api/locations/search');
                const locationsData = await locationsResponse.json();
                if (locationsData.success) {
                    this.currentLocations = locationsData.locations;
                }

                // Check if advanced filters should be shown
                this.checkAdvancedFiltersVisibility();
            } catch (error) {
                console.error('Error loading initial data:', error);
            }
        }

        toggleAdvancedFilters() {
            const section = document.getElementById('advancedFiltersSection');
            const toggle = document.getElementById('advancedFiltersToggle');
            const icon = toggle.querySelector('i');
            
            if (section.style.display === 'none') {
                section.style.display = 'block';
                icon.className = 'fas fa-chevron-up me-1';
                toggle.querySelector('span').textContent = 'Hide Advanced Filters';
            } else {
                section.style.display = 'none';
                icon.className = 'fas fa-chevron-down me-1';
                toggle.querySelector('span').textContent = 'Advanced Filters';
            }
        }

        checkAdvancedFiltersVisibility() {
            // Show advanced filters if any advanced filter has a value
            const category = document.getElementById('categoryInput').value;
            const minPrice = document.getElementById('minPriceInput').value;
            const maxPrice = document.getElementById('maxPriceInput').value;
            const sort = document.querySelector('select[name="sort"]').value;
            
            if (category || minPrice || maxPrice || (sort && sort !== 'newest')) {
                this.toggleAdvancedFilters();
            }
        }
    }; // End of PackageFilters class
}

// Initialize the package filters when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Prevent multiple instantiations
    if (!window.packageFilters) {
        window.packageFilters = new window.PackageFilters();
    }
});