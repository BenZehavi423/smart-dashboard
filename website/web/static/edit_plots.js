///////////// Edit plots page JavaScript functionality /////////////
document.addEventListener("DOMContentLoaded", function () {
  if (typeof socket !== "undefined" && businessName) {
    // When the page loads, tell the server we're starting to edit
    socket.emit("start_editing", { business_name: businessName });

    // Listen for the 'business_locked' event from the server
    socket.on("business_locked", function (data) {
      // If we receive this event, it means we have the lock
    });

    // Listen for the 'lock_failed' event from the server
    socket.on("lock_failed", function (data) {
      // If we receive this event, it means someone else is editing
      // Disable the page and show a message
      document.body.innerHTML = `
                <div class="container">
                    <h1>Editing Locked</h1>
                    <p>This business is currently being edited by <strong>${data.username}</strong>. Please try again later.</p>
                    <a href="/business_page/${businessName}" class="button">Back to Business Page</a>
                </div>
            `;
    });

    // Listen for the 'business_unlocked' event from the server
    socket.on("business_unlocked", function () {
      // If we receive this event, it means the lock has been released
      // You can optionally reload the page to allow editing
      window.location.reload();
    });

    // When the user leaves the page, tell the server we're stopping editing
    window.addEventListener("beforeunload", function () {
      socket.emit("stop_editing", { business_name: businessName });
    });
  }
});

let hasChanges = false;
let plotSelections = {};
let selectedPlotOrder = [];
let plotsData = [];
let originalPlotSelections = {}; // Store original state for comparison
let originalPlotOrder = []; // Store original order for comparison

const container = document.querySelector(".edit-plots-container");
const businessName = container ? container.dataset.businessName : null;

// Initialize data from server
function initializeEditPlots(allPlots, presentedPlots) {
  plotsData = allPlots;

  // Initialize plot selections
  allPlots.forEach((plot) => {
    plotSelections[plot._id] = plot.is_presented;
    originalPlotSelections[plot._id] = plot.is_presented; // Store original state
  });

  // Initialize selected plot order from current presented plots
  presentedPlots.forEach((plot) => {
    selectedPlotOrder.push(plot._id);
    originalPlotOrder.push(plot._id); // Store original order
  });
}

function togglePlotSelection(plotId, isSelected) {
  hasChanges = true;
  plotSelections[plotId] = isSelected;

  if (isSelected && !selectedPlotOrder.includes(plotId)) {
    selectedPlotOrder.push(plotId);
  } else if (!isSelected) {
    selectedPlotOrder = selectedPlotOrder.filter((id) => id !== plotId);
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
  document.getElementById("step1").style.display = "none";
  document.getElementById("step2").style.display = "block";
  populateReorderList();
}

function backToStep1() {
  document.getElementById("step2").style.display = "none";
  document.getElementById("step1").style.display = "block";
}

// Check if current state is different from original state
function hasActualChanges() {
  // Check if plot selections changed
  for (const plotId in plotSelections) {
    if (plotSelections[plotId] !== originalPlotSelections[plotId]) {
      return true;
    }
  }

  // Check if plot order changed
  if (selectedPlotOrder.length !== originalPlotOrder.length) {
    return true;
  }

  for (let i = 0; i < selectedPlotOrder.length; i++) {
    if (selectedPlotOrder[i] !== originalPlotOrder[i]) {
      return true;
    }
  }

  return false;
}

function populateReorderList() {
  const reorderList = document.getElementById("reorderList");
  reorderList.innerHTML = "";

  if (selectedPlotOrder.length === 0) {
    reorderList.innerHTML =
      '<div class="no-plots-message">No plots selected for presentation.</div>';
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
  const dropZone = document.createElement("div");
  dropZone.className = "drop-zone";
  dropZone.dataset.index = index;
  dropZone.innerHTML = '<div class="drop-indicator"></div>';

  dropZone.addEventListener("dragover", handleDropZoneDragOver);
  dropZone.addEventListener("dragenter", handleDropZoneDragEnter);
  dropZone.addEventListener("dragleave", handleDropZoneDragLeave);
  dropZone.addEventListener("drop", handleDropZoneDrop);

  return dropZone;
}

function createReorderItem(plot, index) {
  const item = document.createElement("div");
  item.className = "reorder-item";
  item.draggable = true;
  item.dataset.plotId = plot._id;

  item.innerHTML = `
        <div class="reorder-number">${index + 1}</div>
        <div class="reorder-image">
            <img src="${plot.image}" alt="${
    plot.image_name
  }" style="max-width: 100px; height: auto;">
        </div>
        <div class="reorder-info">
            <strong>${plot.image_name}</strong><br>
            <small>Created: ${new Date(
              plot.created_time
            ).toLocaleString()}</small>
        </div>
        <div class="reorder-actions">
            <button class="button small" onclick="moveUp('${
              plot._id
            }')">↑</button>
            <button class="button small" onclick="moveDown('${
              plot._id
            }')">↓</button>
        </div>
    `;

  // Add enhanced drag and drop functionality
  item.addEventListener("dragstart", handleDragStart);
  item.addEventListener("dragend", handleDragEnd);
  item.addEventListener("dragover", handleDragOver);
  item.addEventListener("dragenter", handleDragEnter);
  item.addEventListener("dragleave", handleDragLeave);
  item.addEventListener("drop", handleDrop);

  return item;
}

function getPlotById(plotId) {
  return plotsData.find((plot) => plot._id === plotId);
}

function moveUp(plotId) {
  const index = selectedPlotOrder.indexOf(plotId);
  if (index > 0) {
    [selectedPlotOrder[index], selectedPlotOrder[index - 1]] = [
      selectedPlotOrder[index - 1],
      selectedPlotOrder[index],
    ];
    hasChanges = true;
    populateReorderList();
  }
}

function moveDown(plotId) {
  const index = selectedPlotOrder.indexOf(plotId);
  if (index < selectedPlotOrder.length - 1) {
    [selectedPlotOrder[index], selectedPlotOrder[index + 1]] = [
      selectedPlotOrder[index + 1],
      selectedPlotOrder[index],
    ];
    hasChanges = true;
    populateReorderList();
  }
}

// Enhanced drag and drop functionality with drop zones
let draggedItem = null;
let activeDropZone = null;

function handleDragStart(e) {
  draggedItem = this;
  e.dataTransfer.effectAllowed = "move";
  this.classList.add("dragging");
}

function handleDragEnd(e) {
  this.classList.remove("dragging");
  draggedItem = null;

  // Remove all drop zone indicators
  document.querySelectorAll(".drop-zone").forEach((zone) => {
    zone.classList.remove("active");
  });
}

function handleDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
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
  e.dataTransfer.dropEffect = "move";
}

function handleDropZoneDragEnter(e) {
  e.preventDefault();
  // Only activate if we're not already on this drop zone
  if (this !== activeDropZone) {
    // Remove active class from previous drop zone
    if (activeDropZone) {
      activeDropZone.classList.remove("active");
    }
    this.classList.add("active");
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
      this.classList.remove("active");
      activeDropZone = null;
    }
  }
}

function handleDropZoneDrop(e) {
  e.preventDefault();
  this.classList.remove("active");
  activeDropZone = null;

  if (draggedItem) {
    const targetIndex = parseInt(this.dataset.index);
    const draggedPlotId = draggedItem.dataset.plotId;
    const currentIndex = selectedPlotOrder.indexOf(draggedPlotId);

    // Don't do anything if dropping at the same position
    if (currentIndex === targetIndex) {
      return;
    }

    // Remove from current position
    selectedPlotOrder.splice(currentIndex, 1);

    // Insert at target position
    selectedPlotOrder.splice(targetIndex, 0, draggedPlotId);
    hasChanges = true;
    populateReorderList();
  }
}

function sortByName(direction = "asc") {
  selectedPlotOrder.sort((a, b) => {
    const plotA = getPlotById(a);
    const plotB = getPlotById(b);
    const comparison = plotA.image_name.localeCompare(plotB.image_name);
    return direction === "asc" ? comparison : -comparison;
  });
  hasChanges = true;
  populateReorderList();
}

function sortByDate(direction = "asc") {
  selectedPlotOrder.sort((a, b) => {
    const plotA = getPlotById(a);
    const plotB = getPlotById(b);
    const comparison =
      new Date(plotA.created_time) - new Date(plotB.created_time);
    return direction === "asc" ? comparison : -comparison;
  });
  hasChanges = true;
  populateReorderList();
}

function resetOrder() {
  // Reset to the order from step 1
  selectedPlotOrder = [];
  Object.keys(plotSelections).forEach((plotId) => {
    if (plotSelections[plotId]) {
      selectedPlotOrder.push(plotId);
    }
  });
  hasChanges = true;
  populateReorderList();
}

function saveAllChanges() {
  if (!businessName) {
    alert("Error: Could not identify the business. Please refresh the page.");
    return;
  }

  if (!hasActualChanges()) {
    showNoChangesModal();
    return;
  }

  const plotUpdates = Object.keys(plotSelections).map((plotId) => ({
    plot_id: plotId,
    is_presented: plotSelections[plotId],
  }));

  fetch(`/edit_plots/${businessName}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      plot_updates: plotUpdates,
      plot_order: selectedPlotOrder,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        hasChanges = false;
        window.location.href = `/business_page/${businessName}?success=changes_saved`;
      } else {
        showInfoModal("Error", "Error saving changes. Please try again.", "OK");
      }
    })
    .catch((error) => {
      console.error("Error saving changes:", error);
      showInfoModal(
        "Error",
        "An unexpected error occurred. Please check the console for details.",
        "OK"
      );
    });
}

// Warn user before leaving page with unsaved changes
window.addEventListener("beforeunload", function (e) {
  if (hasChanges && hasActualChanges()) {
    e.preventDefault();
    e.returnValue = "You have unsaved changes. Are you sure you want to leave?";
  }
});

// Override the "Back to Business Page" link to check for unsaved changes
document.addEventListener("DOMContentLoaded", function () {
  const backLink = document.querySelector(
    `a[href*="/business_page/${businessName}"]`
  );
  if (backLink) {
    backLink.addEventListener("click", function (e) {
      if (hasChanges && hasActualChanges()) {
        e.preventDefault();
        const originalHasChanges = hasChanges;
        hasChanges = false;
        showUnsavedChangesModal(
          () => {
            hasChanges = originalHasChanges;
          },
          () => {
            window.location.href = this.href;
          }
        );
      }
    });
  }
});

// Custom modal system for edit_plots.js
function createCustomModal(title, message, buttons) {
  // Create modal overlay
  const modalOverlay = document.createElement("div");
  modalOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    `;

  // Create modal content
  const modalContent = document.createElement("div");
  modalContent.style.cssText = `
        background: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        max-width: 400px;
        text-align: center;
        font-family: Arial, sans-serif;
    `;

  // Create buttons HTML
  const buttonsHTML = buttons
    .map(
      (button, index) => `
        <button id="customModalBtn${index}" style="
            background: ${button.color};
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: background-color 0.3s;
            margin: 0 5px;
        ">${button.text}</button>
    `
    )
    .join("");

  modalContent.innerHTML = `
        <h3 style="margin: 0 0 20px 0; color: #333; font-size: 20px;">${title}</h3>
        <p style="margin: 0 0 25px 0; color: #666; line-height: 1.5;">
            ${message}
        </p>
        <div style="display: flex; gap: 15px; justify-content: center;">
            ${buttonsHTML}
        </div>
    `;

  // Add hover effects and click handlers for each button
  buttons.forEach((button, index) => {
    const btnElement = modalContent.querySelector(`#customModalBtn${index}`);

    btnElement.addEventListener("mouseenter", () => {
      btnElement.style.backgroundColor = button.hoverColor;
    });
    btnElement.addEventListener("mouseleave", () => {
      btnElement.style.backgroundColor = button.color;
    });

    btnElement.addEventListener("click", () => {
      button.action();
      document.body.removeChild(modalOverlay);
    });
  });

  // Add modal to page
  modalOverlay.appendChild(modalContent);
  document.body.appendChild(modalOverlay);

  // Close modal when clicking outside
  modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) {
      document.body.removeChild(modalOverlay);
    }
  });
}

// Custom modal functions
function showCustomModal(options) {
  createCustomModal(options.title, options.message, options.buttons);
}

function showNoChangesModal() {
  createCustomModal("No Changes Made", "No changes were made to your plots.", [
    {
      text: "Continue Editing",
      action: () => {},
    },
    {
      text: "Return to Business Page",
      action: () => {
        window.location.href = `/business_page/${businessName}`;
      },
    },
  ]);
}

function showUnsavedChangesModal(onContinueEditing, onDiscardChanges) {
  createCustomModal(
    "Unsaved Changes",
    "You have unsaved changes. Are you sure you want to leave without saving?",
    [
      {
        text: "Continue Editing",
        color: "#007bff",
        hoverColor: "#0056b3",
        action: onContinueEditing || (() => {}),
      },
      {
        text: "Discard Changes",
        color: "#dc3545",
        hoverColor: "#c82333",
        action:
          onDiscardChanges ||
          (() => {
            window.location.href = "/profile";
          }),
      },
    ]
  );
}

function showInfoModal(title, message, buttonText = "OK") {
  createCustomModal(title, message, [
    {
      text: buttonText,
      color: "#007bff",
      hoverColor: "#0056b3",
      action: () => {},
    },
  ]);
}

// Assign modal functions to global scope
window.showModal = showCustomModal;
window.showNoChangesModal = showNoChangesModal;
window.showUnsavedChangesModal = showUnsavedChangesModal;
window.showInfoModal = showInfoModal;
