/**
 * Enhanced Lead Modal with Session-Based Verification Cache
 * Handles Firebase OTP verification with session caching to avoid repeated OTP requests
 */

// Prevent multiple script declarations with unique global check
if (typeof window.leadModalDataInitialized === 'undefined') {
    window.leadModalDataInitialized = true;
    window.leadModalData = {};
    window.verificationConfirmationResult = null;
} else {
    // Script already loaded, exit early to prevent conflicts
    console.log('Enhanced lead modal already initialized, skipping duplicate load');
    // Don't define anything else to prevent conflicts
}

// Only proceed if this is the first load
if (typeof window.leadModalDataInitialized !== 'undefined' && window.leadModalDataInitialized === true) {

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already logged in and pre-fill data
    initializeUserSession();
    
    // Check for existing verification when phone number changes
    const phoneInput = document.getElementById('contactPhone');
    if (phoneInput) {
        phoneInput.addEventListener('blur', checkExistingVerification);
        phoneInput.addEventListener('input', debounce(checkExistingVerification, 500));
    }
});

/**
 * Initialize user session and pre-fill form if logged in
 */
function initializeUserSession() {
    if (window.currentUserData && window.currentUserData.isAuthenticated) {
        console.log('User is logged in:', window.currentUserData);
        
        // Pre-fill form with user data
        const nameInput = document.getElementById('contactName');
        const phoneInput = document.getElementById('contactPhone');
        const emailInput = document.getElementById('contactEmail');
        
        if (nameInput && window.currentUserData.name) {
            nameInput.value = window.currentUserData.name;
            nameInput.readOnly = true;
            nameInput.style.backgroundColor = '#f8f9fa';
        }
        
        if (phoneInput && window.currentUserData.phone) {
            phoneInput.value = window.currentUserData.phone;
            phoneInput.readOnly = true;
            phoneInput.style.backgroundColor = '#f8f9fa';
        }
        
        if (emailInput && window.currentUserData.email) {
            emailInput.value = window.currentUserData.email;
        }
        
        // Update submit button for logged-in users
        const submitBtn = document.getElementById('submitContactBtn');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i>Continue as ' + (window.currentUserData.name || 'Verified User');
            submitBtn.classList.remove('btn-primary');
            submitBtn.classList.add('btn-success');
        }
        
        // Show logged-in status
        showLoggedInStatus();
    }
}

/**
 * Check if phone number is already verified in session
 */
async function checkExistingVerification() {
    const phoneInput = document.getElementById('contactPhone');
    const phone = phoneInput?.value?.trim();
    
    if (!phone || phone.length < 10) {
        return;
    }
    
    try {
        const response = await fetch('/api/leads/check-verification', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
            },
            body: JSON.stringify({ phone: phone })
        });
        
        const result = await response.json();
        
        if (result.success && result.verified) {
            showVerifiedPhoneStatus(result.user_data);
        } else {
            hideVerifiedPhoneStatus();
        }
        
    } catch (error) {
        console.error('Error checking phone verification:', error);
        hideVerifiedPhoneStatus();
    }
}

/**
 * Show verified phone status in the form
 */
function showVerifiedPhoneStatus(userData) {
    // Pre-fill form with verified data
    if (userData.name) {
        document.getElementById('contactName').value = userData.name;
    }
    if (userData.email) {
        document.getElementById('contactEmail').value = userData.email;
    }
    
    // Update submit button text
    const submitBtn = document.getElementById('submitContactBtn');
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i>Continue with Verified Number';
        submitBtn.classList.remove('btn-primary');
        submitBtn.classList.add('btn-success');
    }
    
    // Show verification status
    showVerificationBadge();
}

/**
 * Show logged-in user status
 */
function showLoggedInStatus() {
    // Add logged-in indicator to form
    const formContainer = document.getElementById('contact-form');
    if (formContainer) {
        const statusBadge = document.createElement('div');
        statusBadge.className = 'alert alert-info mb-3';
        statusBadge.innerHTML = '<i class="fas fa-user-check me-2"></i>You are logged in - no phone verification needed!';
        formContainer.insertBefore(statusBadge, formContainer.firstChild);
    }
}

/**
 * Hide verified phone status
 */
function hideVerifiedPhoneStatus() {
    const submitBtn = document.getElementById('submitContactBtn');
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-mobile-alt me-2"></i>Send OTP & Continue';
        submitBtn.classList.remove('btn-success');
        submitBtn.classList.add('btn-primary');
    }
    
    hideVerificationBadge();
}

/**
 * Show verification badge
 */
function showVerificationBadge() {
    // Remove existing badge
    hideVerificationBadge();
    
    const phoneInput = document.getElementById('contactPhone');
    if (phoneInput) {
        const badge = document.createElement('div');
        badge.id = 'verificationBadge';
        badge.className = 'text-success mt-1';
        badge.innerHTML = '<i class="fas fa-check-circle me-1"></i>Phone number verified';
        phoneInput.parentNode.appendChild(badge);
    }
}

/**
 * Hide verification badge
 */
function hideVerificationBadge() {
    const badge = document.getElementById('verificationBadge');
    if (badge) {
        badge.remove();
    }
}

/**
 * Submit contact form - either start OTP process or use verified number
 */
async function submitContactForm() {
    const name = document.getElementById('contactName')?.value?.trim();
    const phone = document.getElementById('contactPhone')?.value?.trim();
    const email = document.getElementById('contactEmail')?.value?.trim();
    const message = document.getElementById('contactMessage')?.value?.trim();
    
    if (!name || !phone) {
        showModalError('Please fill in all required fields');
        return;
    }
    
    // Store form data
    leadModalData = {
        name: name,
        phone: phone,
        email: email,
        message: message,
        source_type: window.enhancedLeadModalData?.source_type || 'package',
        source_id: window.enhancedLeadModalData?.source_id || '',
        contact_intent: window.enhancedLeadModalData?.contact_intent || 'whatsapp'
    };
    
    // Check if user is logged in - skip OTP verification
    if (window.currentUserData && window.currentUserData.isAuthenticated) {
        console.log('User is logged in - creating lead directly');
        await createAuthenticatedLead();
        return;
    }
    
    // Check if phone is already verified
    try {
        const response = await fetch('/api/leads/check-verification', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
            },
            body: JSON.stringify({ phone: phone })
        });
        
        const result = await response.json();
        
        if (result.success && result.verified) {
            // Skip OTP - create lead directly with verified number
            await createVerifiedLead();
        } else {
            // Start Firebase OTP process
            await startFirebaseOTP();
        }
        
    } catch (error) {
        console.error('Error checking verification:', error);
        // Fallback to OTP process
        await startFirebaseOTP();
    }
}

/**
 * Create lead for authenticated users - no OTP required
 */
async function createAuthenticatedLead() {
    try {
        showModalLoading('Creating your request...');
        
        const response = await fetch('/api/leads/create-authenticated-lead', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
            },
            body: JSON.stringify(leadModalData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessStep(result);
        } else {
            showModalError(result.message || 'Failed to create lead');
        }
        
    } catch (error) {
        console.error('Error creating authenticated lead:', error);
        showModalError('Network error. Please try again.');
    } finally {
        hideModalLoading();
    }
}

/**
 * Create lead using already verified phone number
 */
async function createVerifiedLead() {
    try {
        showModalLoading('Creating your request...');
        
        const response = await fetch('/api/leads/create-verified-lead', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
            },
            body: JSON.stringify(leadModalData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessStep(result);
        } else {
            if (result.message.includes('verification expired')) {
                // Verification expired, start OTP process
                showModalError('Phone verification expired. Please verify again.');
                setTimeout(startFirebaseOTP, 2000);
            } else {
                showModalError(result.message || 'Failed to create lead');
            }
        }
        
    } catch (error) {
        console.error('Error creating verified lead:', error);
        showModalError('Network error. Please try again.');
    } finally {
        hideModalLoading();
    }
}

/**
 * Start Firebase OTP verification process
 */
async function startFirebaseOTP() {
    try {
        showModalLoading('Sending OTP...');
        
        // Initialize Firebase if not already done
        if (typeof firebase === 'undefined' || !firebase.apps.length) {
            showModalError('SMS service is temporarily unavailable. Please try again later.');
            return;
        }
        
        const phoneNumber = leadModalData.phone;
        const appVerifier = window.recaptchaVerifier;
        
        if (!appVerifier) {
            showModalError('Security verification failed. Please refresh and try again.');
            return;
        }
        
        const auth = firebase.auth();
        verificationConfirmationResult = await auth.signInWithPhoneNumber(phoneNumber, appVerifier);
        
        // Show OTP step
        showOTPStep();
        
    } catch (error) {
        console.error('Firebase OTP error:', error);
        
        if (error.code === 'auth/too-many-requests') {
            showModalError('Too many OTP requests. Please wait a few minutes and try again.');
        } else if (error.code === 'auth/invalid-phone-number') {
            showModalError('Invalid phone number format. Please enter a valid number.');
        } else {
            showModalError('Failed to send OTP. Please try again.');
        }
        
        // Reset reCAPTCHA
        if (window.recaptchaVerifier) {
            window.recaptchaVerifier.clear();
        }
    } finally {
        hideModalLoading();
    }
}

/**
 * Verify OTP and create lead
 */
async function verifyOtp() {
    const otpCode = document.getElementById('otpCode')?.value?.trim();
    
    if (!otpCode || otpCode.length !== 6) {
        showModalError('Please enter a valid 6-digit OTP');
        return;
    }
    
    try {
        showModalLoading('Verifying OTP...');
        
        if (!verificationConfirmationResult) {
            showModalError('Verification session expired. Please try again.');
            return;
        }
        
        // Verify OTP with Firebase
        const result = await verificationConfirmationResult.confirm(otpCode);
        const user = result.user;
        
        // Add Firebase UID to data
        leadModalData.firebase_uid = user.uid;
        
        // Create verified lead via backend
        const response = await fetch('/api/leads/verify-phone', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
            },
            body: JSON.stringify(leadModalData)
        });
        
        const leadResult = await response.json();
        
        if (leadResult.success) {
            showSuccessStep(leadResult);
        } else {
            showModalError(leadResult.message || 'Failed to create lead');
        }
        
    } catch (error) {
        console.error('OTP verification error:', error);
        
        if (error.code === 'auth/invalid-verification-code') {
            showModalError('Invalid OTP code. Please check and try again.');
        } else if (error.code === 'auth/code-expired') {
            showModalError('OTP has expired. Please request a new one.');
        } else {
            showModalError('OTP verification failed. Please try again.');
        }
    } finally {
        hideModalLoading();
    }
}

/**
 * Show OTP verification step
 */
function showOTPStep() {
    // Update progress
    updateProgress(2);
    
    // Hide contact form, show OTP form
    document.getElementById('contact-form').style.display = 'none';
    document.getElementById('otp-verification').style.display = 'block';
    
    // Update phone display
    document.getElementById('otpPhoneDisplay').textContent = leadModalData.phone;
    
    // Focus on OTP input
    setTimeout(() => {
        document.getElementById('otpCode')?.focus();
    }, 100);
}

/**
 * Show success step with contact options
 */
function showSuccessStep(result) {
    // Update progress
    updateProgress(3);
    
    // Hide previous steps
    document.getElementById('contact-form').style.display = 'none';
    document.getElementById('otp-verification').style.display = 'none';
    
    // Show success step
    document.getElementById('success-message').style.display = 'block';
    
    // Update clinic name
    document.getElementById('successClinicName').textContent = result.clinic_name;
    
    // Setup contact buttons
    if (result.contact_url) {
        if (result.contact_intent === 'whatsapp') {
            const whatsappBtn = document.getElementById('successWhatsappBtn');
            whatsappBtn.href = result.contact_url;
            whatsappBtn.style.display = 'block';
        } else if (result.contact_intent === 'call') {
            const callBtn = document.getElementById('successCallBtn');
            callBtn.href = result.contact_url;
            callBtn.style.display = 'block';
        }
    }
}

/**
 * Update progress indicators
 */
function updateProgress(step) {
    // Remove all active/completed classes
    document.querySelectorAll('.step-indicator').forEach(indicator => {
        indicator.classList.remove('active', 'completed');
    });
    
    // Mark completed steps
    for (let i = 1; i < step; i++) {
        const indicator = document.querySelector(`[data-step="${i}"]`);
        if (indicator) indicator.classList.add('completed');
    }
    
    // Mark current active step
    const activeIndicator = document.querySelector(`[data-step="${step}"]`);
    if (activeIndicator) activeIndicator.classList.add('active');
}

/**
 * Show modal error message
 */
function showModalError(message) {
    const errorDiv = document.getElementById('leadModalError');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        // Hide after 5 seconds
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
}

/**
 * Show modal loading state
 */
function showModalLoading(message) {
    // Disable all buttons
    document.querySelectorAll('#enhancedLeadModal button').forEach(btn => {
        btn.disabled = true;
    });
    
    // Show loading message
    showModalError(message);
}

/**
 * Hide modal loading state
 */
function hideModalLoading() {
    // Re-enable all buttons
    document.querySelectorAll('#enhancedLeadModal button').forEach(btn => {
        btn.disabled = false;
    });
}

/**
 * Resend OTP
 */
async function resendOtp() {
    await startFirebaseOTP();
}

/**
 * Debounce utility function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Global functions for inline onclick handlers
window.submitContactForm = submitContactForm;
window.verifyOtp = verifyOtp;
window.resendOtp = resendOtp;

} // End of conditional block for first load only