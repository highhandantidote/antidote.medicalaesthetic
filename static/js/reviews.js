document.addEventListener('DOMContentLoaded', function() {
    console.log("Reviews.js loaded");
    
    // Debug information about the page
    console.log("URL path:", window.location.pathname);
    console.log("All forms:", document.querySelectorAll('form').length);
    console.log("Review reply forms:", document.querySelectorAll('.reply-review-form').length);
    
    // Add toggle buttons for reply forms
    const replyForms = document.querySelectorAll('.reply-review-form');
    
    replyForms.forEach(form => {
        // Get the review ID from the form's data attribute
        const reviewId = form.dataset.reviewId;
        console.log(`Found reply form for review ${reviewId}`);
        
        // Create a toggle button if it doesn't exist
        if (!document.querySelector(`.toggle-reply-btn[data-review-id="${reviewId}"]`)) {
            // Hide the form initially
            form.classList.add('d-none');
            
            // Insert a button before the form
            const toggleButton = document.createElement('button');
            toggleButton.type = 'button';
            toggleButton.className = 'btn btn-outline-primary toggle-reply-btn mb-3';
            toggleButton.dataset.reviewId = reviewId;
            toggleButton.innerHTML = '<i class="fas fa-reply me-1"></i> Reply to Review';
            
            // Add click event to toggle form visibility
            toggleButton.addEventListener('click', function() {
                form.classList.toggle('d-none');
                this.textContent = form.classList.contains('d-none') 
                    ? 'Reply to Review' 
                    : 'Cancel Reply';
                
                if (!form.classList.contains('d-none')) {
                    form.querySelector('textarea').focus();
                }
            });
            
            // Insert the button before the form
            form.parentNode.insertBefore(toggleButton, form);
        }
    });
    
    // Add event handlers for review reply forms
    function setupReviewReplyForms() {
        const replyForms = document.querySelectorAll('.reply-review-form');
        console.log(`Found ${replyForms.length} reply forms`);
        
        replyForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const reviewId = this.dataset.reviewId;
                const formData = new FormData(this);
                
                console.log(`Submitting reply for review ${reviewId}`);
                
                // Submit the form with fetch API
                fetch(`/review/${reviewId}/reply`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Create and append the new reply element
                        const replyContainer = document.querySelector(`#review-${reviewId} .review-replies`);
                        
                        if (replyContainer) {
                            const newReplyElement = document.createElement('div');
                            newReplyElement.className = 'doctor-reply mb-3 p-3 bg-dark rounded';
                            newReplyElement.innerHTML = `
                                <div class="d-flex justify-content-between">
                                    <h6 class="mb-1">Reply from Dr. ${data.reply.doctor_name}</h6>
                                    <small class="text-muted">${data.reply.created_at}</small>
                                </div>
                                <p class="mb-0">${data.reply.text}</p>
                            `;
                            
                            replyContainer.appendChild(newReplyElement);
                            
                            // Clear the form
                            form.querySelector('textarea[name="reply_text"]').value = '';
                            
                            // Show success message
                            alert('Reply submitted successfully!');
                        } else {
                            // If no reply container found, reload the page
                            window.location.reload();
                        }
                    } else {
                        console.error('Failed to submit reply:', data.message);
                        alert('There was a problem submitting your reply: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error submitting reply:', error);
                    alert('There was a problem submitting your reply. Please try again.');
                });
            });
        });
    }
    
    // Handle helpful buttons
    function setupReviewActionButtons() {
        const helpfulButtons = document.querySelectorAll('.mark-helpful-btn');
        console.log(`Found ${helpfulButtons.length} helpful buttons`);
        
        helpfulButtons.forEach(button => {
            button.addEventListener('click', function() {
                const reviewId = this.dataset.reviewId;
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || 
                                 document.querySelector('input[name="csrf_token"]')?.value;
                
                if (!csrfToken) {
                    alert('CSRF token not found. Cannot mark as helpful.');
                    return;
                }
                
                console.log(`Marking review ${reviewId} as helpful`);
                
                const formData = new FormData();
                formData.append('csrf_token', csrfToken);
                
                // Submit the API request
                fetch(`/reviews/${reviewId}/helpful`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update the count in the UI
                        const helpfulCount = this.querySelector('.helpful-count');
                        if (helpfulCount) {
                            helpfulCount.textContent = data.helpful_count;
                        }
                        
                        // Change button appearance to indicate it's been marked helpful
                        this.classList.remove('btn-outline-success');
                        this.classList.add('btn-success');
                        this.disabled = true;
                    } else {
                        alert('Error: ' + (data.message || 'Failed to mark as helpful'));
                    }
                })
                .catch(error => {
                    console.error('Error marking review as helpful:', error);
                    alert('There was a problem marking this review as helpful. Please try again.');
                });
            });
        });
        
        // Find review buttons (for other actions)
        const reviewButtons = document.querySelectorAll('.review-action-btn');
        console.log(`Found ${reviewButtons.length} review buttons`);

        // Report buttons
        const reportButtons = document.querySelectorAll('.report-review-btn');
        console.log(`Found ${reportButtons.length} report buttons`);
        
        if (reportButtons.length > 0) {
            reportButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const reviewId = this.dataset.reviewId;
                    if (window.bootstrap && document.getElementById('reportReviewModal')) {
                        const reportModal = new bootstrap.Modal(document.getElementById('reportReviewModal'));
                        
                        // Set the review ID in the modal form
                        document.getElementById('reportReviewId').value = reviewId;
                        
                        // Show the modal
                        reportModal.show();
                    } else {
                        // Fallback if modal not available
                        alert('Reporting functionality is not available at this time.');
                    }
                });
            });
        }
    }
    
    // Initialize all review functionality
    setupReviewReplyForms();
    setupReviewActionButtons();
});