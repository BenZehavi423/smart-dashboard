/**
 * Client-side validation for SmartDashboard application
 * Provides real-time validation feedback to users
 */

class ClientValidator {
  constructor() {
    this.errorMessages = {};
    this.validationRules = {
      username: {
        pattern: /^[a-zA-Z0-9._-]{3,20}$/,
        message:
          "Username must be 3-20 characters, letters, numbers, underscores, hyphens, and periods only",
      },
      password: {
        pattern: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]{3,30}$/,
        message:
          "Password must be at least 3 characters with 1 letter and 1 number",
      },
      email: {
        pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
        message: "Please enter a valid email address",
      },
      phone: {
        pattern: /^(\+?\d{4,15}|(\*|#)\d{4}|\d+-\d+)$/,
        message: "Invalid phone number format",
      },
      business_name: {
        pattern: /^.{2,50}$/,
        message: "Business name must be 2-50 characters long",
      },
      address: {
        pattern: /^.{5,100}$/,
        message: "Address must be 5-100 characters long",
      },
      analysis_prompt: {
        minLength: 10,
        maxLength: 500,
        message: "Analysis prompt must be 10-500 characters long",
      },
      plot_name: {
        minLength: 2,
        maxLength: 100,
        message: "Plot name must be 2-100 characters long",
      },
    };
  }

  /**
   * Initialize validation for a form
   * @param {string} formId - The ID of the form to validate
   * @param {Object} fieldRules - Object mapping field names to validation rules
   */
  initFormValidation(formId, fieldRules) {
    const form = document.getElementById(formId);
    if (!form) return;

    // Add validation to each field
    Object.keys(fieldRules).forEach((fieldName) => {
      const field = form.querySelector(`[name="${fieldName}"]`);
      if (field) {
        this.addFieldValidation(field, fieldRules[fieldName]);
      }
    });

    // Add form submission validation
    form.addEventListener("submit", (e) => {
      if (!this.validateForm(form, fieldRules)) {
        e.preventDefault();
        return false;
      }
    });
  }

  /**
   * Add validation to a specific field
   * @param {HTMLElement} field - The input field element
   * @param {Object} rules - Validation rules for this field
   */
  addFieldValidation(field, rules) {
    const fieldName = field.name;

    // Create error message container
    const errorContainer = document.createElement("div");
    errorContainer.className = "validation-error";
    errorContainer.style.display = "none";
    errorContainer.style.color = "#dc3545";
    errorContainer.style.fontSize = "0.875rem";
    errorContainer.style.marginTop = "0.25rem";
    field.parentNode.insertBefore(errorContainer, field.nextSibling);

    // Add real-time validation only for non-requirement fields
    if (!field.name.includes("username") && !field.name.includes("password")) {
      field.addEventListener("blur", () => {
        this.validateField(field, rules, errorContainer);
      });

      field.addEventListener("input", () => {
        // Clear error on input if field becomes valid
        if (this.isFieldValid(field, rules)) {
          this.hideError(errorContainer);
        }
      });
    }

    // Add visual feedback classes
    field.addEventListener("focus", () => {
      field.classList.remove("is-invalid", "is-valid");
    });
  }

  /**
   * Validate a single field
   * @param {HTMLElement} field - The input field element
   * @param {Object} rules - Validation rules
   * @param {HTMLElement} errorContainer - Error message container
   * @returns {boolean} - Whether the field is valid
   */
  validateField(field, rules, errorContainer) {
    const value = field.value.trim();
    const fieldName = field.name;

    // Check if required
    if (rules.required && !value) {
      this.showError(
        errorContainer,
        `${
          rules.label ||
          fieldName.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())
        } is required`
      );
      field.classList.add("is-invalid");
      field.classList.remove("is-valid");
      return false;
    }

    // Skip validation if not required and empty
    if (!rules.required && !value) {
      this.hideError(errorContainer);
      field.classList.remove("is-invalid", "is-valid");
      return true;
    }

    // Validate based on type
    let isValid = true;
    let errorMessage = "";

    if (rules.type === "username") {
      isValid = this.validationRules.username.pattern.test(value);
      errorMessage = this.validationRules.username.message;
    } else if (rules.type === "password") {
      isValid = this.validationRules.password.pattern.test(value);
      errorMessage = this.validationRules.password.message;
    } else if (rules.type === "email") {
      isValid = this.validationRules.email.pattern.test(value);
      errorMessage = this.validationRules.email.message;
    } else if (rules.type === "phone") {
      isValid = this.validationRules.phone.pattern.test(value);
      errorMessage = this.validationRules.phone.message;
    } else if (rules.type === "business_name") {
      isValid = this.validationRules.business_name.pattern.test(value);
      errorMessage = this.validationRules.business_name.message;
    } else if (rules.type === "address") {
      isValid = this.validationRules.address.pattern.test(value);
      errorMessage = this.validationRules.address.message;
    } else if (rules.type === "analysis_prompt") {
      isValid =
        value.length >= this.validationRules.analysis_prompt.minLength &&
        value.length <= this.validationRules.analysis_prompt.maxLength;
      errorMessage = this.validationRules.analysis_prompt.message;
    } else if (rules.type === "plot_name") {
      isValid =
        value.length >= this.validationRules.plot_name.minLength &&
        value.length <= this.validationRules.plot_name.maxLength;
      errorMessage = this.validationRules.plot_name.message;
    } else {
      // Default length validation
      if (rules.minLength && value.length < rules.minLength) {
        isValid = false;
        errorMessage = `${
          rules.label ||
          fieldName.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())
        } must be at least ${rules.minLength} characters long`;
      } else if (rules.maxLength && value.length > rules.maxLength) {
        isValid = false;
        errorMessage = `${
          rules.label ||
          fieldName.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())
        } must be no more than ${rules.maxLength} characters long`;
      }
    }

    if (isValid) {
      this.hideError(errorContainer);
      field.classList.add("is-valid");
      field.classList.remove("is-invalid");
    } else {
      this.showError(errorContainer, errorMessage);
      field.classList.add("is-invalid");
      field.classList.remove("is-valid");
    }

    return isValid;
  }

  /**
   * Check if a field is valid without showing error
   * @param {HTMLElement} field - The input field element
   * @param {Object} rules - Validation rules
   * @returns {boolean} - Whether the field is valid
   */
  isFieldValid(field, rules) {
    const value = field.value.trim();

    if (rules.required && !value) {
      return false;
    }

    if (!rules.required && !value) {
      return true;
    }

    if (rules.type === "username") {
      return this.validationRules.username.pattern.test(value);
    } else if (rules.type === "password") {
      return this.validationRules.password.pattern.test(value);
    } else if (rules.type === "email") {
      return this.validationRules.email.pattern.test(value);
    } else if (rules.type === "phone") {
      return this.validationRules.phone.pattern.test(value);
    } else if (rules.type === "business_name") {
      return this.validationRules.business_name.pattern.test(value);
    } else if (rules.type === "address") {
      return this.validationRules.address.pattern.test(value);
    } else if (rules.type === "analysis_prompt") {
      return (
        value.length >= this.validationRules.analysis_prompt.minLength &&
        value.length <= this.validationRules.analysis_prompt.maxLength
      );
    } else if (rules.type === "plot_name") {
      return (
        value.length >= this.validationRules.plot_name.minLength &&
        value.length <= this.validationRules.plot_name.maxLength
      );
    }

    return true;
  }

  /**
   * Validate entire form
   * @param {HTMLElement} form - The form element
   * @param {Object} fieldRules - Validation rules for all fields
   * @returns {boolean} - Whether the form is valid
   */
  validateForm(form, fieldRules) {
    let isValid = true;

    Object.keys(fieldRules).forEach((fieldName) => {
      const field = form.querySelector(`[name="${fieldName}"]`);
      const errorContainer = field ? field.nextElementSibling : null;

      if (
        field &&
        errorContainer &&
        errorContainer.classList.contains("validation-error")
      ) {
        if (!this.validateField(field, fieldRules[fieldName], errorContainer)) {
          isValid = false;
        }
      }
    });

    return isValid;
  }

  /**
   * Show error message
   * @param {HTMLElement} errorContainer - Error message container
   * @param {string} message - Error message to display
   */
  showError(errorContainer, message) {
    if (errorContainer) {
      errorContainer.textContent = message;
      errorContainer.style.display = "block";
    }
  }

  /**
   * Hide error message
   * @param {HTMLElement} errorContainer - Error message container
   */
  hideError(errorContainer) {
    if (errorContainer) {
      errorContainer.style.display = "none";
    }
  }

  /**
   * Validate file upload
   * @param {File} file - The file to validate
   * @param {Array} allowedExtensions - Allowed file extensions
   * @param {number} maxSize - Maximum file size in bytes
   * @returns {Object} - Validation result with isValid and message
   */
  validateFile(file, allowedExtensions = [".csv"], maxSize = 10 * 1024 * 1024) {
    if (!file) {
      return { isValid: false, message: "No file selected" };
    }

    const fileExt = "." + file.name.split(".").pop().toLowerCase();
    if (!allowedExtensions.includes(fileExt)) {
      return {
        isValid: false,
        message: `File type not allowed. Allowed types: ${allowedExtensions.join(
          ", "
        )}`,
      };
    }

    if (file.size === 0) {
      return {
        isValid: false,
        message: "File is empty",
      };
    }

    if (file.size > maxSize) {
      return {
        isValid: false,
        message: `File size too large. Maximum size: ${
          maxSize / (1024 * 1024)
        }MB`,
      };
    }

    return { isValid: true, message: "" };
  }

  /**
   * Get detailed username requirements for UI feedback
   * @param {string} username - The username to check
   * @returns {Object} - Object with requirement keys and boolean values
   */
  getUsernameRequirements(username) {
    const value = username.trim();
    return {
      "Length (3-20 characters)": value.length >= 3 && value.length <= 20,
      "Contains only letters, numbers, underscores, hyphens, and periods":
        this.validationRules.username.pattern.test(value),
    };
  }

  /**
   * Get detailed password requirements for UI feedback
   * @param {string} password - The password to check
   * @returns {Object} - Object with requirement keys and boolean values
   */
  getPasswordRequirements(password) {
    const value = password.trim();
    return {
      "Length (at least 3 characters)": value.length >= 3,
      "Contains at least one letter": /[a-zA-Z]/.test(value),
      "Contains at least one number": /\d/.test(value),
    };
  }

  /**
   * Show detailed requirements for a field
   * @param {HTMLElement} field - The input field
   * @param {Object} requirements - Requirements object with keys and boolean values
   */
  showDetailedRequirements(field, requirements) {
    // Remove existing requirements display
    const existingDisplay = field.parentNode.querySelector(
      ".requirements-display"
    );
    if (existingDisplay) {
      existingDisplay.remove();
    }

    // Create requirements display
    const requirementsDiv = document.createElement("div");
    requirementsDiv.className = "requirements-display";
    requirementsDiv.style.cssText = `
      margin-top: 5px;
      font-size: 0.8rem;
    `;

    Object.entries(requirements).forEach(([requirement, isMet]) => {
      const requirementItem = document.createElement("div");
      requirementItem.style.cssText = `
        margin: 2px 0;
        color: ${isMet ? "#28a745" : "#dc3545"};
      `;
      requirementItem.innerHTML = `${isMet ? "✓" : "✗"} ${requirement}`;
      requirementsDiv.appendChild(requirementItem);
    });

    field.parentNode.insertBefore(requirementsDiv, field.nextSibling);
  }

  /**
   * Show success message
   * @param {string} message - Success message to display
   */
  showSuccess(message) {
    this.showNotification(message, "success");
  }

  /**
   * Show error notification
   * @param {string} message - Error message to display
   */
  showErrorNotification(message) {
    this.showNotification(message, "error");
  }

  /**
   * Show notification
   * @param {string} message - Message to display
   * @param {string} type - Type of notification (success, error, warning)
   */
  showNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            max-width: 300px;
            word-wrap: break-word;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            animation: slideIn 0.3s ease-out;
        `;

    // Set background color based on type
    if (type === "success") {
      notification.style.backgroundColor = "#28a745";
    } else if (type === "error") {
      notification.style.backgroundColor = "#dc3545";
    } else if (type === "warning") {
      notification.style.backgroundColor = "#ffc107";
      notification.style.color = "#212529";
    } else {
      notification.style.backgroundColor = "#17a2b8";
    }

    notification.textContent = message;

    // Add to page
    document.body.appendChild(notification);

    // Remove after 5 seconds
    setTimeout(() => {
      notification.style.animation = "slideOut 0.3s ease-in";
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 5000);
  }
}

// Add CSS animations for notifications
const style = document.createElement("style");
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .is-valid {
        border-color: #28a745 !important;
        box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
    }
    
    .is-invalid {
        border-color: #dc3545 !important;
        box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
    }
    
    .validation-error {
        color: #dc3545;
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
`;
document.head.appendChild(style);

// Create global validator instance
window.validator = new ClientValidator();
