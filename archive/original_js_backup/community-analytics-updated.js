/**
 * Community Analytics Dashboard JavaScript (Optimized Version)
 * 
 * This file contains chart visualizations and filtering functionality
 * for the Community Analytics Dashboard with improved features:
 * - Debounced filter events
 * - Detailed timestamp logs
 * - Improved performance with lazy loading for charts
 * - Real-time polling with debugging logs
 */

// Set up debouncing function to improve performance
function debounce(func, wait, immediate) {
    let timeout;
    return function() {
        const context = this, args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Add timestamp to logs for better tracking
function logWithTimestamp(message, data) {
    const timestamp = new Date().toISOString();
    if (data) {
        console.log(`[${timestamp}] ${message}`, data);
    } else {
        console.log(`[${timestamp}] ${message}`);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    logWithTimestamp('DOM loaded, initializing community analytics dashboard...');
    
    // Lazy load charts when needed
    initializeLazyChartLoading();
    
    // Initialize filter with debouncing
    initializeBodyPartFilter();
    
    // Initialize refresh button
    initializeRefreshButton();
    
    // Set up automatic refresh interval (every 5 minutes)
    const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes
    setInterval(function() {
        logWithTimestamp('Auto-refreshing analytics data after 5 minutes');
        refreshAnalyticsData();
    }, REFRESH_INTERVAL);
    
    logWithTimestamp('Community analytics dashboard initialization complete');
});

/**
 * Initialize lazy loading for charts
 */
function initializeLazyChartLoading() {
    logWithTimestamp('Setting up lazy chart loading');
    
    // Check if charts should be initialized immediately (visible in viewport)
    if (isElementInViewport(document.getElementById('trendingTopicsChart'))) {
        logWithTimestamp('Trending topics chart is visible, initializing immediately');
        initializeTrendingTopicsChart();
    }
    
    if (isElementInViewport(document.getElementById('bodyPartDistributionChart'))) {
        logWithTimestamp('Body part distribution chart is visible, initializing immediately');
        initializeBodyPartDistributionChart();
    }
    
    // Set up scroll event listener to initialize charts when they come into view
    window.addEventListener('scroll', debounce(function() {
        const topicsChart = document.getElementById('trendingTopicsChart');
        const bodyPartChart = document.getElementById('bodyPartDistributionChart');
        
        if (topicsChart && !topicsChart.classList.contains('chart-initialized') && isElementInViewport(topicsChart)) {
            logWithTimestamp('Trending topics chart scrolled into view, initializing');
            initializeTrendingTopicsChart();
        }
        
        if (bodyPartChart && !bodyPartChart.classList.contains('chart-initialized') && isElementInViewport(bodyPartChart)) {
            logWithTimestamp('Body part distribution chart scrolled into view, initializing');
            initializeBodyPartDistributionChart();
        }
    }, 200));
}

/**
 * Check if an element is in the viewport
 */
function isElementInViewport(el) {
    if (!el) return false;
    
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Initialize the trending topics chart
 */
function initializeTrendingTopicsChart() {
    logWithTimestamp('Initializing trending topics chart...');
    try {
        const topicsChartElement = document.getElementById('trendingTopicsChart');
        if (!topicsChartElement) {
            logWithTimestamp('Trending topics chart element not found');
            return;
        }
        
        // Mark as initialized to prevent duplication
        topicsChartElement.classList.add('chart-initialized');
        
        // Get trending topics data from data attribute
        const topicsData = JSON.parse(topicsChartElement.dataset.topics || '[]');
        logWithTimestamp('Trending topics data:', topicsData);
        
        if (topicsData.length === 0) {
            logWithTimestamp('No trending topics data available.');
            return;
        }
        
        // Track render start time for performance measurement
        const renderStartTime = performance.now();
        
        // Extract labels and data
        // Check if the data is in the new format (topic/count objects) or old format [topic, count]
        let labels, data;
        if (topicsData[0] && typeof topicsData[0] === 'object' && topicsData[0].hasOwnProperty('topic')) {
            logWithTimestamp('Using object format for topics (topic/count)');
            labels = topicsData.map(item => item.topic);
            data = topicsData.map(item => item.count);
        } else {
            logWithTimestamp('Using array format for topics [topic, count]');
            labels = topicsData.map(item => item[0]);
            data = topicsData.map(item => item[1]);
        }
        
        // Create the bar chart
        new Chart(topicsChartElement.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Mentions',
                    data: data,
                    backgroundColor: 'rgba(54, 162, 235, 0.7)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            precision: 0
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14
                        },
                        bodyFont: {
                            size: 13
                        },
                        padding: 10,
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.y} mentions`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Top Trends',
                        color: '#666',
                        font: {
                            size: 14
                        },
                        padding: {
                            bottom: 10
                        }
                    }
                }
            }
        });
        
        // Track render time for performance logging
        const renderTime = performance.now() - renderStartTime;
        logWithTimestamp(`Trending topics chart initialized successfully in ${renderTime.toFixed(2)}ms`);
    } catch (error) {
        logWithTimestamp('Error initializing trending topics chart:', error);
    }
}

/**
 * Initialize the body part distribution chart
 */
function initializeBodyPartDistributionChart() {
    logWithTimestamp('Initializing body part distribution chart...');
    try {
        const bodyPartChartElement = document.getElementById('bodyPartDistributionChart');
        if (!bodyPartChartElement) {
            logWithTimestamp('Body part distribution chart element not found');
            return;
        }
        
        // Mark as initialized to prevent duplication
        bodyPartChartElement.classList.add('chart-initialized');
        
        // Get distribution data from data attribute
        const distributionData = JSON.parse(bodyPartChartElement.dataset.distribution || '[]');
        logWithTimestamp('Body part distribution data:', distributionData);
        
        if (distributionData.length === 0) {
            logWithTimestamp('No body part distribution data available.');
            return;
        }
        
        // Track render start time for performance measurement
        const renderStartTime = performance.now();
        
        // Extract labels and data
        // Check if the data is in the new format (body_part/count objects) or old format [body_part, count]
        let labels, data;
        if (distributionData[0] && typeof distributionData[0] === 'object' && distributionData[0].hasOwnProperty('body_part')) {
            logWithTimestamp('Using object format for distribution (body_part/count)');
            labels = distributionData.map(item => item.body_part);
            data = distributionData.map(item => item.count);
        } else {
            logWithTimestamp('Using array format for distribution [body_part, count]');
            labels = distributionData.map(item => item[0]);
            data = distributionData.map(item => item[1]);
        }
        
        // Generate colors for pie chart - use a consistent color palette
        const backgroundColors = [
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 99, 132, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)',
            'rgba(199, 199, 199, 0.7)',
            'rgba(83, 102, 255, 0.7)',
            'rgba(78, 205, 196, 0.7)',
            'rgba(255, 99, 71, 0.7)'
        ];
        
        const borderColors = backgroundColors.map(color => color.replace('0.7', '1'));
        
        // Create the pie chart
        new Chart(bodyPartChartElement.getContext('2d'), {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors.slice(0, data.length),
                    borderColor: borderColors.slice(0, data.length),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 10,
                        right: 20,
                        bottom: 10,
                        left: 10
                    }
                },
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 15,
                            padding: 10,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            size: 14
                        },
                        bodyFont: {
                            size: 13
                        },
                        padding: 10,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} threads (${percentage}%)`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Thread Distribution',
                        color: '#666',
                        font: {
                            size: 14
                        },
                        padding: {
                            bottom: 10
                        }
                    }
                }
            }
        });
        
        // Track render time for performance logging
        const renderTime = performance.now() - renderStartTime;
        logWithTimestamp(`Body part distribution chart initialized successfully in ${renderTime.toFixed(2)}ms`);
    } catch (error) {
        logWithTimestamp('Error initializing body part distribution chart:', error);
    }
}

/**
 * Initialize the body part filter functionality with debounce
 */
function initializeBodyPartFilter() {
    logWithTimestamp('Initializing body part filter...');
    try {
        const bodyPartFilter = document.getElementById('bodyPartFilter');
        const threadItems = document.querySelectorAll('.thread-item');
        
        if (!bodyPartFilter || threadItems.length === 0) {
            logWithTimestamp('Body part filter elements not found, skipping initialization');
            return;
        }
        
        // Use debounce to improve performance
        bodyPartFilter.addEventListener('change', debounce(function() {
            const selectedBodyPart = this.value;
            const filterStartTime = performance.now();
            
            // Log filter change with timestamp for monitoring
            logWithTimestamp(`Filter changed to: ${selectedBodyPart || 'All'}`);
            
            // Track if any threads match the filter
            let matchFound = false;
            let matchCount = 0;
            
            // Filter threads based on body part
            threadItems.forEach(thread => {
                const threadBodyPart = thread.dataset.bodyPart;
                
                if (!selectedBodyPart || threadBodyPart === selectedBodyPart) {
                    thread.style.display = '';
                    matchFound = true;
                    matchCount++;
                } else {
                    thread.style.display = 'none';
                }
            });
            
            // Show a message if no threads match the filter
            const noResultsElement = document.getElementById('noFilterResults');
            if (!matchFound) {
                if (!noResultsElement) {
                    const threadList = document.getElementById('threadList');
                    if (threadList) {
                        const noResults = document.createElement('div');
                        noResults.id = 'noFilterResults';
                        noResults.className = 'list-group-item text-center py-3';
                        noResults.innerHTML = '<p class="mb-0">No threads found for the selected body part. Try a different filter.</p>';
                        threadList.appendChild(noResults);
                    }
                }
            } else if (noResultsElement) {
                noResultsElement.remove();
            }
            
            const filterTime = performance.now() - filterStartTime;
            logWithTimestamp(`Filter applied in ${filterTime.toFixed(2)}ms, showing ${matchCount} threads`);
        }, 100)); // 100ms debounce delay
        
        logWithTimestamp('Body part filter initialized successfully');
    } catch (error) {
        logWithTimestamp('Error initializing body part filter:', error);
    }
}

/**
 * Initialize the refresh button
 */
function initializeRefreshButton() {
    logWithTimestamp('Initializing refresh button...');
    try {
        const refreshButton = document.getElementById('refreshAnalyticsButton');
        if (!refreshButton) {
            logWithTimestamp('Refresh button not found, skipping initialization');
            return;
        }
        
        refreshButton.addEventListener('click', function() {
            logWithTimestamp('Refresh button clicked by user');
            refreshAnalyticsData();
        });
        
        logWithTimestamp('Refresh button initialized successfully');
    } catch (error) {
        logWithTimestamp('Error initializing refresh button:', error);
    }
}

/**
 * Refresh analytics data via API
 */
function refreshAnalyticsData() {
    logWithTimestamp('Refreshing analytics data...');
    try {
        // Track API call performance
        const apiCallStartTime = performance.now();
        
        // Show loading indicator
        const loadingIndicator = document.getElementById('refreshingIndicator');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
        
        // Update last refreshed time
        const lastUpdatedElement = document.getElementById('lastUpdatedTime');
        
        // Fetch updated data from API
        fetch('/api/community/trends')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                return response.json();
            })
            .then(result => {
                const apiCallTime = performance.now() - apiCallStartTime;
                logWithTimestamp(`API call completed in ${apiCallTime.toFixed(2)}ms`);
                
                if (result.success) {
                    logWithTimestamp('Received updated data');
                    const data = result.data;
                    
                    // Update charts with new data
                    updateTrendingTopicsChart(data.trending_topics);
                    updateBodyPartDistributionChart(data.body_part_distribution);
                    
                    // Update statistics
                    updateStatistics(data.stats);
                    
                    // Update last refreshed time
                    if (lastUpdatedElement) {
                        const now = new Date();
                        lastUpdatedElement.textContent = now.toLocaleTimeString();
                    }
                    
                    logWithTimestamp('Analytics data refreshed successfully');
                } else {
                    logWithTimestamp('Failed to refresh analytics data:', result.message);
                }
            })
            .catch(error => {
                logWithTimestamp('Error refreshing analytics data:', error);
            })
            .finally(() => {
                // Hide loading indicator
                if (loadingIndicator) {
                    loadingIndicator.classList.add('d-none');
                }
            });
    } catch (error) {
        logWithTimestamp('Error in refreshAnalyticsData:', error);
        
        // Hide loading indicator in case of error
        const loadingIndicator = document.getElementById('refreshingIndicator');
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
    }
}

/**
 * Update the trending topics chart with new data
 */
function updateTrendingTopicsChart(topicsData) {
    logWithTimestamp('Updating trending topics chart...');
    try {
        const topicsChartElement = document.getElementById('trendingTopicsChart');
        if (!topicsChartElement) {
            logWithTimestamp('Trending topics chart element not found');
            return;
        }
        
        if (!topicsData || topicsData.length === 0) {
            logWithTimestamp('No trending topics data available for update');
            return;
        }
        
        // Update the data attribute
        topicsChartElement.dataset.topics = JSON.stringify(topicsData);
        
        // Remove the initialized class to force re-render
        topicsChartElement.classList.remove('chart-initialized');
        
        // Reinitialize the chart
        initializeTrendingTopicsChart();
        
        logWithTimestamp('Trending topics chart updated successfully');
    } catch (error) {
        logWithTimestamp('Error updating trending topics chart:', error);
    }
}

/**
 * Update the body part distribution chart with new data
 */
function updateBodyPartDistributionChart(distributionData) {
    logWithTimestamp('Updating body part distribution chart...');
    try {
        const bodyPartChartElement = document.getElementById('bodyPartDistributionChart');
        if (!bodyPartChartElement) {
            logWithTimestamp('Body part distribution chart element not found');
            return;
        }
        
        if (!distributionData || distributionData.length === 0) {
            logWithTimestamp('No body part distribution data available for update');
            return;
        }
        
        // Update the data attribute
        bodyPartChartElement.dataset.distribution = JSON.stringify(distributionData);
        
        // Remove the initialized class to force re-render
        bodyPartChartElement.classList.remove('chart-initialized');
        
        // Reinitialize the chart
        initializeBodyPartDistributionChart();
        
        logWithTimestamp('Body part distribution chart updated successfully');
    } catch (error) {
        logWithTimestamp('Error updating body part distribution chart:', error);
    }
}

/**
 * Update statistics display with new data
 */
function updateStatistics(stats) {
    if (!stats) return;
    
    try {
        const threadCountElement = document.getElementById('threadCount');
        const viewCountElement = document.getElementById('viewCount');
        const replyCountElement = document.getElementById('replyCount');
        
        if (threadCountElement) threadCountElement.textContent = stats.thread_count || 0;
        if (viewCountElement) viewCountElement.textContent = stats.total_views || 0;
        if (replyCountElement) replyCountElement.textContent = stats.total_replies || 0;
        
        logWithTimestamp('Statistics updated successfully');
    } catch (error) {
        logWithTimestamp('Error updating statistics:', error);
    }
}