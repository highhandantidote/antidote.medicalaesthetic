/**
 * Theme Switcher for Antidote Platform
 * Manages switching between light and dark themes
 */

// Initialize theme from localStorage or default to light
function initializeTheme() {
    const savedTheme = localStorage.getItem('antidote-theme');
    const htmlElement = document.documentElement;
    
    // Set theme based on saved preference or default to light
    if (savedTheme) {
        htmlElement.setAttribute('data-bs-theme', savedTheme);
    } else {
        // Default to light theme if no preference is found
        htmlElement.setAttribute('data-bs-theme', 'light');
        localStorage.setItem('antidote-theme', 'light');
    }
    
    // Update theme icon based on current theme
    updateThemeIcon();
}

// Toggle between light and dark themes
function toggleTheme() {
    const htmlElement = document.documentElement;
    const currentTheme = htmlElement.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Set the new theme
    htmlElement.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('antidote-theme', newTheme);
    
    // Update the icon to match the current theme
    updateThemeIcon();
}

// Update the theme icon based on current theme
function updateThemeIcon() {
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        
        // Clear existing classes
        themeIcon.classList.remove('fa-sun', 'fa-moon');
        
        // Set appropriate icon
        if (currentTheme === 'dark') {
            themeIcon.classList.add('fa-sun');
            themeIcon.setAttribute('title', 'Switch to light theme');
        } else {
            themeIcon.classList.add('fa-moon');
            themeIcon.setAttribute('title', 'Switch to dark theme');
        }
    }
}

// Initialize theme when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    
    // Add event listener to theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
});