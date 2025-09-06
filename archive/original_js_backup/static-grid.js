/**
 * Static Grid Layout - No Animation at All
 * Displays all categories in a clean grid without any sliding
 */

document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.scrolling-categories');
    if (!container) return;
    
    // Remove any existing animations
    container.style.animation = 'none';
    container.style.transform = 'none';
    
    // Convert to grid layout
    container.style.cssText = `
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        padding: 20px;
        overflow: visible;
        height: auto;
    `;
    
    // Remove any cloned items
    const items = Array.from(container.children);
    const originalCount = Math.ceil(items.length / 2);
    
    for (let i = originalCount; i < items.length; i++) {
        items[i].remove();
    }
});