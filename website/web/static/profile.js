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