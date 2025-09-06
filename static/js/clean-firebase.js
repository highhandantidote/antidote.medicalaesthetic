/**
 * Clean Firebase OTP Implementation - No conflicts
 */

// Wait for window to fully load
window.addEventListener('load', function() {
    // Check if Firebase is available
    if (typeof firebase === 'undefined') {
        console.error('Firebase not loaded');
        return;
    }
    
    console.log('Clean Firebase OTP system initializing...');
    window.cleanFirebaseOTP = new CleanFirebaseOTP();
});

class CleanFirebaseOTP {
    constructor() {
        this.recaptcha = null;
        this.confirmation = null;
        this.formData = {};
        this.init();
    }
    
    init() {
        try {
            // Check if recaptcha container exists
            const container = document.getElementById('recaptcha-container');
            console.log('reCAPTCHA container found:', !!container);
            
            // Initialize reCAPTCHA with better error handling
            this.recaptcha = new firebase.auth.RecaptchaVerifier('recaptcha-container', {
                size: 'invisible',
                callback: (response) => {
                    console.log('✅ reCAPTCHA solved successfully:', response);
                },
                'expired-callback': () => {
                    console.warn('⚠️ reCAPTCHA expired, user needs to solve again');
                }
            });
            
            // Test recaptcha render
            this.recaptcha.render().then((widgetId) => {
                console.log('reCAPTCHA rendered successfully, widget ID:', widgetId);
            }).catch((error) => {
                console.error('reCAPTCHA render failed:', error);
            });
            
            console.log('Clean Firebase OTP initialized successfully');
        } catch (error) {
            console.error('Clean Firebase OTP initialization failed:', error);
        }
    }
    
    async sendOTP(phone) {
        try {
            console.log('🔥 Firebase OTP Debug - Starting OTP send process');
            console.log('📱 Phone number:', phone);
            console.log('🔧 Firebase auth available:', !!firebase.auth);
            console.log('🔧 reCAPTCHA verifier available:', !!this.recaptcha);
            console.log('🔧 Firebase config:', firebase.app().options);
            
            // Validate phone number format
            if (!phone || !phone.startsWith('+') || phone.length < 10) {
                throw new Error('Invalid phone number format. Must include country code (e.g., +1234567890)');
            }
            
            // Check if recaptcha is ready
            if (!this.recaptcha) {
                console.error('❌ reCAPTCHA verifier not initialized');
                throw new Error('reCAPTCHA verifier not initialized');
            }
            
            // Check reCAPTCHA state
            console.log('🔧 Checking reCAPTCHA state before OTP send...');
            
            // Attempt to send OTP with detailed logging
            console.log('📤 Calling firebase.auth().signInWithPhoneNumber...');
            this.confirmation = await firebase.auth().signInWithPhoneNumber(phone, this.recaptcha);
            
            console.log('✅ OTP sent successfully! Confirmation result available:', !!this.confirmation);
            console.log('🔧 Confirmation object type:', typeof this.confirmation);
            
            return { success: true, message: 'OTP sent successfully to ' + phone };
        } catch (error) {
            console.error('❌ Firebase OTP Error - Full Details:');
            console.error('Error code:', error.code);
            console.error('Error message:', error.message);
            console.error('Error stack:', error.stack);
            console.error('Error object:', error);
            
            // Provide specific error handling for common issues
            let userMessage = error.message;
            if (error.code === 'auth/internal-error') {
                userMessage = 'Internal Firebase error. This may be due to reCAPTCHA or configuration issues. Please try again.';
                console.error('🚨 AUTH/INTERNAL-ERROR detected - potential causes:');
                console.error('1. reCAPTCHA configuration issues');
                console.error('2. Firebase project configuration');
                console.error('3. Content Security Policy blocking Firebase requests');
                console.error('4. Missing Firebase domains in CSP');
            } else if (error.code === 'auth/too-many-requests') {
                userMessage = 'Too many OTP requests. Please wait a few minutes and try again.';
            } else if (error.code === 'auth/invalid-phone-number') {
                userMessage = 'Invalid phone number format. Please include country code (e.g., +1234567890).';
            }
            
            return { success: false, error: userMessage, code: error.code };
        }
    }
    
    async verifyOTP(code) {
        try {
            const result = await this.confirmation.confirm(code);
            return { success: true, user: result.user };
        } catch (error) {
            console.error('OTP verification error:', error);
            return { success: false, error: error.message };
        }
    }
}

// Global functions for modal interaction
function openContactModal(sourceType, sourceId, contactIntent) {
    if (!window.cleanFirebaseOTP) {
        console.error('Firebase OTP not initialized');
        return;
    }
    
    window.cleanFirebaseOTP.formData = {
        sourceType: sourceType,
        sourceId: sourceId,
        contactIntent: contactIntent
    };
    
    // Reset and show modal
    document.getElementById('enhancedLeadForm').reset();
    showStep('contact-form');
    clearMessages();
    
    const modal = new bootstrap.Modal(document.getElementById('enhancedLeadModal'));
    modal.show();
    
    // Update title
    const titles = { 
        'whatsapp': 'WhatsApp Contact', 
        'call': 'Phone Call Request' 
    };
    document.getElementById('leadModalTitle').textContent = titles[contactIntent] || 'Contact Request';
}

async function submitContactForm() {
    if (!validateContactForm()) return;
    
    const submitBtn = document.getElementById('submitContactBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending OTP...';
    submitBtn.disabled = true;
    
    try {
        // Store form data
        const otp = window.cleanFirebaseOTP;
        otp.formData.name = document.getElementById('contactName').value.trim();
        otp.formData.phone = formatPhoneNumber(document.getElementById('contactPhone').value.trim());
        otp.formData.email = document.getElementById('contactEmail').value.trim();
        otp.formData.message = document.getElementById('contactMessage').value.trim();
        
        // Send OTP
        const result = await otp.sendOTP(otp.formData.phone);
        
        if (result.success) {
            showStep('otp-verification');
            document.getElementById('otpPhoneDisplay').textContent = otp.formData.phone;
            startOTPCountdown();
            showSuccessMessage('OTP sent successfully!');
        } else {
            showErrorMessage('Failed to send OTP: ' + result.error);
        }
        
    } catch (error) {
        console.error('Submit form error:', error);
        showErrorMessage('Failed to send OTP. Please try again.');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

async function verifyOtp() {
    const otpCode = document.getElementById('otpCode').value.trim();
    
    if (!otpCode || otpCode.length !== 6) {
        showErrorMessage('Please enter a valid 6-digit OTP');
        return;
    }
    
    const verifyBtn = document.getElementById('verifyOtpBtn');
    const originalText = verifyBtn.innerHTML;
    verifyBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Verifying...';
    verifyBtn.disabled = true;
    
    try {
        const result = await window.cleanFirebaseOTP.verifyOTP(otpCode);
        
        if (result.success) {
            await submitVerifiedLead(result.user.uid);
        } else {
            showErrorMessage('Invalid OTP: ' + result.error);
        }
        
    } catch (error) {
        console.error('Verify OTP error:', error);
        showErrorMessage('Invalid OTP. Please try again.');
    } finally {
        verifyBtn.innerHTML = originalText;
        verifyBtn.disabled = false;
    }
}

async function submitVerifiedLead(firebaseUid) {
    try {
        const otp = window.cleanFirebaseOTP;
        const response = await fetch('/api/leads/verify-phone', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({
                name: otp.formData.name,
                phone: otp.formData.phone,
                email: otp.formData.email,
                message: otp.formData.message,
                source_type: otp.formData.sourceType,
                source_id: otp.formData.sourceId,
                contact_intent: otp.formData.contactIntent,
                firebase_uid: firebaseUid
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Lead verified successfully, response:', data);
            console.log('🔗 Contact URL:', data.contact_url);
            closeContactModal();
            executeContactAction(data);
        } else {
            showErrorMessage(data.message || 'Error creating lead');
        }
        
    } catch (error) {
        console.error('Lead submission error:', error);
        showErrorMessage('Error submitting request');
    }
}

async function resendOtp() {
    const resendBtn = document.getElementById('resendOtpBtn');
    const originalText = resendBtn.innerHTML;
    resendBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Resending...';
    resendBtn.disabled = true;
    
    try {
        const result = await window.cleanFirebaseOTP.sendOTP(window.cleanFirebaseOTP.formData.phone);
        
        if (result.success) {
            showSuccessMessage('OTP resent successfully!');
            startOTPCountdown();
        } else {
            showErrorMessage('Failed to resend OTP');
        }
        
    } catch (error) {
        console.error('Resend OTP error:', error);
        showErrorMessage('Failed to resend OTP');
    } finally {
        resendBtn.innerHTML = originalText;
        resendBtn.disabled = false;
    }
}

// Helper functions
function validateContactForm() {
    const name = document.getElementById('contactName').value.trim();
    const phone = document.getElementById('contactPhone').value.trim();
    
    if (!name) {
        showErrorMessage('Please enter your name');
        return false;
    }
    
    if (!phone) {
        showErrorMessage('Please enter your phone number');
        return false;
    }
    
    const phoneRegex = /^(\+91|91)?[6-9]\d{9}$/;
    if (!phoneRegex.test(phone.replace(/[\s\-]/g, ''))) {
        showErrorMessage('Please enter a valid phone number');
        return false;
    }
    
    return true;
}

function formatPhoneNumber(phone) {
    let cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
        cleaned = '+91' + cleaned;
    } else if (cleaned.length === 12 && cleaned.startsWith('91')) {
        cleaned = '+' + cleaned;
    }
    return cleaned;
}

function showStep(stepId) {
    const steps = ['contact-form', 'otp-verification', 'success-message'];
    steps.forEach(step => {
        const element = document.getElementById(step);
        if (element) {
            element.style.display = step === stepId ? 'block' : 'none';
        }
    });
}

function showErrorMessage(message) {
    const errorEl = document.getElementById('leadModalError');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
        setTimeout(() => errorEl.style.display = 'none', 5000);
    }
}

function showSuccessMessage(message) {
    const successEl = document.getElementById('leadModalSuccess');
    if (successEl) {
        successEl.textContent = message;
        successEl.style.display = 'block';
        setTimeout(() => successEl.style.display = 'none', 3000);
    }
}

function clearMessages() {
    const errorEl = document.getElementById('leadModalError');
    const successEl = document.getElementById('leadModalSuccess');
    if (errorEl) errorEl.style.display = 'none';
    if (successEl) successEl.style.display = 'none';
}

function closeContactModal() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('enhancedLeadModal'));
    if (modal) modal.hide();
}

function executeContactAction(data) {
    console.log('🚀 executeContactAction called with:', data);
    console.log('📱 User agent:', navigator.userAgent);
    console.log('🔍 Is mobile:', /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent));
    
    if (data.contact_url) {
        console.log('📱 Opening contact URL:', data.contact_url);
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        if (isMobile) {
            console.log('📱 Mobile detected - using direct navigation');
            showNotification('Verified! Opening contact...', 'success');
            
            // For mobile - use direct window.location change for better reliability
            setTimeout(() => {
                console.log('🔗 Mobile: Navigating to:', data.contact_url);
                try {
                    window.location.href = data.contact_url;
                } catch (error) {
                    console.error('❌ Mobile navigation failed:', error);
                    // Fallback: try window.open
                    window.open(data.contact_url, '_blank');
                }
            }, 500); // Shorter delay for mobile
            
        } else {
            console.log('🖥️ Desktop detected - using window.open');
            showNotification('Verified! Opening contact...', 'success');
            setTimeout(() => {
                console.log('🔗 Desktop: Opening window:', data.contact_url);
                window.open(data.contact_url, '_blank');
            }, 1000);
        }
    } else {
        console.log('⚠️ No contact_url provided in response');
        showNotification('Contact verified successfully!', 'success');
    }
}

function showNotification(message, type) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 3000);
}

function startOTPCountdown() {
    let timeLeft = 30;
    const resendBtn = document.getElementById('resendOtpBtn');
    
    const timer = setInterval(() => {
        timeLeft--;
        if (resendBtn) {
            resendBtn.textContent = `Resend OTP (${timeLeft}s)`;
            resendBtn.disabled = true;
        }
        
        if (timeLeft <= 0) {
            clearInterval(timer);
            if (resendBtn) {
                resendBtn.textContent = 'Resend OTP';
                resendBtn.disabled = false;
            }
        }
    }, 1000);
}

// Auto-verify when 6 digits entered
document.addEventListener('DOMContentLoaded', function() {
    const otpInput = document.getElementById('otpCode');
    if (otpInput) {
        otpInput.addEventListener('input', function(e) {
            if (e.target.value.length === 6) {
                verifyOtp();
            }
        });
    }
});