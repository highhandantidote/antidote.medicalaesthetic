document.addEventListener('DOMContentLoaded', function() {
    // Elements for "Add Another Concern" functionality
    const addAnotherConcernBtn = document.getElementById('addAnotherConcern');
    const additionalConcernsContainer = document.getElementById('additionalConcerns');
    
    // Elements for image upload
    const imageUploadBtn = document.getElementById('imageUploadBtn');
    const imageUploadInput = document.getElementById('imageUploadInput');
    const imageFileName = document.getElementById('imageFileName');
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');
    const imagePreview = document.getElementById('imagePreview');
    
    // Elements for audio recording
    const recordAudioBtn = document.getElementById('recordAudioBtn');
    const audioRecordingStatus = document.getElementById('audioRecordingStatus');
    const stopRecordingBtn = document.getElementById('stopRecordingBtn');
    const audioPlayback = document.getElementById('audioPlayback');
    const audioData = document.getElementById('audioData');
    
    let concernCounter = 1;
    let mediaRecorder;
    let audioChunks = [];
    
    // Add Another Concern functionality
    if (addAnotherConcernBtn && additionalConcernsContainer) {
        addAnotherConcernBtn.addEventListener('click', function() {
            concernCounter++;
            
            const concernDiv = document.createElement('div');
            concernDiv.className = 'mb-3 additional-concern';
            concernDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <label for="query_text_${concernCounter}" class="form-label fw-bold">Additional Concern</label>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-concern">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <textarea class="form-control" id="query_text_${concernCounter}" 
                    name="additional_concern_${concernCounter}" rows="3"></textarea>
            `;
            
            additionalConcernsContainer.appendChild(concernDiv);
            
            // Add event listener to remove button
            const removeBtn = concernDiv.querySelector('.remove-concern');
            removeBtn.addEventListener('click', function() {
                concernDiv.remove();
            });
        });
    }
    
    // Image upload functionality
    if (imageUploadBtn && imageUploadInput) {
        imageUploadBtn.addEventListener('click', function() {
            imageUploadInput.click();
            // Add subtle animation
            this.classList.add('pulse-animation');
            setTimeout(() => {
                this.classList.remove('pulse-animation');
            }, 500);
        });
        
        imageUploadInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                imageFileName.textContent = file.name;
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreviewContainer.classList.remove('d-none');
                    
                    // Animate the image appearance
                    imagePreviewContainer.style.opacity = '0';
                    imagePreviewContainer.style.transform = 'translateY(10px)';
                    setTimeout(() => {
                        imagePreviewContainer.style.transition = 'all 0.3s ease';
                        imagePreviewContainer.style.opacity = '1';
                        imagePreviewContainer.style.transform = 'translateY(0)';
                    }, 10);
                };
                reader.readAsDataURL(file);
            } else {
                imageFileName.textContent = 'No file chosen';
                imagePreviewContainer.classList.add('d-none');
            }
        });
        
        // Add image removal functionality
        const removeImageBtn = document.getElementById('removeImageBtn');
        if (removeImageBtn) {
            removeImageBtn.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Animate the image removal
                imagePreviewContainer.style.opacity = '0';
                imagePreviewContainer.style.transform = 'translateY(10px)';
                
                setTimeout(() => {
                    imagePreviewContainer.classList.add('d-none');
                    imageUploadInput.value = '';
                    imageFileName.textContent = 'No file chosen';
                }, 300);
            });
        }
    }
    
    // Audio recording functionality
    if (recordAudioBtn && stopRecordingBtn) {
        recordAudioBtn.addEventListener('click', startRecording);
        stopRecordingBtn.addEventListener('click', stopRecording);
    }
    
    function startRecording() {
        audioChunks = [];
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                audioRecordingStatus.classList.remove('d-none');
                recordAudioBtn.classList.add('disabled');
                
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = (e) => {
                    audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = processRecording;
                mediaRecorder.start();
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                alert('Could not access your microphone. Please check permissions and try again.');
            });
    }
    
    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            recordAudioBtn.classList.remove('disabled');
            audioRecordingStatus.classList.add('d-none');
        }
    }
    
    function processRecording() {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const audioUrl = URL.createObjectURL(audioBlob);
        audioPlayback.src = audioUrl;
        audioPlayback.classList.remove('d-none');
        
        // Convert to base64 for form submission
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = function() {
            const base64data = reader.result;
            audioData.value = base64data;
        };
    }
    
    // Add CSS for recording indicator
    const style = document.createElement('style');
    style.textContent = `
        .recording-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            background-color: #dc3545;
            border-radius: 50%;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.4; }
            100% { opacity: 1; }
        }
    `;
    document.head.appendChild(style);
});