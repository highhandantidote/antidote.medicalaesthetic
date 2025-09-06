// Prevent class redeclaration
if (typeof ClinicDirectoryFilters === 'undefined') {
class ClinicDirectoryFilters {
    constructor() {
        this.currentLocations = [];
        this.currentSpecialties = [];
        this.currentSearchSuggestions = [];
        this.debounceTimer = null;
        this.locationDebounceTimer = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Search input with auto-suggestions
        const searchInput = document.getElementById('clinicSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });
            
            searchInput.addEventListener('focus', () => {
                this.showSearchSuggestions();
            });
        }

        // Location input with dropdown
        const locationInput = document.getElementById('clinicLocationInput');
        if (locationInput) {
            locationInput.addEventListener('input', (e) => {
                clearTimeout(this.locationDebounceTimer);
                this.locationDebounceTimer = setTimeout(() => {
                    this.handleLocationInput(e.target.value);
                }, 150);
            });
            
            locationInput.addEventListener('focus', () => {
                this.showLocationDropdown();
            });
            
            locationInput.addEventListener('click', () => {
                this.showLocationDropdown();
            });
        }

        // Specialty input with dropdown
        const specialtyInput = document.getElementById('clinicSpecialtyInput');
        if (specialtyInput) {
            specialtyInput.addEventListener('input', (e) => {
                this.handleSpecialtyInput(e.target.value);
            });
            
            specialtyInput.addEventListener('focus', () => {
                this.showSpecialtyDropdown();
            });
        }

        // Clear filters button
        const clearFiltersBtn = document.getElementById('clinicClearFilters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }

        // Advanced filters toggle
        const advancedToggle = document.getElementById('clinicAdvancedFiltersToggle');
        if (advancedToggle) {
            advancedToggle.addEventListener('click', () => {
                this.toggleAdvancedFilters();
            });
        }

        // Use location button
        const useLocationBtn = document.getElementById('useLocationBtn');
        if (useLocationBtn) {
            useLocationBtn.addEventListener('click', () => {
                this.getUserLocation();
            });
        }

        // Close dropdowns on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.position-relative')) {
                this.hideAllDropdowns();
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
                    console.log('Loaded clinic locations:', this.currentLocations.length);
                }
            } else {
                console.error('Failed to load clinic locations:', locationsResponse.status);
            }

            // Load specialties
            const specialtiesResponse = await fetch('/api/clinic/specialties');
            if (specialtiesResponse.ok) {
                const specialtiesData = await specialtiesResponse.json();
                if (specialtiesData.success) {
                    this.currentSpecialties = specialtiesData.specialties;
                }
            }

            // Check if advanced filters should be shown
            this.checkAdvancedFiltersVisibility();
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    handleSearchInput(query) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.searchClinics(query);
        }, 300);
    }

    async searchClinics(query) {
        if (query.length < 2) {
            this.hideSearchSuggestions();
            return;
        }

        try {
            const response = await fetch(`/api/clinic/search?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.currentSearchSuggestions = data.suggestions;
                    this.showSearchSuggestions();
                }
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
        
        if (!dropdown || !this.currentSearchSuggestions.length) return;

        dropdown.innerHTML = this.currentSearchSuggestions.map(suggestion => `
            <div class="dropdown-item" data-value="${suggestion.text}">
                <div class="d-flex align-items-center">
                    <i class="fas ${suggestion.icon || 'fa-search'} me-2 text-muted"></i>
                    <div>
                        <div class="fw-medium">${suggestion.text}</div>
                        ${suggestion.subtitle ? `<small class="text-muted">${suggestion.subtitle}</small>` : ''}
                    </div>
                </div>
            </div>
        `).join('');

        // Add click handlers
        dropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                input.value = item.dataset.value;
                this.hideSearchSuggestions();
                this.submitForm();
            });
        });

        dropdown.style.display = 'block';
    }

    showLocationDropdown(locations = this.currentLocations) {
        const dropdown = document.getElementById('clinicLocationDropdown');
        const input = document.getElementById('clinicLocationInput');
        
        console.log('Trying to show location dropdown:', {
            dropdown: !!dropdown,
            locationsCount: locations.length,
            locations: locations.slice(0, 3)
        });
        
        if (!dropdown) {
            console.error('Location dropdown element not found');
            return;
        }
        
        if (!locations.length) {
            console.log('No locations to display');
            dropdown.style.display = 'none';
            return;
        }

        dropdown.innerHTML = locations.map(location => `
            <div class="dropdown-item" data-value="${location}">
                <i class="fas fa-map-marker-alt me-2 text-muted"></i>
                ${location}
            </div>
        `).join('');

        // Add click handlers
        dropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                input.value = item.dataset.value;
                this.hideLocationDropdown();
            });
        });

        dropdown.style.display = 'block';
        console.log('Location dropdown displayed with', locations.length, 'items');
    }

    showSpecialtyDropdown(specialties = this.currentSpecialties) {
        const dropdown = document.getElementById('clinicSpecialtyDropdown');
        const input = document.getElementById('clinicSpecialtyInput');
        
        if (!dropdown || !specialties.length) return;

        dropdown.innerHTML = specialties.map(specialty => `
            <div class="dropdown-item" data-value="${specialty}">
                <i class="fas fa-stethoscope me-2 text-muted"></i>
                ${specialty}
            </div>
        `).join('');

        // Add click handlers
        dropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                input.value = item.dataset.value;
                this.hideSpecialtyDropdown();
            });
        });

        dropdown.style.display = 'block';
    }

    hideSearchSuggestions() {
        const dropdown = document.getElementById('clinicSearchSuggestions');
        if (dropdown) dropdown.style.display = 'none';
    }

    hideLocationDropdown() {
        const dropdown = document.getElementById('clinicLocationDropdown');
        if (dropdown) dropdown.style.display = 'none';
    }

    hideSpecialtyDropdown() {
        const dropdown = document.getElementById('clinicSpecialtyDropdown');
        if (dropdown) dropdown.style.display = 'none';
    }

    hideAllDropdowns() {
        this.hideSearchSuggestions();
        this.hideLocationDropdown();
        this.hideSpecialtyDropdown();
    }

    toggleAdvancedFilters() {
        const section = document.getElementById('clinicAdvancedFiltersSection');
        const toggle = document.getElementById('clinicAdvancedFiltersToggle');
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
        const specialty = document.getElementById('clinicSpecialtyInput').value;
        const rating = document.querySelector('select[name="rating"]').value;
        const verified = document.querySelector('select[name="verified"]').value;
        const sort = document.querySelector('select[name="sort"]').value;
        
        if (specialty || rating || verified || (sort && sort !== 'rating')) {
            this.toggleAdvancedFilters();
        }
    }

    clearAllFilters() {
        // Clear all form inputs
        document.getElementById('clinicSearchInput').value = '';
        document.getElementById('clinicLocationInput').value = '';
        document.getElementById('clinicSpecialtyInput').value = '';
        document.querySelector('select[name="rating"]').value = '';
        document.querySelector('select[name="verified"]').value = '';
        document.querySelector('select[name="sort"]').value = 'rating';
        
        // Submit form to refresh results
        this.submitForm();
    }

    async getUserLocation() {
        const locationInput = document.getElementById('clinicLocationInput');
        const useLocationBtn = document.getElementById('useLocationBtn');
        
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by this browser.');
            return;
        }

        // Show loading state
        useLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                try {
                    const response = await fetch(`/api/geocode/reverse?lat=${position.coords.latitude}&lng=${position.coords.longitude}`);
                    if (response.ok) {
                        const data = await response.json();
                        if (data.success && data.city) {
                            locationInput.value = data.city;
                        }
                    }
                } catch (error) {
                    console.error('Error getting location:', error);
                } finally {
                    useLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i>';
                }
            },
            (error) => {
                console.error('Error getting location:', error);
                useLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i>';
                alert('Unable to retrieve your location. Please enter manually.');
            }
        );
    }

    submitForm() {
        document.getElementById('clinicFilterForm').submit();
    }
}

} // End of class guard

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('clinicFilterForm') && !window.clinicDirectoryFiltersInitialized) {
        window.clinicDirectoryFiltersInitialized = true;
        new ClinicDirectoryFilters();
    }
});