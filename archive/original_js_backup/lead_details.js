document.addEventListener('DOMContentLoaded', function() {
    console.log("Lead Details JS loaded");
    
    // Check if we're on a lead detail page
    const leadDetailPage = document.querySelector('.lead-detail-page');
    if (!leadDetailPage) {
        console.log("Not on lead detail page");
        return;
    }
    
    // Get the lead ID
    const leadId = leadDetailPage.dataset.leadId;
    if (!leadId) {
        console.error("No lead ID found");
        return;
    }
    
    console.log(`Lead detail page loaded for lead ID: ${leadId}`);
    
    // Handle schedule appointment form
    const scheduleForm = document.getElementById('schedule-form');
    if (scheduleForm) {
        const submitBtn = document.getElementById('schedule-submit-btn');
        
        submitBtn.addEventListener('click', function() {
            console.log("Schedule appointment button clicked");
            
            const appointmentDateInput = scheduleForm.querySelector('#appointment_date');
            if (!appointmentDateInput.value) {
                alert('Please select an appointment date and time.');
                return;
            }
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Scheduling...';
            
            const formData = new FormData(scheduleForm);
            
            fetch(`/lead/${leadId}/update_status`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log("Schedule appointment response:", data);
                
                if (data.success) {
                    alert('Appointment scheduled successfully!');
                    window.location.reload();
                } else {
                    alert('Error: ' + (data.message || 'Failed to schedule appointment. Please try again.'));
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Schedule Appointment';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while scheduling the appointment. Please try again.');
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Schedule Appointment';
            });
        });
    }
    
    // Handle reschedule appointment form
    const rescheduleForm = document.getElementById('reschedule-form');
    if (rescheduleForm) {
        const submitBtn = document.getElementById('reschedule-submit-btn');
        
        submitBtn.addEventListener('click', function() {
            console.log("Reschedule appointment button clicked");
            
            const appointmentDateInput = rescheduleForm.querySelector('#new_appointment_date');
            if (!appointmentDateInput.value) {
                alert('Please select a new appointment date and time.');
                return;
            }
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Rescheduling...';
            
            const formData = new FormData(rescheduleForm);
            
            fetch(`/lead/${leadId}/update_status`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log("Reschedule appointment response:", data);
                
                if (data.success) {
                    alert('Appointment rescheduled successfully!');
                    window.location.reload();
                } else {
                    alert('Error: ' + (data.message || 'Failed to reschedule appointment. Please try again.'));
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Reschedule Appointment';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while rescheduling the appointment. Please try again.');
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Reschedule Appointment';
            });
        });
    }
    
    // Add click event listeners to all action buttons
    document.querySelectorAll('a.btn, button.btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const action = this.dataset.action;
            
            // Skip if this is not an action button or if it's a submit button in a form
            if (!action || this.type === 'submit') return;
            
            console.log(`Button clicked: ${action}`);
            
            // Let the default action happen for navigation buttons
            if (action === 'back') return;
            
            // Handle AJAX actions
            e.preventDefault();
            
            if (action === 'contact') {
                window.location.href = `/lead/${leadId}/contact`;
            } else if (action === 'update_status') {
                window.location.href = `/lead/${leadId}/update_status`;
            } else if (action === 'schedule') {
                const scheduleModal = new bootstrap.Modal(document.getElementById('scheduleModal'));
                scheduleModal.show();
            } else if (action === 'reschedule') {
                const rescheduleModal = new bootstrap.Modal(document.getElementById('rescheduleModal'));
                rescheduleModal.show();
            }
        });
    });
});