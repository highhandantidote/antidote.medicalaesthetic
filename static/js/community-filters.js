// Community Filters JavaScript
class CommunityFilters {
    constructor() {
        this.searchInput = document.getElementById('communitySearchInput');
        this.categoryInput = document.getElementById('communityCategoryInput');
        this.usernameInput = document.getElementById('communityUsernameInput');
        this.searchSuggestions = document.getElementById('communitySearchSuggestions');
        this.advancedFiltersToggle = document.getElementById('communityAdvancedFiltersToggle');
        this.advancedFiltersSection = document.getElementById('communityAdvancedFiltersSection');
        
        this.currentSearchSuggestions = [];
        
        this.init();
    }

    init() {
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.searchDiscussions(e.target.value);
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

    async searchDiscussions(query) {
        if (query.length < 2) {
            this.hideSearchSuggestions();
            return;
        }

        try {
            console.log('Searching discussions for:', query);
            const response = await fetch(`/api/search/community?q=${encodeURIComponent(query)}`);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Discussion search response:', data);
                
                if (data.success && data.suggestions && data.suggestions.length > 0) {
                    this.currentSearchSuggestions = data.suggestions;
                    this.showSearchSuggestions();
                } else {
                    this.hideSearchSuggestions();
                }
            }
        } catch (error) {
            console.error('Error searching discussions:', error);
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
                const form = document.getElementById('communityFilterForm');
                if (form) form.submit();
            });
        });
    }

    hideSearchSuggestions() {
        if (this.searchSuggestions) {
            this.searchSuggestions.style.display = 'none';
        }
    }

    hideAllDropdowns() {
        this.hideSearchSuggestions();
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
    if (document.getElementById('communityFilterForm')) {
        new CommunityFilters();
        console.log('Community filters initialized successfully');
    }
});