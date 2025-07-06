///////////// Profile page JavaScript functionality /////////////

let currentPlotIndex = 0;
let plots = [];

// Initialize plots data from server
function initializePlots(plotsData) {
    plots = plotsData;
    if (plots.length > 0) {
        showPlot(0);
    }
}

function showPlot(index) {
    if (plots.length === 0) return;
    
    currentPlotIndex = index;
    const plot = plots[index];
    document.getElementById('currentPlot').src = plot.image;
    document.getElementById('currentPlotName').textContent = plot.image_name;
    document.getElementById('plotCounter').textContent = `${index + 1}/${plots.length}`;
    
    // Update button states
    document.getElementById('prevBtn').style.display = index === 0 ? 'none' : 'block';
    document.getElementById('nextBtn').style.display = index === plots.length - 1 ? 'none' : 'block';
}

function downloadCurrentPlot() {
    if (plots.length === 0) return;
    
    const plot = plots[currentPlotIndex];
    const link = document.createElement('a');
    link.href = plot.image;
    link.download = `${plot.image_name}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function nextPlot() {
    if (currentPlotIndex < plots.length - 1) {
        showPlot(currentPlotIndex + 1);
    }
}

function previousPlot() {
    if (currentPlotIndex > 0) {
        showPlot(currentPlotIndex - 1);
    }
}

// Temporary success message function for profile page
function showTemporarySuccessMessage(title, message, duration = 3000) {
    // Create success message container
    const successContainer = document.createElement('div');
    successContainer.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 20px 25px;
        border-radius: 12px;
        box-shadow: 0 8px 25px rgba(40, 167, 69, 0.3);
        font-family: Arial, sans-serif;
        font-size: 14px;
        font-weight: 600;
        z-index: 1000;
        transform: translateX(100%);
        transition: transform 0.3s ease-out;
        max-width: 300px;
    `;
    
    successContainer.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="font-size: 18px;">✓</div>
            <div>
                <div style="font-weight: 700; margin-bottom: 4px;">${title}</div>
                <div style="font-weight: 400; opacity: 0.9;">${message}</div>
            </div>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(successContainer);
    
    // Animate in
    setTimeout(() => {
        successContainer.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto-remove after duration
    setTimeout(() => {
        successContainer.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (document.body.contains(successContainer)) {
                document.body.removeChild(successContainer);
            }
        }, 300);
    }, duration);
} 