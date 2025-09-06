// Procedure Filters JavaScript
class ProcedureFilters {
    constructor() {
        this.searchInput = document.getElementById('procedureSearchInput');
        this.bodyPartInput = document.getElementById('procedureBodyPartInput');
        this.categoryInput = document.getElementById('procedureCategoryInput');
        this.searchSuggestions = document.getElementById('procedureSearchSuggestions');
        this.bodyPartDropdown = document.getElementById('procedureBodyPartDropdown');
        this.categoryDropdown = document.getElementById('procedureCategoryDropdown');
        this.advancedFiltersToggle = document.getElementById('procedureAdvancedFiltersToggle');
        this.advancedFiltersSection = document.getElementById('procedureAdvancedFiltersSection');
        
        this.currentSearchSuggestions = [];
        this.currentBodyPartSuggestions = [];
        this.currentCategorySuggestions = [];
        
        this.init();
    }

    init() {
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.searchProcedures(e.target.value);
            });
        }

        if (this.bodyPartInput) {
            this.bodyPartInput.addEventListener('input', (e) => {
                this.searchBodyParts(e.target.value);
            });
        }

        if (this.categoryInput) {
            this.categoryInput.addEventListener('input', (e) => {
                this.searchCategories(e.target.value);
            });
        }

        if (this.advancedFiltersToggle) {
            this.advancedFiltersToggle.addEventListener('click', () => {
                this.toggleAdvancedFilters();
            });
        }

        // Hide dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.position-relative')) {
                this.hideAllDropdowns();
            }
        });
    }

    async searchProcedures(query) {
        if (query.length < 2) {
            this.hideSearchSuggestions();
            return;
        }

        try {
            console.log('Searching procedures for:', query);
            const response = await fetch(`/api/search/procedures?q=${encodeURIComponent(query)}`);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Procedure search response:', data);
                
                if (data.success && data.suggestions && data.suggestions.length > 0) {
                    this.currentSearchSuggestions = data.suggestions;
                    this.showSearchSuggestions();
                } else {
                    this.hideSearchSuggestions();
                }
            }
        } catch (error) {
            console.error('Error searching procedures:', error);
        }
    }

    async searchBodyParts(query) {
        if (query.length < 1) {
            this.hideBodyPartDropdown();
            return;
        }

        try {
            const response = await fetch(`/api/search/body-parts?q=${encodeURIComponent(query)}`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.suggestions && data.suggestions.length > 0) {
                    this.currentBodyPartSuggestions = data.suggestions;
                    this.showBodyPartDropdown();
                } else {
                    this.hideBodyPartDropdown();
                }
            }
        } catch (error) {
            console.error('Error searching body parts:', error);
        }
    }

    async searchCategories(query) {
        if (query.length < 1) {
            this.hideCategoryDropdown();
            return;
        }

        try {
            const response = await fetch(`/api/search/categories?q=${encodeURIComponent(query)}`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.suggestions && data.suggestions.length > 0) {
                    this.currentCategorySuggestions = data.suggestions;
                    this.showCategoryDropdown();
                } else {
                    this.hideCategoryDropdown();
                }
            }
        } catch (error) {
            console.error('Error searching categories:', error);
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
                const form = document.getElementById('procedureFilterForm');
                if (form) form.submit();
            });
        });
    }

    showBodyPartDropdown() {
        if (!this.bodyPartDropdown || !this.currentBodyPartSuggestions.length) return;

        let html = '';
        this.currentBodyPartSuggestions.forEach((suggestion, index) => {
            html += `
                <div class="dropdown-item" data-index="${index}" data-value="${suggestion.text}">
                    <i class="fas fa-user me-2 text-muted"></i>
                    <span class="fw-medium">${suggestion.text}</span>
                </div>
            `;
        });

        this.bodyPartDropdown.innerHTML = html;
        this.bodyPartDropdown.style.display = 'block';

        // Add click handlers
        this.bodyPartDropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                const value = item.getAttribute('data-value');
                this.bodyPartInput.value = value;
                this.hideBodyPartDropdown();
            });
        });
    }

    showCategoryDropdown() {
        if (!this.categoryDropdown || !this.currentCategorySuggestions.length) return;

        let html = '';
        this.currentCategorySuggestions.forEach((suggestion, index) => {
            html += `
                <div class="dropdown-item" data-index="${index}" data-value="${suggestion.text}">
                    <i class="fas fa-tags me-2 text-muted"></i>
                    <span class="fw-medium">${suggestion.text}</span>
                </div>
            `;
        });

        this.categoryDropdown.innerHTML = html;
        this.categoryDropdown.style.display = 'block';

        // Add click handlers
        this.categoryDropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                const value = item.getAttribute('data-value');
                this.categoryInput.value = value;
                this.hideCategoryDropdown();
            });
        });
    }

    hideSearchSuggestions() {
        if (this.searchSuggestions) {
            this.searchSuggestions.style.display = 'none';
        }
    }

    hideBodyPartDropdown() {
        if (this.bodyPartDropdown) {
            this.bodyPartDropdown.style.display = 'none';
        }
    }

    hideCategoryDropdown() {
        if (this.categoryDropdown) {
            this.categoryDropdown.style.display = 'none';
        }
    }

    hideAllDropdowns() {
        this.hideSearchSuggestions();
        this.hideBodyPartDropdown();
        this.hideCategoryDropdown();
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('procedureFilterForm')) {
        new ProcedureFilters();
        console.log('Procedure filters initialized successfully');
    }
});