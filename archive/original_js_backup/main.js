/**
 * Main JavaScript file for Antidote platform
 * Handles client-side functionality and UI enhancements
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Find all elements containing the rupee symbol and add price-display class
    document.querySelectorAll('*').forEach(function(element) {
        if (element.textContent.includes('₹')) {
            element.classList.add('price-display');
        }
    });
    
    // Image preview for thread creation and editing
    const imageUpload = document.getElementById('image');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    
    if (imageUpload && imagePreviewContainer && imagePreview) {
        imageUpload.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreviewContainer.style.display = 'block';
                }
                
                reader.readAsDataURL(this.files[0]);
            } else {
                imagePreviewContainer.style.display = 'none';
            }
        });
    }
    
    // Create Thread button handler
    const createButton = document.querySelector('.create-thread-btn');
    if (createButton) {
        createButton.addEventListener('click', () => {
            console.log('Create Thread clicked');
            window.location.href = '/community/new';
        });
    } else {
        console.log('Create Thread button not found');
    }

    // Action buttons for thread management
    const actionButtons = document.querySelectorAll('.actions button');
    if (actionButtons.length > 0) {
        console.log('Found action buttons:', actionButtons.length);
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                console.log('Action clicked:', e.target.textContent);
                const action = e.target.textContent.toLowerCase();
                const threadId = button.closest('tr')?.dataset.threadId;
                
                if (threadId) {
                    console.log('Thread ID found:', threadId);
                    if (action === 'view') {
                        window.location.href = `/community/thread/${threadId}`;
                    } else if (action === 'edit') {
                        window.location.href = `/dashboard/community/edit/${threadId}`;
                    } else if (action === 'delete') {
                        if (confirm('Are you sure you want to delete this thread?')) {
                            fetch(`/api/community/${threadId}`, { 
                                method: 'DELETE',
                                headers: { 'Content-Type': 'application/json' }
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    location.reload();
                                } else {
                                    alert('Error deleting thread: ' + (data.message || 'Unknown error'));
                                }
                            })
                            .catch(error => {
                                console.error('Error:', error);
                                alert('An error occurred while deleting the thread.');
                            });
                        }
                    }
                } else {
                    console.log('Thread ID not found for action:', action);
                }
            });
        });
    } else {
        console.log('No action buttons found');
    }
    // Initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }

    // Toggle mobile navigation
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarNav = document.querySelector('#navbarNav');
    
    // Handle mobile nav clicks for main menu items
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    if (navbarToggler && navbarNav) {
        // Let Bootstrap handle the toggle through data attributes
        // This ensures proper behavior for both opening and closing
        
        // Additionally, close menu when clicking anywhere outside
        document.addEventListener('click', function(event) {
            // Only act if the menu is open and click is outside the nav
            const isNavbarExpanded = navbarToggler.getAttribute('aria-expanded') === 'true';
            if (isNavbarExpanded && 
                !navbarNav.contains(event.target) && 
                !navbarToggler.contains(event.target)) {
                // Use Bootstrap's collapse API to close the menu
                const bsCollapse = new bootstrap.Collapse(navbarNav);
                bsCollapse.hide();
            }
        });
        
        // Close menu when a nav link is clicked
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                // Only close if we're in mobile view (toggler is visible)
                if (window.getComputedStyle(navbarToggler).display !== 'none') {
                    const bsCollapse = new bootstrap.Collapse(navbarNav);
                    bsCollapse.hide();
                }
            });
        });
    }
    
    // Community thread reply form submission
    const replyForm = document.getElementById('replyForm');
    if (replyForm) {
        replyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const threadId = document.getElementById('threadId').value;
            const replyContent = document.getElementById('replyContent').value;
            const isAnonymous = document.getElementById('anonymousReply').checked;
            const parentReplyId = document.getElementById('parentReplyId').value || null;
            const userId = document.getElementById('userId').value;
            
            if (!replyContent.trim()) {
                alert('Please enter your message before submitting.');
                return;
            }
            
            // Get photo file if available
            const photoFile = document.getElementById('replyPhoto').files[0] || null;
            let photoUrl = null;
            
            // Build request data
            const requestData = {
                thread_id: parseInt(threadId),
                content: replyContent,
                is_anonymous: isAnonymous,
                parent_reply_id: parentReplyId ? parseInt(parentReplyId) : null
            };
            
            // Add user_id only if available and valid
            if (userId && userId.trim() !== '') {
                requestData.user_id = parseInt(userId);
            }
            
            // Submit reply via API
            fetch('/api/community-replies', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Reload page to show the new reply
                    window.location.reload();
                } else {
                    alert('Error posting reply: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while submitting your reply.');
            });
        });
    }
    
    // Handle media preview in community posts
    document.querySelectorAll('.media-preview-trigger').forEach(trigger => {
        trigger.addEventListener('click', function() {
            const mediaType = this.getAttribute('data-media-type');
            const mediaUrl = this.getAttribute('data-media-url');
            const mediaPreviewModal = document.getElementById('mediaPreviewModal');
            
            if (mediaPreviewModal) {
                const modalBody = mediaPreviewModal.querySelector('.modal-body');
                
                // Clear previous content
                modalBody.innerHTML = '';
                
                // Add appropriate media based on type
                if (mediaType === 'photo') {
                    const img = document.createElement('img');
                    img.src = mediaUrl;
                    img.classList.add('img-fluid');
                    modalBody.appendChild(img);
                } else if (mediaType === 'video') {
                    const iframe = document.createElement('iframe');
                    iframe.src = mediaUrl;
                    iframe.classList.add('w-100');
                    iframe.style.height = '400px';
                    iframe.setAttribute('allowfullscreen', true);
                    modalBody.appendChild(iframe);
                }
                
                // Show the modal
                const modal = new bootstrap.Modal(mediaPreviewModal);
                modal.show();
                
                // Add event handler for modal hidden event to properly clean up
                mediaPreviewModal.addEventListener('hidden.bs.modal', function() {
                    // Clear the modal content when it's closed
                    modalBody.innerHTML = '';
                    
                    // Force document body to reset any stuck scroll issues
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                    
                    // Remove modal backdrop if it got stuck
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) {
                        backdrop.remove();
                    }
                }, { once: true }); // Use once: true to avoid memory leaks
            }
        });
    });

    // Handle procedure search functionality
    const procedureSearch = document.getElementById('procedureSearch');
    if (procedureSearch) {
        procedureSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const procedureCards = document.querySelectorAll('.procedure-card');
            
            let resultsFound = false;
            
            procedureCards.forEach(card => {
                const title = card.querySelector('.card-title').textContent.toLowerCase();
                const description = card.querySelector('.card-text').textContent.toLowerCase();
                
                if (title.includes(searchTerm) || description.includes(searchTerm)) {
                    card.style.display = '';
                    resultsFound = true;
                } else {
                    card.style.display = 'none';
                }
            });

            // Show or hide no results message
            let noResultsMsg = document.getElementById('noResultsMessage');
            if (!resultsFound) {
                if (!noResultsMsg) {
                    noResultsMsg = document.createElement('div');
                    noResultsMsg.id = 'noResultsMessage';
                    noResultsMsg.className = 'col-12 mt-3';
                    noResultsMsg.innerHTML = '<div class="alert alert-info">No procedures found matching your search.</div>';
                    document.getElementById('procedureList').appendChild(noResultsMsg);
                }
            } else if (noResultsMsg) {
                noResultsMsg.remove();
            }
        });
    }

    // Doctor filter functionality
    const applyFiltersBtn = document.getElementById('applyFilters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            const locationFilter = document.getElementById('locationFilter').value;
            const specialtyFilter = document.getElementById('specialtyFilter').value;
            const ratingFilterEl = document.querySelector('input[name="ratingFilter"]:checked');
            const ratingFilter = ratingFilterEl ? ratingFilterEl.value : '';
            
            const doctorCards = document.querySelectorAll('.doctor-card');
            let visibleCount = 0;
            
            doctorCards.forEach(card => {
                const location = card.dataset.location;
                const specialty = card.dataset.specialty;
                const rating = parseFloat(card.dataset.rating);
                
                let locationMatch = !locationFilter || location === locationFilter;
                let specialtyMatch = !specialtyFilter || specialty === specialtyFilter;
                let ratingMatch = !ratingFilter || rating >= parseFloat(ratingFilter);
                
                if (locationMatch && specialtyMatch && ratingMatch) {
                    card.style.display = '';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });
            
            // Show message if no results
            let noResultsMsg = document.getElementById('noResultsMessage');
            if (visibleCount === 0) {
                if (!noResultsMsg) {
                    noResultsMsg = document.createElement('div');
                    noResultsMsg.id = 'noResultsMessage';
                    noResultsMsg.className = 'col-12 mt-3';
                    noResultsMsg.innerHTML = '<div class="alert alert-info">No doctors found matching your criteria.</div>';
                    document.getElementById('doctorList').appendChild(noResultsMsg);
                }
            } else if (noResultsMsg) {
                noResultsMsg.remove();
            }
        });
    }

    // Enhance card interaction with hover effects
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.2)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });

    // Smooth scroll to target for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId !== '#' && document.querySelector(targetId)) {
                e.preventDefault();
                document.querySelector(targetId).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Form validation for any forms
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Initialize any custom dropdowns
    const dropdownElementList = document.querySelectorAll('.dropdown-toggle');
    const dropdownList = [...dropdownElementList].map(dropdownToggleEl => {
        if (typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
            return new bootstrap.Dropdown(dropdownToggleEl);
        }
        return null;
    });
    
    // Simple reply form submission as per requirements
    function createReply(threadId, content) {
        // Get CSRF token from the form
        const csrfToken = document.getElementById('reply_csrf_token').value;
        
        fetch(`/api/community/${threadId}/replies`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ 
                content: content, 
                is_anonymous: false,
                csrf_token: csrfToken
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    console.error('Response error:', text);
                    throw new Error('Server error: ' + response.status);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) location.reload();
            else alert(data.message);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error posting reply. Please try again later.');
        });
    }
    
    // Handle simple reply form submission
    document.querySelectorAll('.reply-form').forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const threadId = form.dataset.threadId;
            const content = form.querySelector('textarea').value;
            createReply(threadId, content);
        });
    });

    // Dashboard community actions
    // Handle View, Edit and Delete button clicks with debugging
    console.log('Setting up dashboard button handlers');
    
    // View button (btn-outline-info)
    document.querySelectorAll('.btn-outline-info').forEach(button => {
        if (button.textContent.trim().toLowerCase() === 'view') {
            console.log('Found View button, setting handler');
            button.addEventListener('click', function(e) {
                console.log('View button clicked');
                // View buttons already have href attributes, so we don't need to do anything
            });
        }
    });
    
    // Edit button (btn-outline-warning)
    document.querySelectorAll('.btn-outline-warning').forEach(button => {
        console.log('Found Edit button, setting handler');
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const action = this.getAttribute('data-action') || this.textContent.trim().toLowerCase();
            const itemId = this.getAttribute('data-id');
            console.log('Action clicked:', action, 'ID:', itemId);
            
            const row = this.closest('tr');
            if (!row) {
                console.error('No parent row found for this button');
                return;
            }
            
            // Check if this is for a thread
            const threadId = row.dataset.threadId || itemId;
            if (threadId && (row.dataset.threadId || this.classList.contains('community-action'))) {
                console.log('Editing thread:', threadId);
                window.location.href = `/dashboard/community/edit/${threadId}`;
                return;
            }
            
            // Check if this is for a procedure
            const procedureId = row.dataset.id || itemId;
            if (procedureId && (row.dataset.id || this.closest('#procedures'))) {
                console.log('Editing procedure:', procedureId);
                window.location.href = `/admin/procedures/edit/${procedureId}`;
                return;
            }
            
            // Default fallback using the href attribute if available
            if (this.getAttribute('href') && this.getAttribute('href') !== '#') {
                window.location.href = this.getAttribute('href');
            } else {
                console.error('Unable to determine what to edit. No ID or href found.');
            }
        });
    });
    
    // Delete button (btn-outline-danger)
    document.querySelectorAll('.btn-outline-danger').forEach(button => {
        console.log('Found Delete button, setting handler');
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const action = this.getAttribute('data-action') || this.textContent.trim().toLowerCase();
            const itemId = this.getAttribute('data-id');
            console.log('Action clicked:', action, 'ID:', itemId);
            
            const row = this.closest('tr');
            if (!row) {
                console.error('No parent row found for this button');
                return;
            }
            
            // Check if this is for a thread
            const threadId = row.dataset.threadId || itemId;
            if (threadId && (row.dataset.threadId || this.classList.contains('community-action'))) {
                console.log('Deleting thread:', threadId);
                if (confirm('Are you sure you want to delete this thread?')) {
                    fetch(`/api/community/${threadId}`, { 
                        method: 'DELETE',
                        headers: { 'Content-Type': 'application/json' }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            location.reload();
                        } else {
                            alert('Error deleting thread: ' + (data.message || 'Unknown error'));
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred while deleting the thread.');
                    });
                }
                return;
            }
            
            // Check if this is for a procedure
            const procedureId = row.dataset.id || itemId;
            if (procedureId && (row.dataset.id || this.closest('#procedures'))) {
                console.log('Deleting procedure:', procedureId);
                if (confirm('Are you sure you want to delete this procedure? This action cannot be undone.')) {
                    fetch(`/admin/procedures/delete/${procedureId}`, { 
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Procedure deleted successfully');
                            location.reload();
                        } else {
                            alert('Error deleting procedure: ' + (data.message || 'Unknown error'));
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred while deleting the procedure.');
                    });
                }
                return;
            }
        });
    });

    // Create Thread button
    const createThreadBtns = document.querySelectorAll('.btn-outline-success');
    console.log('Found Create Thread buttons:', createThreadBtns.length);
    
    createThreadBtns.forEach(btn => {
        if (btn.textContent.trim().toLowerCase().includes('create thread')) {
            console.log('Setting up Create Thread button handler');
            btn.addEventListener('click', function(e) {
                console.log('Create Thread button clicked');
                e.preventDefault();
                window.location.href = '/dashboard/community/create';
            });
        }
    });
    
    console.log('Antidote platform JavaScript initialized successfully');
});

// Function to update page view counters (if implemented)
function updateViewCount(entityType, entityId) {
    if (!entityType || !entityId) return;
    
    const url = `/api/${entityType}/${entityId}/view`;
    
    // Use a simple fetch without displaying any results
    // This just records the view without affecting the UI
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    }).catch(error => {
        console.error('Error updating view count:', error);
    });
}

// Function to format currency amounts
function formatCurrency(amount, addHtmlClass = false) {
    if (typeof amount !== 'number') return amount;
    
    const formattedAmount = new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
    
    // If this is being used in HTML with the class parameter, add the price-display class
    if (addHtmlClass) {
        return `<span class="price-display">${formattedAmount}</span>`;
    }
    
    return formattedAmount;
}

// Function to format dates in a human-readable way
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(date);
}

// Function to truncate text with ellipsis
function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}
