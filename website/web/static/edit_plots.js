///////////// Edit plots page JavaScript functionality /////////////

let hasChanges = false;
let plotSelections = {};
let selectedPlotOrder = [];
let plotsData = [];

// Initialize data from server
function initializeEditPlots(allPlots, presentedPlots) {
    plotsData = allPlots;
    
    // Initialize plot selections
    allPlots.forEach(plot => {
        plotSelections[plot._id] = plot.is_presented;
    });
    
    // Initialize selected plot order from current presented plots
    presentedPlots.forEach(plot => {
        selectedPlotOrder.push(plot._id);
    });
}

function togglePlotSelection(plotId, isSelected) {
    hasChanges = true;
    plotSelections[plotId] = isSelected;
    
    if (isSelected && !selectedPlotOrder.includes(plotId)) {
        selectedPlotOrder.push(plotId);
    } else if (!isSelected) {
        selectedPlotOrder = selectedPlotOrder.filter(id => id !== plotId);
    }
}

function togglePlotCard(plotId) {
    const checkbox = document.getElementById(`plot_${plotId}`);
    const isCurrentlySelected = checkbox.checked;
    
    // Toggle the checkbox
    checkbox.checked = !isCurrentlySelected;
    
    // Call the existing toggle function
    togglePlotSelection(plotId, !isCurrentlySelected);
}

function proceedToStep2() {
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = 'block';
    populateReorderList();
}

function backToStep1() {
    document.getElementById('step2').style.display = 'none';
    document.getElementById('step1').style.display = 'block';
}

function populateReorderList() {
    const reorderList = document.getElementById('reorderList');
    reorderList.innerHTML = '';
    
    if (selectedPlotOrder.length === 0) {
        reorderList.innerHTML = '<div class="no-plots-message">No plots selected for presentation.</div>';
        return;
    }
    
    // Add initial drop zone
    const initialDropZone = createDropZone(0);
    reorderList.appendChild(initialDropZone);
    
    selectedPlotOrder.forEach((plotId, index) => {
        const plot = getPlotById(plotId);
        if (plot) {
            const plotItem = createReorderItem(plot, index);
            reorderList.appendChild(plotItem);
            
            // Add drop zone after each item
            const dropZone = createDropZone(index + 1);
            reorderList.appendChild(dropZone);
        }
    });
}

function createDropZone(index) {
    const dropZone = document.createElement('div');
    dropZone.className = 'drop-zone';
    dropZone.dataset.index = index;
    dropZone.innerHTML = '<div class="drop-indicator"></div>';
    
    dropZone.addEventListener('dragover', handleDropZoneDragOver);
    dropZone.addEventListener('dragenter', handleDropZoneDragEnter);
    dropZone.addEventListener('dragleave', handleDropZoneDragLeave);
    dropZone.addEventListener('drop', handleDropZoneDrop);
    
    return dropZone;
}

function createReorderItem(plot, index) {
    const item = document.createElement('div');
    item.className = 'reorder-item';
    item.draggable = true;
    item.dataset.plotId = plot._id;
    
    item.innerHTML = `
        <div class="reorder-number">${index + 1}</div>
        <div class="reorder-image">
            <img src="${plot.image}" alt="${plot.image_name}" style="max-width: 100px; height: auto;">
        </div>
        <div class="reorder-info">
            <strong>${plot.image_name}</strong><br>
            <small>Created: ${new Date(plot.created_time).toLocaleString()}</small>
        </div>
        <div class="reorder-actions">
            <button class="button small" onclick="moveUp('${plot._id}')">↑</button>
            <button class="button small" onclick="moveDown('${plot._id}')">↓</button>
        </div>
    `;
    
    // Add enhanced drag and drop functionality
    item.addEventListener('dragstart', handleDragStart);
    item.addEventListener('dragend', handleDragEnd);
    item.addEventListener('dragover', handleDragOver);
    item.addEventListener('dragenter', handleDragEnter);
    item.addEventListener('dragleave', handleDragLeave);
    item.addEventListener('drop', handleDrop);
    
    return item;
}

function getPlotById(plotId) {
    return plotsData.find(plot => plot._id === plotId);
}

function moveUp(plotId) {
    const index = selectedPlotOrder.indexOf(plotId);
    if (index > 0) {
        [selectedPlotOrder[index], selectedPlotOrder[index - 1]] = [selectedPlotOrder[index - 1], selectedPlotOrder[index]];
        hasChanges = true;
        populateReorderList();
    }
}

function moveDown(plotId) {
    const index = selectedPlotOrder.indexOf(plotId);
    if (index < selectedPlotOrder.length - 1) {
        [selectedPlotOrder[index], selectedPlotOrder[index + 1]] = [selectedPlotOrder[index + 1], selectedPlotOrder[index]];
        hasChanges = true;
        populateReorderList();
    }
}

// Enhanced drag and drop functionality with drop zones
let draggedItem = null;
let activeDropZone = null;

function handleDragStart(e) {
    draggedItem = this;
    e.dataTransfer.effectAllowed = 'move';
    this.classList.add('dragging');
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
    draggedItem = null;
    
    // Remove all drop zone indicators
    document.querySelectorAll('.drop-zone').forEach(zone => {
        zone.classList.remove('active');
    });
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleDragEnter(e) {
    e.preventDefault();
    // This is now handled by drop zones
}

function handleDragLeave(e) {
    e.preventDefault();
    // This is now handled by drop zones
}

function handleDrop(e) {
    e.preventDefault();
    // This is now handled by drop zones
}

// Drop zone handlers with improved stability
function handleDropZoneDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleDropZoneDragEnter(e) {
    e.preventDefault();
    // Only activate if we're not already on this drop zone
    if (this !== activeDropZone) {
        // Remove active class from previous drop zone
        if (activeDropZone) {
            activeDropZone.classList.remove('active');
        }
        this.classList.add('active');
        activeDropZone = this;
    }
}

function handleDropZoneDragLeave(e) {
    e.preventDefault();
    // Check if we're actually leaving the drop zone (not just moving to a child element)
    const rect = this.getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;
    
    // Only deactivate if we're actually outside the drop zone
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
        if (this === activeDropZone) {
            this.classList.remove('active');
            activeDropZone = null;
        }
    }
}

function handleDropZoneDrop(e) {
    e.preventDefault();
    this.classList.remove('active');
    activeDropZone = null;
    
    if (draggedItem) {
        const targetIndex = parseInt(this.dataset.index);
        const draggedPlotId = draggedItem.dataset.plotId;
        const currentIndex = selectedPlotOrder.indexOf(draggedPlotId);
        
        console.log(`Drop operation: plot ${draggedPlotId} from position ${currentIndex} to position ${targetIndex}`);
        
        // Don't do anything if dropping at the same position
        if (currentIndex === targetIndex) {
            console.log('Drop cancelled: same position');
            return;
        }
        
        // Remove from current position
        selectedPlotOrder.splice(currentIndex, 1);
        
        // Insert at target position
        selectedPlotOrder.splice(targetIndex, 0, draggedPlotId);
        
        console.log('Plot order updated after drag and drop');
        hasChanges = true;
        populateReorderList();
    }
}

function sortByName(direction = 'asc') {
    selectedPlotOrder.sort((a, b) => {
        const plotA = getPlotById(a);
        const plotB = getPlotById(b);
        const comparison = plotA.image_name.localeCompare(plotB.image_name);
        return direction === 'asc' ? comparison : -comparison;
    });
    hasChanges = true;
    populateReorderList();
}

function sortByDate(direction = 'asc') {
    selectedPlotOrder.sort((a, b) => {
        const plotA = getPlotById(a);
        const plotB = getPlotById(b);
        const comparison = new Date(plotA.created_time) - new Date(plotB.created_time);
        return direction === 'asc' ? comparison : -comparison;
    });
    hasChanges = true;
    populateReorderList();
}

function resetOrder() {
    // Reset to the order from step 1
    selectedPlotOrder = [];
    Object.keys(plotSelections).forEach(plotId => {
        if (plotSelections[plotId]) {
            selectedPlotOrder.push(plotId);
        }
    });
    hasChanges = true;
    populateReorderList();
}

function saveAllChanges() {
    // Check if any plots are selected
    const selectedCount = Object.values(plotSelections).filter(isSelected => isSelected).length;
    
    console.log(`Saving plot changes: ${selectedCount} plots selected, ${selectedPlotOrder.length} in order`);
    
    if (selectedCount === 0) {
        // No plots selected - show confirmation popup
        const confirmed = confirm('You haven\'t selected any images to present. Are you sure you want to continue? You will be returned to your profile with no plots displayed.');
        
        if (!confirmed) {
            // User cancelled - stay on the page
            console.log('User cancelled saving changes - no plots selected');
            return;
        }
        console.log('User confirmed saving with no plots selected');
    }
    
    const plotUpdates = Object.keys(plotSelections).map(plotId => ({
        plot_id: plotId,
        is_presented: plotSelections[plotId]
    }));
    
    console.log('Sending plot updates to server:', { plotUpdates, selectedPlotOrder });
    
    fetch('/edit_plots', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            plot_updates: plotUpdates,
            plot_order: selectedPlotOrder
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Plot changes saved successfully');
            alert('Changes saved successfully!');
            hasChanges = false;
            window.location.href = '/profile';
        } else {
            console.error('Server returned error when saving plot changes');
            alert('Error saving changes. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error saving plot changes:', error);
        alert('Error saving changes. Please try again.');
    });
}

// Warn user before leaving page with unsaved changes
window.addEventListener('beforeunload', function(e) {
    if (hasChanges) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
    }
}); 