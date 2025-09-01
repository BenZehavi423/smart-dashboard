// Common UI functions for SmartDashboard

// Custom confirmation dialog function
function showCustomConfirm(message, onConfirm, onCancel) {
  // Create overlay
  const overlay = document.createElement("div");
  overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;

  // Create dialog
  const dialog = document.createElement("div");
  dialog.style.cssText = `
        background: white;
        border-radius: 12px;
        padding: 30px;
        max-width: 400px;
        width: 90%;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        transform: scale(0.9);
        transition: transform 0.3s ease;
        font-family: Arial, sans-serif;
    `;

  dialog.innerHTML = `
        <div style="font-size: 24px; margin-bottom: 20px; color: #dc3545;">⚠️</div>
        <div style="font-size: 18px; font-weight: 600; margin-bottom: 15px; color: #333;">Confirm Action</div>
        <div style="font-size: 14px; color: #666; margin-bottom: 25px; line-height: 1.5;">${message}</div>
        <div style="display: flex; gap: 10px; justify-content: center;">
            <button id="confirmBtn" style="
                background: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: background 0.2s ease;
            " onmouseover="this.style.background='#c82333'" onmouseout="this.style.background='#dc3545'">
                Yes, Continue
            </button>
            <button id="cancelBtn" style="
                background: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: background 0.2s ease;
            " onmouseover="this.style.background='#5a6268'" onmouseout="this.style.background='#6c757d'">
                Cancel
            </button>
        </div>
    `;

  // Add to page
  overlay.appendChild(dialog);
  document.body.appendChild(overlay);

  // Animate in
  setTimeout(() => {
    overlay.style.opacity = "1";
    dialog.style.transform = "scale(1)";
  }, 10);

  // Add event listeners
  const confirmBtn = dialog.querySelector("#confirmBtn");
  const cancelBtn = dialog.querySelector("#cancelBtn");

  function closeDialog() {
    overlay.style.opacity = "0";
    dialog.style.transform = "scale(0.9)";
    setTimeout(() => {
      if (document.body.contains(overlay)) {
        document.body.removeChild(overlay);
      }
    }, 300);
  }

  confirmBtn.addEventListener("click", () => {
    closeDialog();
    if (onConfirm) onConfirm();
  });

  cancelBtn.addEventListener("click", () => {
    closeDialog();
    if (onCancel) onCancel();
  });

  // Close on overlay click
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
      closeDialog();
      if (onCancel) onCancel();
    }
  });

  // Close on Escape key
  const handleEscape = (e) => {
    if (e.key === "Escape") {
      closeDialog();
      if (onCancel) onCancel();
      document.removeEventListener("keydown", handleEscape);
    }
  };
  document.addEventListener("keydown", handleEscape);
}

// Temporary success message function
function showTemporarySuccessMessage(title, message, duration = 3000) {
  // Create success message container
  const successContainer = document.createElement("div");
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
    successContainer.style.transform = "translateX(0)";
  }, 100);

  // Auto-remove after duration
  setTimeout(() => {
    successContainer.style.transform = "translateX(100%)";
    setTimeout(() => {
      if (document.body.contains(successContainer)) {
        document.body.removeChild(successContainer);
      }
    }, 300);
  }, duration);
}

// Navigation interceptor for logged-in users
function setupNavigationInterceptor() {
  // Check if user is logged in by looking for logout link in navbar
  const logoutLink = document.querySelector('a[onclick*="confirmLogout"]');
  if (!logoutLink) return; // User is not logged in

  // Intercept navigation to pages that would log out the user
  const logoutPages = ["/", "/login", "/register"];

  // Intercept clicks on links that would navigate to logout pages
  document.addEventListener("click", function (e) {
    const link = e.target.closest("a");
    if (link && link.href) {
      const url = new URL(link.href);

      // Check if the link would navigate to a logout page
      const isLogoutPage = logoutPages.some((logoutPath) => {
        return url.pathname === logoutPath;
      });

      // Skip if it's already a logout confirmation link
      const isAlreadyLogoutLink =
        link.onclick ||
        link.href.includes("_with_logout") ||
        link.href.includes("logout");

      if (isLogoutPage && !isAlreadyLogoutLink) {
        e.preventDefault();

        // Determine which confirmation to show
        if (url.pathname === "/") {
          if (typeof confirmNavigateToHome === "function") {
            confirmNavigateToHome();
          }
        } else if (url.pathname === "/login") {
          if (typeof confirmNavigateToLogin === "function") {
            confirmNavigateToLogin();
          }
        } else if (url.pathname === "/register") {
          if (typeof confirmNavigateToRegister === "function") {
            confirmNavigateToRegister();
          }
        }
      }
    }
  });

  // Intercept browser back/forward navigation
  window.addEventListener("popstate", function (e) {
    const currentPath = window.location.pathname;
    const isLogoutPage = logoutPages.some((logoutPath) => {
      return currentPath === logoutPath;
    });

    if (isLogoutPage) {
      // Prevent the navigation and show confirmation
      e.preventDefault();

      // Determine which confirmation to show
      if (currentPath === "/") {
        if (typeof confirmNavigateToHome === "function") {
          confirmNavigateToHome();
        }
      } else if (currentPath === "/login") {
        if (typeof confirmNavigateToLogin === "function") {
          confirmNavigateToLogin();
        }
      } else if (currentPath === "/register") {
        if (typeof confirmNavigateToRegister === "function") {
          confirmNavigateToRegister();
        }
      }
    }
  });

  // Intercept direct URL navigation (when user types URL in address bar)
  // This is handled by the beforeunload event
  window.addEventListener("beforeunload", function (e) {
    const currentPath = window.location.pathname;
    const isLogoutPage = logoutPages.some((logoutPath) => {
      return currentPath === logoutPath;
    });

    if (isLogoutPage) {
      // Show a generic confirmation message
      e.preventDefault();
      e.returnValue =
        "You will be logged out when visiting this page. Are you sure you want to continue?";
      return e.returnValue;
    }
  });
}

// Initialize navigation interceptor when page loads
document.addEventListener("DOMContentLoaded", setupNavigationInterceptor);
