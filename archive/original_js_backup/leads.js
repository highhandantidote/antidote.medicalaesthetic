document.addEventListener('DOMContentLoaded', function() {
    console.log("Leads.js loaded");
    
    // Add event handlers for lead action buttons
    function setupLeadActionButtons() {
        // Log all buttons on the page for debugging
        const allButtons = document.querySelectorAll('button, a.btn');
        console.log(`Found ${allButtons.length} total buttons on page`);
        
        // Handle the lead action buttons (View, Contact, Update Status)
        const actionButtons = document.querySelectorAll('.lead-action-btn');
        console.log(`Found ${actionButtons.length} lead action buttons`);
        
        if (actionButtons.length === 0) {
            console.log("No lead action buttons found. Trying alternative selectors...");
            // Try alternative selectors that might be used in the actual HTML
            const altButtons = document.querySelectorAll('[data-lead-id]');
            console.log(`Found ${altButtons.length} elements with data-lead-id attribute`);
            if (altButtons.length > 0) {
                console.log("Using alternative selector for lead buttons");
                attachLeadButtonHandlers(altButtons);
            }
        } else {
            attachLeadButtonHandlers(actionButtons);
        }
        
        // Directly attach click handlers to specific buttons by their text
        document.querySelectorAll('a, button').forEach(el => {
            if (el.textContent.trim() === 'View') {
                console.log("Found View button via text content, attaching handler");
                el.addEventListener('click', function(e) {
                    if (!this.dataset.leadId) return; // Skip if no lead ID
                    e.preventDefault();
                    const leadId = this.dataset.leadId;
                    console.log(`View button clicked for lead ${leadId}`);
                    window.location.href = `/lead/${leadId}/view`; // This should be handled by the link's href
                });
            } else if (el.textContent.trim() === 'Contact') {
                console.log("Found Contact button via text content, attaching handler");
                el.addEventListener('click', function(e) {
                    if (!this.dataset.leadId) return; // Skip if no lead ID
                    e.preventDefault();
                    const leadId = this.dataset.leadId;
                    console.log(`Contact button clicked for lead ${leadId}`);
                    window.location.href = `/lead/${leadId}/contact`;
                });
            } else if (el.textContent.trim() === 'Update Status') {
                console.log("Found Update Status button via text content, attaching handler");
                el.addEventListener('click', function(e) {
                    if (!this.dataset.leadId) return; // Skip if no lead ID
                    e.preventDefault();
                    const leadId = this.dataset.leadId;
                    console.log(`Update Status button clicked for lead ${leadId}`);
                    window.location.href = `/lead/${leadId}/update_status`;
                });
            }
        });
    }
    
    function attachLeadButtonHandlers(buttons) {
        buttons.forEach(button => {
            button.addEventListener('click', function(e) {
                console.log("Lead button clicked:", this.textContent.trim());
                e.preventDefault();
                
                const leadId = this.dataset.leadId;
                const action = this.dataset.action;
                
                console.log(`Clicked on ${action} for lead ${leadId}`);
                
                if (action === 'view') {
                    console.log(`View button clicked - navigating to /lead/${leadId}/view`);
                    window.location.href = `/lead/${leadId}/view`;
                } else if (action === 'contact') {
                    console.log(`Contact button clicked - navigating to /lead/${leadId}/contact`);
                    window.location.href = `/lead/${leadId}/contact`;
                } else if (action === 'update_status') {
                    console.log(`Update status button clicked - navigating to /lead/${leadId}/update_status`);
                    window.location.href = `/lead/${leadId}/update_status`;
                }
            });
        });

        // Handle status update forms
        document.querySelectorAll('.update-lead-status-form').forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const leadId = this.dataset.leadId;
                const formData = new FormData(this);
                
                console.log(`Submitting status update for lead ${leadId}`);
                
                // Check if the form has an onchange handler (dropdown select)
                if (this.querySelector('select') && this.querySelector('select').onchange) {
                    console.log("Form has onchange handler, using direct form submission");
                    this.submit();
                    return;
                }
                
                // Get the action URL - either from the form or construct it
                let actionUrl = this.action;
                if (!actionUrl || actionUrl.trim() === "") {
                    actionUrl = `/lead/${leadId}/update_status`;
                    console.log("Constructed action URL:", actionUrl);
                }
                
                // Get the CSRF token
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
                const headers = {
                    'X-Requested-With': 'XMLHttpRequest'
                };
                if (csrfToken) {
                    console.log("Found CSRF token, adding to headers");
                    headers['X-CSRFToken'] = csrfToken;
                } else {
                    console.warn("No CSRF token found");
                }
                
                // Submit the form via AJAX
                fetch(actionUrl, {
                    method: 'POST',
                    body: formData,
                    headers: headers
                })
                .then(response => {
                    console.log("Status update response:", response.status);
                    if (!response.ok) {
                        throw new Error(`Server responded with status ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("Status update success:", data);
                    if (data.success) {
                        alert('Lead status updated successfully!');
                        window.location.reload();
                    } else {
                        alert('Error: ' + (data.message || 'An unknown error occurred.'));
                    }
                })
                .catch(error => {
                    console.error('Status update error:', error);
                    alert('An error occurred while updating the lead status. Please try again.');
                    // As a fallback, try direct form submission on AJAX failure
                    console.log("Attempting direct form submission as fallback");
                    setTimeout(() => {
                        form.removeEventListener('submit', arguments.callee);
                        form.submit();
                    }, 500);
                });
            });
        });
        
        // Quick view buttons
        const quickViewButtons = document.querySelectorAll('.view-lead-details');
        console.log(`Found ${quickViewButtons.length} quick view buttons`);
        
        quickViewButtons.forEach(button => {
            button.addEventListener('click', function() {
                const leadId = this.getAttribute('data-lead-id');
                const detailsContent = document.getElementById('leadDetailsContent');
                
                console.log(`Fetching details for lead ${leadId}`);
                
                // Show loading spinner
                detailsContent.innerHTML = `
                    <div class="d-flex justify-content-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                `;
                
                // Fetch lead details from server
                fetch(`/lead/${leadId}/details`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        const lead = data.lead;
                        // Update modal with actual lead data
                        detailsContent.innerHTML = `
                            <div class="row">
                                <div class="col-md-6">
                                    <h5>Patient Information</h5>
                                    <table class="table table-dark">
                                        <tr>
                                            <th>Name:</th>
                                            <td>${lead.patient_name}</td>
                                        </tr>
                                        <tr>
                                            <th>Contact:</th>
                                            <td>${lead.mobile_number}</td>
                                        </tr>
                                        <tr>
                                            <th>Email:</th>
                                            <td>${lead.email || 'Not provided'}</td>
                                        </tr>
                                        <tr>
                                            <th>City:</th>
                                            <td>${lead.city || 'Not specified'}</td>
                                        </tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <h5>Lead Details</h5>
                                    <table class="table table-dark">
                                        <tr>
                                            <th>Procedure:</th>
                                            <td>${lead.procedure_name}</td>
                                        </tr>
                                        <tr>
                                            <th>Preferred Date:</th>
                                            <td>${lead.preferred_date || 'Not specified'}</td>
                                        </tr>
                                        <tr>
                                            <th>Status:</th>
                                            <td><span class="badge ${getStatusBadgeClass(lead.status)}">${lead.status}</span></td>
                                        </tr>
                                        <tr>
                                            <th>Created:</th>
                                            <td>${lead.created_at}</td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-12">
                                    <h5>Message</h5>
                                    <div class="p-3 bg-darker rounded">
                                        ${lead.message || 'No message provided'}
                                    </div>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-12">
                                    <h5>Actions</h5>
                                    <div class="btn-group" role="group">
                                        <a href="/lead/${lead.id}/contact" class="btn btn-outline-primary">Send Message</a>
                                        <button type="button" class="btn btn-outline-success lead-status-update" data-lead-id="${lead.id}" data-status="scheduled">Schedule Appointment</button>
                                        <button type="button" class="btn btn-outline-warning lead-status-update" data-lead-id="${lead.id}" data-status="contacted">Mark as Contacted</button>
                                    </div>
                                </div>
                            </div>
                        `;
                        
                        // Add event listeners to the newly created buttons
                        attachStatusUpdateButtonListeners();
                    } else {
                        detailsContent.innerHTML = `
                            <div class="alert alert-danger">
                                ${data.message || 'Failed to load lead details. Please try again.'}
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    detailsContent.innerHTML = `
                        <div class="alert alert-danger">
                            Failed to load lead details. Please try again.
                        </div>
                    `;
                });
            });
        });
    }
    
    // Helper function to get appropriate badge class for status
    function getStatusBadgeClass(status) {
        switch(status) {
            case 'pending': return 'bg-warning';
            case 'contacted': return 'bg-info';
            case 'scheduled': return 'bg-primary';
            case 'completed': return 'bg-success';
            case 'rejected': return 'bg-danger';
            default: return 'bg-secondary';
        }
    }
    
    // Attach event listeners to status update buttons in modal
    function attachStatusUpdateButtonListeners() {
        document.querySelectorAll('.lead-status-update').forEach(button => {
            button.addEventListener('click', function() {
                const leadId = this.getAttribute('data-lead-id');
                const status = this.getAttribute('data-status');
                
                // Get CSRF token from a hidden form or meta tag
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || 
                                  document.querySelector('input[name="csrf_token"]')?.value;
                
                if (!csrfToken) {
                    alert('CSRF token not found. Cannot update status.');
                    return;
                }
                
                // Create form data for submission
                const formData = new FormData();
                formData.append('csrf_token', csrfToken);
                formData.append('status', status);
                
                // Submit the update
                fetch(`/lead/${leadId}/update_status`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Lead status updated successfully!');
                        // Close modal if it exists
                        if (window.bootstrap && document.getElementById('leadDetailsModal')) {
                            const modal = bootstrap.Modal.getInstance(document.getElementById('leadDetailsModal'));
                            if (modal) modal.hide();
                        }
                        window.location.reload();
                    } else {
                        alert('Error: ' + (data.message || 'Failed to update lead status'));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while updating the lead status.');
                });
            });
        });
    }
    
    // Initialize the page
    setupLeadActionButtons();
});