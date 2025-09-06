document.addEventListener('DOMContentLoaded', function() {
    console.log("Appointments.js loaded");
    
    // Add event handlers for appointment action buttons
    function setupAppointmentActions() {
        // Find all appointment action forms
        const actionForms = document.querySelectorAll('.appointment-action-form');
        console.log(`Found ${actionForms.length} appointment action forms`);
        
        actionForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Extract action and appointment ID from the form action URL
                const actionUrl = form.getAttribute('action');
                const action = actionUrl.split('action=')[1].split('&')[0];
                const appointmentId = actionUrl.split('id=')[1];
                
                console.log(`Processing appointment action: ${action} for appointment ${appointmentId}`);
                
                // For cancel action, confirm first
                if (action === 'cancel' && !confirm('Are you sure you want to cancel this appointment?')) {
                    return;
                }
                
                // Get CSRF token
                const csrfToken = form.querySelector('input[name="csrf_token"]').value;
                
                // Submit the form with fetch API
                fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: new URLSearchParams({
                        'csrf_token': csrfToken
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // Show success message
                        alert(data.message || `Appointment ${action} successfully`);
                        // Reload the page to reflect changes
                        window.location.reload();
                    } else {
                        // Show error message
                        alert(data.message || `Failed to ${action} appointment`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(`There was a problem with the ${action} action. Please try again.`);
                });
            });
        });
    }
    
    // Initialize the page
    setupAppointmentActions();
});