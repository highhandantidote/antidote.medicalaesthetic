// Show More Doctors Functionality - Standalone
console.log('Show More Doctors script loaded');

// Wait for DOM to be ready and other scripts to finish
document.addEventListener('DOMContentLoaded', function() {
    // Add a small delay to ensure other scripts have finished
    setTimeout(function() {
        console.log('Initializing Show More Doctors functionality');
        
        const showMoreBtn = document.getElementById('showMoreDoctors');
        const loadingDiv = document.getElementById('loadingMoreDoctors');
        const doctorsList = document.getElementById('doctorList');
        
        console.log('Show More button element:', showMoreBtn);
        console.log('Loading div element:', loadingDiv);
        console.log('Doctors list element:', doctorsList);

        if (!showMoreBtn) {
            console.error('Show More button not found');
            return;
        }

        // Get initial offset from the button's data attribute or calculate it
        let currentOffset = 20; // Default to 20 since we show 20 initially
        const showingCountElement = document.getElementById('showingDoctorsCount');
        if (showingCountElement) {
            currentOffset = parseInt(showingCountElement.textContent) || 20;
        }
        
        console.log('Current offset:', currentOffset);
        console.log('Setting up click handler for Show More button');
        
        showMoreBtn.addEventListener('click', function(event) {
            event.preventDefault();
            console.log('Show More button clicked - starting request');
            
            // Hide button and show loading
            showMoreBtn.style.display = 'none';
            if (loadingDiv) {
                loadingDiv.style.display = 'block';
            }

            // Build request URL
            const params = new URLSearchParams();
            params.append('offset', currentOffset);
            params.append('limit', 20);
            params.append('sort_by', 'experience_desc');
            
            // Add any URL parameters
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('location')) {
                params.append('location', urlParams.get('location'));
            }
            if (urlParams.get('specialty')) {
                params.append('specialty', urlParams.get('specialty'));
            }

            const requestUrl = '/api/doctors/load-more?' + params.toString();
            console.log('Making request to:', requestUrl);

            // Make the request
            fetch(requestUrl, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            })
            .then(function(response) {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                console.log('Response data:', data);
                if (data.success && data.doctors) {
                    console.log('Adding', data.doctors.length, 'new doctors');
                    
                    // Add new doctors to the list
                    data.doctors.forEach(function(doctor) {
                        const doctorHTML = createDoctorCard(doctor);
                        console.log('Generated doctor HTML:', doctorHTML.substring(0, 200) + '...');
                        console.log('Doctor URL should be: /doctors/detail/' + doctor.id);
                        if (doctorsList) {
                            doctorsList.insertAdjacentHTML('beforeend', doctorHTML);
                            // Debug: Check if the URL got modified
                            const lastCard = doctorsList.lastElementChild;
                            if (lastCard) {
                                const link = lastCard.querySelector('a');
                                console.log('Actual inserted URL:', link ? link.href : 'No link found');
                            }
                        }
                    });

                    // Update counts
                    currentOffset += data.doctors.length;
                    const countElement = document.getElementById('showingDoctorsCount');
                    if (countElement) {
                        countElement.textContent = currentOffset;
                    }

                    // Show or hide button
                    if (data.has_more) {
                        showMoreBtn.style.display = 'block';
                        const badge = showMoreBtn.querySelector('.badge');
                        if (badge) {
                            const remaining = data.total_count - currentOffset;
                            badge.textContent = remaining + ' more';
                        }
                    } else {
                        showMoreBtn.style.display = 'none';
                    }
                } else {
                    console.error('API returned error:', data.message || 'Unknown error');
                    showMoreBtn.style.display = 'block';
                }
            })
            .catch(function(error) {
                console.error('Request failed:', error);
                showMoreBtn.style.display = 'block';
            })
            .finally(function() {
                if (loadingDiv) {
                    loadingDiv.style.display = 'none';
                }
            });
        });

        console.log('Show More functionality initialized successfully');
    }, 500); // 500ms delay to let other scripts finish
});

// Create doctor card function - matches the exact original template design
function createDoctorCard(doctor) {
    // Doctor image - exactly like original template
    let imageHtml = '';
    if (doctor.profile_image) {
        imageHtml = '<img src="' + doctor.profile_image + '" class="rounded-circle border" style="width: 70px; height: 70px; object-fit: cover;" alt="Dr. ' + doctor.name + '">';
    } else {
        imageHtml = '<div class="rounded-circle bg-light d-flex align-items-center justify-content-center" style="width: 70px; height: 70px;">' +
                    '<i class="fas fa-user-md text-muted" style="font-size: 1.8rem;"></i>' +
                    '</div>';
    }
    
    // Verified badge - exactly like original
    let verifiedBadge = '';
    if (doctor.is_verified) {
        verifiedBadge = '<span class="badge bg-success bg-opacity-10 text-success small">' +
                       '<i class="fas fa-check-circle"></i> Verified' +
                       '</span>';
    }
    
    // Build the card exactly like the original template - EXACT MATCH  
    console.log('Creating card for doctor ID:', doctor.id, 'URL will be: /doctors/detail/' + doctor.id);
    return '<div class="doctor-card" data-location="' + (doctor.city || '') + '" data-specialty="' + (doctor.specialty || '') + '">' +
           '<a href="/doctors/detail/' + doctor.id + '" class="text-decoration-none">' +
           '<div class="card shadow-sm border-0 hover-shadow">' +
           '<div class="card-body p-3">' +
           '<div class="row align-items-center">' +
           
           '<!-- Doctor Image -->' +
           '<div class="col-auto">' +
           imageHtml +
           '</div>' +
           
           '<!-- Doctor Info -->' +
           '<div class="col">' +
           '<div class="d-flex align-items-center mb-1">' +
           '<h5 class="mb-0 me-2">Dr. ' + doctor.name + '</h5>' +
           verifiedBadge +
           '</div>' +
           
           '<p class="text-muted mb-1">' + (doctor.specialty || 'Plastic Surgeon') + '</p>' +
           '<p class="text-muted small mb-2">' + (doctor.qualification || 'MBBS, MS, MCh') + '</p>' +
           
           '<div class="row">' +
           '<div class="col-sm-6 col-12">' +
           '<div class="d-flex align-items-center text-muted small mb-1">' +
           '<i class="fas fa-map-marker-alt text-danger me-2"></i>' +
           '<span>' + (doctor.city || 'Available') + (doctor.state ? ', ' + doctor.state : '') + '</span>' +
           '</div>' +
           '</div>' +
           '<div class="col-sm-6 col-12">' +
           '<div class="d-flex align-items-center text-muted small mb-1">' +
           '<i class="fas fa-briefcase text-primary me-2"></i>' +
           '<span>' + (doctor.experience || 10) + ' years experience</span>' +
           '</div>' +
           '</div>' +
           '</div>' +
           '</div>' +
           
           '<!-- Click indicator -->' +
           '<div class="col-auto">' +
           '<i class="fas fa-chevron-right text-muted"></i>' +
           '</div>' +
           '</div>' +
           '</div>' +
           '</div>' +
           '</a>' +
           '</div>';
}