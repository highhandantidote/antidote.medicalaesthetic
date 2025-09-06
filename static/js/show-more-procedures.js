// Show More Procedures Functionality - Standalone
console.log('Show More Procedures script loaded');

// Wait for DOM to be ready and other scripts to finish
document.addEventListener('DOMContentLoaded', function() {
    // Add a small delay to ensure other scripts have finished
    setTimeout(function() {
        console.log('Initializing Show More Procedures functionality');
        
        const showMoreBtn = document.getElementById('showMoreProcedures');
        const loadingDiv = document.getElementById('loadingMore');
        const proceduresList = document.getElementById('procedureList');
        
        console.log('Show More button element:', showMoreBtn);
        console.log('Loading div element:', loadingDiv);
        console.log('Procedures list element:', proceduresList);

        if (!showMoreBtn) {
            console.error('Show More button not found');
            return;
        }

        // Get initial offset - calculate from current procedures count
        let currentOffset = 0;
        if (proceduresList) {
            const currentProcedures = proceduresList.querySelectorAll('.procedure-card');
            currentOffset = currentProcedures.length;
        }
        
        // Fallback to showing count element if available
        const showingCountElement = document.getElementById('showingCount');
        if (showingCountElement && currentOffset === 0) {
            currentOffset = parseInt(showingCountElement.textContent) || 20;
        }
        
        // Default fallback
        if (currentOffset === 0) {
            currentOffset = 20;
        }
        
        console.log('Current offset:', currentOffset);
        console.log('Setting up click handler for Show More button');
        
        showMoreBtn.addEventListener('click', function(event) {
            event.preventDefault();
            console.log('Show More button clicked - starting request');
            
            // Hide button and show loading
            showMoreBtn.style.display = 'none';
            if (loadingDiv) {
                loadingDiv.style.display = 'block';
            }

            // Build request URL with current filters
            const params = new URLSearchParams();
            params.append('offset', currentOffset);
            params.append('limit', 20);
            
            // Add any URL parameters to preserve filters
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('search')) {
                params.append('search', urlParams.get('search'));
            }
            if (urlParams.get('body_part')) {
                params.append('body_part', urlParams.get('body_part'));
            }
            if (urlParams.get('category')) {
                params.append('category', urlParams.get('category'));
            }
            if (urlParams.get('category_id')) {
                params.append('category_id', urlParams.get('category_id'));
            }
            if (urlParams.get('sort')) {
                params.append('sort', urlParams.get('sort'));
            }
            if (urlParams.get('q')) {
                params.append('search', urlParams.get('q'));
            }

            const requestUrl = '/api/procedures/load-more?' + params.toString();
            console.log('Making request to:', requestUrl);

            // Make the request
            fetch(requestUrl, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            })
            .then(function(response) {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                console.log('Response data:', data);
                if (data.success && data.procedures) {
                    console.log('Adding', data.procedures.length, 'new procedures');
                    
                    // Add new procedures to the list
                    data.procedures.forEach(function(procedure) {
                        const procedureHTML = createProcedureCard(procedure);
                        console.log('Generated procedure HTML preview:', procedureHTML.substring(0, 200) + '...');
                        if (proceduresList) {
                            proceduresList.insertAdjacentHTML('beforeend', procedureHTML);
                        }
                    });

                    // Update counts
                    currentOffset += data.procedures.length;
                    const countElement = document.getElementById('showingCount');
                    if (countElement) {
                        countElement.textContent = currentOffset;
                    }

                    // Show or hide button
                    if (data.has_more) {
                        showMoreBtn.style.display = 'block';
                        const badge = showMoreBtn.querySelector('.badge');
                        if (badge) {
                            const remaining = data.total_count - currentOffset;
                            badge.textContent = remaining + ' more';
                        }
                    } else {
                        showMoreBtn.style.display = 'none';
                    }
                } else {
                    console.error('API returned error:', data.message || 'Unknown error');
                    showMoreBtn.style.display = 'block';
                }
            })
            .catch(function(error) {
                console.error('Request failed:', error);
                showMoreBtn.style.display = 'block';
                // Show user-friendly error message
                if (proceduresList) {
                    const errorHtml = `
                        <div class="col-12 mt-3">
                            <div class="alert alert-warning alert-dismissible fade show" role="alert">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                Unable to load more procedures. Please try again.
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                            </div>
                        </div>
                    `;
                    proceduresList.insertAdjacentHTML('beforeend', errorHtml);
                }
            })
            .finally(function() {
                if (loadingDiv) {
                    loadingDiv.style.display = 'none';
                }
            });
        });

        console.log('Show More Procedures functionality initialized successfully');
    }, 500); // 500ms delay to let other scripts finish
});

// Create procedure card function - matches the exact original template design
function createProcedureCard(procedure) {
    // Build the card exactly like the original template
    console.log('Creating card for procedure ID:', procedure.id);
    
    const cardHTML = `
        <div class="col-md-6 mb-4 procedure-card" 
            data-category="${procedure.category || ''}"
            data-body-part="${procedure.body_part || ''}"
            data-min-cost="${procedure.min_cost || 15000}"
            data-max-cost="${procedure.max_cost || 150000}"
            data-recovery="${procedure.recovery_time || '1-2 weeks'}"
            data-outpatient="true"
            data-insurance="false"
            data-minimally-invasive="false"
            data-pain-free="false">
            <div class="card h-100 shadow-sm border-0 hover-shadow">
                <div class="card-body">
                    <div class="mb-3">
                        <h4 class="card-title mb-0">${procedure.procedure_name}</h4>
                    </div>
                    <p class="card-text mb-3">${procedure.short_description || 'Professional medical procedure with experienced specialists.'}</p>
                    
                    <div class="mb-3">
                        <!-- Cost Range Row -->
                        <div class="d-flex align-items-center mb-2">
                            <i class="fas fa-rupee-sign text-success me-2"></i>
                            <strong class="me-2">Cost Range:</strong>
                            <span class="fw-medium">₹${(procedure.min_cost || 15000).toLocaleString()} - ₹${(procedure.max_cost || 150000).toLocaleString()}</span>
                        </div>
                        <!-- Recovery Row -->
                        <div class="d-flex align-items-center mb-2">
                            <i class="fas fa-clock text-primary me-2"></i>
                            <strong class="me-2">Recovery:</strong>
                            <span>${procedure.recovery_time || '1-2 weeks'}</span>
                        </div>
                    </div>
                    
                    <div class="d-flex gap-2 mt-auto pt-2">
                        <a href="/procedures/detail/${procedure.id}" class="btn btn-primary">
                            Learn More
                        </a>
                        <a href="/doctors?procedure_id=${procedure.id}" class="btn btn-outline-primary">
                            Find Doctors
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return cardHTML;
}