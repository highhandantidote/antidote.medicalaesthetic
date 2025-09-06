/**
 * Community Analytics Dashboard Debug Helper
 * This file provides functions to debug and diagnose chart rendering issues.
 */

// Execute on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Debug helper loaded, checking charts...');
    
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded! This is critical for rendering charts.');
    } else {
        console.log('Chart.js is properly loaded. Version:', Chart.version);
    }
    
    // Debug trending topics data
    debugChartData('trendingTopicsChart', 'trending topics');
    
    // Debug body part distribution data
    debugChartData('bodyPartDistributionChart', 'body part distribution');
    
    // Check for JS errors that might prevent chart rendering
    checkForJSErrors();
});

/**
 * Debug chart data by checking the data attribute and parsing
 */
function debugChartData(chartId, chartName) {
    const chartElement = document.getElementById(chartId);
    
    if (!chartElement) {
        console.error(`${chartName} chart element not found (ID: ${chartId})`);
        return;
    }
    
    console.log(`Found ${chartName} chart element:`, chartElement);
    
    // Check the dataset attribute
    const datasetName = chartId === 'trendingTopicsChart' ? 'topics' : 'distribution';
    const rawData = chartElement.dataset[datasetName];
    
    console.log(`Raw ${chartName} data attribute:`, rawData);
    
    // Try to parse the data
    try {
        const parsedData = JSON.parse(rawData || '[]');
        console.log(`Parsed ${chartName} data:`, parsedData);
        
        if (parsedData.length === 0) {
            console.warn(`No data available for ${chartName} chart. This is why the chart isn't rendering.`);
        } else {
            console.log(`${chartName} chart has data and should render.`);
            
            // Check data format
            if (typeof parsedData[0] === 'object') {
                console.log(`${chartName} data is in object format:`, parsedData[0]);
            } else {
                console.log(`${chartName} data is in array format:`, parsedData[0]);
            }
        }
    } catch (error) {
        console.error(`Error parsing ${chartName} data:`, error);
    }
}

/**
 * Check for common JavaScript errors that might prevent chart rendering
 */
function checkForJSErrors() {
    console.log('Checking for common JavaScript issues...');
    
    // Check if jQuery is loaded (often required by other scripts)
    if (typeof jQuery === 'undefined') {
        console.warn('jQuery is not loaded. This might cause issues if your code depends on it.');
    } else {
        console.log('jQuery is loaded. Version:', jQuery.fn.jquery);
    }
    
    // Check for conflicting libraries
    if (window.$ && window.$ !== jQuery) {
        console.warn('Possible jQuery conflict detected. $ is defined but not equal to jQuery.');
    }
    
    // Verify canvas support
    const canvas = document.createElement('canvas');
    if (!canvas.getContext) {
        console.error('Canvas not supported in this browser. Charts cannot render.');
    } else {
        console.log('Canvas is supported in this browser.');
    }
}