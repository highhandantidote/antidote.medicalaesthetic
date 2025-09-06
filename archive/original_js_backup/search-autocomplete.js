/**
 * Search autocomplete functionality for homepage hero search
 * Handles procedure suggestions and city autocomplete for all tabs:
 * - Doctor tab
 * - Procedures tab
 * - Discussions tab
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements for Doctor tab search functionality
    const doctorSearchInput = document.getElementById('doctorSearch');
    const doctorSuggestionsDropdown = document.getElementById('doctorSuggestions');
    const locationSearchInput = document.getElementById('locationSearch');
    const locationSuggestionsDropdown = document.getElementById('locationSuggestions');
    
    // Elements for Procedures tab search functionality
    const procedureSearchInput = document.getElementById('procedureSearch');
    const procedureSuggestionsDropdown = document.getElementById('procedureSuggestions');
    
    // Elements for Discussions tab search functionality
    const discussionSearchInput = document.getElementById('discussionSearch');
    const discussionSuggestionsDropdown = document.getElementById('discussionSuggestions');
    
    // Common Indian cities for location autocomplete
    const indianCities = [
        'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 
        'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Surat', 
        'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane', 
        'Bhopal', 'Visakhapatnam', 'Patna', 'Vadodara', 'Ghaziabad', 
        'Ludhiana', 'Agra', 'Nashik', 'Faridabad', 'Meerut', 
        'Rajkot', 'Varanasi', 'Srinagar', 'Aurangabad', 'Dhanbad', 
        'Amritsar', 'Allahabad', 'Ranchi', 'Coimbatore', 'Jabalpur'
    ];
    
    // Popular cosmetic procedures for suggestions and related terms
    const popularProcedures = [
        'Rhinoplasty', 'Liposuction', 'Breast Augmentation', 'Botox', 
        'Face Lift', 'Tummy Tuck', 'Lip Fillers', 'Dermal Fillers',
        'Blepharoplasty', 'Hair Transplant', 'Chin Augmentation',
        'Chemical Peel', 'Laser Hair Removal', 'Eyebrow Lift', 'Gynecomastia'
    ];
    
    // Medical terminology dictionary for related terms matching
    const medicalTermsDictionary = {
        // Procedure name mappings (common terms to medical terms)
        "nose job": ["rhinoplasty", "septoplasty", "septorhinoplasty", "nose enhancement", "nasal surgery"],
        "nose surgery": ["rhinoplasty", "septoplasty", "septorhinoplasty"],
        "rhinoplasty": ["nose job", "nose surgery", "septoplasty", "nose reshaping"],
        "tummy tuck": ["abdominoplasty", "stomach reduction", "abdominal surgery"],
        "abdominoplasty": ["tummy tuck", "stomach reduction", "abdominal surgery"],
        "lip job": ["lip augmentation", "lip fillers", "lip enhancement"],
        "boob job": ["breast augmentation", "breast implants", "breast enhancement", "breast surgery"],
        "breast augmentation": ["breast implants", "boob job", "breast enhancement"],
        "face lift": ["rhytidectomy", "facial rejuvenation", "face surgery"],
        "rhytidectomy": ["face lift", "facial rejuvenation"],
        "brow lift": ["forehead lift", "browplasty", "eyebrow lift"],
        "eyelid surgery": ["blepharoplasty", "eye lift", "eyelid lift"],
        "butt lift": ["brazilian butt lift", "bbl", "gluteoplasty", "buttock augmentation"],
        "brazilian butt lift": ["bbl", "butt lift", "gluteoplasty"],
        "hair restoration": ["hair transplant", "hair implants", "fue", "follicular unit extraction"],
        "liposuction": ["lipo", "fat removal", "body contouring", "liposculpture"],
        
        // Recovery related terms
        "recovery": ["post-surgery", "healing", "recuperation", "aftercare", "post-op"],
        "post-op": ["recovery", "healing", "after surgery", "post-surgical"],
        "healing": ["recovery", "post-op", "recuperation"],
        "pain": ["discomfort", "soreness", "aching", "pain management", "pain relief"],
        "swelling": ["edema", "inflammation", "puffiness", "bloating"],
        "scarring": ["scars", "scar management", "scar treatment", "scar healing"],
        "bruising": ["ecchymosis", "discoloration", "black and blue"],
        
        // Complication related terms
        "complications": ["side effects", "risks", "adverse effects", "problems"],
        "infection": ["bacterial infection", "wound infection", "post-surgical infection"],
        "revision": ["corrective surgery", "secondary surgery", "touch-up"],
        
        // Cost related terms
        "cost": ["price", "fees", "expenses", "financing", "payment"],
        "financing": ["payment plans", "emi", "loans", "cost", "payment options"],
        
        // Results related terms
        "results": ["outcome", "after photos", "before and after", "transformation"],
        "before and after": ["results", "outcome", "transformation", "photos"],
        
        // Procedure related general terms
        "non-surgical": ["non-invasive", "minimally invasive", "no surgery"],
        "surgical": ["invasive", "operation", "surgery"],
        "downtime": ["recovery time", "time off", "healing period"]
    };
    
    // Procedure categories for context filtering
    const procedureCategories = [
        'Face', 'Body', 'Breast', 'Hair', 'Skin', 'Non-surgical'
    ];
    
    // For procedure search in Doctor tab - this will show procedure suggestions (not doctors)
    if (doctorSearchInput && doctorSuggestionsDropdown) {
        doctorSearchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            if (query.length >= 2) {
                // Try to make API call to get procedure suggestions
                fetch(`/api/autocomplete?q=${encodeURIComponent(query)}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Clear previous suggestions
                        doctorSuggestionsDropdown.innerHTML = '';
                        
                        // Filter to only show procedures (not doctors)
                        const procedureSuggestions = data.filter(item => item.category === 'Procedure');
                        
                        if (procedureSuggestions.length > 0) {
                            // Add procedure suggestions to dropdown
                            procedureSuggestions.forEach(suggestion => {
                                addProcedureSuggestion(suggestion.text, doctorSuggestionsDropdown, doctorSearchInput);
                            });
                            
                            // Show dropdown
                            doctorSuggestionsDropdown.style.display = 'block';
                        } else {
                            // If no procedures from API, filter from popular list
                            const matchingProcedures = popularProcedures.filter(proc => 
                                proc.toLowerCase().includes(query.toLowerCase())
                            );
                            
                            if (matchingProcedures.length > 0) {
                                matchingProcedures.forEach(proc => {
                                    addProcedureSuggestion(proc, doctorSuggestionsDropdown, doctorSearchInput);
                                });
                                doctorSuggestionsDropdown.style.display = 'block';
                            } else {
                                doctorSuggestionsDropdown.style.display = 'none';
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching procedure suggestions:', error);
                        
                        // Fallback to static list on API error
                        doctorSuggestionsDropdown.innerHTML = '';
                        const matchingProcedures = popularProcedures.filter(proc => 
                            proc.toLowerCase().includes(query.toLowerCase())
                        );
                        
                        if (matchingProcedures.length > 0) {
                            matchingProcedures.forEach(proc => {
                                addProcedureSuggestion(proc, doctorSuggestionsDropdown, doctorSearchInput);
                            });
                            doctorSuggestionsDropdown.style.display = 'block';
                        } else {
                            doctorSuggestionsDropdown.style.display = 'none';
                        }
                    });
            } else {
                doctorSuggestionsDropdown.style.display = 'none';
            }
        });
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!doctorSearchInput.contains(e.target) && !doctorSuggestionsDropdown.contains(e.target)) {
                doctorSuggestionsDropdown.style.display = 'none';
            }
        });
    }
    
    // For city autocomplete
    if (locationSearchInput && locationSuggestionsDropdown) {
        locationSearchInput.addEventListener('input', function() {
            const query = this.value.trim().toLowerCase();
            
            if (query.length >= 1) {
                // Clear previous suggestions
                locationSuggestionsDropdown.innerHTML = '';
                
                // Filter cities based on input
                const matchingCities = indianCities.filter(city => 
                    city.toLowerCase().includes(query)
                );
                
                if (matchingCities.length > 0) {
                    // Add city suggestions to dropdown
                    matchingCities.forEach(city => {
                        const suggestionItem = document.createElement('a');
                        suggestionItem.classList.add('dropdown-item');
                        suggestionItem.href = '#';
                        suggestionItem.innerHTML = highlightMatchText(city, query);
                        
                        suggestionItem.addEventListener('click', function(e) {
                            e.preventDefault();
                            locationSearchInput.value = city;
                            locationSuggestionsDropdown.style.display = 'none';
                        });
                        
                        locationSuggestionsDropdown.appendChild(suggestionItem);
                    });
                    
                    // Show dropdown
                    locationSuggestionsDropdown.style.display = 'block';
                } else {
                    locationSuggestionsDropdown.style.display = 'none';
                }
            } else {
                locationSuggestionsDropdown.style.display = 'none';
            }
        });
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!locationSearchInput.contains(e.target) && !locationSuggestionsDropdown.contains(e.target)) {
                locationSuggestionsDropdown.style.display = 'none';
            }
        });
        
        // Handle keyboard navigation
        locationSearchInput.addEventListener('keydown', function(e) {
            if (locationSuggestionsDropdown.style.display === 'block') {
                const items = locationSuggestionsDropdown.querySelectorAll('.dropdown-item');
                let activeItem = locationSuggestionsDropdown.querySelector('.dropdown-item.active');
                
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    if (!activeItem) {
                        items[0].classList.add('active');
                    } else {
                        activeItem.classList.remove('active');
                        const nextItem = activeItem.nextElementSibling;
                        if (nextItem) {
                            nextItem.classList.add('active');
                        } else {
                            items[0].classList.add('active');
                        }
                    }
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    if (!activeItem) {
                        items[items.length - 1].classList.add('active');
                    } else {
                        activeItem.classList.remove('active');
                        const prevItem = activeItem.previousElementSibling;
                        if (prevItem) {
                            prevItem.classList.add('active');
                        } else {
                            items[items.length - 1].classList.add('active');
                        }
                    }
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (activeItem) {
                        activeItem.click();
                    }
                } else if (e.key === 'Escape') {
                    locationSuggestionsDropdown.style.display = 'none';
                }
            }
        });
    }
    
    // Handle the Procedures tab autocomplete
    if (procedureSearchInput && procedureSuggestionsDropdown) {
        procedureSearchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            if (query.length >= 2) {
                // Try to make API call to get procedure suggestions
                fetch(`/api/autocomplete?q=${encodeURIComponent(query)}&type=procedures`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Clear previous suggestions
                        procedureSuggestionsDropdown.innerHTML = '';
                        
                        // Filter to only show procedures
                        const procedureSuggestions = data.filter(item => item.category === 'Procedure');
                        
                        if (procedureSuggestions.length > 0) {
                            // Add procedure suggestions to dropdown
                            procedureSuggestions.forEach(suggestion => {
                                addProcedureSuggestion(suggestion.text, procedureSuggestionsDropdown, procedureSearchInput);
                            });
                            
                            // Show dropdown
                            procedureSuggestionsDropdown.style.display = 'block';
                        } else {
                            // If no procedures from API, filter from popular list
                            const matchingProcedures = popularProcedures.filter(proc => 
                                proc.toLowerCase().includes(query.toLowerCase())
                            );
                            
                            if (matchingProcedures.length > 0) {
                                matchingProcedures.forEach(proc => {
                                    addProcedureSuggestion(proc, procedureSuggestionsDropdown, procedureSearchInput);
                                });
                                procedureSuggestionsDropdown.style.display = 'block';
                            } else {
                                procedureSuggestionsDropdown.style.display = 'none';
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching procedure suggestions:', error);
                        
                        // Fallback to static list on API error
                        procedureSuggestionsDropdown.innerHTML = '';
                        const matchingProcedures = popularProcedures.filter(proc => 
                            proc.toLowerCase().includes(query.toLowerCase())
                        );
                        
                        if (matchingProcedures.length > 0) {
                            matchingProcedures.forEach(proc => {
                                addProcedureSuggestion(proc, procedureSuggestionsDropdown, procedureSearchInput);
                            });
                            procedureSuggestionsDropdown.style.display = 'block';
                        } else {
                            procedureSuggestionsDropdown.style.display = 'none';
                        }
                    });
            } else {
                procedureSuggestionsDropdown.style.display = 'none';
            }
        });
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!procedureSearchInput.contains(e.target) && !procedureSuggestionsDropdown.contains(e.target)) {
                procedureSuggestionsDropdown.style.display = 'none';
            }
        });
        
        // Key navigation for procedure suggestions
        procedureSearchInput.addEventListener('keydown', function(e) {
            if (procedureSuggestionsDropdown.style.display === 'block') {
                const items = procedureSuggestionsDropdown.querySelectorAll('.dropdown-item');
                let activeItem = procedureSuggestionsDropdown.querySelector('.dropdown-item.active');
                
                if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === 'Escape') {
                    e.preventDefault();
                    handleKeyNavigation(e.key, items, activeItem, procedureSuggestionsDropdown);
                }
            }
        });
    }
    
    // Handle the Discussions tab autocomplete
    if (discussionSearchInput && discussionSuggestionsDropdown) {
        discussionSearchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            if (query.length >= 2) {
                // Try to make API call to get discussion suggestions
                fetch(`/api/autocomplete?q=${encodeURIComponent(query)}&type=threads`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Clear previous suggestions
                        discussionSuggestionsDropdown.innerHTML = '';
                        
                        // Add scroller container for better UX with many suggestions
                        const scrollContainer = document.createElement('div');
                        scrollContainer.className = 'suggestions-scrollable';
                        discussionSuggestionsDropdown.appendChild(scrollContainer);
                        
                        // Check for related terms in the medical dictionary
                        const relatedTerms = findRelatedTerms(query, medicalTermsDictionary);
                        
                        // Add related terms section if any found
                        if (relatedTerms.length > 0) {
                            const relatedTermsSection = document.createElement('div');
                            relatedTermsSection.className = 'related-search-terms';
                            relatedTermsSection.innerHTML = '<strong>Related searches:</strong> ';
                            
                            relatedTerms.forEach(term => {
                                const termSpan = document.createElement('span');
                                termSpan.textContent = term;
                                termSpan.addEventListener('click', function() {
                                    discussionSearchInput.value = term;
                                    discussionSearchInput.dispatchEvent(new Event('input'));
                                });
                                relatedTermsSection.appendChild(termSpan);
                            });
                            
                            scrollContainer.appendChild(relatedTermsSection);
                        }
                        
                        // Add context filter section for procedure-specific filtering
                        const contextSection = document.createElement('div');
                        contextSection.className = 'context-filter-section';
                        
                        const contextLabel = document.createElement('div');
                        contextLabel.className = 'context-filter-label';
                        contextLabel.textContent = 'Filter by:';
                        contextSection.appendChild(contextLabel);
                        
                        const contextTags = document.createElement('div');
                        contextTags.className = 'context-filter-tags';
                        
                        // Add "All" option first
                        const allTag = document.createElement('div');
                        allTag.className = 'context-filter-tag active';
                        allTag.textContent = 'All';
                        allTag.dataset.filter = 'all';
                        contextTags.appendChild(allTag);
                        
                        // Add procedure categories as filters
                        procedureCategories.forEach(category => {
                            const categoryTag = document.createElement('div');
                            categoryTag.className = 'context-filter-tag';
                            categoryTag.textContent = category;
                            categoryTag.dataset.filter = category.toLowerCase();
                            contextTags.appendChild(categoryTag);
                        });
                        
                        // Add special filters for common search types
                        ['Recovery', 'Cost', 'Results', 'Complications'].forEach(searchType => {
                            const typeTag = document.createElement('div');
                            typeTag.className = 'context-filter-tag';
                            typeTag.textContent = searchType;
                            typeTag.dataset.filter = searchType.toLowerCase();
                            contextTags.appendChild(typeTag);
                        });
                        
                        // Setup click handlers for context filters
                        contextTags.querySelectorAll('.context-filter-tag').forEach(tag => {
                            tag.addEventListener('click', function() {
                                // Remove active class from all tags
                                contextTags.querySelectorAll('.context-filter-tag').forEach(t => {
                                    t.classList.remove('active');
                                });
                                
                                // Add active class to clicked tag
                                tag.classList.add('active');
                                
                                // Update the search input with context if not "All"
                                if (tag.dataset.filter !== 'all') {
                                    // If the query already contains the selected filter, don't modify
                                    if (!query.toLowerCase().includes(tag.textContent.toLowerCase())) {
                                        // Check if query is a general term like "recovery"
                                        if (isGeneralTerm(query) && tag.dataset.filter !== query.toLowerCase()) {
                                            discussionSearchInput.value = `${query} for ${tag.textContent}`;
                                            // Trigger a new search with the updated query
                                            discussionSearchInput.dispatchEvent(new Event('input'));
                                            return;
                                        }
                                    }
                                }
                                
                                // Filter visible suggestions based on selected context
                                const suggestions = scrollContainer.querySelectorAll('.thread-suggestion');
                                suggestions.forEach(suggestion => {
                                    if (tag.dataset.filter === 'all') {
                                        suggestion.style.display = 'block';
                                    } else {
                                        // Show only suggestions that match the selected filter
                                        const suggestionText = suggestion.textContent.toLowerCase();
                                        if (suggestionText.includes(tag.dataset.filter)) {
                                            suggestion.style.display = 'block';
                                        } else {
                                            suggestion.style.display = 'none';
                                        }
                                    }
                                });
                            });
                        });
                        
                        contextSection.appendChild(contextTags);
                        scrollContainer.appendChild(contextSection);
                        
                        // Filter to only show discussions/threads
                        const discussionSuggestions = data.filter(item => item.category === 'Thread');
                        
                        if (discussionSuggestions.length > 0) {
                            // Add discussion suggestions to dropdown with enhanced display
                            discussionSuggestions.forEach(suggestion => {
                                addThreadSuggestion(suggestion, scrollContainer, discussionSearchInput);
                            });
                            
                            // Show dropdown
                            discussionSuggestionsDropdown.style.display = 'block';
                        } else {
                            // If no discussions, show popular procedure keywords as discussion topics
                            const matchingProcedures = popularProcedures.filter(proc => 
                                proc.toLowerCase().includes(query.toLowerCase())
                            );
                            
                            if (matchingProcedures.length > 0) {
                                // Add a header for suggested topics
                                const suggestedHeader = document.createElement('div');
                                suggestedHeader.className = 'thread-group-heading';
                                suggestedHeader.textContent = 'Suggested topics:';
                                scrollContainer.appendChild(suggestedHeader);
                                
                                matchingProcedures.forEach(proc => {
                                    const mockSuggestion = {
                                        text: proc + " Discussion",
                                        display: proc + " Discussion",
                                        date: "Recent discussions", 
                                        // Use default values for mock suggestions
                                        id: 0,
                                        url: null, // Will use form submission instead
                                        category: 'Thread',
                                        reply_count: Math.floor(Math.random() * 5 + 1)
                                    };
                                    addThreadSuggestion(mockSuggestion, scrollContainer, discussionSearchInput);
                                });
                                discussionSuggestionsDropdown.style.display = 'block';
                            } else {
                                discussionSuggestionsDropdown.style.display = 'none';
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching discussion suggestions:', error);
                        
                        // Fallback to static list on API error
                        discussionSuggestionsDropdown.innerHTML = '';
                        
                        // Add scrollable container
                        const scrollContainer = document.createElement('div');
                        scrollContainer.className = 'suggestions-scrollable';
                        discussionSuggestionsDropdown.appendChild(scrollContainer);
                        
                        // Check for related terms in the medical dictionary
                        const relatedTerms = findRelatedTerms(query, medicalTermsDictionary);
                        
                        // Add related terms section if any found
                        if (relatedTerms.length > 0) {
                            const relatedTermsSection = document.createElement('div');
                            relatedTermsSection.className = 'related-search-terms';
                            relatedTermsSection.innerHTML = '<strong>Related searches:</strong> ';
                            
                            relatedTerms.forEach(term => {
                                const termSpan = document.createElement('span');
                                termSpan.textContent = term;
                                termSpan.addEventListener('click', function() {
                                    discussionSearchInput.value = term;
                                    discussionSearchInput.dispatchEvent(new Event('input'));
                                });
                                relatedTermsSection.appendChild(termSpan);
                            });
                            
                            scrollContainer.appendChild(relatedTermsSection);
                        }
                        
                        // Add procedure-specific context suggestions based on query
                        if (isGeneralTerm(query)) {
                            // For general terms like "recovery", suggest procedure-specific options
                            const heading = document.createElement('div');
                            heading.className = 'thread-group-heading';
                            heading.textContent = `${capitalizeFirstLetter(query)} for specific procedures:`;
                            scrollContainer.appendChild(heading);
                            
                            // Suggest popular procedures with this term
                            popularProcedures.slice(0, 5).forEach(procedure => {
                                const mockSuggestion = {
                                    text: `${query} for ${procedure}`,
                                    display: `${query} for ${procedure}`,
                                    date: "Popular search", 
                                    reply_count: Math.floor(Math.random() * 5 + 1),
                                    id: 0,
                                    url: null,
                                    category: 'Thread',
                                    // Add metadata for improved display
                                    procedureType: procedure
                                };
                                addThreadSuggestion(mockSuggestion, scrollContainer, discussionSearchInput);
                            });
                        } else {
                            // Fallback to topic suggestions on API error
                            // Suggested discussion topics for general search queries
                            const discussionTopics = [
                                'Recovery Time', 'Post-surgery Experience', 'Cost Considerations', 
                                'Pain Management', 'Before and After', 'Surgeon Recommendations',
                                'Complications', 'Procedure Duration'
                            ];
                            
                            const matchingTopics = discussionTopics.filter(topic => 
                                topic.toLowerCase().includes(query.toLowerCase())
                            );
                            
                            if (matchingTopics.length > 0) {
                                // Add a header for popular topics
                                const topicsHeader = document.createElement('div');
                                topicsHeader.className = 'thread-group-heading';
                                topicsHeader.textContent = 'Popular topics:';
                                scrollContainer.appendChild(topicsHeader);
                                
                                matchingTopics.forEach(topic => {
                                    const mockSuggestion = {
                                        text: topic,
                                        display: topic,
                                        date: "Popular topic", 
                                        // Add metadata for improved display
                                        reply_count: Math.floor(Math.random() * 8 + 2),
                                        id: 0,
                                        url: null,
                                        category: 'Thread'
                                    };
                                    addThreadSuggestion(mockSuggestion, scrollContainer, discussionSearchInput);
                                });
                            }
                        }
                        
                        discussionSuggestionsDropdown.style.display = 'block';
                    });
            } else {
                discussionSuggestionsDropdown.style.display = 'none';
            }
        });
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!discussionSearchInput.contains(e.target) && !discussionSuggestionsDropdown.contains(e.target)) {
                discussionSuggestionsDropdown.style.display = 'none';
            }
        });
        
        // Key navigation for discussion suggestions
        discussionSearchInput.addEventListener('keydown', function(e) {
            if (discussionSuggestionsDropdown.style.display === 'block') {
                const items = discussionSuggestionsDropdown.querySelectorAll('.dropdown-item');
                let activeItem = discussionSuggestionsDropdown.querySelector('.dropdown-item.active');
                
                if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === 'Escape') {
                    e.preventDefault();
                    handleKeyNavigation(e.key, items, activeItem, discussionSuggestionsDropdown);
                }
            }
        });
    }
    
    // Handle the doctor search in the Doctor tab
    if (doctorSearchInput) {
        // Key navigation for procedure suggestions
        doctorSearchInput.addEventListener('keydown', function(e) {
            if (doctorSuggestionsDropdown.style.display === 'block') {
                const items = doctorSuggestionsDropdown.querySelectorAll('.dropdown-item');
                let activeItem = doctorSuggestionsDropdown.querySelector('.dropdown-item.active');
                
                if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === 'Escape') {
                    e.preventDefault();
                    handleKeyNavigation(e.key, items, activeItem, doctorSuggestionsDropdown);
                }
            }
        });
    }
    
    // Helper function to add procedure suggestion to dropdown
    function addProcedureSuggestion(procedureName, dropdown, inputField) {
        const suggestionItem = document.createElement('a');
        suggestionItem.classList.add('dropdown-item');
        suggestionItem.href = '#';
        suggestionItem.innerHTML = highlightMatchText(procedureName, inputField.value.trim());
        
        suggestionItem.addEventListener('click', function(e) {
            e.preventDefault();
            inputField.value = procedureName;
            dropdown.style.display = 'none';
        });
        
        dropdown.appendChild(suggestionItem);
    }
    
    // Helper function to add thread suggestion with enhanced information
    function addThreadSuggestion(suggestion, dropdown, inputField) {
        const suggestionItem = document.createElement('a');
        suggestionItem.classList.add('dropdown-item', 'thread-suggestion');
        suggestionItem.href = suggestion.url || '#';
        
        // Generate enhanced display with title, content preview, and activity information
        let innerHtml = `
            <span class="thread-title">${highlightMatchText(suggestion.text, inputField.value.trim())}</span>
        `;
        
        // Add content preview if available
        if (suggestion.content_preview) {
            innerHtml += `
                <div class="thread-preview">${highlightMatchText(suggestion.content_preview, inputField.value.trim())}</div>
            `;
        }
        
        // Add activity information (replies count and date)
        innerHtml += `
            <div class="thread-activity">
                <div class="thread-replies">
                    <i class="fa fa-comments"></i>
                    ${suggestion.reply_count || 0} replies
                </div>
                <div class="thread-date">
                    <i class="fa fa-calendar"></i>
                    ${suggestion.date || 'Recent'}
                </div>
            </div>
        `;
        
        // Set the inner HTML of the suggestion item
        suggestionItem.innerHTML = innerHtml;
        
        // Handle click event
        suggestionItem.addEventListener('click', function(e) {
            e.preventDefault();
            inputField.value = suggestion.text;
            dropdown.style.display = 'none';
            
            // If URL is provided, navigate to the thread
            if (suggestion.url) {
                window.location.href = suggestion.url;
            } else {
                // Otherwise submit the form to search for this thread
                inputField.closest('form').submit();
            }
        });
        
        // Add the item to the dropdown
        dropdown.appendChild(suggestionItem);
    }
    
    // Helper function to highlight matching text
    function highlightMatchText(text, query) {
        if (!query) return text;
        
        const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
        return text.replace(regex, '<span class="search-highlight">$1</span>');
    }
    
    // Helper function to escape special characters in regex
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    // Helper function to handle keyboard navigation
    function handleKeyNavigation(key, items, activeItem, dropdown) {
        if (key === 'ArrowDown') {
            if (!activeItem) {
                items[0].classList.add('active');
            } else {
                activeItem.classList.remove('active');
                const nextItem = activeItem.nextElementSibling;
                if (nextItem) {
                    nextItem.classList.add('active');
                } else {
                    items[0].classList.add('active');
                }
            }
        } else if (key === 'ArrowUp') {
            if (!activeItem) {
                items[items.length - 1].classList.add('active');
            } else {
                activeItem.classList.remove('active');
                const prevItem = activeItem.previousElementSibling;
                if (prevItem) {
                    prevItem.classList.add('active');
                } else {
                    items[items.length - 1].classList.add('active');
                }
            }
        } else if (key === 'Enter') {
            if (activeItem) {
                activeItem.click();
            }
        } else if (key === 'Escape') {
            dropdown.style.display = 'none';
        }
    }
});