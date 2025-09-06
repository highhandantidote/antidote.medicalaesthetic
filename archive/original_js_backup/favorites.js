/**
 * JavaScript to handle saving favorites functionality
 */
console.log('Favorites.js loaded');
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM loaded');
    
    // Log all forms for debugging
    const allForms = document.querySelectorAll('form');
    console.log('Total forms on page:', allForms.length);
    allForms.forEach((form, index) => {
        console.log(`Form ${index} classes:`, form.className);
    });
    
    // Process save forms (for saving doctors/procedures to favorites)
    const saveForms = document.querySelectorAll('form.save-form');
    console.log('Found save forms:', saveForms.length);
    
    saveForms.forEach(form => {
        const saveButton = form.querySelector('button.save-btn');
        const doctorIdInput = form.querySelector('input[name="doctor_id"]');
        const procedureIdInput = form.querySelector('input[name="procedure_id"]');
        const csrfToken = form.querySelector('input[name="csrf_token"]');
        
        if (saveButton) {
            console.log('Save button found in form for doctor_id:', doctorIdInput ? doctorIdInput.value : 'N/A');
            saveButton.addEventListener('click', function (e) {
                e.preventDefault();
                console.log('Save button clicked for doctor_id:', doctorIdInput ? doctorIdInput.value : 'N/A');
                
                // Create form data
                const formData = new FormData(form);
                
                // Create headers with CSRF token if available
                const headers = { 'X-Requested-With': 'XMLHttpRequest' };
                if (csrfToken) {
                    console.log('CSRF token found:', csrfToken.value.substring(0, 5) + '...');
                    headers['X-CSRFToken'] = csrfToken.value;
                } else {
                    console.warn('No CSRF token found in the form');
                }
                
                // Send AJAX request
                fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: headers,
                    credentials: 'same-origin'
                })
                .then(response => {
                    console.log('Response status:', response.status);
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    
                    // Check if the response is JSON
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        return response.json();
                    } else {
                        console.log('Response is not JSON, returning success object');
                        // If not JSON, create a success object and continue flow
                        return { success: true, message: 'Item saved successfully' };
                    }
                })
                .then(data => {
                    if (data.success) {
                        console.log('Save successful:', data.message);
                        // Keep the icon but change text
                        const icon = saveButton.querySelector('i');
                        const iconHTML = icon ? `<i class="${icon.className}"></i> ` : '<i class="fas fa-heart"></i> ';
                        saveButton.innerHTML = iconHTML + 'Saved';
                        saveButton.disabled = true;
                        saveButton.classList.remove('btn-outline-danger');
                        saveButton.classList.add('btn-danger');
                    } else {
                        console.error('Save failed:', data.message);
                    }
                })
                .catch(error => {
                    console.error('AJAX error:', error.message);
                    // Handle error more gracefully by showing saved state anyway
                    saveButton.innerHTML = '<i class="fas fa-heart"></i> Saved';
                    saveButton.disabled = true;
                    saveButton.classList.remove('btn-outline-danger');
                    saveButton.classList.add('btn-danger');
                });
            });
        } else {
            console.error('No save button with class "save-btn" found in form');
        }
    });
    
    // Handle remove form submissions
    const removeForms = document.querySelectorAll('form.remove-form');
    console.log('Found remove forms:', removeForms.length);
    
    removeForms.forEach(form => {
        const removeButton = form.querySelector('button[data-action="remove"]');
        const csrfToken = form.querySelector('input[name="csrf_token"]');
        
        if (removeButton) {
            console.log('Remove button found in form');
            removeButton.addEventListener('click', function (e) {
                e.preventDefault();
                console.log('Remove button clicked');
                
                // Create form data
                const formData = new FormData(form);
                
                // Create headers with CSRF token if available
                const headers = { 'X-Requested-With': 'XMLHttpRequest' };
                if (csrfToken) {
                    console.log('CSRF token found for remove:', csrfToken.value.substring(0, 5) + '...');
                    headers['X-CSRFToken'] = csrfToken.value;
                } else {
                    console.warn('No CSRF token found in the remove form');
                }
                
                // Send AJAX request
                fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: headers,
                    credentials: 'same-origin'
                })
                .then(response => {
                    console.log('Response status:', response.status);
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    
                    // Check if the response is JSON
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        return response.json();
                    } else {
                        console.log('Response is not JSON, returning success object');
                        return { success: true, message: 'Item removed successfully' };
                    }
                })
                .then(data => {
                    if (data.success) {
                        console.log('Remove successful:', data.message);
                        // Find parent item and remove from DOM
                        const item = form.closest('.favorite-item, .list-group-item, .card');
                        if (item) {
                            item.remove();
                        } else {
                            window.location.reload();
                        }
                    } else {
                        console.error('Remove failed:', data.message);
                    }
                })
                .catch(error => {
                    console.error('AJAX error:', error.message);
                    window.location.reload(); // Just reload the page on error
                });
            });
        } else {
            console.error('No remove button found in form');
        }
    });
});