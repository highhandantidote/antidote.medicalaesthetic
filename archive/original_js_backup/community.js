document.addEventListener('DOMContentLoaded', function() {
    // Set up create thread button
    const createThreadBtn = document.querySelector('#createThreadBtn');
    const threadForm = document.querySelector('#createThreadForm');
    const modalElement = document.getElementById('createThreadModal');
    let modal;

    console.log("DOM loaded");

    if (createThreadBtn) {
        console.log("Found Create Thread button");
        createThreadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Create Thread button clicked');
            if (!modal) {
                modal = new bootstrap.Modal(modalElement, { backdrop: 'static', keyboard: false });
            }
            modal.show();
        });
    } else {
        console.log("Create Thread button not found");
    }

    // Set up thread form submission
    if (threadForm) {
        console.log("Found Create Thread form");
        threadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submission intercepted');
            
            // Get exact form elements by ID
            const titleElement = document.getElementById('threadTitle');
            const contentElement = document.getElementById('threadContent');
            
            if (!titleElement || !contentElement) {
                console.error('Form elements not found:', {
                    titleElement: titleElement ? 'Found' : 'Not found',
                    contentElement: contentElement ? 'Found' : 'Not found'
                });
                alert('Form elements not found. Please contact support.');
                return;
            }
            
            // Get values and log them
            const title = titleElement.value.trim();
            const content = contentElement.value.trim();
            
            console.log('Form values:', {
                titleRaw: titleElement.value,
                contentRaw: contentElement.value,
                titleTrimmed: title,
                contentTrimmed: content,
                titleLength: title.length,
                contentLength: content.length
            });
            
            if (!title || !content) {
                alert('Title and content are required. Debug: Title="' + title + '", Content="' + content + '"');
                return;
            }
            
            const submitBtn = threadForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            
            // Collect additional data if available
            let postData = {
                title: title,
                content: content
            };
            
            const categorySelect = document.getElementById('threadCategory');
            if (categorySelect && categorySelect.value) {
                postData.category_id = parseInt(categorySelect.value);
            }
            
            const procedureSelect = document.getElementById('threadProcedure');
            if (procedureSelect && procedureSelect.value) {
                postData.procedure_id = parseInt(procedureSelect.value);
            }
            
            const anonymousCheckbox = document.getElementById('anonymousThread');
            if (anonymousCheckbox) {
                postData.is_anonymous = anonymousCheckbox.checked;
            }
            
            console.log('Sending data to server:', postData);
            
            // Get CSRF token
            const csrfToken = document.querySelector('input[name="csrf_token"]').value;
            
            // Add the CSRF token to the request data
            postData.csrf_token = csrfToken;
            
            // Submit the form
            fetch('/community/create_thread', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(postData)
            })
            .then(response => {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    console.error('HTTP error! status:', response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('Server response:', data);
                submitBtn.disabled = false;
                if (data.success) {
                    if (modalElement && modal) {
                        modal.hide();
                    }
                    
                    // Clear form
                    threadForm.reset();
                    
                    // Show success message
                    alert('Thread created successfully!');
                    
                    // Redirect to the thread page or reload
                    if (data.thread_id) {
                        window.location.href = `/community/thread/${data.thread_id}`;
                    } else {
                        location.reload();
                    }
                } else {
                    alert(data.message || 'Failed to create thread.');
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                submitBtn.disabled = false;
                alert('An error occurred while creating the thread. Check console for details.');
            });
        });
    } else {
        console.log("Create Thread form not found");
    }
    
    if (modalElement) {
        modalElement.addEventListener('hidden.bs.modal', function () {
            console.log('Modal hidden event');
            modal = null;
        });
        
        modalElement.addEventListener('shown.bs.modal', function () {
            console.log('Modal shown event');
            const titleElement = document.getElementById('threadTitle');
            if (titleElement) {
                titleElement.focus();
            }
        });
    }

    // Set up thread action buttons (like, report, etc.)
    const actionButtons = document.querySelectorAll('.thread-action');
    if (actionButtons.length > 0) {
        console.log("Found action buttons:", actionButtons.length);
        actionButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const threadId = this.getAttribute('data-thread-id');
                const action = this.getAttribute('data-action');
                
                if (!threadId || !action) {
                    console.error('Missing thread ID or action');
                    return;
                }
                
                fetch(`/community/thread/${threadId}/${action}`, {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update the UI without reloading
                        if (action === 'like') {
                            const countElement = this.querySelector('.count');
                            if (countElement) {
                                countElement.textContent = data.count || 0;
                            }
                            this.classList.toggle('active', data.active);
                        } else {
                            alert(data.message || 'Action successful!');
                            if (action === 'delete') {
                                location.reload();
                            }
                        }
                    } else {
                        alert(data.message || 'Action failed.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred. Please try again.');
                });
            });
        });
    } else {
        console.log("No action buttons found");
    }

    console.log("Community.js loaded successfully");
});