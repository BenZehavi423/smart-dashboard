///////////// Analyze Data Page JavaScript functionality /////////////
// TODO: analyze_data

let uploadedImages = [];

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    setupFileUpload();
    setupDragAndDrop();
});

function setupFileUpload() {
    const fileInput = document.getElementById('imageUpload');
    fileInput.addEventListener('change', handleFileSelect);
}

function setupDragAndDrop() {
    const dropzone = document.querySelector('.upload-dropzone');
    
    dropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    
    dropzone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropzone.classList.remove('dragover');
    });
    
    dropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        handleFiles(files);
    });
}

function handleFileSelect(event) {
    const files = event.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    const imageFiles = Array.from(files).filter(file => 
        file.type.startsWith('image/')
    );
    
    if (imageFiles.length === 0) {
        alert('Please select image files only.');
        return;
    }
    
    imageFiles.forEach(file => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const imageData = e.target.result;
            addImageToPreview(file.name, imageData);
        };
        reader.readAsDataURL(file);
    });
    
    // Show preview section
    document.getElementById('imagesPreview').style.display = 'block';
}

function addImageToPreview(originalName, imageData) {
    const imageId = 'img_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    const imageCard = document.createElement('div');
    imageCard.className = 'image-card';
    imageCard.id = imageId;
    
    // Generate a default name from the original filename
    const defaultName = originalName.replace(/\.[^/.]+$/, ""); // Remove extension
    
    imageCard.innerHTML = `
        <div class="image-preview">
            <img src="${imageData}" alt="${defaultName}">
        </div>
        <div class="image-controls">
            <input type="text" class="image-name-input" value="${defaultName}" placeholder="Enter image name">
            <div class="save-checkbox">
                <input type="checkbox" id="save_${imageId}" checked>
                <label for="save_${imageId}">Save to Profile</label>
            </div>
            <button class="remove-image" onclick="removeImage('${imageId}')">Remove</button>
        </div>
    `;
    
    document.getElementById('imagesGrid').appendChild(imageCard);
    
    // Store image data
    uploadedImages.push({
        id: imageId,
        originalName: originalName,
        imageData: imageData,
        name: defaultName,
        saveToProfile: true
    });
    
    // Add event listeners for name changes and checkbox changes
    const nameInput = imageCard.querySelector('.image-name-input');
    const saveCheckbox = imageCard.querySelector('input[type="checkbox"]');
    
    nameInput.addEventListener('input', function() {
        updateImageData(imageId, 'name', this.value);
    });
    
    saveCheckbox.addEventListener('change', function() {
        updateImageData(imageId, 'saveToProfile', this.checked);
    });
}

function updateImageData(imageId, field, value) {
    const imageIndex = uploadedImages.findIndex(img => img.id === imageId);
    if (imageIndex !== -1) {
        uploadedImages[imageIndex][field] = value;
    }
}

function removeImage(imageId) {
    // Remove from DOM
    const imageCard = document.getElementById(imageId);
    if (imageCard) {
        imageCard.remove();
    }
    
    // Remove from data array
    uploadedImages = uploadedImages.filter(img => img.id !== imageId);
    
    // Hide preview section if no images left
    if (uploadedImages.length === 0) {
        document.getElementById('imagesPreview').style.display = 'none';
    }
}

function saveSelectedImages() {
    const imagesToSave = uploadedImages.filter(img => img.saveToProfile);
    
    if (imagesToSave.length === 0) {
        alert('Please select at least one image to save.');
        return;
    }
    
    // Prepare data for server
    const newPlots = imagesToSave.map(img => ({
        image_name: img.name,
        image: img.imageData,
        files: [], // Empty for now, will be populated when analysis is implemented
        save_to_business: true
    }));
    
    // Show loading state
    const saveButton = document.querySelector('.save-actions .button.blue');
    const originalText = saveButton.textContent;
    saveButton.textContent = 'Saving...';
    saveButton.disabled = true;
    
    // Send to server
    fetch('/analyze_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            new_plots: newPlots
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Successfully saved ${data.saved_count} image(s) to your business page!`);
            // Redirect back to business page
            window.location.href = '/business_page';
        } else {
            alert('Error saving images. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error saving images. Please try again.');
    })
    .finally(() => {
        // Restore button state
        saveButton.textContent = originalText;
        saveButton.disabled = false;
    });
}

function clearAllImages() {
    if (uploadedImages.length === 0) {
        return;
    }
    
    if (confirm('Are you sure you want to clear all uploaded images?')) {
        // Clear DOM
        document.getElementById('imagesGrid').innerHTML = '';
        
        // Clear data
        uploadedImages = [];
        
        // Hide preview section
        document.getElementById('imagesPreview').style.display = 'none';
        
        // Reset file input
        document.getElementById('imageUpload').value = '';
    }
}

// Future: Function to handle text analysis requests
function generateAnalysis() {
    const analysisText = document.querySelector('.analysis-request textarea').value;
    
    if (!analysisText.trim()) {
        alert('Please describe the analysis you want.');
        return;
    }
    
    // This will be implemented in the future
    alert('Text analysis feature will be implemented in the future.');
} 