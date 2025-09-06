/**
 * Advanced Clinic Directory Filtering System
 * Provides real-time search, location filtering, and specialty selection with autocomplete
 */

// Prevent duplicate class declaration
if (typeof window.ClinicDirectoryFilters === 'undefined') {

class ClinicDirectoryFilters {
    constructor() {
        this.currentSearchSuggestions = [];
        this.currentLocations = [];
        this.currentSpecialties = [];
        this.searchTimeout = null;
        this.locationTimeout = null;
        this.specialtyTimeout = null;
        
        this.init();
    }

    init() {
        // Initialize all filter components
        this.initSearchFilter();
        this.initLocationFilter();
        this.initSpecialtyFilter();
        this.initAdvancedFilters();
        this.initClearFilters();
        this.loadInitialData();
    }

    initSearchFilter() {
        const searchInput = document.getElementById('clinicSearchInput');
        const searchSuggestions = document.getElementById('clinicSearchSuggestions');
        
        if (!searchInput || !searchSuggestions) return;

        // Handle search input with debouncing
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                if (query.length >= 2) {
                    this.searchClinics(query);
                } else {
                    this.hideSearchSuggestions();
                }
            }, 300);
        });

        // Handle focus to show recent searches or empty state
        searchInput.addEventListener('focus', () => {
            if (searchInput.value.trim().length >= 2) {
                this.searchClinics(searchInput.value.trim());
            }
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
                this.hideSearchSuggestions();
            }
        });

        // Handle keyboard navigation
        searchInput.addEventListener('keydown', (e) => {
            this.handleSearchKeyNavigation(e);
        });
    }

    initLocationFilter() {
        const locationInput = document.getElementById('clinicLocationInput');
        const locationDropdown = document.getElementById('clinicLocationDropdown');
        const useLocationBtn = document.getElementById('useLocationBtn');
        
        if (!locationInput || !locationDropdown) return;

        // Handle location input with filtering
        locationInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            clearTimeout(this.locationTimeout);
            this.locationTimeout = setTimeout(() => {
                this.handleLocationInput(query);
            }, 300);
        });

        // Show all locations on focus
        locationInput.addEventListener('focus', () => {
            this.showLocationDropdown();
        });

        // Use current location button
        if (useLocationBtn) {
            useLocationBtn.addEventListener('click', () => {
                this.useCurrentLocation();
            });
        }

        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!locationInput.contains(e.target) && !locationDropdown.contains(e.target)) {
                this.hideLocationDropdown();
            }
        });

        // Show use location button when input is focused and empty
        locationInput.addEventListener('focus', () => {
            if (!locationInput.value.trim() && navigator.geolocation) {
                useLocationBtn.style.display = 'block';
            }
        });

        locationInput.addEventListener('blur', () => {
            setTimeout(() => {
                useLocationBtn.style.display = 'none';
            }, 200);
        });
    }

    initSpecialtyFilter() {
        const specialtyInput = document.getElementById('clinicSpecialtyInput');
        const specialtyDropdown = document.getElementById('clinicSpecialtyDropdown');
        
        if (!specialtyInput || !specialtyDropdown) return;

        // Handle specialty input with filtering
        specialtyInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            clearTimeout(this.specialtyTimeout);
            this.specialtyTimeout = setTimeout(() => {
                this.handleSpecialtyInput(query);
            }, 300);
        });

        // Show all specialties on focus
        specialtyInput.addEventListener('focus', () => {
            this.showSpecialtyDropdown();
        });

        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!specialtyInput.contains(e.target) && !specialtyDropdown.contains(e.target)) {
                this.hideSpecialtyDropdown();
            }
        });
    }

    initAdvancedFilters() {
        const toggleBtn = document.getElementById('clinicAdvancedFiltersToggle');
        const filtersSection = document.getElementById('clinicAdvancedFiltersSection');
        
        if (!toggleBtn || !filtersSection) return;

        toggleBtn.addEventListener('click', () => {
            const isVisible = filtersSection.style.display !== 'none';
            const icon = toggleBtn.querySelector('i');
            
            if (isVisible) {
                filtersSection.style.display = 'none';
                icon.className = 'fas fa-chevron-down me-1';
                toggleBtn.querySelector('span').textContent = 'Show Advanced Filters';
            } else {
                filtersSection.style.display = 'block';
                icon.className = 'fas fa-chevron-up me-1';
                toggleBtn.querySelector('span').textContent = 'Hide Advanced Filters';
            }
        });
    }

    initClearFilters() {
        const clearBtn = document.getElementById('clinicClearFilters');
        
        if (!clearBtn) return;

        clearBtn.addEventListener('click', () => {
            // Clear all form inputs
            const form = document.getElementById('clinicFilterForm');
            if (form) {
                const inputs = form.querySelectorAll('input, select');
                inputs.forEach(input => {
                    if (input.type === 'text' || input.tagName === 'SELECT') {
                        input.value = '';
                    }
                });
                
                // Hide all dropdowns
                this.hideSearchSuggestions();
                this.hideLocationDropdown();
                this.hideSpecialtyDropdown();
                
                // Submit the form to clear filters
                form.submit();
            }
        });
    }

    async loadInitialData() {
        try {
            // Load locations
            const locationsResponse = await fetch('/clinic/api/clinic/locations');
            if (locationsResponse.ok) {
                const locationsData = await locationsResponse.json();
                if (locationsData.success) {
                    this.currentLocations = locationsData.locations;
                }
            }

            // Load specialties
            const specialtiesResponse = await fetch('/clinic/api/clinic/specialties');
            if (specialtiesResponse.ok) {
                const specialtiesData = await specialtiesResponse.json();
                if (specialtiesData.success) {
                    this.currentSpecialties = specialtiesData.specialties;
                }
            }
        } catch (error) {
            console.error('Error loading initial filter data:', error);
        }
    }

    async searchClinics(query) {
        if (query.length < 2) {
            this.hideSearchSuggestions();
            return;
        }

        try {
            console.log('Searching for:', query);
            const response = await fetch(`/clinic/api/clinic/search?q=${encodeURIComponent(query)}`);
            console.log('Response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Search response:', data);
                
                if (data.success && data.suggestions && data.suggestions.length > 0) {
                    this.currentSearchSuggestions = data.suggestions;
                    this.showSearchSuggestions();
                } else {
                    console.log('No suggestions found');
                    this.hideSearchSuggestions();
                }
            } else {
                console.error('Search request failed with status:', response.status);
            }
        } catch (error) {
            console.error('Error searching clinics:', error);
        }
    }

    handleLocationInput(query) {
        if (query.length < 1) {
            this.showLocationDropdown();
            return;
        }
        
        const filtered = this.currentLocations.filter(location => 
            location.toLowerCase().includes(query.toLowerCase())
        );
        this.showLocationDropdown(filtered);
    }

    handleSpecialtyInput(query) {
        const filtered = this.currentSpecialties.filter(specialty => 
            specialty.toLowerCase().includes(query.toLowerCase())
        );
        this.showSpecialtyDropdown(filtered);
    }

    showSearchSuggestions() {
        const dropdown = document.getElementById('clinicSearchSuggestions');
        const input = document.getElementById('clinicSearchInput');
        
        console.log('Showing suggestions:', this.currentSearchSuggestions);
        
        if (!dropdown || !this.currentSearchSuggestions.length) {
            console.log('No dropdown element or no suggestions');
            return;
        }

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

        dropdown.innerHTML = html;
        dropdown.style.display = 'block';
        console.log('Dropdown displayed with HTML:', html);

        // Add click handlers
        dropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                const value = item.getAttribute('data-value');
                input.value = value;
                this.hideSearchSuggestions();
                
                // Auto-submit the form
                const form = document.getElementById('clinicFilterForm');
                if (form) form.submit();
            });
        });
    }

    showLocationDropdown(filteredLocations = null) {
        const dropdown = document.getElementById('clinicLocationDropdown');
        const input = document.getElementById('clinicLocationInput');
        
        if (!dropdown) return;

        const locations = filteredLocations || this.currentLocations;
        
        if (!locations.length) {
            dropdown.style.display = 'none';
            return;
        }

        let html = '';
        locations.slice(0, 10).forEach((location, index) => {
            html += `
                <div class="dropdown-item" data-index="${index}" data-value="${location}">
                    <i class="fas fa-map-marker-alt me-2 text-muted"></i>
                    <span>${location}</span>
                </div>
            `;
        });

        dropdown.innerHTML = html;
        dropdown.style.display = 'block';

        // Add click handlers
        dropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                const value = item.getAttribute('data-value');
                input.value = value;
                this.hideLocationDropdown();
            });
        });
    }

    showSpecialtyDropdown(filteredSpecialties = null) {
        const dropdown = document.getElementById('clinicSpecialtyDropdown');
        const input = document.getElementById('clinicSpecialtyInput');
        
        if (!dropdown) return;

        const specialties = filteredSpecialties || this.currentSpecialties;
        
        if (!specialties.length) {
            dropdown.style.display = 'none';
            return;
        }

        let html = '';
        specialties.slice(0, 10).forEach((specialty, index) => {
            html += `
                <div class="dropdown-item" data-index="${index}" data-value="${specialty}">
                    <i class="fas fa-medical-kit me-2 text-muted"></i>
                    <span>${specialty}</span>
                </div>
            `;
        });

        dropdown.innerHTML = html;
        dropdown.style.display = 'block';

        // Add click handlers
        dropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                const value = item.getAttribute('data-value');
                input.value = value;
                this.hideSpecialtyDropdown();
            });
        });
    }

    hideSearchSuggestions() {
        const dropdown = document.getElementById('clinicSearchSuggestions');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    }

    hideLocationDropdown() {
        const dropdown = document.getElementById('clinicLocationDropdown');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    }

    hideSpecialtyDropdown() {
        const dropdown = document.getElementById('clinicSpecialtyDropdown');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    }

    handleSearchKeyNavigation(e) {
        const dropdown = document.getElementById('clinicSearchSuggestions');
        if (!dropdown || dropdown.style.display === 'none') return;

        const items = dropdown.querySelectorAll('.dropdown-item');
        let currentActive = dropdown.querySelector('.dropdown-item.active');
        let currentIndex = currentActive ? Array.from(items).indexOf(currentActive) : -1;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            currentIndex = Math.min(currentIndex + 1, items.length - 1);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            currentIndex = Math.max(currentIndex - 1, 0);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (currentActive) {
                currentActive.click();
            }
            return;
        } else if (e.key === 'Escape') {
            this.hideSearchSuggestions();
            return;
        }

        // Update active item
        items.forEach(item => item.classList.remove('active'));
        if (items[currentIndex]) {
            items[currentIndex].classList.add('active');
        }
    }

    useCurrentLocation() {
        const locationInput = document.getElementById('clinicLocationInput');
        
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by this browser.');
            return;
        }

        // Show loading state
        locationInput.value = 'Getting your location...';
        locationInput.disabled = true;

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                try {
                    const { latitude, longitude } = position.coords;
                    
                    // Use a reverse geocoding service to get city name
                    // For now, we'll use a simple approach
                    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`);
                    const data = await response.json();
                    
                    let cityName = '';
                    if (data.address) {
                        cityName = data.address.city || data.address.town || data.address.village || data.address.state_district || '';
                        if (cityName && data.address.state) {
                            cityName = `${cityName}, ${data.address.state}`;
                        }
                    }
                    
                    locationInput.value = cityName || 'Location detected';
                    locationInput.disabled = false;
                    
                } catch (error) {
                    console.error('Error getting location name:', error);
                    locationInput.value = 'Unable to get location name';
                    locationInput.disabled = false;
                }
            },
            (error) => {
                console.error('Error getting location:', error);
                locationInput.value = '';
                locationInput.disabled = false;
                alert('Unable to get your location. Please enter manually.');
            }
        );
    }
}

// Initialize the filter system when DOM is loaded (prevent duplicate initialization)
document.addEventListener('DOMContentLoaded', () => {
    // Check if already initialized to prevent duplicates
    if (!window.clinicDirectoryFiltersInitialized && document.getElementById('clinicFilterForm')) {
        window.clinicDirectoryFiltersInitialized = true;
        new ClinicDirectoryFilters();
        console.log('Clinic directory filters initialized successfully');
    }
});

// Export for potential external use
window.ClinicDirectoryFilters = ClinicDirectoryFilters;

} // End of class declaration check