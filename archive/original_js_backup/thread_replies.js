/**
 * Thread replies management
 * Handles the client-side logic for replying to threads
 */

// Function to create a reply to a thread
function createReply(threadId, content, isAnonymous, parentReplyId = null) {
    console.log('Creating reply:', { threadId, content, isAnonymous, parentReplyId });
    
    // Prepare the request data
    const requestData = {
        content: content,
        is_anonymous: isAnonymous
    };
    
    // Add parent reply ID if provided (for nested replies)
    if (parentReplyId) {
        requestData.parent_reply_id = parentReplyId;
    }
    
    // Make the API request to our backend endpoint
    return fetch(`/api/community/${threadId}/replies`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(requestData)
    }).then(response => {
        console.log('Response status:', response.status, 'OK:', response.ok);
        console.log('Response headers:', response.headers);
        
        if (!response.ok) {
            return response.text().then(text => {
                console.error('Response body:', text);
                throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}...`);
            });
        }
        return response.json();
    }).then(data => {
        if (data.success) {
            console.log('Reply success:', data.message);
            return data;
        } else {
            throw new Error(data.message || 'Reply failed');
        }
    }).catch(error => {
        console.error('Reply error:', error);
        alert('Error posting reply: ' + error.message);
        throw error;
    });
}

// Document ready handler
document.addEventListener('DOMContentLoaded', function() {
    // Main reply form submission
    const replyForm = document.getElementById('replyForm');
    if (replyForm) {
        replyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const threadId = replyForm.getAttribute('data-thread-id') || document.querySelector('meta[name="thread-id"]')?.content;
            const content = document.getElementById('replyContent').value.trim();
            const isAnonymous = document.getElementById('replyAnonymous')?.checked || false;
            
            if (!threadId) {
                console.error('Thread ID not found');
                alert('Thread ID not found. Please refresh the page and try again.');
                return;
            }
            
            if (!content) {
                alert('Reply content is required.');
                return;
            }
            
            // Disable the submit button while processing
            const submitBtn = replyForm.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.disabled = true;
            
            // Submit the reply
            createReply(threadId, content, isAnonymous)
                .then(() => {
                    // Reset the form
                    replyForm.reset();
                    
                    // Re-enable the submit button
                    if (submitBtn) submitBtn.disabled = false;
                    
                    // Reload the page to show the new reply
                    location.reload();
                })
                .catch(() => {
                    // Re-enable the submit button on error
                    if (submitBtn) submitBtn.disabled = false;
                });
        });
    }
    
    // Handle nested reply forms
    const nestedReplyForms = document.querySelectorAll('.nested-reply-form');
    nestedReplyForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const threadId = form.getAttribute('data-thread-id') || document.querySelector('meta[name="thread-id"]')?.content;
            const parentId = form.getAttribute('data-parent-id');
            const content = form.querySelector('textarea').value.trim();
            const isAnonymous = form.querySelector('input[type="checkbox"]')?.checked || false;
            
            if (!threadId) {
                console.error('Thread ID not found for nested reply');
                alert('Thread ID not found. Please refresh the page and try again.');
                return;
            }
            
            if (!parentId) {
                console.error('Parent reply ID not found');
                alert('Parent reply ID not found. Please refresh the page and try again.');
                return;
            }
            
            if (!content) {
                alert('Reply content is required.');
                return;
            }
            
            // Disable the submit button while processing
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.disabled = true;
            
            // Submit the nested reply
            createReply(threadId, content, isAnonymous, parentId)
                .then(() => {
                    // Reset the form
                    form.reset();
                    
                    // Re-enable the submit button
                    if (submitBtn) submitBtn.disabled = false;
                    
                    // Reload the page to show the new reply
                    location.reload();
                })
                .catch(() => {
                    // Re-enable the submit button on error
                    if (submitBtn) submitBtn.disabled = false;
                });
        });
    });
});