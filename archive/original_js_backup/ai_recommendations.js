/**
 * AI Recommendation System JavaScript
 * Handles the AI recommendation form submission and UI interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // AI Recommendation Form handling
    const aiForm = document.getElementById('ai-recommendation-form');
    if (!aiForm) return; // Exit if form doesn't exist
    
    const uploadImageBtn = document.getElementById('upload-image-btn');
    const imageInput = document.getElementById('image-input');
    const imagePreview = document.getElementById('image-preview');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const removeImageBtn = document.getElementById('remove-image-btn');
    const recordAudioBtn = document.getElementById('record-audio-btn');
    
    // Handle image upload
    if (uploadImageBtn && imageInput) {
        uploadImageBtn.addEventListener('click', function() {
            imageInput.click();
        });
        
        imageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreviewContainer.classList.remove('d-none');
                }
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
    
    // Handle remove image button
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function() {
            imageInput.value = '';
            imagePreviewContainer.classList.add('d-none');
        });
    }
    
    // Handle record audio redirection
    if (recordAudioBtn) {
        recordAudioBtn.addEventListener('click', function() {
            const recommendationFormUrl = document.querySelector('meta[name="recommendation-form-url"]').getAttribute('content');
            window.location.href = recommendationFormUrl;
        });
    }
    
    // Handle form submission
    aiForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Create form data to submit
        const formData = new FormData();
        
        // Add text query
        const queryText = document.getElementById('query_text').value;
        if (queryText) {
            formData.append('query_text', queryText);
        }
        
        // Add image if selected
        if (imageInput && imageInput.files && imageInput.files[0]) {
            formData.append('image', imageInput.files[0]);
        }
        
        // If no text and no image, redirect to full form
        if (!queryText && (!imageInput || !imageInput.files || !imageInput.files[0])) {
            const recommendationFormUrl = document.querySelector('meta[name="recommendation-form-url"]').getAttribute('content');
            window.location.href = recommendationFormUrl;
            return;
        }
        
        // Show loading state on submit button
        const submitBtn = aiForm.querySelector('button[type="submit"]');
        const originalBtnHtml = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        submitBtn.disabled = true;
        
        // Get the API URL from meta tag
        const analyzeQueryUrl = document.querySelector('meta[name="analyze-query-url"]').getAttribute('content');
        
        // Submit form via AJAX
        fetch(analyzeQueryUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Reset button
            submitBtn.innerHTML = originalBtnHtml;
            submitBtn.disabled = false;
            
            if (data.success) {
                // Store data in localStorage to be retrieved on the results page
                localStorage.setItem('ai_recommendation_results', JSON.stringify(data));
                
                // Redirect to results page
                const recommendationResultsUrl = document.querySelector('meta[name="recommendation-results-url"]').getAttribute('content');
                window.location.href = recommendationResultsUrl;
            } else {
                alert('Error: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            submitBtn.innerHTML = originalBtnHtml;
            submitBtn.disabled = false;
            alert('An error occurred. Please try again or use the full form.');
        });
    });
});