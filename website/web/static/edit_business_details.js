///////////// Edit business details page JavaScript functionality /////////////
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

// Get business name from the form action URL
const form = document.querySelector("form");
const businessName = form ? form.action.split("/").pop() : null;
