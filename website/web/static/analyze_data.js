document.addEventListener("DOMContentLoaded", function () {
  const fileSelect = document.getElementById("file-select");
  const generateBtn = document.getElementById("generate-plot-btn");
  const analysisPrompt = document.getElementById("analysis-prompt");

  const resultSection = document.getElementById("plot-result-section");
  const loadingSpinner = document.getElementById("plot-loading");
  const plotOutput = document.getElementById("plot-output");
  const plotActions = document.getElementById("plot-actions");
  const plotNameInput = document.getElementById("plot-name-input");
  const savePlotBtn = document.getElementById("save-plot-btn");
  const generateAnotherBtn = document.getElementById("generate-another-btn");

  let generatedPlotData = null; // To store the base64 image data

  const businessName =
    document.querySelector(".analyze-container").dataset.businessName;
  // --- Step 1: Load User's Files into Dropdown ---
  async function loadUserFiles() {
    try {
      const response = await fetch("/dashboard/files");
      if (!response.ok) throw new Error("Failed to fetch files.");

      const data = await response.json();
      fileSelect.innerHTML = '<option value="">-- Select a file --</option>'; // Clear loading text

      if (data.files && data.files.length > 0) {
        // Sort by most recent upload_date (desc)
        data.files
          .sort((a, b) =>
            (b.upload_date || "").localeCompare(a.upload_date || "")
          )
          .forEach((file) => {
            const option = document.createElement("option");
            option.value = file._id;
            option.textContent = file.filename;
            fileSelect.appendChild(option);
          });
      } else {
        fileSelect.innerHTML =
          '<option value="">No CSV files found. Please upload one.</option>';
        generateBtn.disabled = true;
      }
    } catch (error) {
      console.error("Error loading files:", error);
      fileSelect.innerHTML = '<option value="">Error loading files</option>';
    }
  }

  // --- Step 2: Handle Plot Generation ---
  async function handleGeneratePlot() {
    const fileId = fileSelect.value;
    const prompt = analysisPrompt.value.trim();

    if (!fileId) {
      window.validator.showErrorNotification("Please select a file.");
      return;
    }

    // Validate prompt using the validator
    const promptField = document.getElementById("analysis-prompt");
    const promptValid = window.validator.isFieldValid(promptField, {
      type: "analysis_prompt",
      required: true,
    });
    if (!promptValid) {
      window.validator.showErrorNotification(
        "Please provide a valid analysis prompt (10-500 characters)."
      );
      return;
    }

    // Show loading state
    document.querySelector(".analysis-request-section").style.display = "none";
    resultSection.style.display = "block";
    loadingSpinner.style.display = "block";
    plotOutput.style.display = "none";
    plotActions.style.display = "none";

    try {
      const response = await fetch(`/analyze_data/${businessName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: fileId, prompt: prompt }),
      });

      const data = await response.json();

      if (!response.ok || data.success === false) {
        throw new Error(data.error || "Failed to generate plot.");
      }

      // Display the generated plot
      generatedPlotData = data.plot_image; // Store base64 data
      plotOutput.innerHTML = `<img src="${generatedPlotData}" alt="Generated Plot">`;
      plotNameInput.value = `Plot based on ${
        fileSelect.options[fileSelect.selectedIndex].text
      }`;
    } catch (error) {
      console.error("Error generating plot:", error);
      plotOutput.innerHTML = `<p style="color: red;"><strong>Error:</strong> ${error.message}</p>`;
    } finally {
      // Hide loading spinner and show output/actions
      loadingSpinner.style.display = "none";
      plotOutput.style.display = "block";
      plotActions.style.display = "flex";
    }
  }

  // --- Step 3: Handle Saving the Plot ---
  async function handleSavePlot() {
    const plotName = plotNameInput.value.trim();

    // Validate plot name using the validator
    const plotNameField = document.getElementById("plot-name-input");
    const plotNameValid = window.validator.isFieldValid(plotNameField, {
      type: "plot_name",
      required: true,
    });
    if (!plotNameValid) {
      window.validator.showErrorNotification(
        "Please provide a valid plot name (2-100 characters)."
      );
      return;
    }

    if (!generatedPlotData) {
      window.validator.showErrorNotification("No plot data available to save.");
      return;
    }

    savePlotBtn.textContent = "Saving...";
    savePlotBtn.disabled = true;

    try {
      const response = await fetch(`/save_generated_plot/${businessName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_name: plotName,
          image_data: generatedPlotData,
          based_on_file: fileSelect.value,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Failed to save the plot.");
      }

      // On success, redirect to business page
      window.location.href = `/business_page/${businessName}?success=plot_saved`;
    } catch (error) {
      console.error("Error saving plot:", error);
      alert(`Error: ${error.message}`);
      savePlotBtn.textContent = "Save to Profile";
      savePlotBtn.disabled = false;
    }
  }

  // --- Step 4: Reset the UI ---
  function resetUI() {
    document.querySelector(".analysis-request-section").style.display = "block";
    resultSection.style.display = "none";
    analysisPrompt.value = "";
    generatedPlotData = null;
  }

  // --- Attach Event Listeners ---
  generateBtn.addEventListener("click", handleGeneratePlot);
  savePlotBtn.addEventListener("click", handleSavePlot);
  generateAnotherBtn.addEventListener("click", resetUI);

  // --- Initial Load ---
  loadUserFiles();
});
