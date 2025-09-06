#!/usr/bin/env python3
"""
Simple Firebase OTP Test Server
Minimal Flask app to test Firebase OTP functionality
"""

import os
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create minimal Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'test-secret-key')

# Firebase configuration
FIREBASE_CONFIG = {
    'apiKey': os.environ.get('FIREBASE_API_KEY'),
    'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN'),
    'projectId': os.environ.get('FIREBASE_PROJECT_ID'),
    'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET'),
    'messagingSenderId': os.environ.get('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': os.environ.get('FIREBASE_APP_ID')
}

# Minimal Firebase test page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Firebase OTP Test - Antidote</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
        .btn { background: #00A0B0; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; margin: 10px 0; }
        .btn:hover { background: #008A98; }
        .phone-input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; margin: 10px 0; font-size: 16px; }
        #recaptcha-container { margin: 20px 0; }
        .status { padding: 15px; margin: 15px 0; border-radius: 6px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 Firebase OTP Test - Antidote Package</h1>
        
        <div class="status warning">
            <strong>Testing Firebase OTP for Package: Zoh Chin Sculpt Treatment</strong><br>
            This simulates the WhatsApp/Call button functionality
        </div>
        
        <div id="phone-section">
            <label for="phone-number">Enter Phone Number (with country code):</label>
            <input type="tel" id="phone-number" class="phone-input" placeholder="+1234567890" value="+1">
            
            <div id="recaptcha-container"></div>
            
            <button id="send-otp-btn" class="btn">📱 Send OTP (WhatsApp/Call)</button>
        </div>
        
        <div id="otp-section" style="display: none;">
            <label for="otp-code">Enter OTP Code:</label>
            <input type="text" id="otp-code" class="phone-input" placeholder="123456" maxlength="6">
            <button id="verify-otp-btn" class="btn">✅ Verify OTP</button>
        </div>
        
        <div id="status"></div>
        
        <div class="status">
            <strong>Firebase Configuration Status:</strong><br>
            {% for key, value in firebase_config.items() %}
            ✅ {{ key }}: {{ value[:30] }}...<br>
            {% endfor %}
        </div>
    </div>

    <!-- Firebase SDK -->
    <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth-compat.js"></script>

    <script>
        // Firebase Configuration
        const firebaseConfig = {{ firebase_config | tojson }};
        
        // Initialize Firebase
        firebase.initializeApp(firebaseConfig);
        const auth = firebase.auth();
        
        // Global variables
        let confirmationResult;
        
        // Status display function
        function showStatus(message, type = 'warning') {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
            console.log(`${type.toUpperCase()}: ${message}`);
        }
        
        // Initialize reCAPTCHA
        window.onload = function() {
            showStatus('🔥 Firebase initialized successfully! Ready to test OTP.', 'success');
            
            // Setup reCAPTCHA
            window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {
                'size': 'normal',
                'callback': (response) => {
                    console.log('reCAPTCHA solved:', response);
                    showStatus('✅ reCAPTCHA verified! Ready to send OTP.', 'success');
                },
                'expired-callback': () => {
                    showStatus('⚠️ reCAPTCHA expired. Please solve it again.', 'warning');
                }
            });
            
            window.recaptchaVerifier.render().then((widgetId) => {
                window.recaptchaWidgetId = widgetId;
                console.log('reCAPTCHA rendered with widget ID:', widgetId);
            });
        };
        
        // Send OTP
        document.getElementById('send-otp-btn').addEventListener('click', function() {
            const phoneNumber = document.getElementById('phone-number').value.trim();
            
            if (!phoneNumber || phoneNumber.length < 10) {
                showStatus('❌ Please enter a valid phone number with country code', 'error');
                return;
            }
            
            if (!phoneNumber.startsWith('+')) {
                showStatus('❌ Phone number must start with country code (e.g., +1)', 'error');
                return;
            }
            
            showStatus('📱 Sending OTP...', 'warning');
            
            auth.signInWithPhoneNumber(phoneNumber, window.recaptchaVerifier)
                .then((result) => {
                    confirmationResult = result;
                    showStatus(`✅ OTP sent successfully to ${phoneNumber}!`, 'success');
                    document.getElementById('phone-section').style.display = 'none';
                    document.getElementById('otp-section').style.display = 'block';
                })
                .catch((error) => {
                    console.error('OTP send error:', error);
                    showStatus(`❌ Failed to send OTP: ${error.message}`, 'error');
                    
                    // Reset reCAPTCHA
                    window.recaptchaVerifier.render().then((widgetId) => {
                        window.recaptchaWidgetId = widgetId;
                    });
                });
        });
        
        // Verify OTP
        document.getElementById('verify-otp-btn').addEventListener('click', function() {
            const otpCode = document.getElementById('otp-code').value.trim();
            
            if (!otpCode || otpCode.length !== 6) {
                showStatus('❌ Please enter a valid 6-digit OTP code', 'error');
                return;
            }
            
            showStatus('⚡ Verifying OTP...', 'warning');
            
            confirmationResult.confirm(otpCode)
                .then((result) => {
                    const user = result.user;
                    showStatus(`🎉 SUCCESS! Phone verified: ${user.phoneNumber}\\nFirebase OTP is working correctly!`, 'success');
                    console.log('User signed in:', user);
                })
                .catch((error) => {
                    console.error('OTP verification error:', error);
                    showStatus(`❌ Invalid OTP code: ${error.message}`, 'error');
                });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def test_firebase():
    return render_template_string(HTML_TEMPLATE, firebase_config=FIREBASE_CONFIG)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'firebase_configured': all(FIREBASE_CONFIG.values()),
        'project_id': FIREBASE_CONFIG.get('projectId')
    })

if __name__ == '__main__':
    print("🔥 Starting Firebase OTP Test Server...")
    print(f"🌐 Open: http://localhost:5000/")
    print("📱 Test the OTP functionality on the webpage")
    app.run(host='0.0.0.0', port=5000, debug=True)