/**
 * Community Analytics Dashboard JavaScript
 * 
 * This file contains chart visualizations and filtering functionality
 * for the Community Analytics Dashboard.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing community analytics dashboard...');
    
    // Initialize charts
    initializeTrendingTopicsChart();
    initializeBodyPartDistributionChart();
    
    // Initialize body part filter
    initializeBodyPartFilter();
    
    // Initialize refresh button
    initializeRefreshButton();
    
    // Set up automatic refresh interval (every 5 minutes)
    setInterval(refreshAnalyticsData, 5 * 60 * 1000);
});

/**
 * Initialize the trending topics chart
 */
function initializeTrendingTopicsChart() {
    console.log('Initializing trending topics chart...');
    try {
        const topicsChartElement = document.getElementById('trendingTopicsChart');
        if (!topicsChartElement) {
            console.error('Trending topics chart element not found');
            return;
        }
        
        // Get trending topics data from data attribute
        const topicsData = JSON.parse(topicsChartElement.dataset.topics || '[]');
        console.log('Trending topics data:', topicsData);
        
        if (topicsData.length === 0) {
            console.log('No trending topics data available.');
            return;
        }
        
        // Extract labels and data
        // Check if the data is in the new format (topic/count objects) or old format [topic, count]
        let labels, data;
        if (topicsData[0] && typeof topicsData[0] === 'object' && topicsData[0].hasOwnProperty('topic')) {
            console.log('Using object format for topics (topic/count)');
            labels = topicsData.map(item => item.topic);
            data = topicsData.map(item => item.count);
        } else {
            console.log('Using array format for topics [topic, count]');
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
        
        console.log('Trending topics chart initialized successfully');
    } catch (error) {
        console.error('Error initializing trending topics chart:', error);
    }
}

/**
 * Initialize the body part distribution chart
 */
function initializeBodyPartDistributionChart() {
    console.log('Initializing body part distribution chart...');
    try {
        const bodyPartChartElement = document.getElementById('bodyPartDistributionChart');
        if (!bodyPartChartElement) {
            console.error('Body part distribution chart element not found');
            return;
        }
        
        // Get distribution data from data attribute
        const distributionData = JSON.parse(bodyPartChartElement.dataset.distribution || '[]');
        console.log('Body part distribution data:', distributionData);
        
        if (distributionData.length === 0) {
            console.log('No body part distribution data available.');
            return;
        }
        
        // Extract labels and data
        // Check if the data is in the new format (body_part/count objects) or old format [body_part, count]
        let labels, data;
        if (distributionData[0] && typeof distributionData[0] === 'object' && distributionData[0].hasOwnProperty('body_part')) {
            console.log('Using object format for distribution (body_part/count)');
            labels = distributionData.map(item => item.body_part);
            data = distributionData.map(item => item.count);
        } else {
            console.log('Using array format for distribution [body_part, count]');
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
        
        console.log('Body part distribution chart initialized successfully');
    } catch (error) {
        console.error('Error initializing body part distribution chart:', error);
    }
}

/**
 * Initialize the body part filter functionality
 */
function initializeBodyPartFilter() {
    console.log('Initializing body part filter...');
    try {
        const bodyPartFilter = document.getElementById('bodyPartFilter');
        const threadItems = document.querySelectorAll('.thread-item');
        
        if (!bodyPartFilter || threadItems.length === 0) {
            console.log('Body part filter elements not found, skipping initialization');
            return;
        }
        
        bodyPartFilter.addEventListener('change', function() {
            const selectedBodyPart = this.value;
            
            // Log filter change with timestamp for monitoring
            const now = new Date();
            console.log(`[${now.toISOString()}] Filter changed to: ${selectedBodyPart || 'All'}`);
            
            // Track if any threads match the filter
            let matchFound = false;
            
            // Filter threads based on body part
            threadItems.forEach(thread => {
                const threadBodyPart = thread.dataset.bodyPart;
                
                if (!selectedBodyPart || threadBodyPart === selectedBodyPart) {
                    thread.style.display = '';
                    matchFound = true;
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
        });
        
        console.log('Body part filter initialized successfully');
    } catch (error) {
        console.error('Error initializing body part filter:', error);
    }
}

/**
 * Initialize the refresh button
 */
function initializeRefreshButton() {
    console.log('Initializing refresh button...');
    try {
        const refreshButton = document.getElementById('refreshAnalyticsButton');
        if (!refreshButton) {
            console.log('Refresh button not found, skipping initialization');
            return;
        }
        
        refreshButton.addEventListener('click', function() {
            refreshAnalyticsData();
        });
        
        console.log('Refresh button initialized successfully');
    } catch (error) {
        console.error('Error initializing refresh button:', error);
    }
}

/**
 * Refresh analytics data via API
 */
function refreshAnalyticsData() {
    console.log('Refreshing analytics data...');
    try {
        // Log refresh attempt with timestamp for monitoring
        const now = new Date();
        console.log(`[${now.toISOString()}] Refreshing analytics data...`);
        
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
                if (result.success) {
                    console.log('Received updated data:', result);
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
                    
                    console.log('Analytics data refreshed successfully');
                } else {
                    console.error('Failed to refresh analytics data:', result.message);
                }
            })
            .catch(error => {
                console.error('Error refreshing analytics data:', error);
            })
            .finally(() => {
                // Hide loading indicator
                if (loadingIndicator) {
                    loadingIndicator.classList.add('d-none');
                }
            });
    } catch (error) {
        console.error('Error in refreshAnalyticsData:', error);
        
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
    console.log('Updating trending topics chart...');
    try {
        const topicsChartElement = document.getElementById('trendingTopicsChart');
        if (!topicsChartElement) {
            console.error('Trending topics chart element not found');
            return;
        }
        
        if (!topicsData || topicsData.length === 0) {
            console.log('No trending topics data available for update');
            return;
        }
        
        // Update the data attribute
        topicsChartElement.dataset.topics = JSON.stringify(topicsData);
        
        // Reinitialize the chart
        initializeTrendingTopicsChart();
        
        console.log('Trending topics chart updated successfully');
    } catch (error) {
        console.error('Error updating trending topics chart:', error);
    }
}

/**
 * Update the body part distribution chart with new data
 */
function updateBodyPartDistributionChart(distributionData) {
    console.log('Updating body part distribution chart...');
    try {
        const bodyPartChartElement = document.getElementById('bodyPartDistributionChart');
        if (!bodyPartChartElement) {
            console.error('Body part distribution chart element not found');
            return;
        }
        
        if (!distributionData || distributionData.length === 0) {
            console.log('No body part distribution data available for update');
            return;
        }
        
        // Update the data attribute
        bodyPartChartElement.dataset.distribution = JSON.stringify(distributionData);
        
        // Reinitialize the chart
        initializeBodyPartDistributionChart();
        
        console.log('Body part distribution chart updated successfully');
    } catch (error) {
        console.error('Error updating body part distribution chart:', error);
    }
}

/**
 * Update statistics with new data
 */
function updateStatistics(stats) {
    console.log('Updating statistics...');
    try {
        if (!stats) {
            console.log('No statistics data available for update');
            return;
        }
        
        // Update thread count
        const threadCountElement = document.querySelector('.card-body h2[data-stat="thread-count"]');
        if (threadCountElement && stats.thread_count !== undefined) {
            threadCountElement.textContent = stats.thread_count;
        }
        
        // Update reply count
        const replyCountElement = document.querySelector('.card-body h2[data-stat="reply-count"]');
        if (replyCountElement && stats.total_replies !== undefined) {
            replyCountElement.textContent = stats.total_replies;
        }
        
        // Update view count
        const viewCountElement = document.querySelector('.card-body h2[data-stat="view-count"]');
        if (viewCountElement && stats.total_views !== undefined) {
            viewCountElement.textContent = stats.total_views;
        }
        
        console.log('Statistics updated successfully');
    } catch (error) {
        console.error('Error updating statistics:', error);
    }
}