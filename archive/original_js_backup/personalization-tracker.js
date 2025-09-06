/**
 * Anonymous User Personalization Tracker
 * Tracks user behavior without requiring login for personalized recommendations
 */

class PersonalizationTracker {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.fingerprint = null;
        this.interactions = [];
        this.startTime = Date.now();
        this.lastActivity = Date.now();
        
        this.init();
    }
    
    init() {
        this.generateFingerprint();
        this.setupEventListeners();
        this.trackPageView();
        this.loadUserPreferences();
        
        // Send interactions every 30 seconds
        setInterval(() => this.sendInteractions(), 30000);
        
        // Track when user leaves page
        window.addEventListener('beforeunload', () => this.sendInteractions());
        
        // Track activity for time spent calculation
        this.setupActivityTracking();
    }
    
    generateSessionId() {
        return 'sess_' + Math.random().toString(36).substr(2, 16) + Date.now().toString(36);
    }
    
    generateFingerprint() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Browser fingerprint', 2, 2);
        
        const fingerprint = [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            new Date().getTimezoneOffset(),
            canvas.toDataURL(),
            navigator.platform,
            navigator.cookieEnabled
        ].join('|');
        
        this.fingerprint = this.hashCode(fingerprint);
        
        // Store in localStorage for consistency
        localStorage.setItem('antidote_fingerprint', this.fingerprint);
    }
    
    hashCode(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return hash.toString(36);
    }
    
    setupEventListeners() {
        // Track procedure clicks
        document.addEventListener('click', (e) => {
            const procedureLink = e.target.closest('[data-procedure-id]');
            if (procedureLink) {
                this.trackInteraction('click', 'procedure', {
                    procedure_id: procedureLink.dataset.procedureId,
                    procedure_name: procedureLink.dataset.procedureName || procedureLink.textContent,
                    category_id: procedureLink.dataset.categoryId
                });
            }
            
            // Track doctor clicks
            const doctorLink = e.target.closest('[data-doctor-id]');
            if (doctorLink) {
                this.trackInteraction('click', 'doctor', {
                    doctor_id: doctorLink.dataset.doctorId,
                    doctor_name: doctorLink.dataset.doctorName,
                    specialty: doctorLink.dataset.specialty
                });
            }
            
            // Track category clicks
            const categoryLink = e.target.closest('[data-category-id]');
            if (categoryLink) {
                this.trackInteraction('click', 'category', {
                    category_id: categoryLink.dataset.categoryId,
                    category_name: categoryLink.dataset.categoryName,
                    body_part: categoryLink.dataset.bodyPart
                });
            }
            
            // Track search submissions
            const searchBtn = e.target.closest('.hero-search-btn, .search-button');
            if (searchBtn) {
                const searchInput = document.querySelector('#procedureSearch, #doctorSearch, #discussionSearch, .search-input');
                if (searchInput && searchInput.value.trim()) {
                    this.trackSearch(searchInput.value.trim(), this.getSearchType());
                }
            }
        });
        
        // Track scrolling behavior
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            this.lastActivity = Date.now();
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.trackInteraction('scroll', 'page', {
                    scroll_depth: Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100)
                });
            }, 1000);
        });
        
        // Track time spent on page sections
        this.observePageSections();
    }
    
    trackInteraction(type, contentType, data = {}) {
        const interaction = {
            type: type,
            content_type: contentType,
            data: data,
            timestamp: Date.now(),
            page_url: window.location.pathname,
            referrer: document.referrer,
            session_id: this.sessionId
        };
        
        this.interactions.push(interaction);
        this.lastActivity = Date.now();
        
        // Update local preferences immediately for real-time personalization
        this.updateLocalPreferences(interaction);
    }
    
    trackSearch(query, searchType = 'procedures') {
        this.trackInteraction('search', searchType, {
            query: query,
            search_type: searchType
        });
        
        // Store search for local personalization
        const searches = JSON.parse(localStorage.getItem('antidote_searches') || '[]');
        searches.unshift({
            query: query,
            type: searchType,
            timestamp: Date.now()
        });
        // Keep only last 50 searches
        searches.splice(50);
        localStorage.setItem('antidote_searches', JSON.stringify(searches));
    }
    
    trackPageView() {
        this.trackInteraction('view', 'page', {
            page_type: this.getPageType(),
            entry_point: document.referrer ? 'referral' : 'direct'
        });
    }
    
    getPageType() {
        const path = window.location.pathname;
        if (path === '/' || path === '/index') return 'homepage';
        if (path.includes('/procedure/')) return 'procedure_detail';
        if (path.includes('/doctor/')) return 'doctor_detail';
        if (path.includes('/procedures')) return 'procedure_listing';
        if (path.includes('/doctors')) return 'doctor_listing';
        if (path.includes('/community')) return 'community';
        if (path.includes('/search')) return 'search_results';
        return 'other';
    }
    
    getSearchType() {
        const activeTab = document.querySelector('.nav-tabs .nav-link.active');
        if (activeTab) {
            const tabText = activeTab.textContent.toLowerCase();
            if (tabText.includes('doctor')) return 'doctors';
            if (tabText.includes('discussion')) return 'discussions';
        }
        return 'procedures';
    }
    
    updateLocalPreferences(interaction) {
        const preferences = JSON.parse(localStorage.getItem('antidote_preferences') || '{}');
        
        // Update category interests
        if (interaction.data.category_id) {
            const categoryId = interaction.data.category_id;
            preferences.categories = preferences.categories || {};
            preferences.categories[categoryId] = (preferences.categories[categoryId] || 0) + 1;
        }
        
        // Update keyword interests
        if (interaction.data.procedure_name) {
            const keywords = interaction.data.procedure_name.toLowerCase().split(' ');
            preferences.keywords = preferences.keywords || {};
            keywords.forEach(keyword => {
                if (keyword.length > 3) {
                    preferences.keywords[keyword] = (preferences.keywords[keyword] || 0) + 1;
                }
            });
        }
        
        // Update search interests
        if (interaction.type === 'search' && interaction.data.query) {
            const keywords = interaction.data.query.toLowerCase().split(' ');
            preferences.keywords = preferences.keywords || {};
            keywords.forEach(keyword => {
                if (keyword.length > 3) {
                    preferences.keywords[keyword] = (preferences.keywords[keyword] || 0) + 2; // Higher weight for searches
                }
            });
        }
        
        localStorage.setItem('antidote_preferences', JSON.stringify(preferences));
    }
    
    loadUserPreferences() {
        const preferences = JSON.parse(localStorage.getItem('antidote_preferences') || '{}');
        
        // Apply real-time personalization to current page
        if (Object.keys(preferences).length > 0) {
            this.applyPersonalization(preferences);
        }
    }
    
    applyPersonalization(preferences) {
        // Reorder procedure categories based on interests
        if (preferences.categories) {
            const categoryElements = document.querySelectorAll('[data-category-id]');
            const sortedCategories = Array.from(categoryElements).sort((a, b) => {
                const aScore = preferences.categories[a.dataset.categoryId] || 0;
                const bScore = preferences.categories[b.dataset.categoryId] || 0;
                return bScore - aScore;
            });
            
            // Reorder in DOM
            if (sortedCategories.length > 0 && sortedCategories[0].parentNode) {
                const container = sortedCategories[0].parentNode;
                sortedCategories.forEach(element => {
                    container.appendChild(element);
                });
            }
        }
        
        // Highlight relevant procedures in search suggestions
        if (preferences.keywords) {
            const topKeywords = Object.entries(preferences.keywords)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([keyword]) => keyword);
            
            // Add CSS class to highlight relevant content
            document.querySelectorAll('.procedure-link-wrap a').forEach(link => {
                const linkText = link.textContent.toLowerCase();
                if (topKeywords.some(keyword => linkText.includes(keyword))) {
                    link.classList.add('personalized-highlight');
                }
            });
        }
    }
    
    setupActivityTracking() {
        // Track mouse movement, clicks, and scrolls to determine active time
        let isActive = true;
        let inactiveTimeout;
        
        const resetInactiveTimer = () => {
            isActive = true;
            this.lastActivity = Date.now();
            clearTimeout(inactiveTimeout);
            inactiveTimeout = setTimeout(() => {
                isActive = false;
            }, 30000); // 30 seconds of inactivity
        };
        
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, resetInactiveTimer, true);
        });
        
        resetInactiveTimer();
    }
    
    observePageSections() {
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const sectionName = entry.target.dataset.section || entry.target.className;
                        this.trackInteraction('view', 'section', {
                            section: sectionName,
                            visibility_ratio: entry.intersectionRatio
                        });
                    }
                });
            }, {
                threshold: [0.5, 1.0]
            });
            
            // Observe main page sections
            document.querySelectorAll('section, .procedure-categories, .popular-procedures, .top-doctors').forEach(section => {
                observer.observe(section);
            });
        }
    }
    
    sendInteractions() {
        if (this.interactions.length === 0) return;
        
        const payload = {
            fingerprint: this.fingerprint,
            session_id: this.sessionId,
            interactions: this.interactions,
            time_spent: Math.round((this.lastActivity - this.startTime) / 1000),
            page_url: window.location.pathname
        };
        
        // Send each interaction individually to match our API endpoint
        this.interactions.forEach(interaction => {
            const singlePayload = {
                fingerprint: this.fingerprint,
                interaction_type: interaction.type,
                content_type: interaction.content_type,
                content_id: interaction.data.procedure_id || interaction.data.doctor_id || interaction.data.category_id || 0,
                content_name: interaction.data.procedure_name || interaction.data.doctor_name || interaction.data.category_name || interaction.data.query || '',
                page_url: interaction.page_url,
                session_id: this.sessionId
            };
            
            // Use fetch to send to our working endpoint
            fetch('/api/track-interaction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(singlePayload)
            }).catch(error => {
                console.warn('Failed to send interaction data:', error);
            });
        });
        
        // Clear sent interactions
        this.interactions = [];
    }
    
    // Public methods for manual tracking
    trackCustomEvent(eventType, data) {
        this.trackInteraction('custom', eventType, data);
    }
    
    getUserInsights() {
        const preferences = JSON.parse(localStorage.getItem('antidote_preferences') || '{}');
        const searches = JSON.parse(localStorage.getItem('antidote_searches') || '[]');
        
        return {
            fingerprint: this.fingerprint,
            preferences: preferences,
            recent_searches: searches.slice(0, 10),
            visit_frequency: this.getVisitFrequency(),
            interest_level: this.getInterestLevel()
        };
    }
    
    getVisitFrequency() {
        const visits = JSON.parse(localStorage.getItem('antidote_visits') || '[]');
        visits.push(Date.now());
        // Keep last 30 visits
        visits.splice(0, visits.length - 30);
        localStorage.setItem('antidote_visits', JSON.stringify(visits));
        
        return visits.length;
    }
    
    getInterestLevel() {
        const preferences = JSON.parse(localStorage.getItem('antidote_preferences') || '{}');
        const totalInteractions = Object.values(preferences.categories || {}).reduce((a, b) => a + b, 0) +
                                 Object.values(preferences.keywords || {}).reduce((a, b) => a + b, 0);
        
        if (totalInteractions < 5) return 'browsing';
        if (totalInteractions < 20) return 'interested';
        if (totalInteractions < 50) return 'engaged';
        return 'highly_engaged';
    }
}

// Initialize tracker when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.antidoteTracker = new PersonalizationTracker();
});

// Add CSS for personalized highlights
const style = document.createElement('style');
style.textContent = `
    .personalized-highlight {
        background: linear-gradient(135deg, rgba(0, 160, 176, 0.1), rgba(0, 160, 176, 0.2));
        border-radius: 4px;
        padding: 2px 4px;
        font-weight: 500;
    }
    
    .personalized-content {
        border-left: 3px solid #00a0b0;
        padding-left: 12px;
        background: rgba(0, 160, 176, 0.05);
    }
`;
document.head.appendChild(style);