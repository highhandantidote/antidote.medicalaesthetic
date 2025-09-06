/**
 * Face Scan Annotation System
 * 
 * This script enhances the face scan analysis report by adding:
 * 1. Interactive annotations on the facial image
 * 2. Severity indicators for identified conditions
 * 3. Improved formatting for readability
 * 4. Tooltips for technical terms
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the annotation system
    initAnnotationSystem();
    
    // Format and enhance the analysis text
    improveTextFormatting();
    
    // Add tooltips for technical terms
    addMedicalTermTooltips();
});

// =================== ANNOTATION SYSTEM ====================

/**
 * Initialize the facial annotation system
 */
function initAnnotationSystem() {
    const imageContainer = document.querySelector('.structure-diagram');
    const facialImage = document.querySelector('.facial-analysis-img');
    
    if (!imageContainer || !facialImage) return;
    
    // Create annotation overlay if it doesn't exist
    let annotationOverlay = document.querySelector('.annotation-overlay');
    if (!annotationOverlay) {
        annotationOverlay = document.createElement('div');
        annotationOverlay.className = 'annotation-overlay';
        imageContainer.appendChild(annotationOverlay);
        
        // Style the annotation overlay
        annotationOverlay.style.position = 'absolute';
        annotationOverlay.style.top = '0';
        annotationOverlay.style.left = '0';
        annotationOverlay.style.width = '100%';
        annotationOverlay.style.height = '100%';
        annotationOverlay.style.pointerEvents = 'none';
    }
    
    // Extract facial features from analysis text
    const analysisText = document.querySelectorAll('.analysis-text p');
    const features = extractFeaturesFromText(analysisText);
    
    // Add annotations based on extracted features
    addAnnotationsToImage(features, annotationOverlay, facialImage);
}

/**
 * Extract facial features and issues from the analysis text
 * @param {NodeList} paragraphs - The paragraphs of analysis text
 * @return {Array} Array of feature objects with positions and descriptions
 */
function extractFeaturesFromText(paragraphs) {
    const features = [];
    const keywords = {
        'nose': { region: 'center', verticalPosition: 'middle' },
        'eyes': { region: 'top', verticalPosition: 'top' },
        'lips': { region: 'bottom', verticalPosition: 'bottom' },
        'chin': { region: 'bottom', verticalPosition: 'bottom' },
        'forehead': { region: 'top', verticalPosition: 'top' },
        'cheeks': { region: 'sides', verticalPosition: 'middle' },
        'jaw': { region: 'sides', verticalPosition: 'bottom' },
        'eyebrows': { region: 'top', verticalPosition: 'top' },
        'skin': { region: 'full', verticalPosition: 'full' },
        'symmetry': { region: 'full', verticalPosition: 'full' },
        'scarring': { region: 'custom', verticalPosition: 'custom' },
        'wrinkles': { region: 'custom', verticalPosition: 'custom' },
        'hyperpigmentation': { region: 'custom', verticalPosition: 'custom' }
    };
    
    // Process each paragraph to find facial features and concerns
    paragraphs.forEach(paragraph => {
        const text = paragraph.textContent.toLowerCase();
        
        // Loop through our keywords
        Object.keys(keywords).forEach(keyword => {
            if (text.includes(keyword)) {
                // Find severity indicators
                let severity = 'moderate';
                if (text.includes('severe ' + keyword) || text.includes(keyword + ' is severe')) {
                    severity = 'severe';
                } else if (text.includes('mild ' + keyword) || text.includes(keyword + ' is mild')) {
                    severity = 'mild';
                }
                
                // Find position indicators
                let position = { ...keywords[keyword] };
                if (text.includes('left ' + keyword) || text.includes(keyword + ' on the left')) {
                    position.horizontal = 'left';
                } else if (text.includes('right ' + keyword) || text.includes(keyword + ' on the right')) {
                    position.horizontal = 'right';
                }
                
                // Extract the specific description
                let description = extractDescription(text, keyword);
                
                // Add to features
                features.push({
                    name: keyword,
                    severity: severity,
                    position: position,
                    description: description
                });
            }
        });
    });
    
    return features;
}

/**
 * Extract a relevant description for a feature from the text
 * @param {string} text - The paragraph text
 * @param {string} keyword - The feature keyword
 * @return {string} The extracted description
 */
function extractDescription(text, keyword) {
    // Find sentences containing the keyword
    const sentences = text.split(/[.!?]+/);
    for (let sentence of sentences) {
        if (sentence.includes(keyword)) {
            return sentence.trim();
        }
    }
    return '';
}

/**
 * Add visual annotations to the facial image
 * @param {Array} features - The extracted facial features
 * @param {Element} overlay - The annotation overlay element
 * @param {Element} image - The facial image element
 */
function addAnnotationsToImage(features, overlay, image) {
    // Wait for image to load to get dimensions
    image.onload = function() {
        const imageWidth = image.offsetWidth;
        const imageHeight = image.offsetHeight;
        
        // Clear existing annotations
        overlay.innerHTML = '';
        
        // Create annotations for each feature
        features.forEach((feature, index) => {
            // Calculate position based on feature location
            let position = calculatePosition(feature.position, imageWidth, imageHeight);
            
            // Create annotation marker
            const marker = document.createElement('div');
            marker.className = 'annotation-marker ' + feature.severity;
            marker.style.position = 'absolute';
            marker.style.left = position.x + 'px';
            marker.style.top = position.y + 'px';
            marker.style.width = '20px';
            marker.style.height = '20px';
            marker.style.borderRadius = '50%';
            marker.style.border = '2px solid #fff';
            marker.style.boxShadow = '0 0 5px rgba(0,0,0,0.5)';
            marker.style.zIndex = '100';
            marker.style.cursor = 'pointer';
            marker.style.pointerEvents = 'auto';
            
            // Set color based on severity
            if (feature.severity === 'mild') {
                marker.style.backgroundColor = 'rgba(255, 235, 59, 0.7)';
            } else if (feature.severity === 'moderate') {
                marker.style.backgroundColor = 'rgba(255, 152, 0, 0.7)';
            } else if (feature.severity === 'severe') {
                marker.style.backgroundColor = 'rgba(244, 67, 54, 0.7)';
            }
            
            // Add tooltip with description
            const tooltip = document.createElement('div');
            tooltip.className = 'annotation-tooltip';
            tooltip.textContent = feature.name.charAt(0).toUpperCase() + feature.name.slice(1) + 
                                 (feature.description ? ': ' + feature.description : '');
            tooltip.style.position = 'absolute';
            tooltip.style.bottom = '30px';
            tooltip.style.left = '50%';
            tooltip.style.transform = 'translateX(-50%)';
            tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            tooltip.style.color = '#fff';
            tooltip.style.padding = '5px 10px';
            tooltip.style.borderRadius = '4px';
            tooltip.style.fontSize = '12px';
            tooltip.style.width = 'max-content';
            tooltip.style.maxWidth = '200px';
            tooltip.style.display = 'none';
            tooltip.style.zIndex = '101';
            
            // Add tooltip functionality
            marker.appendChild(tooltip);
            marker.addEventListener('mouseenter', () => {
                tooltip.style.display = 'block';
            });
            marker.addEventListener('mouseleave', () => {
                tooltip.style.display = 'none';
            });
            
            overlay.appendChild(marker);
        });
    };
    
    // Trigger onload if image is already loaded
    if (image.complete) {
        image.onload();
    }
}

/**
 * Calculate position for an annotation based on feature location
 * @param {Object} position - The feature position description
 * @param {number} imageWidth - The width of the image
 * @param {number} imageHeight - The height of the image
 * @return {Object} The x,y coordinates for the annotation
 */
function calculatePosition(position, imageWidth, imageHeight) {
    let x = imageWidth / 2; // Default to center
    let y = imageHeight / 2; // Default to middle
    
    // Horizontal position
    if (position.horizontal === 'left') {
        x = imageWidth * 0.25;
    } else if (position.horizontal === 'right') {
        x = imageWidth * 0.75;
    }
    
    // Vertical position
    if (position.verticalPosition === 'top') {
        y = imageHeight * 0.25;
    } else if (position.verticalPosition === 'bottom') {
        y = imageHeight * 0.75;
    }
    
    // Handle specific regions
    if (position.region === 'nose') {
        y = imageHeight * 0.5;
    } else if (position.region === 'eyes') {
        y = imageHeight * 0.35;
    } else if (position.region === 'lips') {
        y = imageHeight * 0.7;
    }
    
    return { x, y };
}

// =================== TEXT FORMATTING IMPROVEMENTS ====================

/**
 * Improve the formatting of analysis text for better readability
 */
function improveTextFormatting() {
    // Get all analysis text elements
    const analysisTexts = document.querySelectorAll('.analysis-text');
    
    analysisTexts.forEach(container => {
        // Replace asterisks with appropriate HTML elements
        container.innerHTML = container.innerHTML.replace(/\*\*\*(.*?)\*\*\*/g, '<h5 class="mt-3 mb-2">$1</h5>');
        container.innerHTML = container.innerHTML.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        container.innerHTML = container.innerHTML.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Improve paragraph spacing
        const paragraphs = container.querySelectorAll('p');
        paragraphs.forEach(p => {
            p.style.marginBottom = '1rem';
            
            // Format sections within paragraphs
            if (p.textContent.includes('Observation:')) {
                formatSection(p, 'Observation:', 'observation-section');
            }
            if (p.textContent.includes('Treatment Options:')) {
                formatSection(p, 'Treatment Options:', 'treatment-section');
            }
            if (p.textContent.includes('Expected Outcomes:')) {
                formatSection(p, 'Expected Outcomes:', 'outcomes-section');
            }
            
            // Add severity indicators
            addSeverityIndicators(p);
        });
    });
}

/**
 * Format a specific section within the analysis text
 * @param {Element} paragraph - The paragraph element
 * @param {string} sectionName - The section name to find
 * @param {string} className - The class to apply
 */
function formatSection(paragraph, sectionName, className) {
    let html = paragraph.innerHTML;
    html = html.replace(
        new RegExp(sectionName, 'g'),
        `<div class="${className}"><strong>${sectionName}</strong>`
    );
    html += '</div>';
    paragraph.innerHTML = html;
}

/**
 * Add visual severity indicators to text
 * @param {Element} paragraph - The paragraph element
 */
function addSeverityIndicators(paragraph) {
    const severityTerms = [
        { term: 'mild', class: 'text-success', icon: 'fa-check-circle' },
        { term: 'moderate', class: 'text-warning', icon: 'fa-exclamation-circle' },
        { term: 'severe', class: 'text-danger', icon: 'fa-exclamation-triangle' }
    ];
    
    let html = paragraph.innerHTML;
    
    severityTerms.forEach(item => {
        const regex = new RegExp(`(\\b${item.term}\\b)`, 'gi');
        html = html.replace(regex, `<span class="severity-indicator ${item.class}"><i class="fas ${item.icon} me-1"></i>$1</span>`);
    });
    
    paragraph.innerHTML = html;
}

// =================== MEDICAL TERM TOOLTIPS ====================

/**
 * Add tooltips to technical medical terms
 */
function addMedicalTermTooltips() {
    const medicalTerms = {
        'hyperpigmentation': 'Darkening of the skin due to excess melanin production',
        'ptosis': 'Drooping of the upper eyelid',
        'rhinoplasty': 'Surgical procedure to reshape the nose',
        'blepharoplasty': 'Surgical procedure to reshape the eyelids',
        'dermal fillers': 'Injectable treatments to add volume to facial areas',
        'botox': 'Injectable treatment that temporarily weakens muscles to reduce wrinkles',
        'chemical peel': 'Treatment that applies a chemical solution to remove damaged skin layers',
        'microdermabrasion': 'Procedure that uses tiny crystals to exfoliate the skin surface',
        'fractional laser': 'Laser treatment that creates microscopic wounds to stimulate collagen',
        'collagen': 'Protein that provides structure and elasticity to the skin',
        'elastin': 'Protein that allows tissues to stretch and return to shape',
        'microneedling': 'Procedure that creates tiny punctures to stimulate skin healing',
        'hyaluronic acid': 'Substance that helps maintain skin hydration',
        'liposuction': 'Surgical procedure to remove excess fat'
    };
    
    // Find and add tooltips to all instances of medical terms
    const analysisContainer = document.querySelector('.facial-assessment-container');
    if (!analysisContainer) return;
    
    Object.keys(medicalTerms).forEach(term => {
        const regex = new RegExp(`\\b${term}\\b`, 'gi');
        
        // Use TreeWalker to find text nodes
        const walker = document.createTreeWalker(
            analysisContainer,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const textNodes = [];
        let node;
        while (node = walker.nextNode()) {
            if (regex.test(node.nodeValue)) {
                textNodes.push(node);
            }
        }
        
        // Replace terms with tooltips in text nodes
        textNodes.forEach(textNode => {
            const parent = textNode.parentNode;
            
            // Skip if parent is already a tooltip or inside one
            if (parent.classList && (parent.classList.contains('medical-term') || 
                parent.closest('.medical-term'))) {
                return;
            }
            
            const fragment = document.createDocumentFragment();
            const parts = textNode.nodeValue.split(new RegExp(`(\\b${term}\\b)`, 'i'));
            
            parts.forEach(part => {
                if (part.toLowerCase() === term.toLowerCase()) {
                    const span = document.createElement('span');
                    span.className = 'medical-term';
                    span.textContent = part;
                    span.style.borderBottom = '1px dotted #33b5a6';
                    span.style.cursor = 'help';
                    span.style.position = 'relative';
                    
                    // Create tooltip
                    const tooltip = document.createElement('span');
                    tooltip.className = 'medical-tooltip';
                    tooltip.textContent = medicalTerms[term];
                    tooltip.style.position = 'absolute';
                    tooltip.style.bottom = '100%';
                    tooltip.style.left = '50%';
                    tooltip.style.transform = 'translateX(-50%)';
                    tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
                    tooltip.style.color = '#fff';
                    tooltip.style.padding = '5px 10px';
                    tooltip.style.borderRadius = '4px';
                    tooltip.style.fontSize = '12px';
                    tooltip.style.width = 'max-content';
                    tooltip.style.maxWidth = '200px';
                    tooltip.style.display = 'none';
                    tooltip.style.zIndex = '1000';
                    
                    // Add event listeners for tooltip
                    span.addEventListener('mouseenter', () => {
                        tooltip.style.display = 'block';
                    });
                    span.addEventListener('mouseleave', () => {
                        tooltip.style.display = 'none';
                    });
                    
                    span.appendChild(tooltip);
                    fragment.appendChild(span);
                } else {
                    fragment.appendChild(document.createTextNode(part));
                }
            });
            
            parent.replaceChild(fragment, textNode);
        });
    });
}