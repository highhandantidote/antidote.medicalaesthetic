document.addEventListener('DOMContentLoaded', function() {
    // Initialize modals
    let editReviewModal;
    let editThreadModal;
    let editReplyModal;
    
    const reviewModalElement = document.getElementById('editReviewModal');
    if (reviewModalElement) {
        editReviewModal = new bootstrap.Modal(reviewModalElement);
    }
    
    const threadModalElement = document.getElementById('editThreadModal');
    if (threadModalElement) {
        editThreadModal = new bootstrap.Modal(threadModalElement);
    }
    
    const replyModalElement = document.getElementById('editReplyModal');
    if (replyModalElement) {
        editReplyModal = new bootstrap.Modal(replyModalElement);
    }

    // Setup appointment action buttons
    document.querySelectorAll('.appointment-actions .btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const appointmentId = this.getAttribute('data-id');
            const action = this.getAttribute('data-action');
            if (!appointmentId || !action) {
                console.error('Missing appointment ID or action');
                return;
            }

            // Confirm actions
            if (action === 'cancel' && !confirm('Are you sure you want to cancel this appointment?')) {
                return;
            }
            
            if (action === 'confirm' && !confirm('Confirm this appointment?')) {
                return;
            }
            
            if (action === 'complete' && !confirm('Mark this appointment as completed?')) {
                return;
            }

            fetch(`/appointment/${action}/${appointmentId}`, {
                method: 'POST',
                headers: { 
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message || 'Action completed successfully!');
                    location.reload();
                } else {
                    alert(data.message || 'Action failed.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing your request. Please try again.');
            });
        });
    });

    // Setup review action buttons
    document.querySelectorAll('.review-actions .btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const reviewId = this.getAttribute('data-id');
            const action = this.getAttribute('data-action');
            if (!reviewId || !action) {
                console.error('Missing review ID or action');
                return;
            }

            if (action === 'edit') {
                // Handle edit action with modal
                fetch(`/review/${reviewId}`, {
                    method: 'GET',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Populate the modal with the review data
                        document.getElementById('editReviewId').value = reviewId;
                        document.getElementById('editRating').value = data.review.rating;
                        document.getElementById('editContent').value = data.review.content;
                        
                        // Show the modal
                        if (editReviewModal) {
                            editReviewModal.show();
                        }
                    } else {
                        alert(data.message || 'Could not retrieve review data.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while retrieving review data.');
                });
            } else if (action === 'delete') {
                // Confirm deletion
                if (!confirm('Are you sure you want to delete this review? This action cannot be undone.')) {
                    return;
                }

                fetch(`/review/delete/${reviewId}`, {
                    method: 'POST',
                    headers: { 
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message || 'Review deleted successfully');
                        location.reload();
                    } else {
                        alert(data.message || 'Failed to delete review');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while deleting the review.');
                });
            }
        });
    });

    // Setup edit review form submission
    const editReviewForm = document.getElementById('editReviewForm');
    if (editReviewForm) {
        editReviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const reviewId = document.getElementById('editReviewId').value;
            const rating = document.getElementById('editRating').value;
            const content = document.getElementById('editContent').value;

            if (!reviewId || !rating || !content) {
                alert('All fields are required');
                return;
            }

            fetch(`/review/edit/${reviewId}`, {
                method: 'POST',
                headers: { 
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    rating: rating,
                    content: content
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (editReviewModal) {
                        editReviewModal.hide();
                    }
                    alert(data.message || 'Review updated successfully');
                    location.reload();
                } else {
                    alert(data.message || 'Failed to update review');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while updating the review.');
            });
        });
    }
    
    // Setup community post action buttons
    document.querySelectorAll('.community-actions .btn').forEach(button => {
        console.log('Setting up community post button:', button.getAttribute('data-action'));
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const threadId = this.getAttribute('data-id');
            const action = this.getAttribute('data-action');
            console.log('Action clicked:', action, 'Thread ID:', threadId);
            
            if (!threadId || !action) {
                console.error('Missing thread ID or action');
                return;
            }
            
            // Find the parent row for this action button for tracking in console
            const parentRow = this.closest('.community-post-card');
            if (!parentRow) {
                console.error('No parent row found for this button');
            }

            if (action === 'view') {
                console.log('View button clicked');
                window.location.href = `/community/thread/${threadId}`;
                return;
            }
            
            if (action === 'edit') {
                console.log('Edit button clicked');
                // Fetch thread data and populate modal
                fetch(`/community/thread/${threadId}`, {
                    method: 'GET',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Thread data received:', data);
                        // Populate modal with thread data
                        document.getElementById('editThreadId').value = threadId;
                        document.getElementById('editThreadTitle').value = data.thread.title;
                        document.getElementById('editThreadContent').value = data.thread.content;
                        
                        // Show modal
                        if (editThreadModal) {
                            editThreadModal.show();
                        } else {
                            console.error('Edit thread modal not initialized');
                            alert('Error: Could not open edit form. Please try again.');
                        }
                    } else {
                        console.error('Failed to get thread data:', data.message);
                        alert(data.message || 'Failed to load thread data.');
                    }
                })
                .catch(error => {
                    console.error('Error fetching thread data:', error);
                    alert('An error occurred while loading thread data.');
                });
            } else if (action === 'delete') {
                console.log('Delete button clicked');
                if (!confirm('Are you sure you want to delete this thread? This cannot be undone.')) {
                    return;
                }
                
                fetch(`/community/delete_thread/${threadId}`, {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Delete response:', data);
                    if (data.success) {
                        alert(data.message || 'Thread deleted successfully!');
                        location.reload();
                    } else {
                        alert(data.message || 'Failed to delete thread.');
                    }
                })
                .catch(error => {
                    console.error('Error deleting thread:', error);
                    alert('An error occurred while deleting the thread.');
                });
            }
        });
    });
    
    // Setup edit thread form submission
    const editThreadForm = document.getElementById('editThreadForm');
    if (editThreadForm) {
        console.log('Found edit thread form, setting up submission handler');
        editThreadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const threadId = document.getElementById('editThreadId').value;
            const title = document.getElementById('editThreadTitle').value.trim();
            const content = document.getElementById('editThreadContent').value.trim();
            
            console.log('Submitting thread edit:', { threadId, title, content });
            
            if (!threadId || !title || !content) {
                alert('Title and content are required.');
                return;
            }
            
            fetch(`/community/edit_thread/${threadId}`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'X-Requested-With': 'XMLHttpRequest' 
                },
                body: JSON.stringify({ title: title, content: content })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Edit response:', data);
                if (data.success) {
                    if (editThreadModal) {
                        editThreadModal.hide();
                    }
                    alert(data.message || 'Thread updated successfully!');
                    location.reload();
                } else {
                    alert(data.message || 'Failed to update thread.');
                }
            })
            .catch(error => {
                console.error('Error updating thread:', error);
                alert('An error occurred while updating the thread.');
            });
        });
    } else {
        console.log('Edit thread form not found');
    }

    // Setup community reply action buttons
    document.querySelectorAll('[data-action="edit-reply"], [data-action="delete-reply"]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const replyId = this.getAttribute('data-id');
            const action = this.getAttribute('data-action');
            console.log('Reply action clicked:', action, 'Reply ID:', replyId);
            
            if (!replyId || !action) {
                console.error('Missing reply ID or action');
                return;
            }
            
            if (action === 'edit-reply') {
                console.log('Edit reply button clicked');
                // Fetch reply data and populate modal
                fetch(`/api/community-replies/${replyId}`, {
                    method: 'GET',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Reply data received:', data);
                        // Populate modal with reply data
                        document.getElementById('editReplyId').value = replyId;
                        document.getElementById('editReplyContent').value = data.reply.content;
                        
                        // Show modal
                        if (editReplyModal) {
                            editReplyModal.show();
                        } else {
                            console.error('Edit reply modal not initialized');
                            alert('Error: Could not open edit form. Please try again.');
                        }
                    } else {
                        console.error('Failed to get reply data:', data.message);
                        alert(data.message || 'Failed to load reply data.');
                    }
                })
                .catch(error => {
                    console.error('Error fetching reply data:', error);
                    alert('An error occurred while loading reply data.');
                });
            } else if (action === 'delete-reply') {
                console.log('Delete reply button clicked');
                if (!confirm('Are you sure you want to delete this reply? This cannot be undone.')) {
                    return;
                }
                
                fetch(`/community/reply/delete/${replyId}`, {
                    method: 'POST',
                    headers: { 
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Delete response:', data);
                    if (data.success) {
                        alert(data.message || 'Reply deleted successfully!');
                        location.reload();
                    } else {
                        alert(data.message || 'Failed to delete reply.');
                    }
                })
                .catch(error => {
                    console.error('Error deleting reply:', error);
                    alert('An error occurred while deleting the reply.');
                });
            }
        });
    });
    
    // Setup edit reply form submission
    const editReplyForm = document.getElementById('editReplyForm');
    if (editReplyForm) {
        console.log('Found edit reply form, setting up submission handler');
        editReplyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const replyId = document.getElementById('editReplyId').value;
            const content = document.getElementById('editReplyContent').value.trim();
            const csrfToken = this.querySelector('input[name="csrf_token"]').value;
            
            console.log('Submitting reply edit:', { replyId, content });
            
            if (!replyId || !content) {
                alert('Reply content is required.');
                return;
            }
            
            fetch(`/community/reply/edit/${replyId}`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ 
                    content: content,
                    csrf_token: csrfToken
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Edit response:', data);
                if (data.success) {
                    if (editReplyModal) {
                        editReplyModal.hide();
                    }
                    alert(data.message || 'Reply updated successfully!');
                    location.reload();
                } else {
                    alert(data.message || 'Failed to update reply.');
                }
            })
            .catch(error => {
                console.error('Error updating reply:', error);
                alert('An error occurred while updating the reply.');
            });
        });
    }

    console.log("Dashboard.js initialized: Set up action handlers for appointments, reviews, community posts and replies");
});